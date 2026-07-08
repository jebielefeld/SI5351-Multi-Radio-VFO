###########################################################################
# about_dialog.py
#
# SI5351 Multi-Radio VFO Platform
#
# Purpose:
#   Provides the About dialog for the application.
###########################################################################

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
)

from PySide6.QtCore import Qt

APP_NAME = "SI5351 Multi-Radio VFO Platform"
APP_VERSION = "Version 6.1d Release"
FIRMWARE_VERSION = "Nano Firmware 6.1c"
DOCUMENTATION_VERSION = "Documentation 1.0"

AUTHOR = "John Bielefeld, K1JEB"
GITHUB_REPO = "https://github.com/jebielefeld/SI5351-Multi-Radio-VFO"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)

        layout = QVBoxLayout(self)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        version = QLabel(f"{APP_VERSION}\n{FIRMWARE_VERSION}\n{DOCUMENTATION_VERSION}")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("font-size: 13px;")
        layout.addWidget(version)

        info = QTextEdit()
        info.setReadOnly(True)

        info.setPlainText(f"""SI5351 Multi-Radio VFO Platform

A software-controlled external VFO system for vintage Amateur Radio equipment.

Designed and Developed by

{AUTHOR}
Amateur Radio Operator

Engineering Assistance

ChatGPT
OpenAI

GitHub Repository

{GITHUB_REPO}

System Purpose

This application controls an Arduino Nano-based SI5351 frequency synthesizer
system. It is designed to emulate or replace external VFOs used with vintage
Amateur Radio transmitters, receivers, and transceivers.

Major Features

- Six independently assignable RF outputs
- Dual SI5351 frequency synthesizer support
- TCA9548A I2C multiplexer support
- Radio profile based frequency translation
- Main radio control window
- Floating multi-radio control windows
- Output Manager with conflict prevention
- RF ON/OFF and SPOT control
- 10 MHz Precision Calibration 
- Developer Console
- Profile Editor
- Session save, load, and automatic restore
- Built-in searchable Help / User Guide
- Windows executable and installer support

Hardware Platform

- Arduino Nano
- TCA9548A I2C multiplexer
- Two Adafruit SI5351A frequency synthesizer modules
- Six RF outputs, labeled Output 1 through Output 6
- Firmware protocol uses OUT0 through OUT5 internally

Architecture

- Python / PySide6 GUI is the system control panel
- Arduino Nano is the hardware execution engine
- PC application performs all radio profile calculations and frequency translation
- Nano firmware receives final output frequencies and RF enable commands

Calibration

- Each SI5351 module can be individually calibrated against an external precision 10 MHz reference. 
  Calibration corrections are stored in the Arduino Nano EEPROM, allowing the VFO hardware to retain its 
  calibration when moved between computers.

License

Copyright © 2026 John Bielefeld

Licensed under the MIT License.

Source code and project information are available on GitHub.

Intended Use

This software is intended for educational, experimental, and Amateur Radio use.

Always verify generated frequencies and RF output routing with appropriate test equipment before transmitting on the air.

73 and enjoy using the SI5351 Multi-Radio VFO Platform! John K1JEB
""")

        layout.addWidget(info)

        button_row = QHBoxLayout()
        button_row.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        button_row.addWidget(close_button)

        layout.addLayout(button_row)
