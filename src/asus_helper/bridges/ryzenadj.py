"""Bridge for ryzenadj - AMD CPU power management."""

import re
from typing import Any

from asus_helper.bridges.base import Bridge


class RyzenadjBridge(Bridge):
    """Bridge for ryzenadj CLI tool.

    Provides control over AMD Ryzen CPU power limits:
    - STAPM limit (sustained power)
    - Fast limit (boost power)
    - Slow limit (avg power)
    - Temperature limit
    """

    COMMAND = "ryzenadj"
    REQUIRES_ROOT = True

    def get_current_state(self) -> dict[str, Any]:
        """Get current CPU power state.

        Note: ryzenadj -i requires root to read values.
        """
        state: dict[str, Any] = {
            "stapm_limit": None,
            "fast_limit": None,
            "slow_limit": None,
            "tctl_temp": None,
        }

        if not self.is_available:
            return state

        try:
            result = self.run("-i", check=False)
            if result.returncode == 0:
                # Parse output like:
                # STAPM LIMIT: 45.000 W
                # PPT LIMIT FAST: 65.000 W
                # PPT LIMIT SLOW: 54.000 W
                # THM LIMIT CORE: 95.000 C

                stapm = re.search(r"STAPM LIMIT\s*:\s*([\d.]+)", result.stdout)
                if stapm:
                    state["stapm_limit"] = int(float(stapm.group(1)))

                fast = re.search(r"PPT LIMIT FAST\s*:\s*([\d.]+)", result.stdout)
                if fast:
                    state["fast_limit"] = int(float(fast.group(1)))

                slow = re.search(r"PPT LIMIT SLOW\s*:\s*([\d.]+)", result.stdout)
                if slow:
                    state["slow_limit"] = int(float(slow.group(1)))

                tctl = re.search(r"THM LIMIT CORE\s*:\s*([\d.]+)", result.stdout)
                if tctl:
                    state["tctl_temp"] = int(float(tctl.group(1)))
        except Exception:
            pass

        return state

    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply CPU power settings."""
        if not self.is_available:
            return

        args = []

        if "cpu_tdp" in settings:
            # Set both STAPM and fast/slow limits
            tdp = int(settings["cpu_tdp"])
            args.extend(
                [
                    f"--stapm-limit={tdp * 1000}",  # milliwatts
                    f"--fast-limit={int(tdp * 1.3) * 1000}",  # 30% boost headroom
                    f"--slow-limit={tdp * 1000}",
                ]
            )

        if "cpu_temp_limit" in settings:
            temp = int(settings["cpu_temp_limit"])
            args.append(f"--tctl-temp={temp}")

        if args:
            try:
                self.run(*args, check=False)
            except Exception:
                pass

    def set_power_limit(
        self,
        stapm_watts: int,
        fast_watts: int | None = None,
        slow_watts: int | None = None,
    ) -> bool:
        """Set CPU power limits.

        Args:
            stapm_watts: Sustained power limit in watts.
            fast_watts: Fast boost limit in watts (default: stapm * 1.3).
            slow_watts: Slow limit in watts (default: stapm).

        Returns:
            True if successful.
        """
        if not self.is_available:
            return False

        fast_watts = fast_watts or int(stapm_watts * 1.3)
        slow_watts = slow_watts or stapm_watts

        try:
            self.run(
                f"--stapm-limit={stapm_watts * 1000}",
                f"--fast-limit={fast_watts * 1000}",
                f"--slow-limit={slow_watts * 1000}",
            )
            return True
        except Exception:
            return False

    def set_sustained_limit(self, watts: int) -> bool:
        """Set sustained power limit (STAPM)."""
        if not self.is_available:
            return False
        try:
            self.run(f"--stapm-limit={watts * 1000}")
            return True
        except Exception:
            return False

    def set_short_limit(self, watts: int) -> bool:
        """Set short boost power limit (slow limit)."""
        if not self.is_available:
            return False
        try:
            self.run(f"--slow-limit={watts * 1000}")
            return True
        except Exception:
            return False

    def set_fast_limit(self, watts: int) -> bool:
        """Set fast boost power limit."""
        if not self.is_available:
            return False
        try:
            self.run(f"--fast-limit={watts * 1000}")
            return True
        except Exception:
            return False

    def set_temp_limit(self, celsius: int) -> bool:
        """Set CPU temperature limit.

        Args:
            celsius: Temperature limit in Celsius.

        Returns:
            True if successful.
        """
        if not self.is_available:
            return False

        try:
            self.run(f"--tctl-temp={celsius}")
            return True
        except Exception:
            return False
