# SI5351 Multi-Radio VFO

# Developer Recovery / New Chat Rebuild Guide

## Version 6.0

---

# Purpose

This document allows a future developer (or future ChatGPT session) to quickly reconstruct the development environment, architecture understanding, and project status for continued development.

This guide is intended to minimize loss of continuity between development sessions.

---

# Current Project Status

Current stable milestone:

```text id="qjlwm3"
SI5351_VFO_PLATFORM_v6_PUBLIC_RELEASE_COMPLETE
```

The platform has transitioned from experimental software into a publicly distributed RF-control platform.

The software architecture, installer pipeline, documentation, and GitHub release workflow are operational and stable.

---

# GitHub Repository

Repository:

```text id="njlwm1"
https://github.com/jebielefeld/SI5351-Multi-Radio-VFO
```

Current branch:

```text id="9jlwm9"
main
```

Developers are encouraged to create their own branches for experimental work.

Example:

```powershell id="4jlwm0"
git checkout -b feature/my_new_feature
```

---

# Development Environment

## Operating System

Primary development system:

* Windows 11

---

# Python Environment

Recommended Python version:

```text id="mjlwm0"
Python 3.11+
```

---

# Required Python Packages

Main dependencies:

```text id="xjlwm8"
PySide6
pyserial
```

Optional build tools:

```text id="9jlwm1"
pyinstaller
```

Install example:

```powershell id="0jlwm2"
pip install PySide6 pyserial pyinstaller
```

---

# Repository Structure

## Main Directories

```text id="sjlwm7"
pc_software/
firmware/
docs/
hardware/
installer/
assets/
```

---

# Important Software Files

## Main Application

```text id="bjlwm4"
pc_software/main.py
```

---

## Main Controller Window

```text id="djlwm2"
pc_software/main_window.py
```

---

## Floating Radio Windows

```text id="wjlwm5"
pc_software/radio_window.py
```

---

## Serial Communications

```text id="5jlwm6"
pc_software/serial_link.py
```

---

## Radio Math Engine

```text id="cjlwm0"
pc_software/radio_maths.py
```

---

## Radio Profiles

```text id="7jlwm4"
pc_software/radio_profiles.json
```

---

## Calibration Window

```text id="jjlwm3"
pc_software/calibration_window.py
```

---

## Profile Editor

```text id="njlwm7"
pc_software/profile_editor.py
```

---

## Architecture Documentation

```text id="qjlwm1"
pc_software/ARCHITECTURE.md
```

---

# Hardware Architecture

Current hardware architecture:

* Arduino Nano ATmega328
* TCA9548A I2C multiplexer
* Two Adafruit SI5351 modules
* Six RF outputs

Output mapping:

```text id="hjlwm2"
OUT0 = SI5351 #1 CLK0
OUT1 = SI5351 #1 CLK1
OUT2 = SI5351 #1 CLK2
OUT3 = SI5351 #2 CLK0
OUT4 = SI5351 #2 CLK1
OUT5 = SI5351 #2 CLK2
```

---

# Serial Protocol

## Frequency Commands

```text id="3jlwm1"
F0xxxxxxxxxxx;
F1xxxxxxxxxxx;
F2xxxxxxxxxxx;
F3xxxxxxxxxxx;
F4xxxxxxxxxxx;
F5xxxxxxxxxxx;
```

---

## RF Enable Commands

```text id="vjlwm7"
E01;
E00;
```

---

## TX/RX Feedback

```text id="0jlwm4"
TX0;
RX0;
```

---

# Current Stable Features

Stable features include:

* Multi-window GUI
* Compact/full modes
* Session persistence
* EEPROM calibration
* Output Manager
* Profile Editor
* Searchable Help system
* Installer packaging
* GitHub Releases workflow
* Printable PDF User Manual
* Wiring documentation

---

# Current Documentation

## Main README

```text id="ljlwm9"
README.md
```

---

## Printable Manual

```text id="xjlwm6"
docs/User_Manual_v1.pdf
```

---

## Wiring Documentation

```text id="8jlwm3"
docs/wiring/System_Wiring_Overview_v1.pdf
```

---

## Software Architecture

```text id="7jlwm8"
pc_software/ARCHITECTURE.md
```

---

# Build / Run Workflow

## Run Application

From:

```text id="4jlwm8"
pc_software/
```

execute:

```powershell id="rjlwm2"
python main.py
```

---

# Build EXE

Use:

```text id="tjlwm6"
installer/build_exe.bat
```

---

# Build Installer

Use:

```text id="yjlwm5"
installer/build_installer.bat
```

---

# GitHub Release Workflow

Typical release process:

1. Commit changes
2. Push to GitHub
3. Create GitHub Release
4. Attach:

   * installer EXE
   * PDF manual
5. Publish release

---

# Architectural Philosophy

Important design philosophy:

```text id="jjlwm0"
GUI owns intelligence.
Nano owns hardware execution.
```

All radio translation math intentionally occurs inside the PC software.

Nano firmware remains intentionally simple.

---

# RF Safety Philosophy

Important safety behaviors:

* RF outputs restore OFF at startup
* TX overrides SPOT
* output conflicts prevented
* calibration isolated from normal operation

These protections are intentional.

---

# Current Next Development Phase

The project is now transitioning into:

```text id="hjlwm4"
Hardware Integration / Enclosure Phase
```

Current priorities:

* enclosure design
* grounding strategy
* shielding
* RF routing
* BNC layout
* power distribution
* relay/filter integration
* serviceability

---

# Long-Term Platform Direction

This project is no longer viewed as merely:

```text id="kjlwm5"
simple SI5351 VFO
```

Current direction is:

```text id="zjlwm2"
Modular RF Signal / Control Infrastructure Platform
```

with future support planned for:

* RF relay switching
* filtering
* panadapter integration
* expanded radio profile support
* hardware carrier PCB
* modular RF routing

---

# Recommended First Reading For New Developers

1. README.md
2. User_Manual_v1.pdf
3. ARCHITECTURE.md
4. radio_profiles.json
5. main_window.py
6. radio_window.py
7. serial_link.py
8. radio_maths.py

---

# Final Notes

This repository now contains:

* stable software
* stable deployment pipeline
* public GitHub releases
* printable documentation
* wiring documentation
* architecture documentation
* installer workflow

The platform is stable enough for continued hardware integration and future RF subsystem expansion.
