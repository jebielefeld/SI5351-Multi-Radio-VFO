Note:
I asked ChatGBT the following:
"Give me the entire rebuild report in CHATGPT_REBUILD_REPORT.md. That is, a file I would need to upload to you, in case, I had to 
rebuild or continue the project, at a later date. Again, so I can give you all the necessary detailed information in a format that can help you resume where we last had a session so, I can start a 'New Session' and resume from our previous session."


# SI5351 Multi-Radio VFO Control Platform
# CHATGPT_REBUILD_REPORT.md

Current stable freeze point:

```text
SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE
```

---

# PROJECT OBJECTIVE

Windows PC-controlled multi-radio VFO platform for vintage ham radio equipment.

Primary goals:

- Replace drifting vintage VFOs
- Support multiple simultaneous radios
- Support multiple simultaneous RF outputs
- Provide stable digitally controlled frequency generation
- Allow flexible radio profile frequency translation
- Provide operator-friendly GUI control
- Support future expansion

Target equipment includes:

- Swan 350C
- Swan 400
- Heathkit DX-100
- Eico 720
- Eico 722
- Clegg Thor 6
- Johnson transmitters
- Other crystal/VFO-based vintage amateur radio equipment

---

# CURRENT STABLE FREEZE POINT

```text
SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE
```

Stable features include:

- Multi-radio floating windows
- OUT0 through OUT5 architecture
- BNC 1 through BNC 6 labeling
- Session persistence
- Output Manager
- RF safety monitor
- Window position safety
- Snap/maximize protection
- Global RF indicator
- COM conflict detection
- Compact/full operator modes

---

# CORE ARCHITECTURE

## System Brain

Python / PySide6 GUI

Responsibilities:

- Radio frequency translation
- Radio profile management
- Window management
- Session management
- Output routing
- RF safety logic
- Output conflict prevention
- User interface behavior

IMPORTANT:

The GUI owns ALL radio frequency translation math.

Do not migrate radio math into the Arduino firmware unless intentionally redesigning the system architecture.

---

## Execution Engine

Arduino Nano firmware

Responsibilities:

- SI5351 control
- RF output enable control
- PTT polling
- Serial command execution
- Frequency output control

The Arduino Nano should remain an execution engine only.

---

# HARDWARE ARCHITECTURE

## Hardware Stack

- Arduino Nano (ATmega328)
- TCA9548A I2C multiplexer
- Two Adafruit SI5351 modules
- Six RF outputs

---

# I2C ARCHITECTURE

Both Adafruit SI5351 modules use the same I2C address:

```text
0x60
```

The TCA9548A isolates the SI5351 modules onto separate channels.

## TCA9548A Mapping

| TCA9548A Channel | Device |
|---|---|
| Channel 0 | SI5351 #1 |
| Channel 1 | SI5351 #2 |

---

# RF OUTPUT ARCHITECTURE

## Physical Output Mapping

| BNC Output | Logical Output | SI5351 Module | Clock |
|---|---|---|---|
| BNC 1 | OUT0 | SI5351 #1 | CLK0 |
| BNC 2 | OUT1 | SI5351 #1 | CLK1 |
| BNC 3 | OUT2 | SI5351 #1 | CLK2 |
| BNC 4 | OUT3 | SI5351 #2 | CLK0 |
| BNC 5 | OUT4 | SI5351 #2 | CLK1 |
| BNC 6 | OUT5 | SI5351 #2 | CLK2 |

Preserve this abstraction model.

GUI and firmware should always refer to outputs as:

```text
OUT0 through OUT5
```

not directly as clock numbers.

---

# SERIAL PROTOCOL

## Frequency Commands

```text
F0xxxxxxxxxxx;
F1xxxxxxxxxxx;
F2xxxxxxxxxxx;
F3xxxxxxxxxxx;
F4xxxxxxxxxxx;
F5xxxxxxxxxxx;
```

Examples:

```text
F00010000000;
F30009058000;
```

---

## RF Enable Commands

```text
E01;   OUT0 RF ON
E00;   OUT0 RF OFF

E11;   OUT1 RF ON
E10;   OUT1 RF OFF
```

---

## PTT Feedback

```text
TXx;
RXx;
```

---

# RF CONTROL MODEL

## TX/RX Logic

- PTT LOW = TX / RF ON
- PTT HIGH = RX / RF OFF

---

## SPOT Behavior

SPOT enables RF during RX only.

Rules:

- SPOT ignored during TX
- TX overrides SPOT
- SPOT cleared automatically when TX begins

---

## Startup Safety Rules

At startup:

- RF OFF
- SPOT OFF

Must never automatically restore RF ON state after application restart.

This is an important safety rule.

---

# GUI ARCHITECTURE

## Main Window

Responsibilities:

- COM port management
- Global controls
- Output Manager
- Session management
- Global RF indicator

---

## Floating RadioControlWindow Instances

Each radio window maintains independent:

- Radio profile
- Band
- Frequency
- Output assignment
- Tuning step
- SPOT state
- Compact/full mode

---

# UI MODES

## FULL MODE

Configuration/setup mode.

Supports:

- Radio selection
- Band selection
- Output selection
- Advanced controls

---

## COMPACT MODE

Small operator tile.

Approximately:

```text
300 x 150
```

Contains:

- Frequency display
- TX/RX indicator
- SPOT control
- Basic tuning controls

---

# SESSION SYSTEM

Session auto-save and auto-restore are implemented.

Stored state includes:

- Window positions
- Window sizes
- Compact/full state
- Radio profile selection
- Band
- Frequency
- Output routing
- Tuning step

---

# WINDOW SAFETY SYSTEM

## Position Safety

All windows forced on-screen after:

- Startup
- Session restore
- Window arrangement
- New window creation

---

## Snap Protection

Floating radio windows automatically restore if accidentally maximized via Windows Snap.

Main window is allowed to maximize normally.

---

# SAFETY SYSTEM

## Current Behavior

Multi-band TX:

```text
Allowed
```

Same-band TX:

```text
Warning generated
```

---

## Current Enforcement

Current safety model is:

```text
Warning only
```

No RF blocking currently implemented.

---

# GLOBAL RF INDICATOR

States include:

- ALL OUTPUTS OFF
- RF ON
- SPOT ACTIVE
- TX ACTIVE

---

# COM PORT SYSTEM

Features:

- Connect/disconnect
- COM conflict detection
- Connection status display

Example status messages:

```text
CONNECTED TO COM5 @ 115200
```

```text
NOT CONNECTED TO USB COM PORT
```

---

# RADIO PROFILE SYSTEM

Profiles stored in:

```text
radio_profiles.json
```

GUI owns all profile math.

Current math models include:

- direct
- multiply
- linear_map

---

# SUPPORTED RADIO PROFILE TYPES

Examples:

- Swan 350C
- Swan 400
- Eico 720
- Heathkit DX-100

---

# KNOWN LIMITATIONS

## SI5351 Library Limitation

Current Adafruit SI5351 library behavior:

- Enable control operates at chip level
- Not true independent per-clock enable

This affects:

- OUT0–OUT2 together
- OUT3–OUT5 together

---

## Safety System Limitation

Current safety system warns only.

No automatic RF shutdown enforcement currently implemented.

---

# REPOSITORY STRUCTURE

```text
firmware/
    Arduino Nano firmware

pc_software/
    Python / PySide6 GUI

docs/
    Documentation
    Manuals
    Architecture notes

installer/
    PyInstaller scripts
    Inno Setup scripts

examples/
    Example radio profiles
    Example configurations
```

---

# IMPORTANT DEVELOPMENT RULES

## Preserve These Architectural Decisions

1. GUI owns all radio math
2. Arduino Nano remains execution engine
3. Preserve OUT0–OUT5 abstraction
4. Preserve floating multi-window architecture
5. Preserve startup RF safety behavior
6. Preserve session restore behavior
7. Preserve compact/full operating modes
8. Preserve Output Manager architecture
9. Preserve global RF indicator
10. Preserve warning-only safety model unless intentionally redesigned

---

# PACKAGING / DISTRIBUTION GOALS

System intended for:

- Non-programmer ham radio operators
- Easy Windows installation
- Public GitHub distribution
- Open-source experimentation

---

# PLANNED NEXT PHASE

## Packaging

- Build standalone Windows EXE
- Build Windows installer

---

## Usability

- Radio profile editor GUI
- Searchable help system
- Version information system

---

## Documentation

- Printable user manual
- Hardware wiring guide
- Complete schematic diagrams

---

## Public Release

- Publish GitHub repository publicly
- Publish installer releases
- Publish stable tagged freeze versions

---

# RECOMMENDED GITHUB WORKFLOW

Normal workflow:

```text
Edit
Commit
Push
```

Definitions:

- Commit = local engineering snapshot
- Push = upload to GitHub server

---

# RECOMMENDED CHATGPT START COMMAND

```text
Continue SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE

Use CHATGPT_REBUILD_REPORT.md as the primary architecture reference.

Do not redesign architecture unless explicitly requested.

GUI owns all radio math.
Arduino Nano is execution engine only.

Preserve:
- OUT0 through OUT5 architecture
- BNC1 through BNC6 mapping
- Session restore
- RF startup safety
- Floating radio windows
- Output Manager
- Global RF indicator
- Warning-only safety monitor

Continue packaging/documentation phase.
```

---

# END OF REBUILD REPORT