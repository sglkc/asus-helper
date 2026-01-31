# ASUS Helper - Progress Log

## Completed

### Phase 1: MVP Infrastructure ✅
- [x] Project setup with uv and PyQt6
- [x] TOML configuration management
- [x] Single instance handling (lock file + SIGUSR1)
- [x] Logging infrastructure with `--debug` flag
- [x] CLI bridge abstraction layer

### Phase 2: CLI Bridges ✅
- [x] asusctl bridge (profiles, LEDs, battery, armoury)
- [x] supergfxctl bridge (GPU mode switching)
- [x] ryzenadj bridge (CPU power/temp limits)
- [x] nvidia-smi bridge (GPU clocks/temp limits)
- [x] Dynamic feature detection

### Phase 3: UI ✅
- [x] Main window with native Qt theming
- [x] System tray icon with context menu
- [x] Power profile buttons
- [x] GPU mode buttons
- [x] CPU settings sliders (ryzenadj)
- [x] GPU settings sliders (nvidia-smi)
- [x] Keyboard brightness slider

### Documentation ✅
- [x] asusctl CLI reference (`docs/asusctl-reference.md`)
- [x] Install script with KWin rules (`scripts/install.sh`)
- [x] README with usage instructions

## In Progress

### Fixes & Polish
- [ ] Fix escaped quotes in main_window.py (user edit artifact)
- [ ] Test all asusctl commands on real hardware
- [ ] Verify KWin rules work correctly

## Git Commits

| Commit | Description |
|--------|-------------|
| `f80350f` | Initial MVP with CLI bridges and PyQt6 UI |
| `b980821` | Position window bottom-right, increase width |
| `db14ca8` | Flexible label widths, KWin rules install script |
| `4997d88` | Comprehensive logging infrastructure |
| `31a5df0` | Rewrite asusctl bridge with correct CLI commands |
| `4fc3daa` | Update UI with correct asusctl profile names |
