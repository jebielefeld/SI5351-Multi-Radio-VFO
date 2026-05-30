from profile_models import RadioProfile


def calculate_preview(
    profile: RadioProfile, rf_hz: int
) -> tuple[bool, str, int | None]:
    """
    Calculate the output/VFO frequency for a given RF input frequency.

    Returns:
        (ok, message, output_hz)

        ok:
            True if calculation succeeded

        message:
            band name or error message

        output_hz:
            calculated output frequency in Hz, or None if invalid
    """

    if rf_hz <= 0:
        return False, "RF frequency must be greater than zero.", None

    matching_band = None

    for band in profile.bands:
        if band.rf_start_hz <= rf_hz <= band.rf_end_hz:
            matching_band = band
            break

    if matching_band is None:
        return False, "RF frequency is outside all defined bands.", None

    if profile.math_mode == "direct":
        return True, matching_band.band, rf_hz

    if profile.math_mode == "multiply":
        output_hz = int(round(rf_hz * matching_band.multiplier))
        return True, matching_band.band, output_hz

    if profile.math_mode == "divide":
        if matching_band.multiplier == 0:
            return False, "Multiplier cannot be zero.", None

        output_hz = int(round(rf_hz / matching_band.multiplier))
        return True, matching_band.band, output_hz

    if profile.math_mode == "linear_map":
        rf_span = matching_band.rf_end_hz - matching_band.rf_start_hz
        out_span = matching_band.output_end_hz - matching_band.output_start_hz

        if rf_span <= 0:
            return False, "Invalid RF frequency span.", None

        fraction = (rf_hz - matching_band.rf_start_hz) / rf_span
        output_hz = int(round(matching_band.output_start_hz + fraction * out_span))

        return True, matching_band.band, output_hz

    return False, f"Unsupported math mode: {profile.math_mode}", None


def format_hz_as_mhz(freq_hz: int | None) -> str:
    if freq_hz is None:
        return "---"

    return f"{freq_hz / 1_000_000:.6f} MHz"
