# Radio Profile Builder Design

# SI5351 Multi-Radio VFO Control Platform

---

# Purpose

The Radio Profile Builder allows users to add their own radios without manually editing `radio_profiles.json`.

The goal is to support many different vintage transmitters, transceivers, external VFO schemes, and local oscillator arrangements.

This feature is intended for normal ham radio operators, not just programmers.

---

# Design Goal

The builder should ask radio-style questions instead of JSON/programming questions.

Good wording:

- My VFO output equals the operating frequency
- My transmitter multiplies the VFO frequency
- My radio uses a separate VFO range
- My transceiver needs a local oscillator offset
- My radio uses high-side or low-side injection

Avoid exposing users to internal terms first, such as:

- `mode = direct`
- `mode = multiply`
- `mode = linear_map`

Those internal names can still exist in the saved JSON.

---

# User Workflow

Recommended workflow:

```text
Add New Radio
→ Enter radio name
→ Choose radio category
→ Add one or more bands
→ Define operating RF range
→ Choose VFO/LO relationship
→ Enter required VFO/output details
→ Validate profile
→ Save profile
→ Reload profiles into GUI