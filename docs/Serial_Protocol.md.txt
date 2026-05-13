# Serial Protocol

# SI5351 Multi-Radio VFO Control Platform

---

# Overview

The PC GUI communicates with the Arduino Nano using a simple ASCII serial protocol.

Connection settings:

```text
115200 baud
8N1
```

Commands are terminated using:

```text
;
```

Examples:

```text
F00010000000;
E01;
```

---

# Frequency Commands

## Format

```text
F<output><frequency>;
```

Where:

| Field | Meaning |
|---|---|
| F | Frequency command |
| output | OUT0 through OUT5 |
| frequency | Frequency in Hz |

---

# Examples

## OUT0 = 10 MHz

```text
F00010000000;
```

---

## OUT3 = 9.058 MHz

```text
F30009058000;
```

---

# RF Enable Commands

## Format

```text
E<output><state>;
```

Where:

| State | Meaning |
|---|---|
| 1 | RF ON |
| 0 | RF OFF |

---

# Examples

## OUT0 ON

```text
E01;
```

## OUT0 OFF

```text
E00;
```

## OUT3 ON

```text
E31;
```

## OUT3 OFF

```text
E30;
```

---

# PTT Feedback

The Nano firmware sends asynchronous TX/RX status messages back to the GUI.

## TX Active

```text
TXx;
```

## RX Active

```text
RXx;
```

---

# RF Control Rules

- PTT LOW = TX / RF ON
- PTT HIGH = RX / RF OFF
- SPOT allowed during RX only
- TX overrides SPOT

---

# Current Protocol Philosophy

The protocol intentionally remains:

- Human-readable
- Debuggable using serial terminals
- Easy to extend
- Low-overhead

---

# Current Stable Outputs

Supported outputs:

```text
OUT0
OUT1
OUT2
OUT3
OUT4
OUT5
```

---

# Important Architecture Rule

Frequency translation math belongs in the GUI, not in the Nano firmware.

The Nano firmware acts as:

- execution engine
- RF controller
- serial command processor

Only.

---

# Future Possible Extensions

Potential future commands:

```text
Status query
Output query
Firmware version query
Temperature monitoring
PLL diagnostics
EEPROM save/load
```