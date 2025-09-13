"""
Process management utilities for safe subprocess handling.
"""

import os
import signal
import subprocess
import threading
import time
from typing import Optional, Tuple, List
import psutil

from backend.utils.logging import get_logger
from backend.core.exceptions import ErrorCode, RecordingException


logger = get_logger(__name__)


class ProcessManager:
    """Safe process manager with timeout and cleanup capabilities."""

    def __init__(self, timeout: Optional[int] = None):
        self.timeout = timeout or 3600  # 1 hour default
        self.process: Optional[subprocess.Popen] = None
        self.pid: Optional[int] = None
        self.is_terminated = False

    def run_command(
        self, cmd: List[str], cwd: Optional[str] = None, env: Optional[dict] = None
    ) -> Tuple[int, str, str]:
        """
        Run command with timeout and proper cleanup.

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        logger.info(
            "Starting subprocess",
            extra={
                "command": " ".join(cmd[:3]) + "..." if len(cmd) > 3 else " ".join(cmd),
                "timeout": self.timeout,
                "cwd": cwd,
            },
        )

        try:
            # Start process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=env,
                preexec_fn=(
                    os.setsid if os.name != "nt" else None
                ),  # Create process group
            )
            self.pid = self.process.pid

            # Start watchdog thread
            watchdog = threading.Thread(target=self._watchdog, daemon=True)
            watchdog.start()

            # Wait for completion
            stdout, stderr = self.process.communicate()
            returncode = self.process.returncode

            logger.info(
                "Subprocess completed",
                extra={
                    "pid": self.pid,
                    "returncode": returncode,
                    "stdout_length": len(stdout) if stdout else 0,
                    "stderr_length": len(stderr) if stderr else 0,
                },
            )

            return returncode, stdout, stderr

        except subprocess.TimeoutExpired:
            logger.error(
                "Process timeout exceeded",
                extra={"pid": self.pid, "timeout": self.timeout},
            )
            self.terminate()
            raise RecordingException(
                "Process timeout exceeded",
                ErrorCode.NETWORK_TIMEOUT,
                details={"timeout": self.timeout},
            )

        except Exception as e:
            logger.exception("Process execution failed", extra={"pid": self.pid})
            self.terminate()
            raise RecordingException(
                f"Process execution failed: {str(e)}",
                ErrorCode.INTERNAL_ERROR,
                details={"error": str(e)},
            )

        finally:
            self.cleanup()

    def _watchdog(self):
        """Watchdog thread to monitor process health."""
        if not self.process:
            return

        start_time = time.time()
        while self.process and self.process.poll() is None:
            elapsed = time.time() - start_time

            if elapsed > self.timeout:
                logger.warning(
                    "Watchdog triggering timeout",
                    extra={
                        "pid": self.pid,
                        "elapsed": elapsed,
                        "timeout": self.timeout,
                    },
                )
                self.terminate()
                break

            time.sleep(5)  # Check every 5 seconds

    def terminate(self):
        """Gracefully terminate the process and its children."""
        if self.is_terminated or not self.process:
            return

        self.is_terminated = True

        try:
            # Get process tree
            parent = psutil.Process(self.pid)
            children = parent.children(recursive=True)

            logger.info(
                "Terminating process tree",
                extra={"parent_pid": self.pid, "children_count": len(children)},
            )

            # Terminate children first
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass

            # Terminate parent
            parent.terminate()

            # Wait for graceful termination
            try:
                parent.wait(timeout=10)
            except psutil.TimeoutExpired:
                # Force kill if still alive
                logger.warning("Force killing process", extra={"pid": self.pid})
                for child in children:
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                parent.kill()

        except psutil.NoSuchProcess:
            # Process already terminated
            logger.info("Process already terminated", extra={"pid": self.pid})
        except Exception as e:
            logger.exception("Failed to terminate process", extra={"pid": self.pid})

    def cleanup(self):
        """Clean up resources."""
        if self.process:
            try:
                if self.process.poll() is None:
                    self.terminate()
            finally:
                self.process = None
                self.pid = None
                self.is_terminated = False


# Global process registry for tracking active processes
_active_processes = {}


def register_process(task_id: str, process_manager: ProcessManager):
    """Register active process for tracking."""
    _active_processes[task_id] = process_manager


def unregister_process(task_id: str):
    """Unregister process."""
    _active_processes.pop(task_id, None)


def cleanup_task_processes(task_id: str):
    """Clean up processes for a specific task."""
    process_manager = _active_processes.get(task_id)
    if process_manager:
        process_manager.terminate()
        unregister_process(task_id)


def cleanup_all_processes():
    """Emergency cleanup of all active processes."""
    logger.warning(
        "Cleaning up all active processes",
        extra={"active_count": len(_active_processes)},
    )

    for task_id, process_manager in list(_active_processes.items()):
        try:
            process_manager.terminate()
        except Exception as e:
            logger.exception(
                "Failed to cleanup process", extra={"task_id": task_id, "error": str(e)}
            )

    _active_processes.clear()
