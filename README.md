# SI5351 Multi-Radio VFO Control Platform

A Windows PC-controlled multi-radio VFO platform for vintage ham radio equipment.

This project uses a Python / PySide6 graphical control program, an Arduino Nano, a TCA9548A I2C multiplexer, and two Adafruit SI5351 clock generator modules to provide up to six independently controlled RF outputs.

Current freeze point:

```text
SI5351_VFO_PC_v4D6E_PREVENT_ACCIDENTAL_MAXIMIZE_STABLE

_________________________________________________________________________

Project Status

This project is currently functional and under active development.

Stable features include:

Multi-radio floating control windows
BNC 1 through BNC 6 output labeling
OUT0 through OUT5 SI5351 output control
Output Manager
Global RF indicator
PTT feedback display
Per-window SPOT control
Session auto-restore
COM port conflict detection
Band-aware safety warning system
Window position safety
Snap/maximize protection for radio windows
Hardware Overview

The hardware platform uses:

Arduino Nano
TCA9548A I2C multiplexer
Two Adafruit SI5351 clock generator modules
Six RF output connectors labeled BNC 1 through BNC 6

Output mapping:

BNC Output	Logical Output	SI5351 Module	Clock Output
BNC 1	OUT0	SI5351 #1	CLK0
BNC 2	OUT1	SI5351 #1	CLK1
BNC 3	OUT2	SI5351 #1	CLK2
BNC 4	OUT3	SI5351 #2	CLK0
BNC 5	OUT4	SI5351 #2	CLK1
BNC 6	OUT5	SI5351 #2	CLK2
Software Architecture

The system uses a split architecture:

Component	Role
Python / PySide6 GUI	System brain
Arduino Nano firmware	Execution engine
SerialLink	Shared COM interface
radio_profiles.json	Radio frequency translation data

The GUI owns all radio math. The Arduino firmware executes frequency and RF enable commands.

Serial Protocol

Frequency commands:

F0xxxxxxxxxxx;   Set OUT0 frequency
F1xxxxxxxxxxx;   Set OUT1 frequency
F2xxxxxxxxxxx;   Set OUT2 frequency
F3xxxxxxxxxxx;   Set OUT3 frequency
F4xxxxxxxxxxx;   Set OUT4 frequency
F5xxxxxxxxxxx;   Set OUT5 frequency

RF enable commands:

E01;   OUT0 RF ON
E00;   OUT0 RF OFF
E11;   OUT1 RF ON
E10;   OUT1 RF OFF

PTT feedback:

TXx;
RXx;
RF Control Model
PTT LOW = TX / RF ON
PTT HIGH = RX / RF OFF
SPOT enables RF in RX only
TX overrides SPOT
RF and SPOT are forced OFF at program startup
Repository Layout
firmware/       Arduino Nano firmware
pc_software/    Python / PySide6 PC control software
docs/           Documentation and reports
installer/      Build and installer scripts
examples/       Example radio profiles and test files
Current Limitations
The Adafruit SI5351 library provides chip-level output enable behavior, not true independent per-clock RF enable.
The current safety system warns the operator but does not block RF operation.
Installer, user manual, profile editor, and full schematic documentation are planned future work.
Planned Next Phase

Planned enhancements:

Build standalone Windows EXE
Create Windows installer for non-programmer users
Add GUI radio profile editor
Add searchable in-app help
Create printable user manual
Create full hardware wiring schematic
Publish first official GitHub release
License

This project is released under the MIT License.

_________________________________________________________________

## Basic Hardware Wiring

### Arduino Nano → TCA9548A

| Nano Pin | TCA9548A |
|---|---|
| A4 | SDA |
| A5 | SCL |
| 5V | VIN |
| GND | GND |

### TCA9548A → SI5351 Modules

Both SI5351 modules use I2C address 0x60 and are isolated through separate TCA9548A channels.

| TCA9548A Channel | Device |
|---|---|
| Channel 0 | SI5351 #1 |
| Channel 1 | SI5351 #2 |

### RF Output Mapping

| Output | Physical Connector |
|---|---|
| OUT0 | BNC 1 |
| OUT1 | BNC 2 |
| OUT2 | BNC 3 |
| OUT3 | BNC 4 |
| OUT4 | BNC 5 |
| OUT5 | BNC 6 |