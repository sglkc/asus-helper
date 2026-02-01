# ASUS Helper - TODO

## High Priority

### Bugs
- [ ] Test asusctl set commands on hardware
- [ ] Verify supergfxctl mode switching works
- [ ] Test battery limit setting

### Missing Features
- [x] Battery charge limit UI control
- [x] Apply profile on startup (from config)
- [x] Save slider values to config on change

## Medium Priority

### Profile System
- [x] Simplified to 3 profiles: LowPower (Silent), Balanced, Performance (Turbo)
- [x] Click profile button applies all settings at once
- [x] Auto-save slider changes to current profile
- [x] Apply last-used profile on startup

### Armoury Controls
- [ ] ppt_pl1_spl (CPU sustained power)
- [ ] ppt_pl2_sppt (CPU short boost)
- [ ] ppt_pl3_fppt (CPU fast boost)
- [ ] nv_temp_target (GPU temp target)
- [ ] gpu_mux_mode (MUX switch)

## Low Priority

### Advanced Features
- [ ] Fan curve editor (interactive graph)
- [ ] Keyboard shortcuts (global hotkeys)
- [ ] Aura/RGB LED zone controls
- [ ] Display refresh rate switching

### Polish
- [ ] App icon (custom, not placeholder)
- [ ] About dialog
- [ ] Settings dialog for general options
- [ ] Minimize to tray notification on first close

## Research Needed

- [ ] How to read current fan curves from asusctl
- [ ] supergfxctl mode change may require logout
- [ ] ryzenadj requires running as root
- [ ] Polkit integration as alternative to running as root
