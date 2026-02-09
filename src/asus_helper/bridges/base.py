"""Base class for CLI bridges."""

import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Any

from asus_helper.logging import get_logger


class Bridge(ABC):
    """Abstract base class for CLI tool bridges.

    Each bridge wraps a specific CLI tool (asusctl, ryzenadj, etc.)
    and provides a Python interface to its functionality.
    """

    # Override in subclasses with the CLI command name
    COMMAND: str = ""

    # Set to True if this tool requires root privileges
    REQUIRES_ROOT: bool = False

    def __init__(self) -> None:
        self._available: bool | None = None
        self._log = get_logger(f"bridge.{self.COMMAND or 'base'}")
        self._is_root = os.geteuid() == 0
        self._pkexec_available: bool | None = None

    @property
    def is_available(self) -> bool:
        """Check if the CLI tool is available on the system."""
        if self._available is None:
            self._available = shutil.which(self.COMMAND) is not None
            self._log.debug(
                "Availability check: %s", "found" if self._available else "not found"
            )
        return self._available

    @property
    def _has_pkexec(self) -> bool:
        """Check if pkexec is available."""
        if self._pkexec_available is None:
            self._pkexec_available = shutil.which("pkexec") is not None
        return self._pkexec_available

    def _needs_privilege_escalation(self) -> bool:
        """Check if we need to use pkexec for this bridge."""
        return self.REQUIRES_ROOT and not self._is_root

    def run(
        self, *args: str, check: bool = True, capture: bool = True
    ) -> subprocess.CompletedProcess:
        """Run the CLI command with given arguments.

        Args:
            *args: Arguments to pass to the command.
            check: Raise exception on non-zero exit code.
            capture: Capture stdout/stderr.

        Returns:
            CompletedProcess with output.

        Raises:
            RuntimeError: If the tool is not available.
            subprocess.CalledProcessError: If check=True and command fails.
        """
        if not self.is_available:
            self._log.error("Command not available: %s", self.COMMAND)
            raise RuntimeError(f"{self.COMMAND} is not available")

        # Build command with optional privilege escalation
        if self._needs_privilege_escalation() and self._has_pkexec:
            cmd = ["pkexec", self.COMMAND, *args]
            self._log.debug("Running (via pkexec): %s", " ".join(cmd[1:]))
        else:
            cmd = [self.COMMAND, *args]
            self._log.debug("Running: %s", " ".join(cmd))

        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
        )

        if result.returncode != 0:
            # Check for pkexec auth cancelled
            if result.returncode == 126:
                self._log.warning("Authentication cancelled by user")
            else:
                self._log.warning(
                    "Command failed (exit %d): %s",
                    result.returncode,
                    result.stderr.strip() if result.stderr else "",
                )
        else:
            self._log.debug(
                "Command succeeded: %s",
                result.stdout.strip()[:100] if result.stdout else "(no output)",
            )

        return result

    @abstractmethod
    def get_current_state(self) -> dict[str, Any]:
        """Get the current state/settings from the tool.

        Returns:
            Dict with current settings. Keys depend on the specific bridge.
        """
        ...

    @abstractmethod
    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply settings using the tool.

        Args:
            settings: Dict with settings to apply. Keys depend on the specific bridge.
        """
        ...
