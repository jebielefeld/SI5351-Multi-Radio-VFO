# File: app_settings.py
#
# Small persistent application settings file for the SI5351 VFO GUI.
#
# This is intentionally separate from session profiles.
# Sessions describe radio/window setups.
# app_settings.json stores simple application preferences such as the last USB COM port.
#
# Windows installer note:
# Do NOT write app_settings.json into Program Files.
# Installed Windows applications normally do not have write permission there.
# Store user-writable settings under %LOCALAPPDATA%.

import json
import os
from pathlib import Path

APP_DATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "SI5351_Multi_Radio_VFO"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


class AppSettings:
    def __init__(self, filename="app_settings.json"):
        self.path = APP_DATA_DIR / filename
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
