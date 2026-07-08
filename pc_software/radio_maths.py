###########################################################################
# radio_maths.py
#
# SI5351 Multi-Radio VFO Platform
#
# Frequency Translation Engine
#
# Purpose:
#   Converts the operator's desired RF frequency into the actual SI5351
#   output frequency required by the selected radio and band.
#
# Description:
#   Vintage radios often do not use a VFO frequency that is the same as the
#   frequency shown on the dial. Depending on the radio design, the oscillator
#   may operate directly on the RF frequency, at a divided/multiplied
#   frequency, above the RF frequency, below the RF frequency, or across a
#   mapped range.
#
#   This module performs that translation in the PC application. The Arduino
#   Nano firmware receives only the final SI5351 output frequency.
#
# Ham Radio Analogy:
#   This module is the equivalent of the frequency conversion chart or dial
#   calibration mechanism inside a vintage transmitter or transceiver.
#
# Design Rule:
#   The PC owns the radio-specific math. The Nano firmware remains simple:
#   it only generates the frequency it is told to generate.
#
# Supported Translation Modes:
#   direct:
#       SI5351 output frequency equals the desired RF frequency.
#
#   multiply:
#       SI5351 output frequency equals RF frequency divided by a multiplier.
#       This is useful when the radio multiplies the oscillator internally.
#
#   lo_offset:
#       SI5351 output frequency is offset from the RF frequency by an IF or
#       mixing frequency.
#
#   linear_map:
#       RF frequency is mapped across a separate VFO range. This is useful
#       for vintage VFOs where the dial tuning range does not numerically
#       match the final RF output range.
#
# Revision History:
#   v6.1c
#       - Stable profile-based frequency translation.
#       - Supports direct, multiply, lo_offset, and linear_map modes.
#       - Returns structured FrequencyResult objects for GUI use.
#
###########################################################################

from dataclasses import dataclass


###########################################################################
# dataclass FrequencyResult
#
# Purpose:
#   Return object used by calculate_output_frequency().
#
# Description:
#   A dataclass is a compact Python way to define a simple data container.
#   It is similar to a C struct used to return several related values from
#   one function.
#
# Fields:
#   ok:
#       True if the calculation succeeded.
#
#   rf_hz:
#       Operator-requested RF frequency in Hertz.
#
#   output_hz:
#       Calculated SI5351 output frequency in Hertz.
#
#   filter_band:
#       Optional filter-band name from the radio profile.
#
#   message:
#       Human-readable status or error message.
#
###########################################################################
@dataclass
class FrequencyResult:
    ok: bool
    rf_hz: int
    output_hz: int
    filter_band: str
    message: str = ""


###########################################################################
# calculate_output_frequency()
#
# Purpose:
#   Convert desired RF operating frequency into SI5351 output frequency.
#
# Inputs:
#   profile:
#       Radio profile dictionary loaded from radio_profiles.json.
#
#   band_id:
#       Selected band identifier from the profile.
#
#   rf_hz:
#       Desired operating frequency in Hertz.
#
# Returns:
#   FrequencyResult object containing:
#       - success/failure flag
#       - requested RF frequency
#       - calculated SI5351 output frequency
#       - optional filter-band name
#       - status/error message
#
# Operation:
#   1. Locate the selected band in the radio profile.
#   2. Confirm the band is enabled.
#   3. Confirm the requested RF frequency is inside the allowed band range.
#   4. Apply the selected translation mode.
#   5. Return the calculated SI5351 output frequency.
#
# Notes for Hams:
#   The "RF frequency" is what the operator thinks of as the operating
#   frequency. The "output frequency" is what the SI5351 must actually
#   generate to make that radio operate on the desired RF frequency.
#
###########################################################################
def calculate_output_frequency(
    profile: dict, band_id: str, rf_hz: int
) -> FrequencyResult:
    band = find_band(profile, band_id)

    if band is None:
        return FrequencyResult(False, rf_hz, 0, "", "Band not found")

    if not band.get("enabled", True):
        return FrequencyResult(False, rf_hz, 0, "", "Band is disabled")

    if rf_hz < band["rf_min_hz"] or rf_hz > band["rf_max_hz"]:
        return FrequencyResult(False, rf_hz, 0, "", "Frequency outside selected band")

    translation = band["translation"]
    mode = translation["mode"]

    #######################################################################
    # direct mode
    #
    # The SI5351 output frequency is exactly the requested RF frequency.
    #######################################################################
    if mode == "direct":
        output_hz = rf_hz

    #######################################################################
    # multiply mode
    #
    # Some radios multiply the oscillator internally. In that case, the VFO
    # must run at the RF frequency divided by the radio's multiplier.
    #######################################################################
    elif mode == "multiply":
        multiplier = translation["multiplier"]
        output_hz = round(rf_hz / multiplier)

    #######################################################################
    # lo_offset mode
    #
    # Used when the oscillator is offset from the RF frequency by an IF or
    # mixing frequency.
    #
    # high-side LO:
    #       oscillator = RF + IF
    #
    # low-side LO:
    #       oscillator = RF - IF
    #######################################################################
    elif mode == "lo_offset":
        if_hz = translation["if_hz"]
        lo_side = translation["lo_side"]

        if lo_side == "high":
            output_hz = rf_hz + if_hz
        elif lo_side == "low":
            output_hz = rf_hz - if_hz
        else:
            return FrequencyResult(False, rf_hz, 0, "", "Invalid LO side")

    #######################################################################
    # linear_map mode
    #
    # Maps one frequency range onto another frequency range.
    #
    # This is useful for emulating vintage VFOs where the radio's operating
    # band and the VFO tuning range move together but are not numerically
    # identical.
    #######################################################################
    elif mode == "linear_map":
        rf_start = translation["rf_start_hz"]
        rf_end = translation["rf_end_hz"]
        vfo_start = translation["vfo_start_hz"]
        vfo_end = translation["vfo_end_hz"]

        if rf_hz < rf_start or rf_hz > rf_end:
            return FrequencyResult(
                False,
                rf_hz,
                0,
                "",
                "Frequency outside VFO mapping range",
            )

        rf_span = rf_end - rf_start
        vfo_span = vfo_end - vfo_start

        output_hz = round(vfo_start + ((rf_hz - rf_start) * vfo_span / rf_span))

    else:
        return FrequencyResult(
            False,
            rf_hz,
            0,
            "",
            f"Unsupported translation mode: {mode}",
        )

    return FrequencyResult(
        ok=True,
        rf_hz=rf_hz,
        output_hz=output_hz,
        filter_band=band.get("filter_band", ""),
        message="OK",
    )


###########################################################################
# find_band()
#
# Purpose:
#   Locate a band definition inside a radio profile.
#
# Inputs:
#   profile:
#       Radio profile dictionary.
#
#   band_id:
#       Band identifier to find.
#
# Returns:
#   Band dictionary if found.
#   None if no matching band exists.
#
# Notes:
#   The profile file may contain several bands for one radio. This helper
#   isolates the lookup logic so calculate_output_frequency() can focus on
#   the frequency math.
#
###########################################################################
def find_band(profile: dict, band_id: str):
    for band in profile.get("bands", []):
        if band.get("id") == band_id:
            return band

    return None
