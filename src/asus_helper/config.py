"""Configuration management using TOML."""

from pathlib import Path
from typing import Any

import tomli
import tomli_w

from asus_helper.logging import get_logger

log = get_logger("config")


class Config:
    """Manages application configuration stored in TOML format."""
    
    DEFAULT_CONFIG_DIR = Path.home() / ".config" / "asus-helper"
    DEFAULT_CONFIG_FILE = "config.toml"
    
    # Default configuration values
    # Profile names match asusctl power profiles: LowPower, Balanced, Performance
    # Displayed as: Silent, Balanced, Turbo
    DEFAULTS: dict[str, Any] = {
        "general": {
            "start_on_boot": False,
            "current_profile": "Balanced",
        },
        "profiles": {
            "LowPower": {
                "gpu_mode": "Integrated",
                "cpu_tdp": 25,
                "cpu_temp_limit": 75,
                "gpu_clock_min": 300,
                "gpu_clock_max": 900,
                "gpu_temp_limit": 80,
                "battery_limit": 60,
                "keyboard_brightness": "off",
            },
            "Balanced": {
                "gpu_mode": "Hybrid",
                "cpu_tdp": 45,
                "cpu_temp_limit": 85,
                "gpu_clock_min": 300,
                "gpu_clock_max": 1500,
                "gpu_temp_limit": 87,
                "battery_limit": 80,
                "keyboard_brightness": "low",
            },
            "Performance": {
                "gpu_mode": "Hybrid",
                "cpu_tdp": 65,
                "cpu_temp_limit": 95,
                "gpu_clock_min": 300,
                "gpu_clock_max": 2100,
                "gpu_temp_limit": 90,
                "battery_limit": 100,
                "keyboard_brightness": "med",
            },
        },
    }
    
    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize config manager.
        
        Args:
            config_dir: Override config directory (for testing).
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.config_file = self.config_dir / self.DEFAULT_CONFIG_FILE
        self._data: dict[str, Any] = {}
        self._load()
    
    def _load(self) -> None:
        """Load config from file, creating defaults if needed."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "rb") as f:
                    self._data = tomli.load(f)
                log.debug("Loaded config from %s", self.config_file)
            except (tomli.TOMLDecodeError, OSError) as e:
                log.warning("Could not load config: %s. Using defaults.", e)
                self._data = self._deep_copy(self.DEFAULTS)
        else:
            log.info("Config file not found, creating with defaults: %s", self.config_file)
            self._data = self._deep_copy(self.DEFAULTS)
            self._save()
    
    def _save(self) -> None:
        """Save current config to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "wb") as f:
            tomli_w.dump(self._data, f)
        log.debug("Saved config to %s", self.config_file)
    
    def _deep_copy(self, d: dict) -> dict:
        """Create a deep copy of a nested dict."""
        result = {}
        for k, v in d.items():
            if isinstance(v, dict):
                result[k] = self._deep_copy(v)
            else:
                result[k] = v
        return result
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a config value by nested keys.
        
        Example: config.get("profiles", "balanced", "cpu_tdp")
        """
        value = self._data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *keys_and_value: Any) -> None:
        """Set a config value by nested keys.
        
        Last argument is the value, all others are keys.
        Example: config.set("profiles", "balanced", "cpu_tdp", 50)
        """
        if len(keys_and_value) < 2:
            raise ValueError("Need at least one key and a value")
        
        *keys, value = keys_and_value
        
        # Navigate to parent
        parent = self._data
        for key in keys[:-1]:
            if key not in parent:
                parent[key] = {}
            parent = parent[key]
        
        # Set value
        parent[keys[-1]] = value
        self._save()
    
    def get_current_profile(self) -> dict[str, Any]:
        """Get the currently active profile settings."""
        profile_name = self.get("general", "current_profile", default="balanced")
        return self.get("profiles", profile_name, default=self.DEFAULTS["profiles"]["balanced"])
    
    def set_current_profile(self, name: str) -> None:
        """Set the active profile by name."""
        self.set("general", "current_profile", name)
    
    def get_profile_names(self) -> list[str]:
        """Get list of available profile names."""
        profiles = self.get("profiles", default={})
        return list(profiles.keys())
    
    @property
    def start_on_boot(self) -> bool:
        """Whether to start on boot."""
        return self.get("general", "start_on_boot", default=False)
    
    @start_on_boot.setter
    def start_on_boot(self, value: bool) -> None:
        self.set("general", "start_on_boot", value)
