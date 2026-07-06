# File: main_window.py
#
# Main controller window for the SI5351 Multi-Radio VFO Control Platform.
#
# v4D Output Manager Phase 1:
#   - Adds centralized OutputManager.
#   - Adds Output Manager window.
#   - Operator-facing output labels are Output 1 through Output 6.
#   - Internal firmware protocol remains OUT0 through OUT5.

import json
import subprocess
import sys
from pathlib import Path

from tkinter import dialog

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QMessageBox,
    QInputDialog,
    QApplication,
)
from PySide6.QtCore import Qt, QEvent, QTimer

from serial_link import SerialLink
from cat_radio import CatRadio
from config import MIN_FREQ_HZ, MAX_FREQ_HZ, DEFAULT_BAUD
from radio_maths import calculate_output_frequency
from radio_window import RadioControlWindow
from output_manager import (
    OutputManager,
    index_to_output_name,
    output_name_to_index,
    output_name_to_user_label,
    index_to_color,
)
from output_manager_window import OutputManagerWindow
from session_manager import SessionManager
from app_settings import AppSettings
from about_dialog import AboutDialog
from help_window import HelpWindow
from calibration_window import CalibrationWindow
from developer_console import DeveloperConsole


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Nano Si5351A Ham Radio VFO - Main Controller")

        # Main window is intentionally kept narrower than early development builds.
        # The top controls are split into two rows so the program feels more like
        # a bench RF instrument and less like a wide engineering dashboard.
        self.normal_width = 690
        self.normal_height = 485
        self.monitor_height = 610

        self.resize(self.normal_width, self.normal_height)

        self.link = SerialLink()
        self.link.add_callback(self.debug_serial)
        self.radio = CatRadio(self.link)

        self.output_manager = OutputManager()
        self.output_manager_window = None
        self.profile_editor_process = None
        self.help_window = None
        self.calibration_window = None
        self.output_manager.conflict_detected.connect(self.log_message)
        self.session_manager = SessionManager()
        self.app_settings = AppSettings()
        self.auto_restore_done = False

        self.profile_manager = None
        self.profiles = []

        self.window_id = "MAIN_RADIO_1"
        self.window_name = "Main Radio 1"
        self.active_owner_id = self.window_id
        self.last_safety_warning_key = None

        self.current_profile = None
        self.current_band_id = None
        self.current_clock = "OUT0"
        self.previous_clock = self.current_clock

        self.current_rf_hz = 7_100_000
        self.current_vfo_hz = 0
        self.pending_tune_hz = self.current_rf_hz

        self.step_list = [10_000_000, 1_000_000, 100_000, 10_000, 1_000, 100, 10, 1]
        self.step_index = 5
        self.step_hz = self.step_list[self.step_index]

        self.tune_send_timer = QTimer(self)
        self.tune_send_timer.setSingleShot(True)
        self.tune_send_timer.timeout.connect(self.send_pending_tune_frequency)

        self.spot_active = False
        self.tx_active = False
        self.monitor_visible = False
        self.compact_mode = False

        self.radio_windows = []

        self.output_manager.claim_output(
            self.current_clock,
            self.window_id,
            self.window_name,
        )

        self.build_ui()
        self.refresh_ports()

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.blink_status)
        self.blink_state = False

        self.set_connected_state(False)
        self.update_output_manager_state()
        self.apply_active_highlights()
        self.ensure_all_windows_visible()

    def build_ui(self):
        central = QWidget()
        central.setObjectName("mainActiveFrame")
        central.setAttribute(Qt.WA_StyledBackground, True)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(5)
        central.setLayout(main_layout)

        #
        # Top controls are split into two rows.
        #
        # Row 1: operating/session controls.
        # Row 2: tools/utility controls.
        #

        control_row = QHBoxLayout()
        control_row.setContentsMargins(0, 0, 0, 0)
        control_row.setSpacing(4)

        self.port_label = QLabel("COM:")
        self.port_combo = QComboBox()
        self.port_combo.setFixedWidth(95)
        self.refresh_button = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")
        self.new_window_button = QPushButton("New Radio")
        self.output_manager_button = QPushButton("Outputs")
        self.save_session_button = QPushButton("Save")
        self.load_session_button = QPushButton("Load")
        self.arrange_windows_button = QPushButton("Arrange")

        self.profile_editor_button = QPushButton("Profiles")
        self.reload_profiles_button = QPushButton("Reload")
        self.monitor_button = QPushButton("Monitor OFF")
        self.calibration_button = QPushButton("Calibration")
        self.developer_console_button = QPushButton("Dev Console")
        self.help_button = QPushButton("Help")
        self.about_button = QPushButton("About")

        self.refresh_button.clicked.connect(self.refresh_ports)
        self.connect_button.clicked.connect(self.connect_radio)
        self.disconnect_button.clicked.connect(self.disconnect_radio)
        self.new_window_button.clicked.connect(self.open_radio_window)
        self.output_manager_button.clicked.connect(self.show_output_manager)
        self.profile_editor_button.clicked.connect(self.open_profile_editor)
        self.reload_profiles_button.clicked.connect(self.reload_profiles_from_disk)
        self.save_session_button.clicked.connect(self.save_session_profile)
        self.load_session_button.clicked.connect(self.load_session_profile)
        self.arrange_windows_button.clicked.connect(self.arrange_radio_windows)
        self.monitor_button.clicked.connect(self.toggle_monitor)
        self.calibration_button.clicked.connect(self.show_calibration_window)
        self.developer_console_button.clicked.connect(self.show_developer_console)
        self.help_button.clicked.connect(self.show_help_window)
        self.about_button.clicked.connect(self.show_about_dialog)

        control_row.addWidget(self.port_label)
        control_row.addWidget(self.port_combo)
        control_row.addWidget(self.refresh_button)
        control_row.addWidget(self.connect_button)
        control_row.addWidget(self.disconnect_button)
        control_row.addWidget(self.new_window_button)
        control_row.addWidget(self.output_manager_button)
        control_row.addWidget(self.arrange_windows_button)
        control_row.addStretch()

        main_layout.addLayout(control_row)

        tool_row = QHBoxLayout()
        tool_row.setContentsMargins(0, 0, 0, 0)
        tool_row.setSpacing(4)

        tool_row.addWidget(self.monitor_button)
        tool_row.addWidget(self.calibration_button)
        tool_row.addWidget(self.developer_console_button)
        tool_row.addWidget(self.reload_profiles_button)
        tool_row.addWidget(self.profile_editor_button)
        tool_row.addWidget(self.save_session_button)
        tool_row.addWidget(self.load_session_button)
        tool_row.addWidget(self.help_button)
        tool_row.addWidget(self.about_button)
        tool_row.addStretch()

        main_layout.addLayout(tool_row)

        radio_row = QHBoxLayout()
        radio_row.setContentsMargins(0, 0, 0, 0)
        radio_row.setSpacing(5)
        self.radio_label = QLabel("Radio:")
        self.band_label = QLabel("Band:")
        self.output_label = QLabel("Output:")
        self.radio_combo = QComboBox()
        self.radio_combo.setMinimumWidth(220)
        self.band_combo = QComboBox()
        self.band_combo.setMinimumWidth(95)
        self.clock_combo = QComboBox()
        self.clock_combo.setMinimumWidth(110)
        self.populate_output_combo(self.clock_combo)

        self.radio_combo.currentIndexChanged.connect(self.on_radio_changed)
        self.band_combo.currentIndexChanged.connect(self.on_band_changed)
        self.clock_combo.currentIndexChanged.connect(self.on_clock_combo_changed)

        radio_row.addWidget(self.radio_label)
        radio_row.addWidget(self.radio_combo)
        radio_row.addWidget(self.band_label)
        radio_row.addWidget(self.band_combo)
        radio_row.addWidget(self.output_label)
        radio_row.addWidget(self.clock_combo)
        main_layout.addLayout(radio_row)

        self.output_color_label = QLabel("Output 1")
        self.output_color_label.setAlignment(Qt.AlignCenter)
        self.output_color_label.setStyleSheet(
            "background-color: #1f77b4; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
        )
        main_layout.addWidget(self.output_color_label)

        self.compact_identity_label = QLabel("")
        self.compact_identity_label.setAlignment(Qt.AlignCenter)
        self.compact_identity_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.compact_identity_label.setVisible(False)
        main_layout.addWidget(self.compact_identity_label)

        self.status_label = QLabel("Not connected")
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        self.txrx_label = QLabel("RX")
        self.txrx_label.setAlignment(Qt.AlignCenter)
        self.txrx_label.setStyleSheet(
            "background-color: green; color: white; font-size: 24px; font-weight: bold;"
        )
        main_layout.addWidget(self.txrx_label)

        self.global_rf_label = QLabel("GLOBAL RF: ALL OUTPUTS OFF")
        self.global_rf_label.setAlignment(Qt.AlignCenter)
        self.global_rf_label.setStyleSheet(
            "background-color: #333333; color: white; font-size: 16px; font-weight: bold; padding: 4px;"
        )
        main_layout.addWidget(self.global_rf_label)

        self.safety_label = QLabel("SAFETY: OK")
        self.safety_label.setAlignment(Qt.AlignCenter)
        self.safety_label.setStyleSheet(
            "background-color: #444444; color: white; font-size: 15px; font-weight: bold; padding: 4px;"
        )
        main_layout.addWidget(self.safety_label)

        self.freq_display = QLabel()
        self.freq_display.setAlignment(Qt.AlignCenter)
        self.freq_display.setFocusPolicy(Qt.StrongFocus)
        self.freq_display.setStyleSheet(
            "font-family: Consolas; font-size: 40px; font-weight: bold;"
        )
        self.freq_display.mousePressEvent = self.freq_display_clicked
        self.freq_display.wheelEvent = self.freq_display_wheel
        self.freq_display.installEventFilter(self)
        main_layout.addWidget(self.freq_display)

        self.step_display = QLabel()
        self.step_display.setAlignment(Qt.AlignCenter)
        self.step_display.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(self.step_display)
        self.update_frequency_display()

        self.vfo_display = QLabel("VFO: --- MHz")
        self.vfo_display.setAlignment(Qt.AlignCenter)
        self.vfo_display.setStyleSheet("font-size: 20px; color: yellow;")
        main_layout.addWidget(self.vfo_display)

        freq_row = QHBoxLayout()
        freq_row.setContentsMargins(0, 0, 0, 0)
        freq_row.setSpacing(5)
        self.freq_entry = QLineEdit()
        self.freq_entry.setPlaceholderText(
            "Examples: 7.100 | 7100 | 7100000 | 14.250 MHz"
        )
        self.freq_entry.setText(str(self.current_rf_hz))
        self.set_freq_button = QPushButton("Set Frequency")
        self.read_freq_button = QPushButton("Read Frequency")
        self.set_freq_button.clicked.connect(self.set_frequency)
        self.read_freq_button.clicked.connect(self.read_frequency)
        freq_row.addWidget(self.freq_entry)
        freq_row.addWidget(self.set_freq_button)
        freq_row.addWidget(self.read_freq_button)
        main_layout.addLayout(freq_row)

        rf_row = QHBoxLayout()
        rf_row.setContentsMargins(0, 0, 0, 0)
        rf_row.setSpacing(5)
        self.rf_on_button = QPushButton("RF ON")
        self.rf_off_button = QPushButton("RF OFF")
        self.spot_button = QPushButton("SPOT OFF")
        self.compact_button = QPushButton("COMPACT")
        self.id_button = QPushButton("ID Test")
        self.cal_button = QPushButton("Read Calibration")

        self.rf_on_button.clicked.connect(self.rf_on)
        self.rf_off_button.clicked.connect(self.rf_off)
        self.spot_button.clicked.connect(self.toggle_spot)
        self.compact_button.clicked.connect(self.toggle_compact)
        self.id_button.clicked.connect(self.id_test)
        self.cal_button.clicked.connect(self.read_calibration)

        rf_row.addWidget(self.rf_on_button)
        rf_row.addWidget(self.rf_off_button)
        rf_row.addWidget(self.spot_button)
        rf_row.addWidget(self.compact_button)
        rf_row.addWidget(self.id_button)
        rf_row.addWidget(self.cal_button)
        main_layout.addLayout(rf_row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setVisible(False)
        main_layout.addWidget(self.log)

    def populate_output_combo(self, combo):
        combo.clear()
        for i in range(6):
            combo.addItem(
                output_name_to_user_label(index_to_output_name(i)),
                index_to_output_name(i),
            )

    def combo_current_output(self, combo):
        data = combo.currentData()
        if data:
            return data
        text = combo.currentText()
        if text.startswith("Output "):
            # Accept both old "Output 1" and new "Output 1 (BNC 1)" formats.
            try:
                output_num = int(text.split()[1])
                return index_to_output_name(output_num - 1)
            except Exception:
                return text
        return text

    def set_combo_to_output(self, combo, output_name):
        idx = combo.findData(output_name)
        if idx >= 0:
            combo.blockSignals(True)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)

    def init_profiles(self):
        if not self.profiles:
            return
        self.radio_combo.clear()
        for profile in self.profiles:
            self.radio_combo.addItem(profile["display_name"], profile)
        if self.radio_combo.count() > 0:
            self.radio_combo.setCurrentIndex(0)

        self.schedule_auto_restore()

    def load_profiles_from_file(self):
        profile_path = Path(__file__).with_name("radio_profiles.json")

        if not profile_path.exists():
            raise FileNotFoundError(f"Could not find {profile_path}")

        with open(profile_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict) and "profiles" in raw_data:
            raw_profiles = raw_data["profiles"]
        else:
            raw_profiles = raw_data

        loaded_profiles = []

        if isinstance(raw_profiles, list):
            for profile in raw_profiles:
                if isinstance(profile, dict):
                    loaded_profiles.append(profile)

        elif isinstance(raw_profiles, dict):
            for profile_id, profile in raw_profiles.items():
                if isinstance(profile, dict):
                    if "id" not in profile:
                        profile = dict(profile)
                        profile["id"] = profile_id
                    loaded_profiles.append(profile)

        else:
            raise ValueError(
                "radio_profiles.json does not contain a valid profile list"
            )

        return loaded_profiles

    def reload_profiles_from_disk(self):
        try:
            previous_profile_id = None
            previous_profile_name = ""
            previous_band_id = self.current_band_id

            if self.current_profile:
                previous_profile_id = self.current_profile.get("id")
                previous_profile_name = self.current_profile.get("display_name", "")

            loaded_profiles = self.load_profiles_from_file()

            if not loaded_profiles:
                QMessageBox.warning(
                    self,
                    "Reload Profiles",
                    "No profiles were found in radio_profiles.json.",
                )
                return

            # Keep the same list object so existing floating windows that hold
            # a reference to self.profiles see the updated profile table too.
            self.profiles.clear()
            self.profiles.extend(loaded_profiles)

            self.radio_combo.blockSignals(True)
            self.radio_combo.clear()
            for profile in self.profiles:
                self.radio_combo.addItem(
                    profile.get("display_name", "Unnamed Radio"), profile
                )
            self.radio_combo.blockSignals(False)

            row_to_select = 0
            for row in range(self.radio_combo.count()):
                profile = self.radio_combo.itemData(row)
                if not profile:
                    continue
                if previous_profile_id and profile.get("id") == previous_profile_id:
                    row_to_select = row
                    break
                if (
                    previous_profile_name
                    and profile.get("display_name") == previous_profile_name
                ):
                    row_to_select = row
                    break

            self.radio_combo.setCurrentIndex(row_to_select)
            self.current_profile = self.radio_combo.currentData()
            self.update_band_list()

            if previous_band_id:
                band_row = self.find_band_index_by_id(previous_band_id)
                if band_row >= 0:
                    self.band_combo.setCurrentIndex(band_row)

            self.update_compact_identity()
            self.update_output_manager_state()

            if self.output_manager_window is not None:
                try:
                    self.output_manager_window.refresh()
                except Exception:
                    pass

            self.log_message(f"Reloaded {len(self.profiles)} radio profiles from disk")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Reload Profiles Failed",
                str(e),
            )
            self.log_message(f"Reload profiles error: {e}")

    def on_radio_changed(self, *_):
        self.current_profile = self.radio_combo.currentData()
        self.update_band_list()
        self.update_compact_identity()
        self.update_output_manager_state()

    def update_band_list(self):
        self.band_combo.clear()
        if not self.current_profile:
            return
        for band in self.current_profile.get("bands", []):
            if band.get("enabled", True):
                self.band_combo.addItem(band["display_name"], band["id"])
        if self.band_combo.count() > 0:
            self.band_combo.setCurrentIndex(0)

    def on_band_changed(self, *_):
        self.current_band_id = self.band_combo.currentData()
        if not self.current_profile or not self.current_band_id:
            return
        for band in self.current_profile.get("bands", []):
            if band["id"] == self.current_band_id:
                default_hz = band.get("default_rf_hz")
                if default_hz:
                    self.current_rf_hz = int(default_hz)
                    self.pending_tune_hz = self.current_rf_hz
                    self.current_vfo_hz = 0
                    self.freq_entry.setText(str(self.current_rf_hz))
                    self.update_frequency_display()
                    self.vfo_display.setText("VFO: --- MHz")
                break

        self.update_compact_identity()
        self.update_output_manager_state()

    def on_clock_combo_changed(self, *_):
        self.on_clock_changed(self.combo_current_output(self.clock_combo))

    def on_clock_changed(self, clock_name):
        if clock_name == self.current_clock:
            return

        old_output = self.current_clock

        approved = self.output_manager.reassign_output(
            old_output,
            clock_name,
            self.window_id,
            self.window_name,
        )

        if not approved:
            self.set_combo_to_output(self.clock_combo, self.current_clock)
            self.log_message(
                f"{output_name_to_user_label(clock_name)} is already in use"
            )
            return

        if self.spot_active and self.link.is_connected():
            self.current_clock = old_output
            self.set_rf_output(False, reason="Output changed")
            self.spot_active = False
            self.spot_button.setText("SPOT OFF")
            self.spot_button.setStyleSheet("")

        self.current_clock = clock_name
        self.previous_clock = clock_name
        self.update_compact_identity()
        self.update_output_manager_state()
        self.log_message(
            f"Main Radio 1 selected {output_name_to_user_label(clock_name)} ({clock_name})"
        )

    def open_radio_window(self):
        output = self.output_manager.find_free_output_name()
        if output is None:
            self.log_message("No free outputs available for a new radio window")
            return

        window_number = len(self.radio_windows) + 2
        window = RadioControlWindow(
            controller=self,
            link=self.link,
            profiles=self.profiles,
            preferred_output=output,
            output_manager=self.output_manager,
            window_name=f"Radio {window_number}",
        )

        self.radio_windows.append(window)
        window.show()
        self.clamp_widget_to_visible_screen(window)
        self.set_active_window(window.window_id)
        self.log_message(
            f"Opened floating radio window on {output_name_to_user_label(output)} ({output})"
        )

    def find_free_output(self):
        return self.output_manager.find_free_output_name()

    def is_output_assigned_to_child(self, output_name):
        owner = self.output_manager.owner_for_output(output_name)
        return owner not in (None, self.window_id)

    def request_output_assignment(self, owner, new_output, old_output=None):
        owner_id = getattr(owner, "window_id", str(id(owner)))
        owner_name = getattr(owner, "window_name", "Radio Window")
        old_output = old_output or getattr(owner, "current_clock", new_output)

        approved = self.output_manager.reassign_output(
            old_output,
            new_output,
            owner_id,
            owner_name,
        )

        if not approved:
            self.log_message(
                f"{output_name_to_user_label(new_output)} is already assigned"
            )
            return False

        return True

    def release_output_assignment(self, owner):
        owner_id = getattr(owner, "window_id", None)
        if owner_id:
            self.output_manager.release_owner(owner_id)

        if owner in self.radio_windows:
            self.radio_windows.remove(owner)

    def schedule_auto_restore(self):
        """
        Run auto-restore after profile initialization and after the window
        has entered the Qt event loop.
        """
        if self.auto_restore_done:
            return
        self.auto_restore_done = True
        QTimer.singleShot(100, self.auto_restore_last_session)

    def auto_restore_last_session(self):
        """
        Restore the last automatic recovery session, if present.

        Safety rule:
          RF, SPOT, and TX are never restored.
        """
        try:
            if not self.session_manager.has_last_session():
                return

            data = self.session_manager.load_last_session()
            self.apply_session_state(data)
            self.log_message("Auto-restored last session")
        except Exception as e:
            self.log_message(f"Auto-restore skipped: {e}")

    def auto_save_last_session(self):
        """
        Save current layout/configuration for power-loss/restart recovery.
        """
        try:
            path = self.session_manager.save_last_session(self.get_session_state())
            self.log_message(f"Auto-saved last session: {path}")
        except Exception as e:
            self.log_message(f"Auto-save error: {e}")

    def find_radio_index_by_name(self, display_name):
        for i in range(self.radio_combo.count()):
            profile = self.radio_combo.itemData(i)
            if profile and profile.get("display_name") == display_name:
                return i
        return -1

    def find_band_index_by_id(self, band_id):
        for i in range(self.band_combo.count()):
            if self.band_combo.itemData(i) == band_id:
                return i
        return -1

    def get_session_state(self):
        radio_name = ""
        if self.current_profile:
            radio_name = self.current_profile.get("display_name", "")

        return {
            "main": {
                "x": self.x(),
                "y": self.y(),
                "w": self.width(),
                "h": self.height(),
                "compact": bool(self.compact_mode),
                "monitor_visible": bool(self.monitor_visible),
                "radio_name": radio_name,
                "band_id": self.current_band_id,
                "output": self.current_clock,
                "rf_hz": int(self.current_rf_hz),
                "step_hz": int(self.step_hz),
            },
            "floating_windows": [
                window.get_session_state()
                for window in list(self.radio_windows)
                if hasattr(window, "get_session_state")
            ],
        }

    def save_session_profile(self):
        try:
            name, ok = QInputDialog.getText(
                self,
                "Save Session Profile",
                "Session name:",
                text="Swan Station",
            )
            if not ok:
                return

            path = self.session_manager.save(name, self.get_session_state())
            self.log_message(f"Saved session profile: {path}")
        except Exception as e:
            QMessageBox.warning(self, "Save Session Profile", str(e))
            self.log_message(f"Save session error: {e}")

    def load_session_profile(self):
        try:
            names = self.session_manager.list_sessions()
            if not names:
                QMessageBox.information(
                    self,
                    "Load Session Profile",
                    "No saved session profiles were found.",
                )
                return

            name, ok = QInputDialog.getItem(
                self,
                "Load Session Profile",
                "Choose session:",
                names,
                0,
                False,
            )
            if not ok:
                return

            data = self.session_manager.load(name)
            self.apply_session_state(data)
            self.log_message(f"Loaded session profile: {name}")
        except Exception as e:
            QMessageBox.warning(self, "Load Session Profile", str(e))
            self.log_message(f"Load session error: {e}")

    def close_floating_windows_for_session_load(self):
        for window in list(self.radio_windows):
            try:
                window.close()
            except Exception:
                pass
        self.radio_windows.clear()

    def apply_main_session_state(self, state):
        output = state.get("output", self.current_clock)
        if output != self.current_clock:
            approved = self.output_manager.reassign_output(
                self.current_clock,
                output,
                self.window_id,
                self.window_name,
            )
            if approved:
                self.current_clock = output
                self.set_combo_to_output(self.clock_combo, output)
        else:
            self.set_combo_to_output(self.clock_combo, output)

        radio_name = state.get("radio_name", "")
        if radio_name:
            idx = self.find_radio_index_by_name(radio_name)
            if idx >= 0:
                self.radio_combo.setCurrentIndex(idx)

        band_id = state.get("band_id")
        if band_id:
            idx = self.find_band_index_by_id(band_id)
            if idx >= 0:
                self.band_combo.setCurrentIndex(idx)

        self.current_rf_hz = int(state.get("rf_hz", self.current_rf_hz))
        self.pending_tune_hz = self.current_rf_hz
        self.freq_entry.setText(str(self.current_rf_hz))

        saved_step = int(state.get("step_hz", self.step_hz))
        if saved_step in self.step_list:
            self.step_hz = saved_step
            self.step_index = self.step_list.index(saved_step)

        self.current_vfo_hz = 0
        self.vfo_display.setText("VFO: --- MHz")

        self.spot_active = False
        self.tx_active = False
        self.spot_button.setText("SPOT OFF")
        self.spot_button.setStyleSheet("")
        self.txrx_label.setText("RX")
        self.txrx_label.setStyleSheet(
            "background-color: green; color: white; font-size: 24px; font-weight: bold;"
        )

        self.update_frequency_display()
        self.update_compact_identity()
        self.update_output_manager_state()

        desired_compact = bool(state.get("compact", False))
        if desired_compact != self.compact_mode:
            self.toggle_compact()

        #
        # Restore position, but do NOT restore old wide development-era size.
        #
        # Earlier session files may contain a very wide main-window geometry.
        # The v9B/v9C main window uses a narrower two-row toolbar layout, so
        # restoring the old saved width defeats the new ergonomic design.
        #
        # Keep the saved screen position, then force the current intended size.
        #

        x = int(state.get("x", self.x()))
        y = int(state.get("y", self.y()))

        if self.compact_mode:
            self.setGeometry(x, y, 390, 245)
        else:
            target_height = (
                self.monitor_height if self.monitor_visible else self.normal_height
            )
            self.setGeometry(x, y, self.normal_width, target_height)

    def apply_session_state(self, data):
        """
        Restore saved station profile.
        RF, SPOT, and TX are intentionally forced OFF.
        """
        if self.link.is_connected():
            for i in range(6):
                try:
                    self.link.send_output_enable(f"OUT{i}", False)
                except Exception:
                    pass

        self.output_manager.force_all_rf_off()
        self.update_global_rf_indicator()
        self.close_floating_windows_for_session_load()

        main_state = data.get("main", {})
        self.apply_main_session_state(main_state)

        for index, window_state in enumerate(data.get("floating_windows", []), start=2):
            preferred_output = window_state.get("output")
            if not preferred_output:
                preferred_output = self.output_manager.find_free_output_name()

            if preferred_output is None:
                self.log_message("Skipping saved window: no free output available")
                continue

            window = RadioControlWindow(
                controller=self,
                link=self.link,
                profiles=self.profiles,
                preferred_output=preferred_output,
                output_manager=self.output_manager,
                window_name=window_state.get("window_name", f"Radio {index}"),
            )
            self.radio_windows.append(window)
            window.apply_session_state(window_state)
            window.show()

        self.output_manager.force_all_rf_off()
        self.update_global_rf_indicator()
        self.update_output_manager_state()
        self.set_active_window(self.window_id)
        self.ensure_all_windows_visible()  # v4D6E

    def set_active_window(self, owner_id):
        """
        Mark one radio control window as active.

        This is visual only. It does not change RF, output ownership,
        or serial routing.
        """
        self.active_owner_id = owner_id
        self.apply_active_highlights()

    def apply_active_highlights(self):
        """
        Apply active/inactive visual styling to main and floating windows.
        """
        try:
            main_active = self.active_owner_id == self.window_id
            self.apply_main_active_style(main_active)

            for window in list(self.radio_windows):
                if hasattr(window, "set_active_visual"):
                    window.set_active_visual(
                        getattr(window, "window_id", None) == self.active_owner_id
                    )

            if self.output_manager_window is not None:
                try:
                    self.output_manager_window.refresh()
                except Exception:
                    pass

        except Exception as e:
            self.log_message(f"Active highlight error: {e}")

    def apply_main_active_style(self, active):
        """
        Main controller active indicator.

        The output color strip remains the output identity.
        The border/outline indicates active control focus.
        """
        if active:
            self.centralWidget().setStyleSheet(
                "#mainActiveFrame { border: 4px solid #E69F00; }"
            )
        else:
            self.centralWidget().setStyleSheet(
                "#mainActiveFrame { border: 1px solid #BBBBBB; }"
            )

    def mousePressEvent(self, event):
        self.set_active_window(self.window_id)
        super().mousePressEvent(event)

    def clamp_widget_to_visible_screen(self, widget):
        """
        Force a window/widget back onto the visible desktop area.

        This prevents saved/restored positions from opening partly off-screen
        after monitor, DPI, or resolution changes.
        """
        try:
            if widget is None:
                return

            screen = QApplication.screenAt(widget.frameGeometry().center())
            if screen is None:
                screen = QApplication.primaryScreen()
            if screen is None:
                return

            area = screen.availableGeometry()
            geo = widget.frameGeometry()

            # If the window is wider/taller than the screen, keep its top-left visible.
            max_x = max(area.x(), area.right() - geo.width())
            max_y = max(area.y(), area.bottom() - geo.height())

            x = min(max(geo.x(), area.x()), max_x)
            y = min(max(geo.y(), area.y()), max_y)

            widget.move(x, y)

        except Exception as e:
            self.log_message(f"Window position safety error: {e}")

    def ensure_visible_on_screen(self):
        """
        Keep the main controller window visible.
        """
        self.clamp_widget_to_visible_screen(self)

    def ensure_all_windows_visible(self):
        """
        Keep main and all floating radio windows visible.
        """
        self.ensure_visible_on_screen()
        for window in list(self.radio_windows):
            self.clamp_widget_to_visible_screen(window)

    def visible_radio_windows(self):
        """
        Return floating radio windows that still exist and are visible.
        """
        return [
            window
            for window in list(self.radio_windows)
            if window is not None and window.isVisible()
        ]

    def arrange_radio_windows(self):
        """
        Tile the main window and floating radio windows into a clean shack layout.

        Layout model:
          - Main controller at upper-left.
          - Floating radio tiles arranged to the right and then below.
          - Compact windows keep compact size.
          - Full windows keep larger setup size.
        """
        try:
            screen = QApplication.primaryScreen()
            if screen is None:
                self.log_message("Arrange Windows: no screen found")
                return

            area = screen.availableGeometry()

            margin = 20
            gap = 12

            x0 = area.x() + margin
            y0 = area.y() + margin

            # Main window remains the controller anchor.
            if self.compact_mode:
                main_w, main_h = 390, 245
            else:
                main_w, main_h = self.normal_width, self.normal_height

            self.setGeometry(x0, y0, main_w, main_h)

            windows = self.visible_radio_windows()

            # Operating tile sizes. These match the current compact/full intent.
            compact_w, compact_h = 375, 205
            full_w, full_h = 560, 360

            # Start floating windows to the right of the main controller if possible.
            start_x = x0 + main_w + gap
            start_y = y0

            max_right = area.x() + area.width() - margin

            x = start_x
            y = start_y
            row_h = 0

            # If there is not enough room to the right, start below main.
            if start_x + compact_w > max_right:
                x = x0
                y = y0 + main_h + gap

            for window in windows:
                if getattr(window, "compact_mode", False):
                    w, h = compact_w, compact_h
                else:
                    w, h = full_w, full_h

                if x + w > max_right:
                    x = x0
                    y += row_h + gap
                    row_h = 0

                window.setGeometry(x, y, w, h)
                window.showNormal()
                window.raise_()

                x += w + gap
                row_h = max(row_h, h)

            self.raise_()
            self.activateWindow()
            self.apply_active_highlights()
            self.ensure_all_windows_visible()
            self.log_message("Arranged radio windows")

        except Exception as e:
            self.log_message(f"Arrange Windows error: {e}")

    def focus_window_by_owner_id(self, owner_id):
        """
        Bring the window that owns a selected Output Manager row to the front.
        """
        try:
            if owner_id == self.window_id:
                self.set_active_window(self.window_id)
                self.showNormal()
                self.raise_()
                self.activateWindow()
                self.freq_display.setFocus()
                self.log_message("Focused Main Radio 1")
                return

            for window in list(self.radio_windows):
                if getattr(window, "window_id", None) == owner_id:
                    self.set_active_window(owner_id)
                    window.showNormal()
                    window.raise_()
                    window.activateWindow()
                    if hasattr(window, "freq_display"):
                        window.freq_display.setFocus()
                    self.log_message(
                        f"Focused {getattr(window, 'window_name', 'Radio Window')}"
                    )
                    return

            self.log_message("No open window found for selected output")

        except Exception as e:
            self.log_message(f"Focus window error: {e}")

    def show_calibration_window(self):
        if self.calibration_window is None:
            self.calibration_window = CalibrationWindow(self)

        self.calibration_window.show()
        self.calibration_window.raise_()
        self.calibration_window.activateWindow()

    def show_developer_console(self):
        self.developer_console = DeveloperConsole(self.link, self)
        self.developer_console.show()

    def show_help_window(self):
        if self.help_window is None:
            self.help_window = HelpWindow(self)

        self.help_window.show()
        self.help_window.raise_()
        self.help_window.activateWindow()

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def open_profile_editor(self):
        """
        Launch the Radio Profile Editor as a separate non-blocking process.

        Source mode:
            Starts profile_editor.py with the current Python interpreter.

        PyInstaller EXE mode:
            Starts this same EXE with --profile-editor. This avoids Windows
            trying to open profile_editor.py as a text/source file and keeps
            the packaged application self-contained.
        """
        try:
            if (
                self.profile_editor_process is not None
                and self.profile_editor_process.poll() is None
            ):
                self.log_message("Profile Editor is already running")
                return

            if getattr(sys, "frozen", False):
                exe_path = Path(sys.executable).resolve()
                work_dir = exe_path.parent / "_internal"

                if not work_dir.exists():
                    work_dir = exe_path.parent

                self.profile_editor_process = subprocess.Popen(
                    [str(exe_path), "--profile-editor"],
                    cwd=str(work_dir),
                )
            else:
                editor_path = Path(__file__).with_name("profile_editor.py")

                if not editor_path.exists():
                    QMessageBox.warning(
                        self,
                        "Profile Editor Not Found",
                        f"Could not find:\n\n{editor_path}",
                    )
                    return

                self.profile_editor_process = subprocess.Popen(
                    [sys.executable, str(editor_path)],
                    cwd=str(editor_path.parent),
                )

            self.log_message("Opened Radio Profile Editor")

        except Exception as e:
            QMessageBox.warning(
                self,
                "Profile Editor Launch Failed",
                str(e),
            )
            self.log_message(f"Profile Editor launch error: {e}")

    def show_output_manager(self):
        if self.output_manager_window is None:
            self.output_manager_window = OutputManagerWindow(
                self.output_manager,
                self,
            )
        self.output_manager_window.show()
        self.output_manager_window.raise_()
        self.output_manager_window.activateWindow()

    def update_output_manager_state(self):
        if hasattr(self, "output_color_label"):
            self.update_output_color_label()

        radio_name = ""
        if self.current_profile:
            radio_name = self.current_profile.get("display_name", "")

        band_name = self.band_combo.currentText() if hasattr(self, "band_combo") else ""

        self.output_manager.update_radio_state(
            owner_id=self.window_id,
            radio_name=radio_name,
            band_name=band_name,
            frequency_hz=self.current_rf_hz,
            vfo_hz=self.current_vfo_hz,
            step_hz=self.step_hz,
        )
        if hasattr(self, "safety_label"):
            self.update_safety_monitor(allow_popup=False)

    def set_frequency(self):
        try:
            rf_hz = self.parse_frequency_entry(self.freq_entry.text())
            if rf_hz < MIN_FREQ_HZ or rf_hz > MAX_FREQ_HZ:
                self.log_message("Frequency out of range")
                return
            if not self.current_profile or not self.current_band_id:
                self.log_message("Select radio and band first")
                return
            result = calculate_output_frequency(
                self.current_profile, self.current_band_id, rf_hz
            )
            if not result.ok:
                self.log_message(result.message)
                return
            response = self.link.send_frequency(result.output_hz, self.current_clock)
            self.current_rf_hz = int(result.rf_hz)
            self.current_vfo_hz = int(result.output_hz)
            self.pending_tune_hz = self.current_rf_hz
            self.update_frequency_display()
            self.vfo_display.setText(f"VFO: {self.format_frequency(result.output_hz)}")
            self.update_output_manager_state()
            self.log_message(
                f"Main {self.current_clock} | {self.current_profile['display_name']} | "
                f"{self.current_band_id} | RF {result.rf_hz} -> VFO {result.output_hz} -> {response}"
            )
        except Exception as e:
            self.log_message(f"Set frequency error: {e}")

    def adjust_frequency(self, direction):
        try:
            new_hz = self.current_rf_hz + direction * self.step_hz
            new_hz = max(MIN_FREQ_HZ, min(MAX_FREQ_HZ, new_hz))
            self.current_rf_hz = int(new_hz)
            self.pending_tune_hz = int(new_hz)
            self.freq_entry.setText(str(new_hz))
            self.update_frequency_display()
            self.update_output_manager_state()
            self.tune_send_timer.start(30)
        except Exception as e:
            self.log_message(f"Tune error: {e}")

    def send_pending_tune_frequency(self):
        try:
            if not self.current_profile or not self.current_band_id:
                return
            if not self.link.is_connected():
                return
            result = calculate_output_frequency(
                self.current_profile,
                self.current_band_id,
                self.pending_tune_hz,
            )
            if not result.ok:
                return
            cmd = f"F{self.current_clock[3]}{result.output_hz:011d};"
            self.link.ser.write(cmd.encode("ascii"))
            self.current_vfo_hz = int(result.output_hz)
            self.vfo_display.setText(f"VFO: {self.format_frequency(result.output_hz)}")
            self.update_output_manager_state()
        except Exception as e:
            self.log_message(f"Tune send error: {e}")

    def eventFilter(self, obj, event):
        if obj == self.freq_display and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                self.adjust_frequency(+1)
                return True
            if event.key() == Qt.Key_Down:
                self.adjust_frequency(-1)
                return True
            if event.key() == Qt.Key_Left:
                self.set_step_by_index(self.step_index - 1)
                return True
            if event.key() == Qt.Key_Right:
                self.set_step_by_index(self.step_index + 1)
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.adjust_frequency(+1)
        elif event.key() == Qt.Key_Down:
            self.adjust_frequency(-1)
        elif event.key() == Qt.Key_Left:
            self.set_step_by_index(self.step_index - 1)
        elif event.key() == Qt.Key_Right:
            self.set_step_by_index(self.step_index + 1)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.adjust_frequency(+1)
        elif event.angleDelta().y() < 0:
            self.adjust_frequency(-1)
        else:
            super().wheelEvent(event)

    def freq_display_wheel(self, event):
        self.freq_display.setFocus()
        if event.angleDelta().y() > 0:
            self.adjust_frequency(+1)
        elif event.angleDelta().y() < 0:
            self.adjust_frequency(-1)
        event.accept()

    def freq_display_clicked(self, event):
        self.freq_display.setFocus()
        text = self.display_frequency_text()
        font_metrics = self.freq_display.fontMetrics()
        text_width = font_metrics.horizontalAdvance(text)
        left_edge = (self.freq_display.width() - text_width) / 2
        x = event.position().x() - left_edge
        char_width = font_metrics.horizontalAdvance("0")
        char_index = int(x // char_width)
        digit_to_step = {
            0: 10_000_000,
            1: 1_000_000,
            3: 100_000,
            4: 10_000,
            5: 1_000,
            6: 100,
            7: 10,
            8: 1,
        }
        if char_index in digit_to_step:
            self.set_step_by_hz(digit_to_step[char_index])

    def blink_status(self):
        """
        Blink the USB COM-port warning while not connected.
        """
        if self.link.is_connected():
            return

        self.blink_state = not self.blink_state

        if self.blink_state:
            self.status_label.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; padding: 3px;"
            )
        else:
            self.status_label.setStyleSheet(
                "background-color: black; color: red; font-weight: bold; padding: 3px;"
            )

    def set_connected_state(self, connected):
        self.connect_button.setEnabled(not connected)
        self.disconnect_button.setEnabled(connected)
        self.refresh_button.setEnabled(not connected)
        self.port_combo.setEnabled(not connected)

        self.new_window_button.setEnabled(True)
        self.output_manager_button.setEnabled(True)
        self.profile_editor_button.setEnabled(True)
        self.calibration_button.setEnabled(True)
        self.help_button.setEnabled(True)
        self.about_button.setEnabled(True)
        self.save_session_button.setEnabled(True)
        self.load_session_button.setEnabled(True)
        self.arrange_windows_button.setEnabled(True)
        self.monitor_button.setEnabled(True)
        self.compact_button.setEnabled(True)

        self.set_freq_button.setEnabled(True)
        self.read_freq_button.setEnabled(True)

        self.rf_on_button.setEnabled(connected)
        self.rf_off_button.setEnabled(connected)
        self.spot_button.setEnabled(connected)
        self.id_button.setEnabled(connected)
        self.cal_button.setEnabled(connected)

        if not connected:
            self.status_label.setText("NOT CONNECTED TO USB COM PORT")
            self.blink_timer.start(700)
        else:
            self.blink_timer.stop()

            port = self.port_combo.currentText()
            if not port:
                port = "COM?"

            self.status_label.setText(f"CONNECTED TO {port} @ {DEFAULT_BAUD}")
            self.status_label.setStyleSheet(
                "background-color: green; color: white; font-weight: bold; padding: 3px;"
            )

    def toggle_monitor(self):
        self.monitor_visible = not self.monitor_visible
        self.log.setVisible(self.monitor_visible)
        if self.monitor_visible:
            self.monitor_button.setText("Monitor ON")
            self.resize(self.normal_width, self.monitor_height)
        else:
            self.monitor_button.setText("Monitor OFF")
            self.resize(self.normal_width, self.normal_height)

    def toggle_compact(self):
        self.compact_mode = not self.compact_mode
        self.apply_compact_mode()

    def apply_compact_mode(self):
        self.update_compact_identity()

        if self.compact_mode:
            self.compact_button.setText("FULL")

            self.port_label.setVisible(False)
            self.port_combo.setVisible(False)
            self.refresh_button.setVisible(False)
            self.connect_button.setVisible(False)
            self.disconnect_button.setVisible(False)
            self.new_window_button.setVisible(False)
            self.output_manager_button.setVisible(False)
            self.save_session_button.setVisible(False)
            self.load_session_button.setVisible(False)
            self.arrange_windows_button.setVisible(False)
            self.monitor_button.setVisible(False)
            self.calibration_button.setVisible(False)
            self.reload_profiles_button.setVisible(False)
            self.profile_editor_button.setVisible(False)
            self.help_button.setVisible(False)
            self.about_button.setVisible(False)

            self.radio_label.setVisible(False)
            self.radio_combo.setVisible(False)
            self.band_label.setVisible(False)
            self.band_combo.setVisible(False)
            self.output_label.setVisible(False)
            self.clock_combo.setVisible(False)
            self.compact_identity_label.setVisible(True)

            self.freq_entry.setVisible(False)
            self.set_freq_button.setVisible(False)
            self.read_freq_button.setVisible(False)
            self.rf_on_button.setVisible(False)
            self.rf_off_button.setVisible(False)
            self.id_button.setVisible(False)
            self.cal_button.setVisible(False)

            self.log.setVisible(False)
            self.monitor_visible = False
            self.monitor_button.setText("Monitor OFF")

            self.resize(390, 245)
        else:
            self.compact_button.setText("COMPACT")

            self.port_label.setVisible(True)
            self.port_combo.setVisible(True)
            self.refresh_button.setVisible(True)
            self.connect_button.setVisible(True)
            self.disconnect_button.setVisible(True)
            self.new_window_button.setVisible(True)
            self.output_manager_button.setVisible(True)
            self.save_session_button.setVisible(True)
            self.load_session_button.setVisible(True)
            self.arrange_windows_button.setVisible(True)
            self.monitor_button.setVisible(True)
            self.calibration_button.setVisible(True)
            self.reload_profiles_button.setVisible(True)
            self.profile_editor_button.setVisible(True)
            self.help_button.setVisible(True)
            self.about_button.setVisible(True)

            self.radio_label.setVisible(True)
            self.radio_combo.setVisible(True)
            self.band_label.setVisible(True)
            self.band_combo.setVisible(True)
            self.output_label.setVisible(True)
            self.clock_combo.setVisible(True)
            self.compact_identity_label.setVisible(False)

            self.freq_entry.setVisible(True)
            self.set_freq_button.setVisible(True)
            self.read_freq_button.setVisible(True)
            self.rf_on_button.setVisible(True)
            self.rf_off_button.setVisible(True)
            self.id_button.setVisible(True)
            self.cal_button.setVisible(True)

            self.log.setVisible(self.monitor_visible)
            self.resize(
                self.normal_width,
                self.monitor_height if self.monitor_visible else self.normal_height,
            )

    def update_output_color_label(self):
        try:
            index = output_name_to_index(self.current_clock)
            label = output_name_to_user_label(self.current_clock)
            color = index_to_color(index)
            self.output_color_label.setText(f"{label}  ({self.current_clock})")
            self.output_color_label.setStyleSheet(
                f"background-color: {color}; color: white; font-size: 14px; "
                "font-weight: bold; padding: 3px;"
            )
        except Exception:
            pass

    def update_compact_identity(self):
        self.update_output_color_label()
        radio_name = "No radio"
        if self.current_profile:
            radio_name = self.current_profile.get("display_name", "Radio")

        band_name = "No band"
        if self.band_combo.currentText():
            band_name = self.band_combo.currentText()

        self.compact_identity_label.setText(
            f"Main Radio 1 | {radio_name} | {band_name} | "
            f"{output_name_to_user_label(self.current_clock)}"
        )

    def log_message(self, text):
        if hasattr(self, "log"):
            self.log.append(str(text))
        else:
            print(text)

    def debug_serial(self, line):
        line = line.strip()
        if self.monitor_visible:
            self.log_message(f"RX: {line}")

        if len(line) == 4 and line.startswith("TX") and line.endswith(";"):
            output = f"OUT{line[2]}"
            self.output_manager.update_tx_state_by_output(output, True)
            self.update_global_rf_indicator()
            self.update_safety_monitor()
            self.route_ptt_event(output, True)
            return

        if len(line) == 4 and line.startswith("RX") and line.endswith(";"):
            output = f"OUT{line[2]}"
            self.output_manager.update_tx_state_by_output(output, False)
            self.update_global_rf_indicator()
            self.update_safety_monitor()
            self.route_ptt_event(output, False)
            return

    def route_ptt_event(self, output, is_tx):
        if output == self.current_clock:
            self.handle_ptt_event(is_tx)
            return
        for window in list(self.radio_windows):
            if getattr(window, "current_clock", None) == output:
                window.handle_ptt_event(is_tx)
                return

    def handle_ptt_event(self, is_tx):
        if is_tx:
            self.tx_active = True
            self.txrx_label.setText("TX")
            self.txrx_label.setStyleSheet(
                "background-color: red; color: white; font-size: 24px; font-weight: bold;"
            )
            self.set_rf_output(True, reason="PTT TX")
        else:
            self.tx_active = False
            self.txrx_label.setText("RX")
            self.txrx_label.setStyleSheet(
                "background-color: green; color: white; font-size: 24px; font-weight: bold;"
            )
            if self.spot_active:
                self.set_rf_output(True, reason="SPOT")
            else:
                self.set_rf_output(False, reason="PTT RX")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.link.list_ports()
        self.port_combo.addItems(ports)

        last_port = self.app_settings.get("last_com_port", "")
        if last_port:
            idx = self.port_combo.findText(last_port)
            if idx >= 0:
                self.port_combo.setCurrentIndex(idx)
                self.log_message(f"Selected last USB COM port: {last_port}")
            elif ports:
                self.log_message(f"Last USB COM port {last_port} was not found")

    def connect_radio(self):
        port = self.port_combo.currentText()

        if not port:
            self.log_message("No USB COM port selected")
            return

        #
        # STEP 1:
        # Open serial port ONLY.
        #
        try:
            print("CONNECT CALLED")
            print(f"OPEN SERIAL: {port}")

            self.link.connect(port)

            print("SERIAL OPEN SUCCESS")

        except Exception as e:

            error_text = str(e)
            lower_error = error_text.lower()

            self.status_label.setText(f"{port} NOT AVAILABLE")
            self.status_label.setStyleSheet(
                "background-color: red; color: white; font-weight: bold; padding: 3px;"
            )

            if (
                "access is denied" in lower_error
                or "permission" in lower_error
                or "could not open port" in lower_error
                or "resource busy" in lower_error
            ):

                nl = chr(10)

                message = (
                    f"{port} appears to be used by another program."
                    + nl
                    + nl
                    + "Close Arduino Serial Monitor, another terminal program, "
                    + "or any other program using that COM port."
                )

                QMessageBox.warning(self, "USB COM Port Busy", message)

            else:

                QMessageBox.warning(
                    self,
                    "USB COM Connection Failed",
                    error_text,
                )

            self.set_connected_state(False)
            return

        #
        # STEP 2:
        # Everything after serial open.
        #
        try:

            self.app_settings.set("last_com_port", port)

            self.log_message(f"Connected to {port} @ {DEFAULT_BAUD}")

            self.set_connected_state(True)

            self.freq_display.setFocus()

        except Exception as e:

            QMessageBox.warning(
                self,
                "Post-Connect Error",
                f"Serial port opened successfully, but GUI initialization failed:\n\n{e}",
            )

            self.log_message(f"Post-connect error: {e}")

    def disconnect_radio(self):
        try:
            if self.link.is_connected():
                self.set_rf_output(False, reason="Disconnect")
                for window in list(self.radio_windows):
                    window.set_rf_output(False, reason="Disconnect")
        except Exception:
            pass
        self.output_manager.force_all_rf_off()
        self.update_global_rf_indicator()
        self.link.disconnect()
        self.log_message("Disconnected from USB COM port")
        self.set_connected_state(False)

    def parse_frequency_entry(self, text):
        text = text.strip().lower().replace(",", "")
        if not text:
            raise ValueError("Empty frequency")
        if text.endswith("mhz"):
            return int(round(float(text[:-3].strip()) * 1_000_000))
        if text.endswith("khz"):
            return int(round(float(text[:-3].strip()) * 1_000))
        if text.endswith("hz"):
            return int(round(float(text[:-2].strip())))
        if "." in text:
            return int(round(float(text) * 1_000_000))
        value = int(text)
        if value >= 1_000_000:
            return value
        if value >= 1000:
            return value * 1000
        return value * 1_000_000

    def id_test(self):
        try:
            self.log_message(self.radio.get_id())
        except Exception as e:
            self.log_message(f"ID error: {e}")

    def read_frequency(self):
        try:
            self.log_message(self.radio.get_frequency())
        except Exception as e:
            self.log_message(f"Read frequency error: {e}")

    def rf_on(self):
        self.spot_active = False
        self.spot_button.setText("SPOT OFF")
        self.spot_button.setStyleSheet("")
        self.set_rf_output(True, reason="Manual RF ON")

    def rf_off(self):
        self.spot_active = False
        self.spot_button.setText("SPOT OFF")
        self.spot_button.setStyleSheet("")
        self.set_rf_output(False, reason="Manual RF OFF")

    def toggle_spot(self):
        self.spot_active = not self.spot_active
        if self.spot_active:
            self.spot_button.setText("SPOT ON")
            self.spot_button.setStyleSheet(
                "background-color: orange; color: black; font-weight: bold;"
            )
            self.set_rf_output(True, reason="SPOT ON")
        else:
            self.spot_button.setText("SPOT OFF")
            self.spot_button.setStyleSheet("")
            if self.tx_active:
                self.set_rf_output(True, reason="TX still active")
            else:
                self.set_rf_output(False, reason="SPOT OFF")

    def read_calibration(self):
        try:
            self.log_message(self.radio.get_calibration())
        except Exception as e:
            self.log_message(f"Calibration read error: {e}")

    def format_frequency(self, hz):
        return f"{hz / 1_000_000:.6f} MHz"

    def display_frequency_text(self):
        hz = int(self.current_rf_hz)
        return f"{hz // 1_000_000:02d}.{hz % 1_000_000:06d} MHz"

    def format_step(self):
        if self.step_hz >= 1_000_000:
            return f"{self.step_hz // 1_000_000} MHz"
        if self.step_hz >= 1_000:
            return f"{self.step_hz // 1_000} kHz"
        return f"{self.step_hz} Hz"

    def update_frequency_display(self):
        text = self.display_frequency_text()
        digit_map = {
            10_000_000: 0,
            1_000_000: 1,
            100_000: 3,
            10_000: 4,
            1_000: 5,
            100: 6,
            10: 7,
            1: 8,
        }
        active_pos = digit_map.get(self.step_hz, 6)
        html = ""
        for i, ch in enumerate(text):
            if i == active_pos:
                html += (
                    "<span style='background-color: orange; color: black;'>"
                    + ch
                    + "</span>"
                )
            else:
                html += ch
        self.freq_display.setText(html)
        self.step_display.setText(f"Step: {self.format_step()}")

    def set_step_by_index(self, index):
        self.step_index = max(0, min(len(self.step_list) - 1, index))
        self.step_hz = self.step_list[self.step_index]
        self.update_frequency_display()
        self.update_output_manager_state()
        self.log_message(f"Main Step: {self.format_step()}")

    def set_step_by_hz(self, step_hz):
        if step_hz in self.step_list:
            self.step_index = self.step_list.index(step_hz)
            self.step_hz = step_hz
            self.update_frequency_display()
            self.update_output_manager_state()
            self.log_message(f"Main Step: {self.format_step()}")

    def normalize_band_name(self, band_name):
        """
        Normalize band names enough for safety comparison.

        The profile display names may be "75m", "80m", "6m", etc.
        We compare exact normalized text. This is intentionally conservative.
        """
        text = str(band_name or "").strip().lower()
        text = text.replace("meters", "m").replace("meter", "m")
        text = text.replace(" ", "")
        return text

    def evaluate_safety_state(self):
        """
        Return (level, message, key).

        level:
          OK
          CAUTION
          DANGER
        """
        try:
            tx_by_band = {}
            caution_items = []

            for state in self.output_manager.all_states():
                if not state.owner_id:
                    continue

                band = self.normalize_band_name(state.band_name)
                label = state.user_label
                radio = state.radio_name or state.owner_name or "Radio"

                if state.tx_active:
                    if not band or band in ("---", "none", "noband"):
                        caution_items.append(f"{label}: TX with unknown band")
                    else:
                        tx_by_band.setdefault(band, []).append(
                            f"{label}: {radio} {state.band_name}"
                        )

            danger_messages = []
            for band, entries in tx_by_band.items():
                if len(entries) > 1:
                    danger_messages.append(
                        "Same-band TX conflict on " + band + " — " + "; ".join(entries)
                    )

            if danger_messages:
                message = "SAFETY: DANGER - " + " | ".join(danger_messages)
                key = "DANGER:" + "|".join(sorted(danger_messages))
                return "DANGER", message, key

            if caution_items:
                message = "SAFETY: CAUTION - " + "; ".join(caution_items)
                key = "CAUTION:" + "|".join(sorted(caution_items))
                return "CAUTION", message, key

            return "OK", "SAFETY: OK", "OK"

        except Exception as e:
            return "CAUTION", f"SAFETY: MONITOR ERROR - {e}", "MONITOR_ERROR"

    def update_safety_monitor(self, allow_popup=True):
        """
        Update the persistent safety bar and optionally warn on dangerous states.

        Current policy:
          - Multi-band TX is allowed.
          - Same-band simultaneous TX is dangerous.
          - v4D6E is WARN ONLY. It does not block RF.
        """
        level, message, key = self.evaluate_safety_state()

        if hasattr(self, "safety_label"):
            if level == "DANGER":
                self.safety_label.setText(message)
                self.safety_label.setStyleSheet(
                    "background-color: red; color: white; font-size: 15px; font-weight: bold; padding: 4px;"
                )
            elif level == "CAUTION":
                self.safety_label.setText(message)
                self.safety_label.setStyleSheet(
                    "background-color: #E69F00; color: black; font-size: 15px; font-weight: bold; padding: 4px;"
                )
            else:
                self.safety_label.setText("SAFETY: OK")
                self.safety_label.setStyleSheet(
                    "background-color: #444444; color: white; font-size: 15px; font-weight: bold; padding: 4px;"
                )

        if level == "DANGER" and allow_popup and key != self.last_safety_warning_key:
            self.last_safety_warning_key = key
            QMessageBox.warning(
                self,
                "Band-Aware Safety Warning",
                message
                + chr(10)
                + chr(10)
                + "Multi-band TX is allowed."
                + chr(10)
                + "Same-band simultaneous TX is dangerous."
                + chr(10)
                + chr(10)
                + "v4D6E is warning only and has not blocked RF.",
            )

        if level == "OK":
            self.last_safety_warning_key = None

        if self.output_manager_window is not None:
            try:
                self.output_manager_window.refresh()
            except Exception:
                pass

    def update_global_rf_indicator(self):
        """
        Show one global RF safety summary for the whole VFO system.

        Priority:
          TX ACTIVE > SPOT ACTIVE > RF ON > ALL OFF
        """
        try:
            tx_outputs = []
            spot_outputs = []
            rf_outputs = []

            for state in self.output_manager.all_states():
                label = state.user_label
                if state.tx_active:
                    tx_outputs.append(label)
                elif state.spot_enabled:
                    spot_outputs.append(label)
                elif state.rf_enabled:
                    rf_outputs.append(label)

            if tx_outputs:
                text = "GLOBAL RF: TX ACTIVE ON " + ", ".join(tx_outputs)
                style = "background-color: red; color: white; font-size: 16px; font-weight: bold; padding: 4px;"
            elif spot_outputs:
                text = "GLOBAL RF: SPOT ACTIVE ON " + ", ".join(spot_outputs)
                style = "background-color: orange; color: black; font-size: 16px; font-weight: bold; padding: 4px;"
            elif rf_outputs:
                text = "GLOBAL RF: RF ON " + ", ".join(rf_outputs)
                style = "background-color: #008000; color: white; font-size: 16px; font-weight: bold; padding: 4px;"
            else:
                text = "GLOBAL RF: ALL OUTPUTS OFF"
                style = "background-color: #333333; color: white; font-size: 16px; font-weight: bold; padding: 4px;"

            if hasattr(self, "global_rf_label"):
                self.global_rf_label.setText(text)
                self.global_rf_label.setStyleSheet(style)

        except Exception as e:
            self.log_message(f"Global RF indicator error: {e}")

    def set_rf_output(self, enabled, reason=""):
        if not self.link.is_connected():
            self.log_message("RF enable ignored: serial port not connected")
            self.output_manager.update_rf_state_by_owner(
                self.window_id,
                False,
                False,
                self.tx_active,
            )
            self.update_global_rf_indicator()
            self.update_safety_monitor()
            return
        try:
            command = self.link.send_output_enable(self.current_clock, enabled)
            state_text = "ON" if enabled else "OFF"
            self.output_manager.update_rf_state_by_owner(
                self.window_id,
                enabled,
                self.spot_active,
                self.tx_active,
            )
            self.update_global_rf_indicator()
            self.update_safety_monitor()
            self.log_message(
                f"{self.current_clock} RF {state_text} via {reason}: {command}"
            )
        except Exception as e:
            self.log_message(f"RF enable error: {e}")

    def shutdown_system(self):
        self.log_message("System shutdown initiated")

        self.auto_save_last_session()

        try:
            if self.link.is_connected():
                for i in range(6):
                    try:
                        self.link.send_output_enable(f"OUT{i}", False)
                    except Exception:
                        pass
        except Exception:
            pass

        if hasattr(self, "output_manager"):
            self.output_manager.force_all_rf_off()
        self.update_global_rf_indicator()

        for window in list(self.radio_windows):
            try:
                window.close()
            except Exception:
                pass

    def closeEvent(self, event):
        """
        Clean shutdown handler.

        Purpose:
        - Stop timers
        - Save session state
        - Close child windows
        - Disconnect serial port
        - Allow Python/EXE process to terminate cleanly
        """

        print("APPLICATION SHUTDOWN")

        try:
            # Stop monitor/update timers if they exist.
            if hasattr(self, "monitor_timer"):
                self.monitor_timer.stop()

            if hasattr(self, "status_timer"):
                self.status_timer.stop()

            # Save current session before closing child windows.
            if hasattr(self, "save_session"):
                self.save_session()

            # Close floating radio windows.
            if hasattr(self, "radio_windows"):
                for window in list(self.radio_windows):
                    try:
                        window.close()
                    except Exception as e:
                        print(f"Radio window close error: {e}")

            # Close Output Manager if open.
            if hasattr(self, "output_manager") and self.output_manager is not None:
                try:
                    self.output_manager.close()
                except Exception as e:
                    print(f"Output Manager close error: {e}")

            # Disconnect serial link.
            if hasattr(self, "link"):
                self.link.disconnect()
            elif hasattr(self, "serial"):
                self.serial.disconnect()

        except Exception as e:
            print(f"Shutdown cleanup error: {e}")

        QApplication.quit()
        event.accept()

    def closeEvent(self, event):
        """
        Clean application shutdown.

        Prevents orphaned background processes that can
        leave COM ports locked after the GUI closes.
        """

        print("APPLICATION SHUTDOWN")

        try:

            # Stop timers.
            if hasattr(self, "monitor_timer"):
                self.monitor_timer.stop()

            if hasattr(self, "status_timer"):
                self.status_timer.stop()

            # Save session state.
            if hasattr(self, "save_session"):
                self.save_session()

            # Close floating radio windows.
            if hasattr(self, "radio_windows"):
                for window in list(self.radio_windows):
                    try:
                        window.close()
                    except Exception as e:
                        print(f"Radio window close error: {e}")

            # Close Calibration window.
            if hasattr(self, "calibration_window"):
                if self.calibration_window is not None:
                    try:
                        self.calibration_window.close()
                    except Exception as e:
                        print(f"Calibration window close error: {e}")

            # Close Help window.
            if hasattr(self, "help_window"):
                if self.help_window is not None:
                    try:
                        self.help_window.close()
                    except Exception as e:
                        print(f"Help window close error: {e}")

            # Close Output Manager window.
            if hasattr(self, "output_manager_window"):
                if self.output_manager_window is not None:
                    try:
                        self.output_manager_window.close()
                    except Exception as e:
                        print(f"Output Manager close error: {e}")

            # Disconnect serial link.
            if hasattr(self, "link"):
                self.link.disconnect()

            elif hasattr(self, "serial"):
                self.serial.disconnect()

        except Exception as e:
            print(f"Shutdown cleanup error: {e}")

        QApplication.quit()

        event.accept()
