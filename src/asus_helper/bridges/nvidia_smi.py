"""Bridge for nvidia-smi - NVIDIA GPU management."""

import re
from typing import Any

from asus_helper.bridges.base import Bridge


class NvidiaSMIBridge(Bridge):
    """Bridge for nvidia-smi CLI tool.
    
    Provides control over NVIDIA GPU:
    - GPU clock limits (min/max)
    - Temperature limit
    - Power limit
    """
    
    COMMAND = "nvidia-smi"
    
    def get_current_state(self) -> dict[str, Any]:
        """Get current GPU state."""
        state: dict[str, Any] = {
            "gpu_clock_current": None,
            "gpu_clock_max": None,
            "gpu_temp": None,
            "gpu_power": None,
            "gpu_name": None,
        }
        
        if not self.is_available:
            return state
        
        try:
            # Query GPU info
            result = self.run(
                "--query-gpu=name,clocks.gr,clocks.max.gr,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
                check=False,
            )
            if result.returncode == 0:
                parts = [p.strip() for p in result.stdout.strip().split(",")]
                if len(parts) >= 5:
                    state["gpu_name"] = parts[0]
                    state["gpu_clock_current"] = int(parts[1]) if parts[1].isdigit() else None
                    state["gpu_clock_max"] = int(parts[2]) if parts[2].isdigit() else None
                    state["gpu_temp"] = int(parts[3]) if parts[3].isdigit() else None
                    try:
                        state["gpu_power"] = float(parts[4])
                    except ValueError:
                        pass
        except Exception:
            pass
        
        return state
    
    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply GPU settings."""
        if not self.is_available:
            return
        
        # Enable persistence mode first (needed for some settings)
        self.run("-pm", "1", check=False)
        
        # Lock GPU clocks
        if "gpu_clock_min" in settings and "gpu_clock_max" in settings:
            self.set_clock_limits(
                settings["gpu_clock_min"],
                settings["gpu_clock_max"],
            )
        
        # Set temperature limit
        if "gpu_temp_limit" in settings:
            self.set_temp_limit(settings["gpu_temp_limit"])
    
    def set_clock_limits(self, min_mhz: int, max_mhz: int) -> bool:
        """Lock GPU clock to a specific range.
        
        Args:
            min_mhz: Minimum clock speed in MHz.
            max_mhz: Maximum clock speed in MHz.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        try:
            self.run("-lgc", f"{min_mhz},{max_mhz}")
            return True
        except Exception:
            return False
    
    def reset_clocks(self) -> bool:
        """Reset GPU clocks to default.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        try:
            self.run("-rgc")
            return True
        except Exception:
            return False
    
    def set_temp_limit(self, celsius: int) -> bool:
        """Set GPU temperature target.
        
        Args:
            celsius: Temperature limit in Celsius.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        try:
            # Set thermal throttle temperature
            self.run("-gtt", str(celsius))
            return True
        except Exception:
            return False
    
    def set_power_limit(self, watts: int) -> bool:
        """Set GPU power limit.
        
        Args:
            watts: Power limit in watts.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        try:
            self.run("-pl", str(watts))
            return True
        except Exception:
            return False
