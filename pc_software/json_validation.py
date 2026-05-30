from profile_models import RadioProfile

VALID_MATH_MODES = {
    "direct",
    "multiply",
    "divide",
    "linear_map",
}

VALID_OUTPUTS = {
    "OUT0",
    "OUT1",
    "OUT2",
    "OUT3",
    "OUT4",
    "OUT5",
}


def validate_profile(
    profile: RadioProfile, existing_ids: set[str] | None = None
) -> list[str]:
    errors: list[str] = []

    if not profile.profile_id.strip():
        errors.append("Profile ID is blank.")

    if existing_ids is not None:
        matching_ids = [pid for pid in existing_ids if pid == profile.profile_id]
        if len(matching_ids) > 1:
            errors.append(f"Duplicate profile ID: {profile.profile_id}")

    if not profile.display_name.strip():
        errors.append("Display name is blank.")

    if profile.math_mode not in VALID_MATH_MODES:
        errors.append(f"Invalid math mode: {profile.math_mode}")

    if profile.default_output and profile.default_output not in VALID_OUTPUTS:
        errors.append(f"Invalid default output: {profile.default_output}")

    if not profile.bands:
        errors.append("Profile has no bands.")

    errors.extend(validate_bands(profile))

    return errors


def validate_bands(profile: RadioProfile) -> list[str]:
    errors: list[str] = []

    for index, band in enumerate(profile.bands):
        label = band.band or f"Band row {index + 1}"

        if not band.band.strip():
            errors.append(f"{label}: band name is blank.")

        if band.rf_start_hz <= 0:
            errors.append(f"{label}: RF start frequency must be greater than zero.")

        if band.rf_end_hz <= 0:
            errors.append(f"{label}: RF end frequency must be greater than zero.")

        if band.rf_start_hz >= band.rf_end_hz:
            errors.append(f"{label}: RF start must be lower than RF end.")

        if profile.math_mode == "linear_map":
            if band.output_start_hz <= 0:
                errors.append(
                    f"{label}: output start frequency must be greater than zero."
                )

            if band.output_end_hz <= 0:
                errors.append(
                    f"{label}: output end frequency must be greater than zero."
                )

            if band.output_start_hz >= band.output_end_hz:
                errors.append(f"{label}: output start must be lower than output end.")

        if profile.math_mode in {"multiply", "divide"}:
            if band.multiplier <= 0:
                errors.append(f"{label}: multiplier must be greater than zero.")

    errors.extend(validate_no_overlapping_rf_ranges(profile))

    return errors


def validate_no_overlapping_rf_ranges(profile: RadioProfile) -> list[str]:
    errors: list[str] = []

    sorted_bands = sorted(profile.bands, key=lambda b: b.rf_start_hz)

    for first, second in zip(sorted_bands, sorted_bands[1:]):
        if first.rf_end_hz > second.rf_start_hz:
            errors.append(f"RF band overlap: {first.band} overlaps {second.band}.")

    return errors


def validate_all_profiles(profiles: dict[str, RadioProfile]) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}

    ids = set(profiles.keys())

    for profile_id, profile in profiles.items():
        profile.profile_id = profile_id
        results[profile_id] = validate_profile(profile, ids)

    return results
