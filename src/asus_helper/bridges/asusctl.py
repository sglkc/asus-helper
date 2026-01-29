"""Bridge for asusctl - ASUS laptop control daemon."""

import re
from typing import Any

from asus_helper.bridges.base import Bridge


class AsusctlBridge(Bridge):
    """Bridge for asusctl CLI tool.
    
    Provides control over:
    - Power profiles (quiet, balanced, performance)
    - Keyboard backlight (brightness, color, mode)
    - Fan curves
    """
    
    COMMAND = "asusctl"
    
    # Power profiles supported by asusctl
    POWER_PROFILES = ["quiet", "balanced", "performance"]
    
    def get_current_state(self) -> dict[str, Any]:
        """Get current asusctl state."""
        state: dict[str, Any] = {
            "power_profile": None,
            "keyboard_brightness": None,
        }
        
        if not self.is_available:
            return state
        
        try:
            # Get power profile
            result = self.run("profile", "-p", check=False)
            if result.returncode == 0:
                # Output like "Active profile is balanced"
                match = re.search(r"Active profile is (\w+)", result.stdout)
                if match:
                    state["power_profile"] = match.group(1).lower()
            
            # Get keyboard brightness
            result = self.run("-k", check=False)
            if result.returncode == 0:
                # Parse keyboard state
                match = re.search(r"brightness:\s*(\d+)", result.stdout.lower())
                if match:
                    state["keyboard_brightness"] = int(match.group(1))
        except Exception:
            pass
        
        return state
    
    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply asusctl settings."""
        if not self.is_available:
            return
        
        if "power_profile" in settings:
            profile = settings["power_profile"]
            if profile in self.POWER_PROFILES:
                self.run("profile", "-P", profile, check=False)
        
        if "keyboard_brightness" in settings:
            brightness = settings["keyboard_brightness"]
            if 0 <= brightness <= 3:
                self.run("-k", str(brightness), check=False)
    
    def set_power_profile(self, profile: str) -> bool:
        """Set power profile.
        
        Args:
            profile: One of 'quiet', 'balanced', 'performance'.
        
        Returns:
            True if successful.
        """
        if not self.is_available or profile not in self.POWER_PROFILES:
            return False
        
        try:
            self.run("profile", "-P", profile)
            return True
        except Exception:
            return False
    
    def set_keyboard_brightness(self, level: int) -> bool:
        """Set keyboard backlight brightness.
        
        Args:
            level: Brightness level 0-3.
        
        Returns:
            True if successful.
        """
        if not self.is_available or not 0 <= level <= 3:
            return False
        
        try:
            self.run("-k", str(level))
            return True
        except Exception:
            return False
    
    def get_power_profile(self) -> str | None:
        """Get current power profile."""
        state = self.get_current_state()
        return state.get("power_profile")
