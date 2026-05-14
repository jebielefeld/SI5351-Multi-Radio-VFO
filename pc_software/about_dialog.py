# File: about_dialog.py
#
# About dialog for the SI5351 Multi-Radio VFO Control Platform.

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QHBoxLayout,
)

from PySide6.QtCore import Qt

APP_NAME = "SI5351 Multi-Radio VFO"
APP_VERSION = "v4D6E"
FREEZE_POINT = "SI5351_VFO_PC_v4D6E_WINDOWS_INSTALLER_DEPLOYMENT_STABLE"
AUTHOR = "John Bielefeld"
GITHUB_REPO = "https://github.com/jebielefeld/SI5351-Multi-Radio-VFO"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle(f"About {APP_NAME}")
        self.setMinimumWidth(520)
        self.setMinimumHeight(420)

        layout = QVBoxLayout(self)

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        version = QLabel(f"Version: {APP_VERSION}")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        freeze = QLabel(f"Freeze Point:\n{FREEZE_POINT}")
        freeze.setAlignment(Qt.AlignCenter)
        freeze.setWordWrap(True)
        layout.addWidget(freeze)

        info = QTextEdit()
        info.setReadOnly(True)

        info.setPlainText(f"""SI5351 Multi-Radio VFO Control Platform

Author:
{AUTHOR}

GitHub Repository:
{GITHUB_REPO}

System Purpose:
A Windows PC-controlled multi-radio VFO platform for vintage ham radio transmitters and transceivers.

Stable Features:
- OUT0 through OUT5 SI5351 output support
- Multi-radio floating control windows
- Output Manager
- Session save and restore
- RF startup safety
- SPOT control
- Windows installer support
- Custom VFO application icon

Architecture:
- Python / PySide6 GUI is the system brain
- Arduino Nano is the execution engine
- GUI owns all radio frequency translation math
- Arduino firmware executes serial commands only

Hardware Platform:
- Arduino Nano
- TCA9548A I2C multiplexer
- Two Adafruit SI5351 clock generator modules
""")

        layout.addWidget(info)

        button_row = QHBoxLayout()
        button_row.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)

        button_row.addWidget(close_button)

        layout.addLayout(button_row)
