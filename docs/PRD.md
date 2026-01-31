# ASUS Helper - Product Requirements Document

A PyQt6-based power management tool for ASUS laptops on Linux, inspired by G-Helper.

## Target Hardware & Software

| Component | Requirement |
|-----------|-------------|
| **Laptop** | ASUS laptops (ROG, TUF, Zephyrus) |
| **OS** | Arch-based Linux |
| **Desktop** | KDE Plasma 6 (Wayland) |
| **GPU** | AMD iGPU + NVIDIA dGPU |

## CLI Bridges

| Tool | Purpose | Required |
|------|---------|----------|
| `asusctl` | Power profiles, keyboard LEDs, armoury, battery | No |
| `supergfxctl` | GPU mode switching (Integrated/Hybrid/Dedicated) | No |
| `ryzenadj` | AMD CPU power/temp limits (overrides asusctl) | No |
| `nvidia-smi` | NVIDIA GPU clocks/temp limits (overrides asusctl) | No |

All bridges are optional - UI adapts based on availability.

## Core Features

### Must Have
- [x] Lightweight PyQt6 application
- [x] System tray icon with left-click toggle
- [x] Native Qt theming (Breeze Dark)
- [x] Single instance handling
- [x] TOML configuration (`~/.config/asus-helper/`)
- [x] Dynamic UI based on available bridges
- [x] Logging with `--debug` flag

### Power Management
- [x] Power profile switching (LowPower/Balanced/Performance)
- [x] GPU mode switching (Integrated/Hybrid/Dedicated)
- [x] CPU power limits via ryzenadj
- [x] GPU clock limits via nvidia-smi
- [x] Keyboard LED brightness

### Nice to Have
- [ ] Profile system (save/load configurations)
- [ ] Battery charge limit control
- [ ] Interactive fan curve editor
- [ ] Keyboard shortcut support
- [ ] Armoury attribute controls (ppt_pl1, nv_temp_target)

## UI Design

Window behavior:
- Native Qt window (not frameless)
- Keep above other windows
- Position: bottom-right (via KWin rules on Wayland)
- System tray integration

Inspired by G-Helper UI - see reference images in `brain/` directory.

## Technical Notes

### Wayland Limitations
Apps cannot set window position on Wayland. Use KWin rules instead:
```bash
./scripts/install.sh  # Sets up kwinrulesrc
```

### Qt Event Overrides
Qt event methods use camelCase and must not be renamed:
- `showEvent()` - not `show_event()`
- `closeEvent()` - not `close_event()`

### Override Priority
ryzenadj and nvidia-smi settings take precedence over asusctl armoury when both control the same values.
