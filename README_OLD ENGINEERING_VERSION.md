# SI5351 Multi-Radio VFO Control System

A PC-controlled multi-radio synthesized VFO platform for vintage amateur radio equipment using Arduino Nano, dual SI5351 synthesizers, and a PySide6 desktop control application.

---

# Overview

The SI5351 Multi-Radio VFO Control System is designed to replace or augment unstable vintage analog VFOs and crystal oscillators with highly stable digitally synthesized frequency sources.

The system supports multiple simultaneous radio control windows, multiple RF outputs, radio-specific frequency translation profiles, and desktop-based operating control.

The architecture separates:

- GUI intelligence and radio math
- hardware execution
- RF output routing
- session management
- radio profile configuration

The project is intended for:

- Vintage ham radio restoration
- Multi-radio operating desks
- Lab/bench signal generation
- External VFO replacement
- Stable LO/VFO experimentation

---

# Major Features

- Multi-radio simultaneous control
- 6 independent RF outputs (OUT0–OUT5)
- Dual SI5351 synthesizer support
- TCA9548A I2C multiplexer architecture
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

---

# System Architecture

## Hardware

### Controller
- Arduino Nano

### I2C Multiplexer
- TCA9548A @ 0x70

### RF Synthesizers
- 2 × Adafruit SI5351A modules

Each SI5351 provides:
- CLK0
- CLK1
- CLK2

Total outputs:
- OUT0–OUT5

---

# Output Mapping

| Output | Hardware |
|---|---|
| OUT0 | SI5351 #1 CLK0 |
| OUT1 | SI5351 #1 CLK1 |
| OUT2 | SI5351 #1 CLK2 |
| OUT3 | SI5351 #2 CLK0 |
| OUT4 | SI5351 #2 CLK1 |
| OUT5 | SI5351 #2 CLK2 |

GUI labels:
- BNC1–BNC6

---

# Supported Radios

| Radio | Translation Model |
|---|---|
| Swan 400 | linear_map |
| Swan 350C | linear_map |
| Eico 720 | multiply |
| Heathkit DX-100 | multiply/direct |
| Clegg Thor 6 | direct |

Additional radio profiles can be added.

---

# Software Architecture

## Python GUI = System Brain

The PySide6 GUI performs:

- Radio profile math
- Frequency translation
- Session management
- Output assignment
- Multi-window coordination
- Serial communication management

## Arduino Nano = Execution Engine

The Nano performs:

- SI5351 frequency programming
- RF output switching
- PTT state reporting
- Hardware-level execution only

Important architectural rule:

> Radio frequency translation logic remains in Python and is NOT performed in the Arduino firmware.

---

# Serial Protocol

## Frequency Commands

```text
F0xxxxxxxxxxx;
F1xxxxxxxxxxx;
F2xxxxxxxxxxx;
F3xxxxxxxxxxx;
F4xxxxxxxxxxx;
F5xxxxxxxxxxx;
```

## RF Enable Commands

```text
E01;
E00;
E31;
E30;
```

## PTT Feedback

```text
TXx;
RXx;
```

---

# RF / PTT / SPOT Logic

- PTT LOW = RF ON
- PTT HIGH = RF OFF
- SPOT enables RF during RX only
- TX overrides SPOT
- RF state is NOT restored at startup for safety

---

# Current Stable Freeze

```text
SI5351_VFO_PC_v4D6I_INSTALLER_DEPLOYMENT_VALIDATED
```

Stable features verified:

- COM reconnect
- EXE shutdown
- Session restore
- Floating windows
- Output Manager
- Installer deployment
- No orphan EXE processes

---

# Screenshots

## Main Window

![Main Window](assets/screenshots/main_window.png)

---

## Compact Radio Window

![Compact Window](assets/screenshots/compact_window.png)

---

## Full Radio Window

![Full Window](assets/screenshots/full_window.png)

---

## Output Manager

![Output Manager](assets/screenshots/Output_Manager.png)

---

## About Dialog

![About Dialog](assets/screenshots/About_Dialog.png)


Suggested screenshots:

- Main Window
- Compact Radio Window
- Full Radio Window
- Output Manager
- About Dialog

---

# Installation

## End User Installation

1. Run installer:
   - `SI5351_Multi_Radio_VFO_Setup.exe`

2. Launch from desktop shortcut

3. Connect Arduino Nano USB

4. Select COM port

5. Press Connect

---

# Developer Setup

## Requirements

- Python 3.14+
- PySide6
- pyserial
- pyinstaller

Install dependencies:

```bash
pip install pyside6 pyserial pyinstaller
```

---

# Build EXE

From:

```text
pc_software/
```

Run:

```bash
pyinstaller --onefile --windowed --name SI5351_Multi_Radio_VFO main.py
```

Output EXE:

```text
dist/SI5351_Multi_Radio_VFO.exe
```

---

# Inno Setup Installer

The installer packages the EXE generated from:

```text
dist/SI5351_Multi_Radio_VFO.exe
```

Important:
Always rebuild the EXE before rebuilding the installer.

---

# Current Directory Structure

```text
SI5351-Multi-Radio-VFO/
│
├── firmware/
├── hardware/
├── pc_software/
│   ├── assets/
│   ├── screenshots/
│   ├── main.py
│   ├── main_window.py
│   ├── radio_profiles.json
│   └── ...
│
├── docs/
└── releases/
```

---

# Future Roadmap

## v4E
- README modernization
- screenshots
- branding

## v4F
- installer polish
- release packaging

## v5.0
- Radio Profile Editor GUI
- searchable help system
- printable user manual

---

# Engineering Rules

## Serial Architecture

Only ONE global:

```python
SerialLink()
```

instance is allowed.

All windows share the same serial connection.

## GUI Ownership

The GUI owns:

- profile math
- translation logic
- session logic

The firmware remains execution-only.

---

# License

(Define later)

---

# Acknowledgments

Built for experimentation, restoration, and operation of classic amateur radio equipment using modern digital synthesis techniques.