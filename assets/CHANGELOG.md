# Changelog

All notable changes to this project will be documented in this file.

---

# v0.9.0-beta

Initial public beta release.

## Added

- Multi-radio simultaneous control
- OUT0–OUT5 architecture
- Dual SI5351 support
- TCA9548A I2C multiplexer support
- Floating radio control windows
- Compact and full operating modes
- Session save/restore
- Output conflict prevention
- RF ON/OFF control
- PTT/TX/RX synchronization
- SPOT mode support
- Radio profile translation system
- PyInstaller standalone EXE support
- Inno Setup installer support

## Validated

- Desktop installer deployment
- COM reconnect after reboot
- Session restore after reboot
- Multi-window restoration
- Output Manager operation
- EXE shutdown cleanup
- Desktop shortcut launch

## Known Limitations

- SI5351 outputs are square-wave RF sources
- Fractional frequencies may show minor counter jitter
- Current firmware uses shared enable per SI5351 chip
- PLL optimization not yet implemented
- Windows is the primary tested platform