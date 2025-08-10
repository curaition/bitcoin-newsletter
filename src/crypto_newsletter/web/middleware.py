"""FastAPI middleware for logging and monitoring."""

import time
from typing import Callable

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} in {process_time:.3f}s",
                extra={
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "path": request.url.path,
                }
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {e}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "process_time": process_time,
                }
            )
            
            raise


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Middleware for health check optimization."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Optimize health check requests."""
        # Skip detailed logging for health checks
        if request.url.path.startswith("/health/"):
            return await call_next(request)
        
        return await call_next(request)
