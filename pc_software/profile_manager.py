# File: profile_manager.py
#
# Loads and manages radio_profiles.json.
# This file does not perform frequency math.
# It only loads profiles and helps the GUI find radios and bands.
#
# PyInstaller note:
# radio_profiles.json is bundled into the EXE using --add-data.
# When running as a one-file EXE, PyInstaller extracts bundled data
# to sys._MEIPASS. The resource_path() helper handles both normal
# Python execution and frozen EXE execution.

import json
import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """
    Return an absolute path to a bundled resource.

    Works for:
    - normal Python execution
    - PyInstaller one-file EXE execution
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path

    return Path(__file__).resolve().parent / relative_path


class ProfileManager:
    def __init__(self, filename="radio_profiles.json"):
        self.filename = resource_path(filename)
        self.data = {}
        self.profiles = []

    def load(self):
        if not self.filename.exists():
            raise FileNotFoundError(f"Profile file not found: {self.filename}")

        with open(self.filename, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.profiles = self.data.get("profiles", [])

        if not self.profiles:
            raise ValueError("No radio profiles found in radio_profiles.json")

        return self.profiles

    def get_profile_names(self):
        return [p["display_name"] for p in self.profiles]

    def get_profile_by_id(self, profile_id):
        for profile in self.profiles:
            if profile.get("id") == profile_id:
                return profile
        return None

    def get_profile_by_name(self, display_name):
        for profile in self.profiles:
            if profile.get("display_name") == display_name:
                return profile
        return None

    def get_enabled_bands(self, profile):
        return [band for band in profile.get("bands", []) if band.get("enabled", True)]
