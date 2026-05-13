# Radio Profile System

# SI5351 Multi-Radio VFO Control Platform

---

# Overview

Radio profiles define how operating frequency maps to SI5351 output frequency.

Profiles are stored in:

```text
radio_profiles.json
```

The GUI performs all frequency translation math.

The Arduino Nano firmware receives final output frequencies only.

---

# Design Philosophy

Different vintage radios require different VFO/LO behavior.

Examples:

- Direct VFO replacement
- Frequency multiplication
- Linear frequency translation
- Heterodyne local oscillator operation

The radio profile system allows the GUI to support many radio architectures without modifying firmware.

---

# IMPORTANT ARCHITECTURE RULE

The GUI owns all radio math.

Do not move radio profile math into Arduino firmware unless intentionally redesigning system architecture.

---

# Current Math Models

## direct

Output frequency equals operating frequency.

Example:

```text
RF = 7.100 MHz
OUT = 7.100 MHz
```

---

## multiply

Used for crystal multiplier transmitters.

Examples:

| Band | RF | VFO Output |
|---|---|---|
| 20m | 14.2 MHz | 7.1 MHz |
| 15m | 21.3 MHz | 7.1 MHz |
| 10m | 28.4 MHz | 7.1 MHz |

---

## linear_map

Used for radios requiring translated VFO ranges.

Examples:

- Swan 350C
- Swan 400

---

# Example Profile Structure

```json
{
  "radio_name": "Example Radio",
  "bands": {
    "80m": {
      "mode": "direct",
      "rf_min": 3500000,
      "rf_max": 4000000,
      "vfo_min": 3500000,
      "vfo_max": 4000000
    }
  }
}
```

---

# Supported Radio Types

Examples currently supported:

- Swan 350C
- Swan 400
- Eico 720
- Heathkit DX-100

---

# GUI Responsibilities

The GUI performs:

- Frequency translation
- Band validation
- Output routing
- Range checking
- User interaction

---

# Firmware Responsibilities

The Nano firmware performs:

- Frequency output
- RF enable control
- Serial processing
- PTT polling

Only.

---

# Planned Future Features

Planned enhancements include:

- GUI profile editor
- Profile validation tools
- Import/export support
- User profile library
- Profile templates

---

# Future Expansion Possibilities

Possible future profile types:

- Offset local oscillator
- Multiple conversion stages
- Dynamic band switching
- External relay control
- PLL optimization