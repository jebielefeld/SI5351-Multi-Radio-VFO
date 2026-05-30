# File: radio_math.py
#
# Converts the desired operating frequency into the actual Si5351 output frequency.
# The PC GUI owns this math.
# The Arduino Nano should only receive the final output frequency.

from dataclasses import dataclass


@dataclass
class FrequencyResult:
    ok: bool
    rf_hz: int
    output_hz: int
    filter_band: str
    message: str = ""


def calculate_output_frequency(profile: dict, band_id: str, rf_hz: int) -> FrequencyResult:
    band = find_band(profile, band_id)

    if band is None:
        return FrequencyResult(False, rf_hz, 0, "", "Band not found")

    if not band.get("enabled", True):
        return FrequencyResult(False, rf_hz, 0, "", "Band is disabled")

    if rf_hz < band["rf_min_hz"] or rf_hz > band["rf_max_hz"]:
        return FrequencyResult(False, rf_hz, 0, "", "Frequency outside selected band")

    translation = band["translation"]
    mode = translation["mode"]

    if mode == "direct":
        output_hz = rf_hz

    elif mode == "multiply":
        multiplier = translation["multiplier"]
        output_hz = round(rf_hz / multiplier)

    elif mode == "lo_offset":
        if_hz = translation["if_hz"]
        lo_side = translation["lo_side"]

        if lo_side == "high":
            output_hz = rf_hz + if_hz
        elif lo_side == "low":
            output_hz = rf_hz - if_hz
        else:
            return FrequencyResult(False, rf_hz, 0, "", "Invalid LO side")

    elif mode == "linear_map":
        rf_start = translation["rf_start_hz"]
        rf_end = translation["rf_end_hz"]
        vfo_start = translation["vfo_start_hz"]
        vfo_end = translation["vfo_end_hz"]

        if rf_hz < rf_start or rf_hz > rf_end:
            return FrequencyResult(False, rf_hz, 0, "", "Frequency outside VFO mapping range")

        rf_span = rf_end - rf_start
        vfo_span = vfo_end - vfo_start

        output_hz = round(vfo_start + ((rf_hz - rf_start) * vfo_span / rf_span))

    else:
        return FrequencyResult(False, rf_hz, 0, "", f"Unsupported translation mode: {mode}")

    return FrequencyResult(
        ok=True,
        rf_hz=rf_hz,
        output_hz=output_hz,
        filter_band=band.get("filter_band", ""),
        message="OK"
    )


def find_band(profile: dict, band_id: str):
    for band in profile.get("bands", []):
        if band.get("id") == band_id:
            return band
    return None