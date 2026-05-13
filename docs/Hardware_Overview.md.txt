# Hardware Overview

# SI5351 Multi-Radio VFO Control Platform

---

# Hardware Architecture

The system uses:

- Arduino Nano
- TCA9548A I2C multiplexer
- Two Adafruit SI5351 clock generator modules
- Six RF outputs

The PC GUI communicates with the Nano over USB serial.

The Nano communicates with the SI5351 modules over I2C.

---

# System Architecture

```text
PC GUI
   |
USB Serial
   |
Arduino Nano
   |
TCA9548A I2C Multiplexer
   |
+-------------------+
|                   |
SI5351 #1       SI5351 #2
```

---

# I2C Addressing

Both SI5351 modules use:

```text
0x60
```

The TCA9548A isolates the devices onto separate I2C channels.

---

# TCA9548A Channel Mapping

| Channel | Device |
|---|---|
| 0 | SI5351 #1 |
| 1 | SI5351 #2 |

---

# RF Output Mapping

| BNC Output | Logical Output | SI5351 Module | Clock |
|---|---|---|---|
| BNC 1 | OUT0 | SI5351 #1 | CLK0 |
| BNC 2 | OUT1 | SI5351 #1 | CLK1 |
| BNC 3 | OUT2 | SI5351 #1 | CLK2 |
| BNC 4 | OUT3 | SI5351 #2 | CLK0 |
| BNC 5 | OUT4 | SI5351 #2 | CLK1 |
| BNC 6 | OUT5 | SI5351 #2 | CLK2 |

---

# USB Interface

The Nano connects to the PC via USB serial.

Default configuration:

```text
115200 baud
8N1
```

---

# RF Control Model

- PTT LOW = TX / RF ON
- PTT HIGH = RX / RF OFF
- SPOT enables RF during RX only
- TX overrides SPOT

---

# Important Safety Rule

At startup:

- RF OFF
- SPOT OFF

The application must never automatically restore RF ON state after restart.

---

# Current Hardware Limitations

The current Adafruit SI5351 library performs enable control at chip level.

This means:

- OUT0–OUT2 are grouped together
- OUT3–OUT5 are grouped together

True independent per-clock RF enable is not currently implemented.

---

# Future Planned Hardware Documentation

Planned future additions:

- Full wiring diagrams
- Power supply documentation
- RF output filtering
- PTT interface examples
- Complete schematic diagrams