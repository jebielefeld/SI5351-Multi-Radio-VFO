# SI5351 Multi-Radio VFO Control System
# Release Notes — v0.9.0-beta

---

# Overview

This release represents the first public beta deployment of the SI5351 Multi-Radio VFO Control System.

The platform has now been validated for:

- installer-based deployment
- desktop shortcut launching
- COM reconnect after reboot
- session persistence
- multi-window operation
- dual SI5351 hardware support
- OUT0–OUT5 routing architecture

---

# Major Features

## Multi-Radio Control

The application supports multiple simultaneous radio control windows using a shared serial architecture.

## OUT0–OUT5 Architecture

Two SI5351 synthesizer modules are routed through a TCA9548A I2C multiplexer to provide six independently controlled RF outputs.

## Session Persistence

Window layouts, radio selections, frequencies, and operating states are restored automatically between sessions.

## RF Safety Behavior

RF ON and SPOT are intentionally disabled at startup for operating safety.

---

# Deployment Validation

Validated successfully:

- Windows reboot recovery
- COM reconnect
- installer deployment
- desktop shortcut launch
- session restore
- Output Manager operation
- floating radio window restore
- EXE shutdown cleanup

---

# Supported Radios

- Swan 400
- Swan 350C
- Eico 720
- Heathkit DX-100
- Clegg Thor 6

Additional radio profiles can be added.

---

# Known Limitations

- SI5351 outputs are square-wave RF sources
- Fractional frequency jitter may appear on counters
- Shared enable currently exists per SI5351 chip
- PLL optimization remains future work

---

# Future Development

Planned future enhancements include:

- Radio Profile Editor GUI
- searchable help system
- printable user manual
- expanded radio profile library
- PLL optimization
- SDR/panadapter integration support