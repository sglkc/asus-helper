"""Bridge for asusctl - ASUS laptop control daemon."""

import re
from typing import Any

from asus_helper.bridges.base import Bridge


class AsusctlBridge(Bridge):
    """Bridge for asusctl CLI tool.
    
    Provides control over:
    - Power profiles (LowPower, Balanced, Performance)
    - Keyboard LED brightness (off, low, med, high)
    - Armoury attributes (CPU power limits, GPU temp target, etc.)
    - Battery charge limit
    - Fan curves
    """
    
    COMMAND = "asusctl"
    
    # Power profiles supported by asusctl
    POWER_PROFILES = ["LowPower", "Balanced", "Performance"]
    
    # Keyboard brightness levels
    LED_LEVELS = ["off", "low", "med", "high"]
    
    def get_current_state(self) -> dict[str, Any]:
        """Get current asusctl state."""
        state: dict[str, Any] = {
            "power_profile": None,
            "keyboard_brightness": None,
            "battery_limit": None,
            "armoury": {},
        }
        
        if not self.is_available:
            return state
        
        # Get power profile
        try:
            result = self.run("profile", "get", check=False)
            if result.returncode == 0:
                # Output: "Active profile: LowPower"
                match = re.search(r"Active profile:\s*(\w+)", result.stdout)
                if match:
                    state["power_profile"] = match.group(1)
        except Exception:
            pass
        
        # Get keyboard brightness
        try:
            result = self.run("leds", "get", check=False)
            if result.returncode == 0:
                # Output: "Current keyboard led brightness: Off"
                match = re.search(r"brightness:\s*(\w+)", result.stdout, re.IGNORECASE)
                if match:
                    level = match.group(1).lower()
                    if level in self.LED_LEVELS:
                        state["keyboard_brightness"] = level
        except Exception:
            pass
        
        # Get battery limit
        try:
            result = self.run("battery", "info", check=False)
            if result.returncode == 0:
                # Output: "Current battery charge limit: 60%"
                match = re.search(r"charge limit:\s*(\d+)", result.stdout)
                if match:
                    state["battery_limit"] = int(match.group(1))
        except Exception:
            pass
        
        # Get armoury attributes
        try:
            state["armoury"] = self.get_armoury_attributes()
        except Exception:
            pass
        
        return state
    
    def get_armoury_attributes(self) -> dict[str, Any]:
        """Get all armoury firmware attributes."""
        attributes: dict[str, Any] = {}
        
        if not self.is_available:
            return attributes
        
        try:
            result = self.run("armoury", "list", check=False)
            if result.returncode != 0:
                return attributes
            
            # Parse the armoury list output
            # Format:
            # ppt_pl1_spl:
            #   current: 15..[15]..35
            #   default: 35
            
            current_attr = None
            for line in result.stdout.split("\n"):
                line = line.rstrip()
                
                # Attribute name line (no leading space, ends with colon)
                if line and not line.startswith(" ") and line.endswith(":"):
                    current_attr = line[:-1]
                    attributes[current_attr] = {"current": None, "default": None, "options": None}
                
                # Current value line
                elif current_attr and "current:" in line:
                    value_part = line.split("current:", 1)[1].strip()
                    
                    # Format: [(0),1] for discrete options
                    if value_part.startswith("["):
                        # Extract selected value from [(x),y,z] format
                        match = re.search(r"\((\d+)\)", value_part)
                        if match:
                            attributes[current_attr]["current"] = int(match.group(1))
                        # Extract all options
                        options = re.findall(r"\d+", value_part)
                        attributes[current_attr]["options"] = [int(o) for o in options]
                    
                    # Format: 15..[15]..35 for ranges
                    elif ".." in value_part:
                        match = re.search(r"(\d+)\.\.?\[(\d+)\]\.\.?(\d+)", value_part)
                        if match:
                            attributes[current_attr]["min"] = int(match.group(1))
                            attributes[current_attr]["current"] = int(match.group(2))
                            attributes[current_attr]["max"] = int(match.group(3))
                
                # Default value line
                elif current_attr and "default:" in line:
                    value_part = line.split("default:", 1)[1].strip()
                    try:
                        attributes[current_attr]["default"] = int(value_part)
                    except ValueError:
                        attributes[current_attr]["default"] = value_part
        
        except Exception:
            pass
        
        return attributes
    
    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply asusctl settings."""
        if not self.is_available:
            return
        
        if "power_profile" in settings:
            self.set_power_profile(settings["power_profile"])
        
        if "keyboard_brightness" in settings:
            self.set_keyboard_brightness(settings["keyboard_brightness"])
        
        if "battery_limit" in settings:
            self.set_battery_limit(settings["battery_limit"])
    
    # Power Profile Methods
    
    def get_power_profile(self) -> str | None:
        """Get current power profile."""
        state = self.get_current_state()
        return state.get("power_profile")
    
    def get_power_profiles(self) -> list[str]:
        """Get list of available power profiles."""
        if not self.is_available:
            return []
        
        try:
            result = self.run("profile", "list", check=False)
            if result.returncode == 0:
                return [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
        except Exception:
            pass
        
        return self.POWER_PROFILES
    
    def set_power_profile(self, profile: str) -> bool:
        """Set power profile.
        
        Args:
            profile: One of 'LowPower', 'Balanced', 'Performance'.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        # Allow case-insensitive matching
        for p in self.POWER_PROFILES:
            if p.lower() == profile.lower():
                profile = p
                break
        
        try:
            result = self.run("profile", "set", profile, check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    # Keyboard LED Methods
    
    def get_keyboard_brightness(self) -> str | None:
        """Get current keyboard brightness level."""
        state = self.get_current_state()
        return state.get("keyboard_brightness")
    
    def set_keyboard_brightness(self, level: str | int) -> bool:
        """Set keyboard backlight brightness.
        
        Args:
            level: One of 'off', 'low', 'med', 'high' or 0-3.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        # Convert int to string level
        if isinstance(level, int):
            if 0 <= level < len(self.LED_LEVELS):
                level = self.LED_LEVELS[level]
            else:
                return False
        
        level = level.lower()
        if level not in self.LED_LEVELS:
            return False
        
        try:
            result = self.run("leds", "set", level, check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    # Battery Methods
    
    def get_battery_limit(self) -> int | None:
        """Get current battery charge limit."""
        state = self.get_current_state()
        return state.get("battery_limit")
    
    def set_battery_limit(self, limit: int) -> bool:
        """Set battery charge limit.
        
        Args:
            limit: Charge limit percentage (20-100).
        
        Returns:
            True if successful.
        """
        if not self.is_available or not 20 <= limit <= 100:
            return False
        
        try:
            result = self.run("battery", "limit", str(limit), check=False)
            return result.returncode == 0
        except Exception:
            return False
    
    # Armoury Methods
    
    def get_armoury_attribute(self, name: str) -> dict[str, Any] | None:
        """Get a specific armoury attribute.
        
        Args:
            name: Attribute name (e.g., 'ppt_pl1_spl', 'nv_temp_target').
        
        Returns:
            Dict with current, default, min, max values, or None.
        """
        attributes = self.get_armoury_attributes()
        return attributes.get(name)
    
    def set_armoury_attribute(self, name: str, value: int) -> bool:
        """Set an armoury firmware attribute.
        
        Args:
            name: Attribute name (e.g., 'ppt_pl1_spl').
            value: Value to set.
        
        Returns:
            True if successful.
        """
        if not self.is_available:
            return False
        
        try:
            result = self.run("armoury", "set", name, str(value), check=False)
            return result.returncode == 0
        except Exception:
            return False
