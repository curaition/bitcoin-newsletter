#!/usr/bin/env python3
"""
Multi-process manager for crypto newsletter application.
Manages web server, Celery worker, and Celery beat scheduler in a single container.
"""

import subprocess
import signal
import sys
import os
import time
import logging
from typing import List, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('process_manager')


class ProcessManager:
    """Manages multiple processes with proper signal handling and cleanup."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.shutdown_requested = False
        
    def signal_handler(self, sig: int, frame) -> None:
        """Handle shutdown signals gracefully."""
        signal_name = signal.Signals(sig).name
        logger.info(f"Received signal {signal_name} ({sig}), initiating graceful shutdown...")
        self.shutdown_requested = True
        self.shutdown_processes()
        
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def start_process(self, name: str, command: List[str], fallback_command: Optional[List[str]] = None) -> Optional[subprocess.Popen]:
        """Start a subprocess and add it to the managed processes list."""
        try:
            logger.info(f"Starting {name} process with command: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1  # Line buffered
            )
            self.processes.append(process)
            logger.info(f"Started {name} process with PID: {process.pid}")
            return process
        except Exception as e:
            logger.error(f"Failed to start {name} process with primary command: {e}")

            # Try fallback command if provided
            if fallback_command:
                try:
                    logger.info(f"Trying fallback command for {name}: {' '.join(fallback_command)}")
                    process = subprocess.Popen(
                        fallback_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1  # Line buffered
                    )
                    self.processes.append(process)
                    logger.info(f"Started {name} process with fallback command, PID: {process.pid}")
                    return process
                except Exception as fallback_e:
                    logger.error(f"Fallback command also failed for {name}: {fallback_e}")

            return None
            
    def shutdown_processes(self) -> None:
        """Shutdown all managed processes gracefully."""
        if not self.processes:
            logger.info("No processes to shutdown")
            return
            
        logger.info("Terminating processes...")
        
        # Send TERM signal to all processes
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                try:
                    logger.info(f"Terminating process {process.pid}")
                    process.terminate()
                except Exception as e:
                    logger.error(f"Error terminating process {process.pid}: {e}")
        
        # Wait for graceful shutdown
        logger.info("Waiting for processes to terminate gracefully...")
        time.sleep(5)
        
        # Force kill any remaining processes
        for process in self.processes:
            if process.poll() is None:
                try:
                    logger.warning(f"Force killing process {process.pid}")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error killing process {process.pid}: {e}")
        
        # Wait for all processes to finish
        for process in self.processes:
            try:
                process.wait(timeout=2)
                logger.info(f"Process {process.pid} terminated with exit code {process.returncode}")
            except subprocess.TimeoutExpired:
                logger.error(f"Process {process.pid} did not terminate within timeout")
                
        logger.info("All processes terminated")
        
    def start_all_processes(self) -> bool:
        """Start all application processes."""
        port = os.getenv("PORT", "8000")

        # Start web server FIRST - this is critical for Railway health checks
        logger.info("Starting web server first for Railway health checks...")

        # Try UV first, fallback to direct uvicorn if UV fails
        web_cmd = [
            "uv", "run", "--frozen", "uvicorn", "crypto_newsletter.web.main:app",
            "--host", "0.0.0.0", "--port", port, "--timeout-keep-alive", "30"
        ]

        # Fallback command using system python and uvicorn
        web_fallback_cmd = [
            "python", "-m", "uvicorn", "crypto_newsletter.web.main:app",
            "--host", "0.0.0.0", "--port", port, "--timeout-keep-alive", "30"
        ]

        web_process = self.start_process("web-server", web_cmd, web_fallback_cmd)
        if not web_process:
            logger.error("Failed to start web server - this is critical for Railway")
            return False

        # Give web server time to start before starting background processes
        logger.info("Waiting for web server to initialize...")
        time.sleep(10)

        # Check if web server is still running
        if web_process.poll() is not None:
            logger.error(f"Web server died during startup with exit code {web_process.returncode}")

            # Capture and log the error output
            try:
                stdout, stderr = web_process.communicate(timeout=1)
                if stdout:
                    logger.error(f"Web server stdout: {stdout}")
                if stderr:
                    logger.error(f"Web server stderr: {stderr}")
            except Exception as e:
                logger.error(f"Failed to capture web server output: {e}")

            return False

        # Start Celery worker
        logger.info("Starting Celery worker...")
        worker_cmd = [
            "uv", "run", "--frozen", "celery", "-A", "crypto_newsletter.shared.celery.app",
            "worker", "--loglevel=WARNING", "--concurrency=2",
            "--queues=default,ingestion,monitoring,maintenance"
        ]
        worker_process = self.start_process("celery-worker", worker_cmd)
        if not worker_process:
            logger.warning("Failed to start Celery worker - continuing anyway")

        # Start Celery beat scheduler
        logger.info("Starting Celery beat scheduler...")
        beat_cmd = [
            "uv", "run", "--frozen", "celery", "-A", "crypto_newsletter.shared.celery.app",
            "beat", "--loglevel=WARNING", "--pidfile="
        ]
        beat_process = self.start_process("celery-beat", beat_cmd)
        if not beat_process:
            logger.warning("Failed to start Celery beat - continuing anyway")

        return True
        
    def monitor_processes(self) -> None:
        """Monitor processes and handle failures."""
        logger.info("Starting process monitoring...")

        while not self.shutdown_requested:
            try:
                # Check if any process has died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        process_name = "unknown"
                        if i == 0:
                            process_name = "web-server"
                        elif i == 1:
                            process_name = "celery-worker"
                        elif i == 2:
                            process_name = "celery-beat"

                        logger.error(f"Process {process_name} (PID {process.pid}) has died with exit code {process.returncode}")

                        # Only shutdown everything if the web server dies
                        # Celery processes can fail without killing the whole service
                        if process_name == "web-server":
                            logger.error("Web server has died - this is critical for Railway, shutting down all processes")
                            self.shutdown_requested = True
                            break
                        else:
                            logger.warning(f"{process_name} has died but web server is still running - continuing")

                if self.shutdown_requested:
                    break

                # Sleep before next check
                time.sleep(5)  # Check less frequently to reduce log noise

            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt")
                self.shutdown_requested = True
                break
            except Exception as e:
                logger.error(f"Error in process monitoring: {e}")
                time.sleep(5)

        self.shutdown_processes()
        
    def run(self) -> int:
        """Main entry point to start and manage all processes."""
        logger.info("Starting Crypto Newsletter application...")

        # Debug environment
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"PATH: {os.environ.get('PATH', 'Not set')}")
        logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")

        # Set up signal handlers
        self.setup_signal_handlers()
        
        try:
            # Start all processes
            if not self.start_all_processes():
                logger.error("Failed to start all processes")
                return 1
                
            logger.info("All processes started successfully")
            
            # Monitor processes
            self.monitor_processes()
            
            logger.info("Process manager shutting down")
            return 0
            
        except Exception as e:
            logger.error(f"Unexpected error in process manager: {e}")
            self.shutdown_processes()
            return 1


def main() -> int:
    """Main entry point."""
    manager = ProcessManager()
    return manager.run()


if __name__ == "__main__":
    sys.exit(main())
