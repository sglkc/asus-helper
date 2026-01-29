"""Bridge abstraction layer for CLI tools."""

from asus_helper.bridges.base import Bridge
from asus_helper.bridges.asusctl import AsusctlBridge
from asus_helper.bridges.supergfxctl import SupergfxctlBridge
from asus_helper.bridges.ryzenadj import RyzenadjBridge
from asus_helper.bridges.nvidia_smi import NvidiaSMIBridge

__all__ = [
    "Bridge",
    "AsusctlBridge",
    "SupergfxctlBridge",
    "RyzenadjBridge",
    "NvidiaSMIBridge",
]
