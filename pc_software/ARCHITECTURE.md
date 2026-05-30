# SI5351 Multi-Radio VFO

# Software Architecture Overview

## Version 6.0

---

# Purpose

This document describes the internal software architecture of the SI5351 Multi-Radio VFO platform.

It is intended for:

* future developers
* maintainers
* contributors
* advanced users
* future rebuild/recovery work

This document focuses on:

* module responsibilities
* application flow
* serial architecture
* profile architecture
* session persistence
* RF safety behavior

---

# High-Level Architecture

The platform intentionally separates:

* GUI logic
* radio frequency translation math
* hardware execution
* calibration storage
* RF output management

The architecture philosophy is:

```text id="vjlwm3"
GUI owns intelligence.
Nano owns hardware execution.
```

The PC software performs:

* radio profile translation
* frequency calculations
* window management
* safety management
* session persistence

The Arduino Nano performs:

* SI5351 programming
* RF enable control
* EEPROM storage
* calibration storage
* TX/RX monitoring

---

# Major Software Modules

---

# main.py

Application entry point.

Responsibilities:

* initializes QApplication
* creates MainWindow
* starts GUI event loop
* handles top-level startup sequencing

This file should remain intentionally small.

---

# main_window.py

Primary application controller.

Responsibilities:

* COM-port management
* top-level GUI layout
* toolbar controls
* session management
* radio-window creation
* output-manager launching
* profile reload handling
* calibration window launching
* help window launching

This is effectively the central orchestration layer of the GUI.

---

# radio_window.py

Implements floating RadioControlWindow instances.

Each radio window independently manages:

* radio profile
* band selection
* RF output assignment
* tuning state
* compact/full mode
* SPOT state
* TX/RX display

Multiple simultaneous radio windows are supported.

---

# serial_link.py

Central serial communications layer.

Responsibilities:

* USB COM communications
* command transmission
* serial receive processing
* Nano communication abstraction

This module intentionally isolates all serial-port operations from the GUI logic.

---

# cat_radio.py

Low-level CAT command formatter.

Responsibilities:

* frequency command generation
* RF enable commands
* calibration commands
* serial protocol abstraction

Typical commands include:

```text id="z0lajy"
F0xxxxxxxxxxx;
E01;
TX0;
RX0;
```

This layer prevents GUI code from directly building protocol strings.

---

# radio_maths.py

Radio frequency translation engine.

This module performs all radio-specific frequency calculations.

Responsibilities:

* direct translation
* linear mapping
* multiply translation
* RF-to-VFO conversion
* band-specific translation

Important architectural decision:

```text id="u75kfc"
ALL radio math occurs in the PC software.
```

The Nano firmware intentionally remains translation-agnostic.

This allows new radio support without firmware modification.

---

# radio_profiles.json

Primary radio configuration database.

Contains:

* radio definitions
* band mappings
* translation modes
* LO/VFO conversion rules

The JSON architecture allows expansion without modifying application code.

---

# profile_editor.py

Graphical editor for radio_profiles.json.

Responsibilities:

* profile creation
* profile editing
* validation
* band editing
* translation-mode management
* save/revert workflow

The editor eliminates direct manual JSON editing for most users.

---

# profile_models.py

Internal data-model abstraction for profile editing.

Separates:

* GUI widgets
* JSON serialization
* validation logic

This improves maintainability of the Profile Editor subsystem.

---

# json_validation.py

Validation engine for radio profile data.

Responsibilities:

* field validation
* band validation
* translation validation
* configuration integrity checking

Helps prevent invalid profile configurations.

---

# profile_preview.py

Preview subsystem for profile visualization.

Used to display:

* translation behavior
* calculated outputs
* profile interpretation

during editing operations.

---

# calibration_window.py

Implements SI5351 calibration workflow.

Responsibilities:

* 10 MHz calibration generation
* EEPROM correction management
* correction stepping
* SAVE CAL workflow
* calibration display

The calibration system stores correction values inside Nano EEPROM.

---

# help_window.py

Integrated searchable help/documentation viewer.

Responsibilities:

* embedded operator help
* quick-start instructions
* calibration guidance
* troubleshooting guidance

---

# Output Manager Architecture

The Output Manager provides centralized visibility of:

* OUT0–OUT5 ownership
* RF state
* SPOT state
* TX state
* radio assignments

This becomes critical during multi-window operation.

---

# Session Persistence

The application automatically restores:

* window positions
* compact/full modes
* radio assignments
* frequencies
* output assignments

RF outputs intentionally restore OFF at startup for safety.

Session data is stored locally in:

```text id="1q0vma"
sessions/
```

---

# RF Safety Architecture

Several important safety behaviors exist:

* RF outputs restore OFF at startup
* TX overrides SPOT
* output conflicts are prevented
* output ownership is tracked
* calibration mode isolates RF generation

These protections are intentional and should not be bypassed casually.

---

# Hardware Architecture Summary

Current hardware architecture:

* Arduino Nano ATmega328
* TCA9548A I2C multiplexer
* Two Adafruit SI5351 modules
* Six RF outputs

Output mapping:

```text id="31hjlwm"
OUT0 = SI5351 #1 CLK0
OUT1 = SI5351 #1 CLK1
OUT2 = SI5351 #1 CLK2
OUT3 = SI5351 #2 CLK0
OUT4 = SI5351 #2 CLK1
OUT5 = SI5351 #2 CLK2
```

---

# Serial Protocol Summary

Typical serial commands:

## Frequency Commands

```text id="c08v8n"
F0xxxxxxxxxxx;
F1xxxxxxxxxxx;
F2xxxxxxxxxxx;
F3xxxxxxxxxxx;
F4xxxxxxxxxxx;
F5xxxxxxxxxxx;
```

## RF Enable Commands

```text id="uqlnyv"
E01;
E00;
```

## TX/RX Status

```text id="6cdl8w"
TX0;
RX0;
```

---

# Current Architectural Philosophy

The project has evolved beyond a simple VFO.

Current direction:

```text id="hqjlwm"
Modular RF Signal / Control Infrastructure Platform
```

The architecture is intentionally designed to support:

* additional radios
* RF switching
* relay sequencing
* filtering
* panadapter integration
* enclosure integration
* future RF instrumentation expansion

---

# Important Developer Notes

## Avoid Moving Radio Math Into Firmware

The GUI-based translation architecture is intentional.

Keeping translation logic in the GUI:

* simplifies firmware
* accelerates radio support
* improves maintainability

---

## Maintain RF Safety Defaults

RF outputs restoring OFF at startup is intentional safety behavior.

Do not remove casually.

---

## Preserve Output Ownership Logic

The Output Manager conflict-prevention system is critical during multi-radio operation.

---

# Current Status

Current stable milestone:

```text id="2qb4y5"
SI5351_VFO_PLATFORM_v6_PUBLIC_RELEASE_COMPLETE
```

Platform now includes:

* stable GUI
* installer deployment
* calibration subsystem
* profile editor
* printable documentation
* release packaging
* public GitHub distribution
