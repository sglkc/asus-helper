"""Bridge for supergfxctl - GPU mode switching."""

import re
from typing import Any

from asus_helper.bridges.base import Bridge


class SupergfxctlBridge(Bridge):
    """Bridge for supergfxctl CLI tool.
    
    Provides control over GPU mode:
    - Integrated: Use only AMD iGPU
    - Hybrid: AMD iGPU + NVIDIA dGPU (on-demand)
    - Dedicated: Use only NVIDIA dGPU (requires reboot/logout)
    """
    
    COMMAND = "supergfxctl"
    
    # GPU modes supported by supergfxctl
    GPU_MODES = ["integrated", "hybrid", "dedicated", "vfio"]
    
    def get_current_state(self) -> dict[str, Any]:
        """Get current GPU mode."""
        state: dict[str, Any] = {
            "gpu_mode": None,
        }
        
        if not self.is_available:
            return state
        
        try:
            result = self.run("-g", check=False)
            if result.returncode == 0:
                mode = result.stdout.strip().lower()
                if mode in self.GPU_MODES:
                    state["gpu_mode"] = mode
        except Exception:
            pass
        
        return state
    
    def apply_settings(self, settings: dict[str, Any]) -> None:
        """Apply GPU mode settings."""
        if not self.is_available:
            return
        
        if "gpu_mode" in settings:
            self.set_gpu_mode(settings["gpu_mode"])
    
    def set_gpu_mode(self, mode: str) -> bool:
        """Set GPU mode.
        
        Args:
            mode: One of 'integrated', 'hybrid', 'dedicated', 'vfio'.
        
        Returns:
            True if successful.
        
        Note:
            Switching to/from 'dedicated' may require logout/reboot.
        """
        if not self.is_available:
            return False
        
        # Capitalize first letter for supergfxctl
        mode_arg = mode.capitalize()
        
        try:
            self.run("-m", mode_arg)
            return True
        except Exception:
            return False
    
    def get_gpu_mode(self) -> str | None:
        """Get current GPU mode."""
        state = self.get_current_state()
        return state.get("gpu_mode")
