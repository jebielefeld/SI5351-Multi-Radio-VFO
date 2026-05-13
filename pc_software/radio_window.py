# File: radio_window.py
#
# Floating radio-control window for the SI5351 Multi-Radio VFO.
#
# v4D Output Manager Phase 1:
#   - Uses OutputManager for all output assignment/conflict checks.
#   - Operator-facing labels are Output 1 through Output 6.
#   - Internal firmware protocol remains OUT0 through OUT5.

import uuid

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
)
from PySide6.QtCore import Qt, QEvent, QTimer

from config import MIN_FREQ_HZ, MAX_FREQ_HZ
from radio_math import calculate_output_frequency
from output_manager import (
    index_to_output_name,
    output_name_to_user_label,
    output_name_to_index,
    index_to_color,
)


class RadioControlWindow(QWidget):
    """
    Floating radio-control window for one assigned output.

    The main controller owns the shared SerialLink and routes TXx/RXx events here.
    This window owns only radio profile/band/frequency UI state for one radio instance.
    """

    def __init__(
        self,
        controller,
        link,
        profiles,
        preferred_output="OUT1",
        output_manager=None,
        window_name="Radio",
    ):
        super().__init__()

        self.setObjectName("radioWindowFrame")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self.controller = controller
        self.link = link
        self.profiles = profiles or []
        self.output_manager = output_manager

        self.window_id = str(uuid.uuid4())
        self.window_name = window_name

        self.current_profile = None
        self.current_band_id = None
        self.current_clock = preferred_output

        self.current_rf_hz = 7_100_000
        self.current_vfo_hz = 0
        self.pending_tune_hz = self.current_rf_hz

        self.step_list = [10_000_000, 1_000_000, 100_000, 10_000, 1_000, 100, 10, 1]
        self.step_index = 5
        self.step_hz = self.step_list[self.step_index]

        self.spot_active = False
        self.tx_active = False
        self.compact_mode = False

        self.tune_send_timer = QTimer(self)
        self.tune_send_timer.setSingleShot(True)
        self.tune_send_timer.timeout.connect(self.send_pending_tune_frequency)

        if self.output_manager:
            self.output_manager.claim_output(
                self.current_clock,
                self.window_id,
                self.window_name,
            )

        self.setWindowTitle(f"{self.window_name} - {output_name_to_user_label(self.current_clock)}")
        self.resize(560, 360)

        self.build_ui()
        self.init_profiles()
        self.set_output_combo_to(preferred_output)
        self.update_title()
        self.update_output_manager_state()
        self.freq_display.setFocus()

    def build_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        top_row = QHBoxLayout()
        self.top_row = top_row

        self.radio_combo = QComboBox()
        self.band_combo = QComboBox()
        self.clock_combo = QComboBox()
        self.populate_output_combo(self.clock_combo)

        self.radio_combo.currentIndexChanged.connect(self.on_radio_changed)
        self.band_combo.currentIndexChanged.connect(self.on_band_changed)
        self.clock_combo.currentIndexChanged.connect(self.on_clock_combo_changed)

        top_row.addWidget(QLabel("Radio:"))
        top_row.addWidget(self.radio_combo)
        top_row.addWidget(QLabel("Band:"))
        top_row.addWidget(self.band_combo)
        top_row.addWidget(QLabel("Output:"))
        top_row.addWidget(self.clock_combo)
        main_layout.addLayout(top_row)

        self.output_color_label = QLabel(output_name_to_user_label(self.current_clock))
        self.output_color_label.setAlignment(Qt.AlignCenter)
        self.output_color_label.setStyleSheet(
            "background-color: #1f77b4; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
        )
        main_layout.addWidget(self.output_color_label)

        self.compact_info_label = QLabel()
        self.compact_info_label.setAlignment(Qt.AlignCenter)
        self.compact_info_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.compact_info_label.setVisible(False)
        main_layout.addWidget(self.compact_info_label)

        self.txrx_label = QLabel("RX")
        self.txrx_label.setAlignment(Qt.AlignCenter)
        self.txrx_label.setStyleSheet(
            "background-color: green; color: white; font-size: 22px; font-weight: bold;"
        )
        main_layout.addWidget(self.txrx_label)

        self.freq_display = QLabel()
        self.freq_display.setAlignment(Qt.AlignCenter)
        self.freq_display.setFocusPolicy(Qt.StrongFocus)
        self.freq_display.setStyleSheet(
            "font-family: Consolas; font-size: 38px; font-weight: bold;"
        )
        self.freq_display.mousePressEvent = self.freq_display_clicked
        self.freq_display.wheelEvent = self.freq_display_wheel
        self.freq_display.installEventFilter(self)
        main_layout.addWidget(self.freq_display)

        self.step_display = QLabel()
        self.step_display.setAlignment(Qt.AlignCenter)
        self.step_display.setStyleSheet("font-size: 15px; font-weight: bold;")
        main_layout.addWidget(self.step_display)

        self.vfo_display = QLabel("VFO: --- MHz")
        self.vfo_display.setAlignment(Qt.AlignCenter)
        self.vfo_display.setStyleSheet("font-size: 18px; color: yellow;")
        main_layout.addWidget(self.vfo_display)

        freq_row = QHBoxLayout()
        self.freq_row = freq_row
        self.freq_entry = QLineEdit()
        self.freq_entry.setPlaceholderText(
            "Examples: 7.100 | 7100 | 7100000 | 14.250 MHz"
        )
        self.freq_entry.setText(str(self.current_rf_hz))

        self.set_freq_button = QPushButton("Set Frequency")
        self.set_freq_button.clicked.connect(self.set_frequency)

        freq_row.addWidget(self.freq_entry)
        freq_row.addWidget(self.set_freq_button)
        main_layout.addLayout(freq_row)

        rf_row = QHBoxLayout()
        self.rf_row = rf_row
        self.rf_on_button = QPushButton("RF ON")
        self.rf_off_button = QPushButton("RF OFF")
        self.spot_button = QPushButton("SPOT OFF")
        self.compact_button = QPushButton("COMPACT")

        self.rf_on_button.clicked.connect(self.rf_on)
        self.rf_off_button.clicked.connect(self.rf_off)
        self.spot_button.clicked.connect(self.toggle_spot)
        self.compact_button.clicked.connect(self.toggle_compact)

        rf_row.addWidget(self.rf_on_button)
        rf_row.addWidget(self.rf_off_button)
        rf_row.addWidget(self.spot_button)
        rf_row.addWidget(self.compact_button)
        main_layout.addLayout(rf_row)

        self.update_frequency_display()

    def populate_output_combo(self, combo):
        combo.clear()
        for i in range(6):
            combo.addItem(output_name_to_user_label(index_to_output_name(i)), index_to_output_name(i))

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
        self.radio_combo.clear()
        for profile in self.profiles:
            self.radio_combo.addItem(profile["display_name"], profile)
        if self.radio_combo.count() > 0:
            self.radio_combo.setCurrentIndex(0)

    def set_output_combo_to(self, output_name):
        self.set_combo_to_output(self.clock_combo, output_name)
        self.current_clock = output_name
        self.update_title()

    def on_radio_changed(self, *_):
        self.current_profile = self.radio_combo.currentData()
        self.update_band_list()
        self.update_title()
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
        self.update_title()
        self.update_output_manager_state()

    def on_clock_combo_changed(self, *_):
        self.on_clock_changed(self.combo_current_output(self.clock_combo))

    def on_clock_changed(self, clock_name):
        old_output = self.current_clock
        if clock_name == old_output:
            return

        approved = self.controller.request_output_assignment(
            self,
            clock_name,
            old_output,
        )

        if not approved:
            self.set_combo_to_output(self.clock_combo, old_output)
            return

        if self.spot_active:
            self.current_clock = old_output
            self.set_rf_output(False, reason="Output changed")
            self.spot_active = False
            self.spot_button.setText("SPOT OFF")
            self.spot_button.setStyleSheet("")

        self.current_clock = clock_name
        self.update_title()
        self.update_output_manager_state()
        self.controller.log_message(
            f"{self.window_name} assigned to {output_name_to_user_label(clock_name)} ({clock_name})"
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

    def update_title(self):
        self.update_output_color_label()
        radio_name = "Radio"
        if self.current_profile:
            radio_name = self.current_profile.get("display_name", "Radio")
        band = self.current_band_id or "---"
        output_label = output_name_to_user_label(self.current_clock)
        title = f"{self.window_name} | {radio_name} {band} | {output_label}"
        self.setWindowTitle(title)
        if hasattr(self, "compact_info_label"):
            self.compact_info_label.setText(
                f"{self.window_name} | {radio_name} | {band}"
            )

        if self.output_manager:
            self.output_manager.update_owner_name(self.window_id, self.window_name)

    def update_output_manager_state(self):
        if not self.output_manager:
            return

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
        if hasattr(self.controller, "update_safety_monitor"):
            self.controller.update_safety_monitor(allow_popup=False)

    def set_frequency(self):
        try:
            rf_hz = self.parse_frequency_entry(self.freq_entry.text())
            if rf_hz < MIN_FREQ_HZ or rf_hz > MAX_FREQ_HZ:
                self.controller.log_message(
                    f"{self.current_clock}: Frequency out of range"
                )
                return
            if not self.current_profile or not self.current_band_id:
                self.controller.log_message(
                    f"{self.current_clock}: Select radio and band first"
                )
                return

            result = calculate_output_frequency(
                self.current_profile, self.current_band_id, rf_hz
            )
            if not result.ok:
                self.controller.log_message(f"{self.current_clock}: {result.message}")
                return

            response = self.link.send_frequency(result.output_hz, self.current_clock)
            self.current_rf_hz = int(result.rf_hz)
            self.current_vfo_hz = int(result.output_hz)
            self.pending_tune_hz = self.current_rf_hz
            self.update_frequency_display()
            self.vfo_display.setText(f"VFO: {self.format_frequency(result.output_hz)}")
            self.update_output_manager_state()
            self.controller.log_message(
                f"{self.current_clock} | {self.current_profile['display_name']} | "
                f"{self.current_band_id} | RF {result.rf_hz} -> VFO {result.output_hz} -> {response}"
            )
        except Exception as e:
            self.controller.log_message(
                f"{self.current_clock}: Set frequency error: {e}"
            )

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
            self.controller.log_message(f"{self.current_clock}: Tune error: {e}")

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
            self.controller.log_message(f"{self.current_clock}: Tune send error: {e}")

    def toggle_compact(self):
        self.compact_mode = not self.compact_mode

        if self.compact_mode:
            self.compact_button.setText("FULL")

            self.radio_combo.setVisible(False)
            self.band_combo.setVisible(False)
            self.clock_combo.setVisible(False)
            self.freq_entry.setVisible(False)
            self.set_freq_button.setVisible(False)
            self.rf_on_button.setVisible(False)
            self.rf_off_button.setVisible(False)

            self.compact_info_label.setVisible(True)
            self.update_title()

            self.resize(375, 205)
            self.freq_display.setFocus()

        else:
            self.compact_button.setText("COMPACT")

            self.radio_combo.setVisible(True)
            self.band_combo.setVisible(True)
            self.clock_combo.setVisible(True)
            self.freq_entry.setVisible(True)
            self.set_freq_button.setVisible(True)
            self.rf_on_button.setVisible(True)
            self.rf_off_button.setVisible(True)

            self.compact_info_label.setVisible(False)

            self.resize(560, 360)
            self.freq_display.setFocus()


    def set_active_visual(self, active):
        """
        Apply active/inactive styling to this floating radio window.

        The selector targets only this top-level window frame. It does not
        put orange borders around buttons, fields, combo boxes, or labels.
        """
        self.setObjectName("radioWindowFrame")
        self.setAttribute(Qt.WA_StyledBackground, True)

        if active:
            self.setStyleSheet(
                "#radioWindowFrame { border: 4px solid #E69F00; }"
            )
        else:
            self.setStyleSheet(
                "#radioWindowFrame { border: 1px solid #BBBBBB; }"
            )

    def mousePressEvent(self, event):
        if hasattr(self.controller, "set_active_window"):
            self.controller.set_active_window(self.window_id)
        super().mousePressEvent(event)


    def handle_ptt_event(self, is_tx):
        if is_tx:
            self.tx_active = True
            self.txrx_label.setText("TX")
            self.txrx_label.setStyleSheet(
                "background-color: red; color: white; font-size: 22px; font-weight: bold;"
            )
            self.set_rf_output(True, reason="PTT TX")
        else:
            self.tx_active = False
            self.txrx_label.setText("RX")
            self.txrx_label.setStyleSheet(
                "background-color: green; color: white; font-size: 22px; font-weight: bold;"
            )
            if self.spot_active:
                self.set_rf_output(True, reason="SPOT")
            else:
                self.set_rf_output(False, reason="PTT RX")

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

    def set_rf_output(self, enabled, reason=""):
        if not self.link.is_connected():
            self.controller.log_message(
                f"{self.current_clock}: RF enable ignored: serial not connected"
            )
            if self.output_manager:
                self.output_manager.update_rf_state_by_owner(
                    self.window_id,
                    False,
                    False,
                    self.tx_active,
                )
                if hasattr(self.controller, "update_global_rf_indicator"):
                    self.controller.update_global_rf_indicator()
                if hasattr(self.controller, "update_safety_monitor"):
                    self.controller.update_safety_monitor()
            return
        try:
            command = self.link.send_output_enable(self.current_clock, enabled)
            state_text = "ON" if enabled else "OFF"
            if self.output_manager:
                self.output_manager.update_rf_state_by_owner(
                    self.window_id,
                    enabled,
                    self.spot_active,
                    self.tx_active,
                )
                if hasattr(self.controller, "update_global_rf_indicator"):
                    self.controller.update_global_rf_indicator()
                if hasattr(self.controller, "update_safety_monitor"):
                    self.controller.update_safety_monitor()
            self.controller.log_message(
                f"{self.current_clock} RF {state_text} via {reason}: {command}"
            )
        except Exception as e:
            self.controller.log_message(f"{self.current_clock}: RF enable error: {e}")

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
        if hasattr(self.controller, "set_active_window"):
            self.controller.set_active_window(self.window_id)
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
        if hasattr(self.controller, "set_active_window"):
            self.controller.set_active_window(self.window_id)
        self.freq_display.setFocus()
        if event.angleDelta().y() > 0:
            self.adjust_frequency(+1)
        elif event.angleDelta().y() < 0:
            self.adjust_frequency(-1)
        event.accept()

    def freq_display_clicked(self, event):
        if hasattr(self.controller, "set_active_window"):
            self.controller.set_active_window(self.window_id)
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
        self.controller.log_message(f"{self.current_clock} Step: {self.format_step()}")

    def set_step_by_hz(self, step_hz):
        if step_hz in self.step_list:
            self.step_index = self.step_list.index(step_hz)
            self.step_hz = step_hz
            self.update_frequency_display()
            self.update_output_manager_state()
            self.controller.log_message(
                f"{self.current_clock} Step: {self.format_step()}"
            )


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
            "window_name": self.window_name,
            "x": self.x(),
            "y": self.y(),
            "w": self.width(),
            "h": self.height(),
            "compact": bool(self.compact_mode),
            "radio_name": radio_name,
            "band_id": self.current_band_id,
            "output": self.current_clock,
            "rf_hz": int(self.current_rf_hz),
            "step_hz": int(self.step_hz),
        }

    def apply_session_state(self, state):
        """
        Restore window configuration only.
        RF, SPOT, and TX state are intentionally forced OFF.
        """
        self.window_name = state.get("window_name", self.window_name)

        output = state.get("output", self.current_clock)
        if output != self.current_clock:
            approved = self.controller.request_output_assignment(
                self,
                output,
                self.current_clock,
            )
            if approved:
                self.current_clock = output
                self.set_output_combo_to(output)
        else:
            self.set_output_combo_to(output)

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
            "background-color: green; color: white; font-size: 22px; font-weight: bold;"
        )

        self.update_frequency_display()
        self.update_title()
        self.update_output_manager_state()

        desired_compact = bool(state.get("compact", False))
        if desired_compact != self.compact_mode:
            self.toggle_compact()

        x = int(state.get("x", self.x()))
        y = int(state.get("y", self.y()))
        w = int(state.get("w", self.width()))
        h = int(state.get("h", self.height()))
        self.setGeometry(x, y, w, h)
        if hasattr(self.controller, "clamp_widget_to_visible_screen"):
            self.controller.clamp_widget_to_visible_screen(self)



    def restore_from_accidental_maximize(self):
        """
        Restore this floating radio window if Windows Snap/Aero Snap maximized it.

        This keeps floating radio controls behaving like instrument tiles instead
        of becoming full-screen panels.
        """
        try:
            if self.isMaximized():
                self.showNormal()

                if self.compact_mode:
                    self.resize(375, 205)
                else:
                    self.resize(560, 360)

                if hasattr(self.controller, "clamp_widget_to_visible_screen"):
                    self.controller.clamp_widget_to_visible_screen(self)

                if hasattr(self.controller, "log_message"):
                    self.controller.log_message(
                        f"{self.window_name}: accidental maximize restored"
                    )
        except Exception:
            pass

    def changeEvent(self, event):
        """
        Detect Windows Snap/Aero Snap maximize events.
        """
        if event.type() == QEvent.WindowStateChange:
            QTimer.singleShot(0, self.restore_from_accidental_maximize)

        super().changeEvent(event)


    def closeEvent(self, event):
        try:
            if self.link.is_connected():
                self.set_rf_output(False, reason="Window closed")
        except Exception:
            pass

        self.controller.release_output_assignment(self)
        super().closeEvent(event)
