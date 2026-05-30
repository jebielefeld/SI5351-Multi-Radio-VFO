# File: calibration_window.py
#
# Calibration window for the SI5351 Multi-Radio VFO Control Platform.
#
# Purpose:
#   - Provide an operator-friendly calibration UI for the Nano firmware
#     calibration commands.
#   - Keep the same general look and feel as the floating Radio Window.
#   - Use the Nano EEPROM as the source of truth for calibration values.
#
# Firmware protocol used:
#   XC0;        read SI5351 #1 correction
#   XC1;        read SI5351 #2 correction
#   C0;         enter calibration mode for SI5351 #1, output 10.000000 MHz on OUT0
#   C1;         enter calibration mode for SI5351 #2, output 10.000000 MHz on OUT3
#   CU0,+10;    nudge SI5351 #1 correction up by 10 ppb
#   CD1,+100;   nudge SI5351 #2 correction down by 100 ppb
#   CS0;        save SI5351 #1 correction to EEPROM
#   CS1;        save SI5351 #2 correction to EEPROM
#   CX;         exit calibration mode
#
# v1.1 safety update:
#   - Adds explicit EXIT button to close the window.
#   - Window X also exits calibration mode before closing.

from __future__ import annotations

import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from output_manager import index_to_color, output_name_to_user_label


class CalibrationWindow(QWidget):
    def __init__(self, controller):
        super().__init__()

        self.controller = controller
        self.link = controller.link

        self.setWindowTitle("SI5351 Calibration")
        self.resize(520, 360)

        self.active_chip = 0
        self.in_calibration = False
        self.compact_mode = False

        self.build_ui()
        self.refresh_current_corrections()
        self.update_target_display()

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.title_label = QLabel("SI5351 Calibration")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        target_row = QHBoxLayout()
        self.target_label = QLabel("Target:")
        self.target_combo = QComboBox()
        self.target_combo.addItem("SI5351 #1  —  OUT0 / Output 1", 0)
        self.target_combo.addItem("SI5351 #2  —  OUT3 / Output 4", 1)
        self.target_combo.currentIndexChanged.connect(self.on_target_changed)
        target_row.addWidget(self.target_label)
        target_row.addWidget(self.target_combo)
        layout.addLayout(target_row)

        self.output_color_label = QLabel("Output 1  (OUT0)")
        self.output_color_label.setAlignment(Qt.AlignCenter)
        self.output_color_label.setStyleSheet(
            "background-color: #1f77b4; color: white; font-size: 14px; "
            "font-weight: bold; padding: 4px;"
        )
        layout.addWidget(self.output_color_label)

        self.freq_label = QLabel("10.000000 MHz")
        self.freq_label.setAlignment(Qt.AlignCenter)
        self.freq_label.setStyleSheet(
            "font-family: Consolas; font-size: 38px; font-weight: bold;"
        )
        layout.addWidget(self.freq_label)

        self.instruction_label = QLabel(
            "Connect frequency counter to the shown output. Enter calibration, then nudge until the counter reads exactly 10.000000 MHz."
        )
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setAlignment(Qt.AlignCenter)
        self.instruction_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(self.instruction_label)

        self.correction_label = QLabel("Correction: ---")
        self.correction_label.setAlignment(Qt.AlignCenter)
        self.correction_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.correction_label)

        step_row = QHBoxLayout()
        self.step_label = QLabel("Step:")
        self.step_combo = QComboBox()
        for step in [1, 10, 100, 1000, 10000]:
            self.step_combo.addItem(str(step), step)
        self.step_combo.setCurrentText("10")
        step_row.addWidget(self.step_label)
        step_row.addWidget(self.step_combo)
        layout.addLayout(step_row)

        nudge_row = QHBoxLayout()
        self.down_button = QPushButton("DOWN")
        self.up_button = QPushButton("UP")
        self.down_button.clicked.connect(self.nudge_down)
        self.up_button.clicked.connect(self.nudge_up)
        nudge_row.addWidget(self.down_button)
        nudge_row.addWidget(self.up_button)
        layout.addLayout(nudge_row)

        command_row = QHBoxLayout()
        self.enter_button = QPushButton("ENTER CAL")
        self.save_button = QPushButton("SAVE CAL")
        self.exit_button = QPushButton("EXIT CAL")
        self.refresh_button = QPushButton("READ CAL")
        self.compact_button = QPushButton("COMPACT")
        self.close_button = QPushButton("EXIT")

        self.enter_button.clicked.connect(self.enter_calibration)
        self.save_button.clicked.connect(self.save_calibration)
        self.exit_button.clicked.connect(self.exit_calibration)
        self.refresh_button.clicked.connect(self.refresh_current_corrections)
        self.compact_button.clicked.connect(self.toggle_compact)
        self.close_button.clicked.connect(self.safe_close_window)

        command_row.addWidget(self.enter_button)
        command_row.addWidget(self.save_button)
        command_row.addWidget(self.exit_button)
        command_row.addWidget(self.refresh_button)
        command_row.addWidget(self.compact_button)
        command_row.addWidget(self.close_button)
        layout.addLayout(command_row)

        self.status_label = QLabel("Calibration idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "background-color: #444444; color: white; font-size: 14px; "
            "font-weight: bold; padding: 4px;"
        )
        layout.addWidget(self.status_label)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(90)
        layout.addWidget(self.log)

        self.update_button_state()

    def current_chip(self) -> int:
        data = self.target_combo.currentData()
        if data is None:
            return 0
        return int(data)

    def current_output_name(self) -> str:
        return "OUT0" if self.current_chip() == 0 else "OUT3"

    def current_output_index(self) -> int:
        return 0 if self.current_chip() == 0 else 3

    def current_step(self) -> int:
        data = self.step_combo.currentData()
        if data is None:
            return 10
        return int(data)

    def on_target_changed(self, *_):
        if self.in_calibration:
            QMessageBox.warning(
                self,
                "Calibration Active",
                "Exit calibration mode before changing SI5351 target.",
            )
            self.target_combo.blockSignals(True)
            self.target_combo.setCurrentIndex(self.active_chip)
            self.target_combo.blockSignals(False)
            return

        self.active_chip = self.current_chip()
        self.update_target_display()
        self.refresh_current_corrections()

    def update_target_display(self):
        chip = self.current_chip()
        output_name = self.current_output_name()
        output_index = self.current_output_index()
        output_label = output_name_to_user_label(output_name)
        color = index_to_color(output_index)

        self.output_color_label.setText(f"{output_label}  ({output_name})")
        self.output_color_label.setStyleSheet(
            f"background-color: {color}; color: white; font-size: 14px; "
            "font-weight: bold; padding: 4px;"
        )
        self.title_label.setText(f"SI5351 #{chip + 1} Calibration")

    def require_connected(self) -> bool:
        if not self.link.is_connected():
            QMessageBox.warning(
                self,
                "Not Connected",
                "Connect to the Nano USB COM port before using calibration.",
            )
            return False
        return True

    def send_query(self, command: str) -> str:
        response = self.link.query(command)
        text = str(response).strip()
        self.log_message(f"> {command}")
        self.log_message(text)
        return text

    def log_message(self, text: str):
        self.log.append(str(text))
        if hasattr(self.controller, "log_message"):
            self.controller.log_message(str(text))

    def parse_correction_response(self, text: str, chip: int) -> int | None:
        pattern = rf"XC{chip},([+-]\d+);?"
        match = re.search(pattern, text)
        if not match:
            # Legacy/defensive: accept XC+000001234; for chip 0 only.
            if chip == 0:
                match = re.search(r"XC([+-]\d+);?", text)
            if not match:
                return None
        try:
            return int(match.group(1))
        except Exception:
            return None

    def set_correction_label(self, value: int | None):
        if value is None:
            self.correction_label.setText("Correction: unknown")
            return
        sign = "+" if value >= 0 else "-"
        self.correction_label.setText(f"Correction: {sign}{abs(value):09d} ppb")

    def refresh_current_corrections(self):
        if not self.link.is_connected():
            self.set_correction_label(None)
            return

        chip = self.current_chip()
        try:
            response = self.send_query(f"XC{chip};")
            value = self.parse_correction_response(response, chip)
            self.set_correction_label(value)
        except Exception as e:
            self.set_correction_label(None)
            self.log_message(f"Read calibration error: {e}")

    def enter_calibration(self):
        if not self.require_connected():
            return

        chip = self.current_chip()

        result = QMessageBox.question(
            self,
            "Enter Calibration Mode",
            "This will force all RF outputs OFF, then enable only the calibration output at 10.000000 MHz.\n\n"
            f"Target: SI5351 #{chip + 1}\n"
            f"Output: {output_name_to_user_label(self.current_output_name())} ({self.current_output_name()})\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        try:
            response = self.send_query(f"C{chip};")
            self.in_calibration = True
            self.active_chip = chip
            self.status_label.setText("CALIBRATION ACTIVE - 10.000000 MHz OUTPUT")
            self.status_label.setStyleSheet(
                "background-color: orange; color: black; font-size: 14px; "
                "font-weight: bold; padding: 4px;"
            )
            self.refresh_current_corrections()
            self.update_button_state()
            self.log_message(f"Calibration mode response: {response}")
        except Exception as e:
            QMessageBox.warning(self, "Calibration Error", str(e))
            self.log_message(f"Enter calibration error: {e}")

    def nudge_up(self):
        self.nudge("CU")

    def nudge_down(self):
        self.nudge("CD")

    def nudge(self, direction_cmd: str):
        if not self.require_connected():
            return
        if not self.in_calibration:
            QMessageBox.warning(
                self,
                "Calibration Not Active",
                "Click ENTER CAL before nudging the correction.",
            )
            return

        chip = self.current_chip()
        step = self.current_step()

        try:
            response = self.send_query(f"{direction_cmd}{chip},+{step};")
            self.log_message(f"Nudge response: {response}")
            self.refresh_current_corrections()
        except Exception as e:
            QMessageBox.warning(self, "Nudge Error", str(e))
            self.log_message(f"Nudge error: {e}")

    def save_calibration(self):
        if not self.require_connected():
            return
        if not self.in_calibration:
            QMessageBox.warning(
                self,
                "Calibration Not Active",
                "Enter calibration mode before saving calibration.",
            )
            return

        chip = self.current_chip()

        result = QMessageBox.question(
            self,
            "Save Calibration",
            f"Save SI5351 #{chip + 1} calibration correction to Nano EEPROM?\n\n"
            "Only do this after the frequency counter reads exactly 10.000000 MHz.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        try:
            response = self.send_query(f"CS{chip};")
            self.refresh_current_corrections()
            QMessageBox.information(
                self,
                "Calibration Saved",
                f"SI5351 #{chip + 1} calibration saved to Nano EEPROM.\n\n{response}",
            )
        except Exception as e:
            QMessageBox.warning(self, "Save Calibration Error", str(e))
            self.log_message(f"Save calibration error: {e}")

    def exit_calibration(self):
        if not self.link.is_connected():
            self.in_calibration = False
            self.update_button_state()
            return

        try:
            response = self.send_query("CX;")
            self.in_calibration = False
            self.status_label.setText("Calibration idle")
            self.status_label.setStyleSheet(
                "background-color: #444444; color: white; font-size: 14px; "
                "font-weight: bold; padding: 4px;"
            )
            self.update_button_state()
            self.refresh_current_corrections()
            self.log_message(f"Exit calibration response: {response}")
        except Exception as e:
            QMessageBox.warning(self, "Exit Calibration Error", str(e))
            self.log_message(f"Exit calibration error: {e}")

    def update_button_state(self):
        self.target_combo.setEnabled(not self.in_calibration)
        self.enter_button.setEnabled(not self.in_calibration)
        self.save_button.setEnabled(self.in_calibration)
        self.exit_button.setEnabled(self.in_calibration)
        self.up_button.setEnabled(self.in_calibration)
        self.down_button.setEnabled(self.in_calibration)

    def toggle_compact(self):
        self.compact_mode = not self.compact_mode
        if self.compact_mode:
            self.compact_button.setText("FULL")
            self.instruction_label.setVisible(False)
            self.log.setVisible(False)
            self.resize(430, 240)
        else:
            self.compact_button.setText("COMPACT")
            self.instruction_label.setVisible(True)
            self.log.setVisible(True)
            self.resize(520, 360)

    def safe_close_window(self):
        if self.in_calibration:
            result = QMessageBox.question(
                self,
                "Exit Calibration?",
                "Calibration mode is active. Exit calibration mode and close this window?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                return

            self.exit_calibration()

        self.close()

    def closeEvent(self, event):
        if self.in_calibration:
            result = QMessageBox.question(
                self,
                "Exit Calibration?",
                "Calibration mode is active. Exit calibration mode and close this window?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if result != QMessageBox.Yes:
                event.ignore()
                return

            self.exit_calibration()

        event.accept()
