"""Centralized logging configuration for the crypto newsletter application."""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime

from loguru import logger
from crypto_newsletter.shared.config.settings import get_settings


class LoggingConfig:
    """Centralized logging configuration manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self._configured = False
    
    def configure(self) -> None:
        """Configure logging for the application."""
        if self._configured:
            return
        
        # Remove default handler
        logger.remove()
        
        # Configure based on environment
        if self.settings.is_production:
            self._configure_production()
        else:
            self._configure_development()
        
        # Add common handlers
        self._add_file_handlers()
        self._configure_external_loggers()
        
        self._configured = True
        logger.info("Logging configuration initialized", extra={
            "environment": self.settings.railway_environment,
            "log_level": self.settings.log_level,
            "service_type": self.settings.service_type
        })
    
    def _configure_production(self) -> None:
        """Configure logging for production environment."""
        # Simple structured logging for production (avoid Loguru recursion issues)
        logger.add(
            sys.stdout,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level=self.settings.log_level,
            serialize=False,  # Disable JSON serialization to avoid recursion
            backtrace=False,
            diagnose=False,
            enqueue=True,
            catch=True
        )
    
    def _configure_development(self) -> None:
        """Configure logging for development environment."""
        # Colorized console logging for development
        logger.add(
            sys.stderr,
            format=self._get_console_formatter(),
            level=self.settings.log_level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            enqueue=False,
            catch=True
        )
    
    def _add_file_handlers(self) -> None:
        """Add file-based logging handlers."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Application log file
        logger.add(
            log_dir / "app.log",
            format=self._get_file_formatter(),
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # Error log file
        logger.add(
            log_dir / "error.log",
            format=self._get_file_formatter(),
            level="ERROR",
            rotation="5 MB",
            retention="90 days",
            compression="gz",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        # Service-specific log file
        if self.settings.service_type:
            logger.add(
                log_dir / f"{self.settings.service_type}.log",
                format=self._get_file_formatter(),
                level="DEBUG",
                rotation="5 MB",
                retention="7 days",
                compression="gz",
                enqueue=True,
                filter=lambda record: record.get("extra", {}).get("service_type") == self.settings.service_type
            )
    
    def _configure_external_loggers(self) -> None:
        """Configure external library loggers."""
        import logging
        
        # Intercept standard library logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # Get corresponding Loguru level if it exists
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                
                # Find caller from where originated the logged message
                frame, depth = logging.currentframe(), 2
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                
                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )
        
        # Replace handlers for specific loggers
        loggers_to_intercept = [
            "uvicorn",
            "uvicorn.access",
            "fastapi",
            "sqlalchemy.engine",
            "celery",
            "redis",
            "httpx",
            "alembic"
        ]
        
        for logger_name in loggers_to_intercept:
            logging.getLogger(logger_name).handlers = [InterceptHandler()]
            logging.getLogger(logger_name).setLevel(logging.INFO)
    
    def _get_console_formatter(self) -> str:
        """Get console log format for development."""
        return (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    def _get_file_formatter(self) -> str:
        """Get file log format."""
        return (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            f"{self.settings.service_type or 'unknown'} | "
            "{message}"
        )
    
    def _get_json_formatter(self) -> str:
        """Get JSON log format for production."""
        def json_formatter(record):
            """Custom JSON formatter for structured logging."""
            log_entry = {
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "function": record["function"],
                "line": record["line"],
                "message": record["message"],
                "service": self.settings.service_type,
                "environment": self.settings.railway_environment,
            }
            
            # Add extra fields
            if record["extra"]:
                log_entry["extra"] = record["extra"]
            
            # Add exception info if present
            if record["exception"]:
                log_entry["exception"] = {
                    "type": record["exception"].type.__name__,
                    "value": str(record["exception"].value),
                    "traceback": record["exception"].traceback
                }
            
            return json.dumps(log_entry)
        
        return json_formatter


# Global logging configuration instance
_logging_config = LoggingConfig()


def configure_logging() -> None:
    """Configure application logging."""
    _logging_config.configure()


def get_logger(name: str) -> Any:
    """Get a logger instance with the specified name."""
    return logger.bind(service=get_settings().service_type, logger_name=name)


# Context managers for structured logging
class LogContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, **context):
        self.context = context
        self.token = None
    
    def __enter__(self):
        self.token = logger.contextualize(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            self.token.__exit__(exc_type, exc_val, exc_tb)


class RequestLogContext(LogContext):
    """Context manager for HTTP request logging."""
    
    def __init__(self, method: str, path: str, client_ip: Optional[str] = None, **kwargs):
        super().__init__(
            request_method=method,
            request_path=path,
            client_ip=client_ip,
            **kwargs
        )


class TaskLogContext(LogContext):
    """Context manager for Celery task logging."""
    
    def __init__(self, task_name: str, task_id: str, **kwargs):
        super().__init__(
            task_name=task_name,
            task_id=task_id,
            **kwargs
        )


# Utility functions for common logging patterns
def log_function_call(func_name: str, **kwargs):
    """Log function call with parameters."""
    logger.debug(f"Calling function: {func_name}", extra={
        "function_name": func_name,
        "parameters": kwargs
    })


def log_database_operation(operation: str, table: str, **kwargs):
    """Log database operation."""
    logger.debug(f"Database operation: {operation} on {table}", extra={
        "db_operation": operation,
        "db_table": table,
        **kwargs
    })


def log_api_call(url: str, method: str, status_code: Optional[int] = None, **kwargs):
    """Log external API call."""
    logger.info(f"API call: {method} {url}", extra={
        "api_url": url,
        "api_method": method,
        "api_status_code": status_code,
        **kwargs
    })


def log_performance_metric(metric_name: str, value: float, unit: str = "ms", **kwargs):
    """Log performance metric."""
    logger.info(f"Performance metric: {metric_name} = {value}{unit}", extra={
        "metric_name": metric_name,
        "metric_value": value,
        "metric_unit": unit,
        **kwargs
    })


def log_business_event(event_name: str, **kwargs):
    """Log business event for analytics."""
    logger.info(f"Business event: {event_name}", extra={
        "event_name": event_name,
        "event_timestamp": datetime.utcnow().isoformat(),
        **kwargs
    })


# Error logging utilities
def log_error_with_context(error: Exception, context: Dict[str, Any], **kwargs):
    """Log error with additional context."""
    logger.error(f"Error occurred: {str(error)}", extra={
        "error_type": type(error).__name__,
        "error_message": str(error),
        "error_context": context,
        **kwargs
    })


def log_validation_error(field: str, value: Any, reason: str, **kwargs):
    """Log validation error."""
    logger.warning(f"Validation error: {field} = {value} - {reason}", extra={
        "validation_field": field,
        "validation_value": str(value),
        "validation_reason": reason,
        **kwargs
    })


# Security logging
def log_security_event(event_type: str, severity: str = "INFO", **kwargs):
    """Log security-related event."""
    logger.log(severity, f"Security event: {event_type}", extra={
        "security_event_type": event_type,
        "security_severity": severity,
        **kwargs
    })


def log_rate_limit_exceeded(client_ip: str, endpoint: str, **kwargs):
    """Log rate limit exceeded event."""
    log_security_event(
        "RATE_LIMIT_EXCEEDED",
        severity="WARNING",
        client_ip=client_ip,
        endpoint=endpoint,
        **kwargs
    )
