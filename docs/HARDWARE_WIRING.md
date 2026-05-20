# SI5351 Multi-Radio VFO Hardware Wiring Guide

## Overview

This document describes the hardware wiring architecture for the SI5351 Multi-Radio VFO platform.

The system is a USB-powered RF synthesis and control platform intended for vintage radio experimentation and multi-radio frequency generation.

The platform currently includes:

- Arduino Nano controller
- TCA9548A I2C multiplexer
- Two Adafruit SI5351 modules
- Six RF outputs
- Six PTT input connections
- USB PC control and power

The platform intentionally excludes radio-specific RF conditioning hardware.

Future accessory modules may include:

- RF buffering
- low-pass filtering
- level conversion
- radio-specific drive adaptation
- relay switching
- amplifier interface modules


## Hardware Architecture Schematic

The current hardware architecture schematic is shown below.

![Hardware Architecture](../hardware/kicad/SI5351_Multi_Radio_VFO_Hardware/docs/schematics/SI5351_VFO_HW_v0_9_ARCHITECTURE_STABLE.svg)


## System Architecture

The current hardware platform is organized as:

PC USB
→ Arduino Nano
→ TCA9548A I2C Multiplexer
→ Two Adafruit SI5351 Modules
→ Six RF Outputs

The Arduino Nano provides:

- USB communications
- USB power distribution
- PTT input monitoring
- frequency command routing
- output control

The TCA9548A allows multiple SI5351 modules with identical I2C addresses to coexist on the same I2C bus.

Current output mapping:

| Output | Module | Clock |
|---|---|---|
| OUT0 | SI5351 #1 | CLK0 |
| OUT1 | SI5351 #1 | CLK1 |
| OUT2 | SI5351 #1 | CLK2 |
| OUT3 | SI5351 #2 | CLK0 |
| OUT4 | SI5351 #2 | CLK1 |
| OUT5 | SI5351 #2 | CLK2 |


## Power Architecture

The current platform is powered entirely from the host PC USB connection through the Arduino Nano USB interface.

The Arduino Nano distributes the +5V_SYSTEM rail to:

- TCA9548A I2C multiplexer
- SI5351 module #1
- SI5351 module #2

Current architecture intentionally avoids:

- internal AC mains wiring
- internal switching power supplies
- high-current RF amplification stages

Advantages of the current USB-powered architecture include:

- reduced RF noise
- simplified grounding
- reduced enclosure complexity
- lower heat generation
- simplified development and debugging

Future accessory modules may use independent external power sources as required.


## Arduino Nano Connections

The Arduino Nano acts as the central controller for the platform.

Primary Nano responsibilities include:

- USB communications with PC software
- I2C master control
- SI5351 frequency command routing
- PTT input monitoring
- future expansion control functions

### Nano Power Connections

| Nano Pin | Function |
|---|---|
| 5V | +5V_SYSTEM distribution |
| GND | system ground |

### Nano I2C Connections

| Nano Pin | Destination |
|---|---|
| A4 | TCA9548A SDA |
| A5 | TCA9548A SCL |

### Nano PTT Inputs

| Nano Pin | Function |
|---|---|
| D2 | PTT0_IN |
| D3 | PTT1_IN |
| D4 | PTT2_IN |
| D5 | PTT3_IN |
| D6 | PTT4_IN |
| D7 | PTT5_IN |

PTT inputs are intended for future TX/RX awareness and output control functions.


## TCA9548A I2C Multiplexer Connections

The TCA9548A allows multiple SI5351 modules with identical I2C addresses to coexist on the same I2C bus.

Default TCA9548A I2C address:

```text
0x70
```

### TCA9548A Power Connections

| TCA9548A Pin | Connection |
|---|---|
| VIN | +5V_SYSTEM |
| GND | system ground |

### TCA9548A I2C Connections

| TCA9548A Pin | Destination |
|---|---|
| SDA | Arduino Nano A4 |
| SCL | Arduino Nano A5 |

### TCA9548A Channel Assignments

| TCA9548A Channel | Destination |
|---|---|
| CH0 | SI5351 Module #1 |
| CH1 | SI5351 Module #2 |

Unused TCA9548A channels are reserved for future expansion.


## SI5351 Module Connections

The platform currently uses two Adafruit SI5351 clock-generator breakout modules.

Each SI5351 module provides:

- three independent clock outputs
- programmable RF synthesis
- shared I2C control through the TCA9548A multiplexer

Default SI5351 I2C address:

```text
0x60
```

### SI5351 Module Power Connections

| SI5351 Pin | Connection |
|---|---|
| VIN | +5V_SYSTEM |
| GND | system ground |

### SI5351 Module I2C Connections

| SI5351 Pin | Destination |
|---|---|
| SDA | TCA9548A SDA |
| SCL | TCA9548A SCL |

### SI5351 RF Output Mapping

| SI5351 Output | System Output |
|---|---|
| Module #1 CLK0 | OUT0 | (AdaFruit SI5351 Module_1)
| Module #1 CLK1 | OUT1 |
| Module #1 CLK2 | OUT2 |
| Module #2 CLK0 | OUT3 | (Adafruit SI5351 Module_2)
| Module #2 CLK1 | OUT4 |
| Module #2 CLK2 | OUT5 |

Each SI5351 module includes onboard I2C pullup resistors.


## RF Output Connectors

The platform currently provides six independent RF outputs.

RF outputs are intended for rear-panel BNC connectors.

### RF Output Connector Mapping

| Connector | Source |
|---|---|
| RF_OUT0_BNC | SI5351 Module #1 CLK0 |
| RF_OUT1_BNC | SI5351 Module #1 CLK1 |
| RF_OUT2_BNC | SI5351 Module #1 CLK2 |
| RF_OUT3_BNC | SI5351 Module #2 CLK0 |
| RF_OUT4_BNC | SI5351 Module #2 CLK1 |
| RF_OUT5_BNC | SI5351 Module #2 CLK2 |

Current RF outputs are low-level synthesis outputs only.

Future accessory modules may provide:

- RF buffering
- filtering
- level conversion
- radio-specific drive adaptation
- amplifier interfaces


## PTT Input Connectors

The platform currently provides six independent PTT input connections.

PTT inputs are intended for rear-panel RCA connectors.

Current PTT logic convention:

```text
LOW  = TX active
HIGH = RX mode
```

### PTT Connector Mapping

| Connector | Nano Pin |
|---|---|
| PTT0_IN | D2 |
| PTT1_IN | D3 |
| PTT2_IN | D4 |
| PTT3_IN | D5 |
| PTT4_IN | D6 |
| PTT5_IN | D7 |

Future firmware may use PTT status for:

- TX/RX indication
- RF output enable control
- sequencing functions
- radio-state awareness


## Grounding Notes

The platform is intended for mixed digital and RF experimentation.

Recommended grounding practices include:

- minimize shared return-current paths
- keep RF return currents separated from digital switching currents
- use short ground connections where practical
- avoid ground-loop wiring between external radio equipment
- maintain clean RF connector grounding to enclosure panels

USB-powered operation currently simplifies grounding and reduces RF noise complications during development.


## Future Expansion

Future accessory modules may include:

- RF buffer amplifiers
- low-pass filter modules
- relay switching modules
- amplifier interface adapters
- radio-specific drive modules
- calibration distribution modules
- output isolation modules

The current platform architecture intentionally separates RF synthesis/control from radio-specific RF hardware.

This allows future experimentation and expansion without redesigning the core platform.


