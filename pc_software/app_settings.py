# File: app_settings.py
#
# Small persistent application settings file for the SI5351 VFO GUI.
#
# This is intentionally separate from session profiles.
# Sessions describe radio/window setups.
# app_settings.json stores simple application preferences such as the last USB COM port.

import json
from pathlib import Path


class AppSettings:
    def __init__(self, filename="app_settings.json"):
        self.path = Path(filename)
        self.data = {}
        self.load()

    def load(self):
        try:
            if self.path.exists():
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            else:
                self.data = {}
        except Exception:
            self.data = {}

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()
