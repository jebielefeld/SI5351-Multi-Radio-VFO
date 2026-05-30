# SI5351 Multi-Radio VFO User Manual

## Version 6.0

Author: John Bielefeld K1JEB

---

# 1. Introduction

The SI5351 Multi-Radio VFO platform is a PC-controlled RF frequency synthesis and radio-control system designed primarily for vintage amateur radio transmitters and transceivers.

The platform combines:

* Arduino Nano firmware
* Multiple Adafruit SI5351 frequency synthesizer modules
* TCA9548A I2C expansion hardware
* PySide6 desktop GUI software
* Radio profile translation architecture
* Multi-window radio control
* EEPROM calibration storage
* RF output management

The system evolved beyond a simple VFO into a modular RF instrumentation and radio-control platform capable of supporting multiple simultaneous radio configurations.

The architecture allows the operator to:

* control multiple radios simultaneously
* assign radios to independent RF outputs
* perform automatic frequency translation
* calibrate synthesizer hardware
* save and restore operating sessions
* manage RF output routing
* create and edit radio profiles

The platform is especially useful for vintage equipment that originally depended on:

* crystal oscillators
* external VFOs
* local oscillators
* frequency control units

Currently supported radio profiles include:

* Swan 400
* Swan 350C
* Heathkit DX-100
* Eico 720

Additional profiles may be added using the integrated Profile Editor subsystem.

---

# 2. Installation

## 2.1 Installer Installation

The Windows installer package installs:

* the main application
* required Qt runtime libraries
* support modules
* desktop shortcut
* packaged configuration support

To install:

1. Run:

```text
SI5351_Multi_Radio_VFO_Setup.exe
```

2. Follow the installer prompts.

3. Allow desktop shortcut creation if desired.

4. Complete installation.

After installation, launch the application using:

```text
SI5351 Multi-Radio VFO
```

from either:

* the desktop shortcut
* the Windows Start Menu

---

## 2.2 USB Connection

The hardware platform communicates through a USB serial connection using the Arduino Nano.

Depending on the Nano hardware version, Windows may require:

* CH340 driver
* FTDI driver

Most modern Windows installations install these automatically.

After connecting the Nano:

1. Open the application.
2. Use the COM-port selector.
3. Select the appropriate COM port.
4. Press:

```text
Connect
```

The connection status will update when communication is successful.

---

## 2.3 First Startup

At first startup:

* RF outputs restore OFF for safety
* the last operating session may restore automatically
* previously saved window layouts may restore
* saved calibration values automatically reload from Nano EEPROM

This behavior prevents accidental RF output after restart or reboot.

---

# 3. Main Window Overview

The Main Window acts as the primary system control console.

Functions include:

* COM-port management
* connection control
* radio-window management
* output management
* calibration access
* profile-editor access
* session management
* monitor control
* help/documentation access

---

## 3.1 Main Window Layout

The Main Window contains two primary control rows.

### Operating Controls

Primary operating controls include:

* COM selection
* Refresh
* Connect
* Disconnect
* New Radio
* Outputs
* Arrange

These controls are used during normal operating workflow.

---

### Utility Controls

Secondary utility controls include:

* Monitor
* Calibration
* Reload
* Profiles
* Save
* Load
* Help
* About

These controls provide access to support subsystems and utilities.

---

## 3.2 Frequency Display

The large central frequency display provides the active operating frequency information.

The display is intentionally large and centered for:

* bench operation
* operating visibility
* RF instrumentation appearance

The display design emphasizes:

* readability
* operator focus
* reduced visual clutter

---

## 3.3 Monitor Mode

The Monitor ON/OFF button controls the visibility of serial-monitor communications.

Important:

The following responses are visible only when:

```text
Monitor ON
```

is enabled:

* ID Test
* Read Calibration
* calibration responses
* serial diagnostic responses

This behavior is intentional and helps reduce unnecessary serial output during normal operation.

---

## 3.4 Session Management

The Main Window supports session persistence.

The platform can automatically save and restore:

* window positions
* radio assignments
* output assignments
* tuning states
* compact/full window modes

Safety behavior:

```text
RF outputs always restore OFF
```

after restart or application launch.

This prevents accidental RF transmission.

---

# 4. Calibration System

The SI5351 Multi-Radio VFO platform includes a complete EEPROM-based frequency calibration architecture.

Calibration allows the operator to precisely align each SI5351 synthesizer board to a known frequency reference using an external frequency counter.

Unlike many hobby synthesizer systems, the calibration values are stored locally inside the Arduino Nano EEPROM. This allows each physical hardware unit to retain its own correction values independently from the PC software installation.

Advantages include:

* portable calibrated hardware
* automatic calibration restoration
* simplified hardware swapping
* per-unit frequency correction

---

## 4.1 Calibration Philosophy

The calibration system works by generating a highly stable:

```text
10.000000 MHz
```

test signal.

The operator connects a precision frequency counter to the selected RF output and adjusts the calibration correction value until the counter reads exactly:

```text
10.000000 MHz
```

The correction value is then stored in EEPROM.

At future startup:

* the Nano automatically restores the saved correction values
* the PC software automatically reads and uses the restored calibration

This creates a persistent hardware-based calibration architecture.

---

## 4.2 Opening the Calibration Window

To open the Calibration Window:

1. Launch the main application.
2. Connect to the Nano using the correct COM port.
3. Press:

```text
Calibration
```

from the Main Window.

The Calibration Window will appear.

Screenshot:

![Calibration Window](screenshots/calibration_window.png)

---

## 4.3 Selecting SI5351 #1 or #2

The system supports calibration of both installed SI5351 boards.

Use the:

```text
Target
```

selector to choose:

* SI5351 #1
* SI5351 #2

The selected target determines which synthesizer receives the calibration commands.

---

## 4.4 Frequency Counter Connection

Connect the frequency counter to the appropriate RF output.

Recommended:

* use a stable frequency counter
* use short RF cables
* avoid excessive loading

A GPS-disciplined counter or laboratory-grade counter provides the best results.

---

## 4.5 Entering Calibration Mode

Press:

```text
Start Calibration
```

The selected synthesizer begins generating:

```text
10.000000 MHz
```

The frequency counter should now display approximately 10 MHz.

---

## 4.6 Adjusting Calibration

Use the UP and DOWN controls to adjust the correction value.

Step sizes may include:

* 1000
* 100
* 10
* 1

The operator should gradually reduce the step size while approaching the target frequency.

Example workflow:

1. Coarse adjustment using 1000-step increments
2. Fine adjustment using 100-step increments
3. Final trim using 10-step increments
4. Optional final correction using 1-step increments

Adjust until the frequency counter reads:

```text
10.000000 MHz
```

exactly.

---

## 4.7 Saving Calibration

After achieving the correct frequency:

1. Press:

```text
SAVE CAL
```

2. The correction value is written into Nano EEPROM.

The value will automatically restore at future startup.

---

## 4.8 Exiting Calibration Mode

To safely exit calibration mode:

1. Press:

```text
EXIT
```

This ensures the Nano properly exits calibration operation and returns to normal RF-control mode.

Do not simply close the window using the window-frame X button unless the calibration session has already been exited normally.

---

# 5. Compact Radio Window

The Compact Radio Window is designed for efficient operating workflow and reduced desktop clutter.

The compact layout allows multiple radio windows to remain visible simultaneously while preserving important operating controls.

Screenshot:

![Compact Window](screenshots/compact_window.png)

---

## 5.1 Purpose

The Compact Window supports:

* multi-radio operation
* reduced screen usage
* rapid tuning workflow
* simultaneous radio monitoring

The window is optimized for actual operating use rather than configuration editing.

---

## 5.2 Controls

The Compact Window includes:

* frequency display
* tuning controls
* band selection
* output assignment
* SPOT control
* TX/RX indication
* compact/full toggle

---

## 5.3 TX/RX Indicators

The TX/RX indicators provide immediate RF-state visibility.

Typical behavior:

* Green = RX
* Red = TX

This allows rapid visual confirmation of radio state.

---

## 5.4 SPOT Mode

SPOT mode allows RF output during receive operation for tuning and alignment purposes.

Important behavior:

* SPOT operates only during RX
* TX overrides SPOT
* RF safety logic remains active

---

## 5.5 Compact vs Full Mode

Each Radio Window can switch between:

* Compact mode
* Full mode

Compact mode emphasizes operating efficiency and reduced desktop footprint.

Full mode exposes additional controls and configuration options.

The platform automatically remembers the selected mode during session restore.

---

# 6. Output Manager

The Output Manager provides centralized visualization of RF output assignments.

Screenshot:

![Output Manager](screenshots/output_manager.png)

---

## 6.1 Purpose

The Output Manager allows the operator to quickly identify:

* which radio owns each output
* active RF state
* SPOT state
* TX state
* output assignments

This becomes increasingly important when operating multiple simultaneous radio windows.

---

## 6.2 Output Architecture

The system currently supports:

```text
OUT0 through OUT5
```

Mapped as:

```text
OUT0 = SI5351 #1 CLK0
OUT1 = SI5351 #1 CLK1
OUT2 = SI5351 #1 CLK2
OUT3 = SI5351 #2 CLK0
OUT4 = SI5351 #2 CLK1
OUT5 = SI5351 #2 CLK2
```

---

## 6.3 Conflict Prevention

The software includes output conflict prevention logic.

This prevents multiple radio windows from accidentally controlling the same RF output simultaneously.

The Output Manager provides immediate visibility into current ownership status.

---

## 6.4 RF Safety

RF outputs always restore OFF at startup.

This prevents accidental RF transmission after:

* reboot
* restart
* session restore

The operator must intentionally re-enable RF operation.

---

# 7. Profile Editor

The Profile Editor allows graphical creation and editing of radio profiles.

Screenshot:

![Profile Editor](screenshots/profile_window.png)

---

## 7.1 Purpose

The Profile Editor replaces manual editing of:

```text
radio_profiles.json
```

This greatly simplifies profile management and reduces configuration errors.

---

## 7.2 Supported Functions

The Profile Editor supports:

* profile creation
* profile editing
* band mapping
* translation-mode selection
* validation checking
* profile previewing

---

## 7.3 Translation Modes

Supported translation modes include:

* direct
* linear_map
* multiply

These modes allow the GUI to calculate required VFO or LO frequencies for different radio architectures.

---

## 7.4 Validation System

The integrated validation system checks profiles for:

* missing fields
* invalid ranges
* translation errors
* configuration mistakes

This helps prevent invalid operating configurations.

---

## 7.5 Reload Profiles

After editing profiles:

1. Save changes.
2. Return to the Main Window.
3. Press:

```text
Reload
```

This reloads profiles without restarting the application.

---

# 8. Troubleshooting

## 8.1 COM Port Not Available

Possible causes:

* Nano disconnected
* USB driver missing
* COM port already in use

Solutions:

* reconnect USB cable
* restart application
* verify Device Manager
* verify CH340 or FTDI driver installation

---

## 8.2 No RF Output

Possible causes:

* output disabled
* SPOT inactive
* TX not active
* incorrect output assignment

Solutions:

* verify Output Manager
* verify output assignment
* enable SPOT
* verify TX state

---

## 8.3 Calibration Not Saving

Possible causes:

* SAVE CAL not pressed
* EEPROM write failure
* serial communication interruption

Solutions:

* repeat calibration
* verify COM connection
* restart application
* verify Nano operation

---

## 8.4 Monitor Responses Not Visible

Important:

Serial responses are visible only when:

```text
Monitor ON
```

is enabled.

This includes:

* ID Test
* Read Calibration
* serial diagnostic responses

---

## 8.5 Profile Changes Not Appearing

After editing profiles:

1. Save profile changes.
2. Press:

```text
Reload
```

from the Main Window.

This reloads profile data without restarting the application.

---

## 8.6 RF Output Restores OFF After Restart

This is intentional safety behavior.

The platform always restores RF outputs OFF at startup to prevent accidental transmission.

---

# 9. Hardware Architecture

The SI5351 Multi-Radio VFO platform uses a modular RF-control architecture centered around the Arduino Nano and multiple SI5351 synthesizer modules.

The design intentionally separates:

* GUI control logic
* radio translation math
* RF synthesis hardware
* output routing
* calibration storage

This allows the system to scale into a flexible RF instrumentation platform rather than a single-purpose VFO.

---

## 9.1 Core Hardware Components

Current hardware architecture includes:

* Arduino Nano ATmega328
* TCA9548A I2C multiplexer
* Two Adafruit SI5351 synthesizer modules
* USB serial interface
* RF output routing
* future RF expansion capability

---

## 9.2 Arduino Nano

The Arduino Nano acts as the hardware-control engine.

Primary Nano responsibilities:

* serial communications
* SI5351 programming
* RF-output control
* EEPROM calibration storage
* PTT monitoring
* output enable control

The Nano intentionally does not perform radio frequency translation calculations.

All radio translation math is handled by the PC GUI software.

This design simplifies firmware architecture and allows rapid radio-profile expansion without firmware changes.

---

## 9.3 TCA9548A I2C Multiplexer

The TCA9548A allows multiple SI5351 modules with identical I2C addresses to coexist on the same bus.

Current architecture uses:

```text id="mbj4dg"
TCA9548A address 0x70
```

with:

* Channel 0 → SI5351 #1
* Channel 1 → SI5351 #2

This architecture allows future expansion beyond a single synthesizer module.

---

## 9.4 SI5351 Synthesizer Modules

The current platform uses:

* Two Adafruit SI5351 modules
* Each providing three clock outputs

Total available outputs:

```text id="zjlwm2"
6 RF outputs
```

Mapped as:

```text id="4ikrbz"
OUT0 = SI5351 #1 CLK0
OUT1 = SI5351 #1 CLK1
OUT2 = SI5351 #1 CLK2
OUT3 = SI5351 #2 CLK0
OUT4 = SI5351 #2 CLK1
OUT5 = SI5351 #2 CLK2
```

---

## 9.5 Output Architecture

The software abstracts the hardware into logical outputs:

```text id="1yuyvf"
OUT0 through OUT5
```

This abstraction simplifies:

* radio assignment
* RF routing
* output management
* future hardware changes

The operator interacts with logical outputs rather than low-level hardware details.

---

## 9.6 EEPROM Calibration Storage

Each Nano stores calibration values locally inside EEPROM.

Advantages include:

* portable calibrated hardware
* independent hardware calibration
* automatic calibration restoration
* simplified hardware replacement

This allows multiple hardware units to maintain independent correction values without modifying the PC software.

---

## 9.7 USB Communications

The PC communicates with the Nano using USB serial communications.

The serial link carries:

* frequency commands
* RF enable commands
* calibration commands
* diagnostic responses
* TX/RX status

---

## 9.8 RF Safety Architecture

The platform includes several RF safety mechanisms.

Examples:

* RF outputs restore OFF at startup
* TX overrides SPOT
* output conflict prevention
* session-restore RF disable

These protections reduce the possibility of accidental RF transmission.

---

# 10. Session Persistence

The platform includes automatic session persistence.

This allows restoration of operating layouts after:

* reboot
* application restart
* shutdown
* crash recovery

---

## 10.1 Saved Session Information

The platform can restore:

* window positions
* compact/full modes
* radio assignments
* output assignments
* frequency states
* tuning step sizes

This allows rapid recovery of operating configurations.

---

## 10.2 Automatic RF Safety

For safety reasons:

```text id="3ec4mx"
RF outputs always restore OFF
```

after startup.

The operator must intentionally re-enable RF activity.

This prevents accidental RF transmission after restart.

---

## 10.3 Multi-Window Restoration

The platform can restore multiple floating Radio Windows automatically.

This is especially useful for:

* multi-radio operation
* bench testing
* simultaneous receiver/transmitter operation

---

# 11. Multi-Window Operation

One of the major architectural features of the platform is simultaneous multi-radio operation.

The GUI supports multiple independent Radio Windows operating concurrently.

Screenshot:

![Multi Window Layout](screenshots/multi_window_layout.png)

---

## 11.1 Purpose

Multi-window operation allows:

* multiple radios
* multiple outputs
* simultaneous monitoring
* rapid radio switching
* laboratory-style RF workflow

This transforms the platform from a single VFO into a true RF-control environment.

---

## 11.2 Independent Radio Windows

Each Radio Window independently maintains:

* selected radio profile
* selected band
* assigned output
* tuning frequency
* SPOT state
* compact/full mode

This allows simultaneous operation of multiple radios.

---

## 11.3 Output Ownership

The software prevents multiple windows from accidentally controlling the same output simultaneously.

The Output Manager displays current ownership information.

---

## 11.4 Compact Operating Workflow

Compact windows allow efficient desktop usage.

This is especially useful when:

* multiple radios are active
* bench equipment occupies screen space
* continuous monitoring is required

---

# 12. Future Expansion Architecture

The project architecture intentionally supports future expansion.

The platform is evolving toward a modular RF instrumentation system.

---

## 12.1 Planned RF Expansion

Planned RF subsystems include:

* RF switching
* relay sequencing
* output filtering
* RF buffering
* external amplifier stages

---

## 12.2 Panadapter Integration

Future architecture may include:

* AirSpy SDR integration
* spectrum display
* panadapter support

The current GUI architecture already supports future subsystem expansion.

---

## 12.3 Expanded Radio Profiles

Future radio-profile support may include:

* additional Swan radios
* Clegg Thor 6
* Collins equipment
* Johnson transmitters
* Heathkit transceivers
* additional vintage radio platforms

---

## 12.4 Hardware Carrier PCB

Future hardware plans may include:

* integrated carrier PCB
* modular RF connectors
* integrated power routing
* output switching
* enclosure integration

---

## 12.5 Enclosure Development

Future enclosure goals include:

* standalone operation
* RF shielding
* front-panel integration
* professional bench appearance

---

# 13. Version History and Freeze Points

The project uses engineering freeze points to identify stable architecture milestones.

Freeze points allow:

* stable rollback targets
* milestone tracking
* architectural documentation
* release management

---

## 13.1 Important Freeze Points

### Initial Multi-Output Architecture

```text id="tdot1w"
SI5351_VFO_PC_v2_OUT0_OUT5_STABLE
```

Established:

* TCA9548A architecture
* dual SI5351 support
* OUT0–OUT5 mapping

---

### Multi-Window Architecture

```text id="0id16y"
SI5351_VFO_PC_v4A_FLOATING_WINDOWS
```

Established:

* independent radio windows
* simultaneous radio operation

---

### Session Persistence

```text id="tm8v87"
SI5351_VFO_PC_v4C_SESSION_RESTORE
```

Established:

* automatic session restoration
* window persistence
* operating-state persistence

---

### Installer Validation

```text id="ob8tcu"
SI5351_VFO_PLATFORM_v6_INSTALLER_VALIDATED
```

Established:

* PyInstaller deployment
* Inno Setup installer
* desktop shortcut installation
* packaged runtime validation

---

### Main Window Ergonomic Freeze

```text id="tqkjzl"
SI5351_VFO_MAIN_WINDOW_v9E_690PX_STABLE
```

Established:

* compact two-row toolbar architecture
* improved operator ergonomics
* production UI layout

---

## 13.2 Current Project Status

Current project status:

```text id="a98m0l"
SI5351_VFO_PLATFORM_v6_DOCUMENTATION_PHASE_ACTIVE
```

The platform now includes:

* stable architecture
* stable GUI
* installer deployment
* calibration subsystem
* profile editor
* help system
* release documentation
* user manual development


---


