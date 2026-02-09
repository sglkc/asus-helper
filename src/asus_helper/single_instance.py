"""Single instance handling to prevent duplicate app instances."""

import fcntl
import os
import sys
import signal
from pathlib import Path

from asus_helper.logging import get_logger

log = get_logger("single_instance")


class SingleInstance:
    """Ensures only one instance of the app runs at a time.

    Uses a lock file with fcntl for atomic locking.
    Sends SIGUSR1 to existing instance to bring it to foreground.
    """

    LOCK_FILE = Path("/tmp/asus-helper.lock")

    def __init__(self) -> None:
        self._lock_fd: int | None = None

    def try_acquire(self) -> bool:
        """Try to acquire the singleton lock.

        Returns:
            True if lock acquired (we are the only instance).
            False if another instance is running.
        """
        try:
            self._lock_fd = os.open(str(self.LOCK_FILE), os.O_CREAT | os.O_RDWR, 0o600)
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Write our PID to the lock file
            os.ftruncate(self._lock_fd, 0)
            os.write(self._lock_fd, str(os.getpid()).encode())
            log.debug(
                "Lock acquired, PID %d written to %s", os.getpid(), self.LOCK_FILE
            )
            return True
        except (OSError, IOError) as e:
            log.debug("Could not acquire lock: %s", e)
            # Lock is held by another process
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None
            return False

    def signal_existing_instance(self) -> bool:
        """Signal the existing instance to show its window.

        Returns:
            True if signal was sent successfully.
        """
        try:
            with open(self.LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGUSR1)
            log.info("Sent SIGUSR1 to existing instance (PID %d)", pid)
            return True
        except (
            FileNotFoundError,
            ValueError,
            ProcessLookupError,
            PermissionError,
        ) as e:
            log.warning("Could not signal existing instance: %s", e)
            return False

    def release(self) -> None:
        """Release the lock."""
        if self._lock_fd is not None:
            try:
                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                os.close(self._lock_fd)
                self.LOCK_FILE.unlink(missing_ok=True)
                log.debug("Lock released")
            except OSError as e:
                log.warning("Error releasing lock: %s", e)
            self._lock_fd = None


def ensure_single_instance() -> SingleInstance:
    """Ensure only one instance is running.

    If another instance is running, signals it and exits.

    Returns:
        The SingleInstance object (must be kept alive).
    """
    instance = SingleInstance()

    if not instance.try_acquire():
        # Another instance is running - signal it and exit
        log.info("Another instance is running")
        if instance.signal_existing_instance():
            log.info("Signaled existing instance to show window")
        else:
            log.warning("Could not signal existing instance")
        sys.exit(0)

    return instance
