# File: main.py
#
# Program entry point for the SI5351 VFO GUI.
# Loads the radio profile system, creates the Qt application,
# and starts the main GUI window.

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from profile_manager import ProfileManager
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Load radio profiles before starting the GUI.
    try:
        profile_manager = ProfileManager()
        profiles = profile_manager.load()

        print("Available radios:")
        for profile in profiles:
            print(" -", profile["display_name"])

    except Exception as e:
        QMessageBox.critical(
            None, "Profile Load Error", f"Unable to load radio_profiles.json.\n\n{e}"
        )
        sys.exit(1)

    # Create main window.
    window = MainWindow()

    window.profile_manager = profile_manager
    window.profiles = profiles
    window.init_profiles()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
