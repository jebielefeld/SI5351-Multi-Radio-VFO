# Developer Setup Guide

# SI5351 Multi-Radio VFO Control Platform

This document describes how to set up the development environment for the SI5351 Multi-Radio VFO Control Platform.

---

# Required Software

## Python

Recommended:

- Python 3.12 or newer

Download:

https://www.python.org/

---

## Visual Studio Code

Recommended editor:

https://code.visualstudio.com/

Recommended extensions:

- Python
- Pylance

---

## Arduino IDE

Required for Nano firmware development:

https://www.arduino.cc/en/software

---

## GitHub Desktop

Recommended Git client:

https://desktop.github.com/

---

# Python Dependencies

Install required Python packages:

```text
pip install pyside6 pyserial
```

---

# Project Structure

```text
firmware/
    Arduino Nano firmware

pc_software/
    Python GUI application

docs/
    Documentation

installer/
    Build scripts and installers

examples/
    Example configurations
```

---

# Running The GUI

Navigate to:

```text
pc_software/
```

Run:

```text
python main.py
```

---

# Arduino Firmware

Firmware located in:

```text
firmware/
```

Primary sketch:

```text
SI5351_VFO_PC.ino
```

---

# Serial Configuration

Default serial settings:

```text
115200 baud
8N1
```

---

# Hardware Requirements

Required hardware:

- Arduino Nano
- TCA9548A I2C multiplexer
- Two Adafruit SI5351 modules

---

# IMPORTANT ARCHITECTURE RULE

GUI owns all radio frequency translation math.

Arduino Nano firmware remains execution engine only.

Do not migrate radio math into firmware unless intentionally redesigning architecture.

---

# Current Stable Freeze Point

```text
SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE
```