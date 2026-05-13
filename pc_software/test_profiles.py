from profile_manager import ProfileManager
from radio_math import calculate_output_frequency


pm = ProfileManager()
profiles = pm.load()

print("Loaded radio profiles:")
for profile in profiles:
    print(" -", profile["display_name"])


tests = [
    ("swan_400", "80m", 3885000, 9058000),
    ("swan_350c", "80m", 3885000, 9385000),

    ("eico_720", "80m", 3885000, 3885000),
    ("eico_720", "20m", 14286000, 7143000),
    ("eico_720", "15m", 21300000, 7100000),
    ("eico_720", "10m", 28600000, 7150000),

    ("heathkit_dx100", "160m", 1885000, 1885000),
    ("heathkit_dx100", "80m", 3885000, 1942500),
    ("heathkit_dx100", "40m", 7150000, 7150000),
    ("heathkit_dx100", "20m", 14286000, 7143000),
    ("heathkit_dx100", "15m", 21300000, 7100000),
    ("heathkit_dx100", "10m", 28600000, 7150000),
]

print()
print("Profile math tests:")

for profile_id, band_id, rf_hz, expected_output in tests:
    profile = pm.get_profile_by_id(profile_id)

    result = calculate_output_frequency(profile, band_id, rf_hz)

    status = "PASS" if result.ok and result.output_hz == expected_output else "FAIL"

    print(
        f"{status}: {profile_id} {band_id} "
        f"RF {rf_hz} -> VFO {result.output_hz} "
        f"expected {expected_output}"
    )