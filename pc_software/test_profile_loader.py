import json
from pathlib import Path

from profile_models import RadioProfile
from json_validation import validate_all_profiles

PROFILE_FILE = Path("radio_profiles.json")


def load_profiles() -> dict[str, RadioProfile]:
    if not PROFILE_FILE.exists():
        raise FileNotFoundError(f"Missing file: {PROFILE_FILE}")

    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    profiles: dict[str, RadioProfile] = {}

    for profile_id, profile_data in raw_data.items():
        try:
            profile = RadioProfile.from_dict(profile_id, profile_data)
            profiles[profile_id] = profile

        except Exception as e:
            print(f"ERROR loading profile '{profile_id}': {e}")

    return profiles


def print_profile_summary(profiles: dict[str, RadioProfile]) -> None:
    print()
    print("========================================")
    print("PROFILE SUMMARY")
    print("========================================")

    for profile_id, profile in profiles.items():
        print()
        print(f"Profile ID     : {profile.profile_id}")
        print(f"Display Name   : {profile.display_name}")
        print(f"Math Mode      : {profile.math_mode}")
        print(f"Default Output : {profile.default_output}")
        print(f"Bands          : {len(profile.bands)}")

        for band in profile.bands:
            print(
                f"  {band.band}: "
                f"RF {band.rf_start_hz} -> {band.rf_end_hz} Hz | "
                f"OUT {band.output_start_hz} -> {band.output_end_hz} Hz"
            )


def print_validation_results(results: dict[str, list[str]]) -> None:
    print()
    print("========================================")
    print("VALIDATION RESULTS")
    print("========================================")

    total_errors = 0

    for profile_id, errors in results.items():
        print()

        if not errors:
            print(f"{profile_id}: OK")
        else:
            print(f"{profile_id}:")
            for error in errors:
                print(f"  ERROR: {error}")
                total_errors += 1

    print()
    print("========================================")
    print(f"TOTAL ERRORS: {total_errors}")
    print("========================================")


def main():
    print()
    print("Loading radio profiles...")
    print()

    profiles = load_profiles()

    print(f"Loaded {len(profiles)} profiles.")

    print_profile_summary(profiles)

    validation_results = validate_all_profiles(profiles)

    print_validation_results(validation_results)


if __name__ == "__main__":
    main()
