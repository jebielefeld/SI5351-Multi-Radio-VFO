from dataclasses import dataclass, field
from typing import Any


@dataclass
class BandProfile:
    band: str
    rf_start_hz: int
    rf_end_hz: int
    output_start_hz: int
    output_end_hz: int
    multiplier: float = 1.0
    notes: str = ""
    translation_mode: str = "direct"

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "BandProfile":
        translation = data.get("translation", {})

        if not isinstance(translation, dict):
            translation = {}

        translation_mode = str(
            translation.get(
                "mode",
                data.get("translation_mode", data.get("math_mode", "direct")),
            )
        )

        return BandProfile(
            band=str(data.get("id", data.get("band", ""))),
            rf_start_hz=int(
                translation.get(
                    "rf_start_hz",
                    data.get("rf_start_hz", data.get("rf_min_hz", 0)),
                )
            ),
            rf_end_hz=int(
                translation.get(
                    "rf_end_hz",
                    data.get("rf_end_hz", data.get("rf_max_hz", 0)),
                )
            ),
            output_start_hz=int(
                translation.get(
                    "vfo_start_hz",
                    data.get("output_start_hz", data.get("vfo_start_hz", 0)),
                )
            ),
            output_end_hz=int(
                translation.get(
                    "vfo_end_hz",
                    data.get("output_end_hz", data.get("vfo_end_hz", 0)),
                )
            ),
            multiplier=float(
                translation.get(
                    "multiplier",
                    data.get("multiplier", 1.0),
                )
            ),
            notes=str(data.get("notes", data.get("display_name", ""))),
            translation_mode=translation_mode,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "band": self.band,
            "rf_start_hz": self.rf_start_hz,
            "rf_end_hz": self.rf_end_hz,
            "output_start_hz": self.output_start_hz,
            "output_end_hz": self.output_end_hz,
            "multiplier": self.multiplier,
            "notes": self.notes,
            "translation_mode": self.translation_mode,
        }


@dataclass
class RadioProfile:
    profile_id: str
    display_name: str
    manufacturer: str = ""
    radio_type: str = ""
    description: str = ""
    math_mode: str = "direct"
    default_output: str = "OUT0"
    notes: str = ""
    bands: list[BandProfile] = field(default_factory=list)

    @staticmethod
    def from_dict(profile_id: str, data: dict[str, Any]) -> "RadioProfile":
        bands_data = data.get("bands", [])
        bands = []

        if isinstance(bands_data, list):
            for band_data in bands_data:
                if isinstance(band_data, dict):
                    bands.append(BandProfile.from_dict(band_data))

        return RadioProfile(
            profile_id=profile_id,
            display_name=str(data.get("display_name", data.get("name", profile_id))),
            manufacturer=str(data.get("manufacturer", "")),
            radio_type=str(data.get("radio_type", "")),
            description=str(data.get("description", "")),
            math_mode=str(data.get("math_mode", "per-band")),
            default_output=str(data.get("default_output", "OUT0")),
            notes=str(data.get("notes", "")),
            bands=bands,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "manufacturer": self.manufacturer,
            "radio_type": self.radio_type,
            "description": self.description,
            "math_mode": self.math_mode,
            "default_output": self.default_output,
            "notes": self.notes,
            "bands": [band.to_dict() for band in self.bands],
        }
