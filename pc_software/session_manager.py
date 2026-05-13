# File: session_manager.py
#
# Named Session Profile manager for the SI5351 Multi-Radio VFO Control Platform.
#
# v4D.6E Auto Restore:
#   - Saves and loads named shack setups.
#   - Stores window geometry, compact/full mode, radio, band, output, frequency, and step.
#   - Does NOT restore RF ON, SPOT ON, or TX state.
#
# Session files are stored in:
#   sessions/<profile_name>.json

import json
import re
from pathlib import Path


SESSION_SCHEMA_VERSION = "v4D.6E"
LAST_SESSION_NAME = "_last_session"


class SessionManager:
    def __init__(self, session_dir="sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)

    def sanitize_name(self, name):
        text = str(name).strip()
        if not text:
            raise ValueError("Session name cannot be empty")
        text = re.sub(r'[<>:"/\\|?*]+', "_", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            raise ValueError("Session name cannot be empty")
        return text

    def path_for(self, name):
        safe = self.sanitize_name(name)
        return self.session_dir / f"{safe}.json"

    def list_sessions(self):
        return [path.stem for path in sorted(self.session_dir.glob("*.json")) if path.stem != LAST_SESSION_NAME]

    def save(self, name, data):
        safe = self.sanitize_name(name)
        path = self.path_for(safe)
        payload = dict(data)
        payload["schema_version"] = SESSION_SCHEMA_VERSION
        payload["session_name"] = safe
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load(self, name):
        path = self.path_for(name)
        if not path.exists():
            raise FileNotFoundError(f"Session profile not found: {name}")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_last_session(self, data):
        """
        Save automatic recovery session.

        This is separate from named operator profiles.
        """
        return self.save(LAST_SESSION_NAME, data)

    def has_last_session(self):
        return self.path_for(LAST_SESSION_NAME).exists()

    def load_last_session(self):
        return self.load(LAST_SESSION_NAME)

    def delete(self, name):
        path = self.path_for(name)
        if path.exists():
            path.unlink()
