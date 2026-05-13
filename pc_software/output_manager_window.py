# File: output_manager_window.py
#
# Output Manager visual panel for the SI5351 Multi-Radio VFO.
#
# v4D.1 Visual Polish:
#   - Operator-facing labels are Output 1 through Output 6.
#   - Internal OUT0 through OUT5 names remain visible for troubleshooting.
#   - Output rows are color-tagged for quick shack operation.

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
)


class OutputManagerWindow(QWidget):
    def __init__(self, manager, controller):
        super().__init__()

        self.manager = manager
        self.controller = controller

        self.setWindowTitle("Output Manager")
        self.resize(860, 330)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        title = QLabel("Output Manager - Operator Outputs 1 through 6")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 17px; font-weight: bold;")
        main_layout.addWidget(title)

        subtitle = QLabel("Operators use Output 1-6 as rear-panel BNC connectors. Click a row to bring that radio window forward.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: gray;")
        main_layout.addWidget(subtitle)

        self.global_rf_summary_label = QLabel("GLOBAL RF: ALL OUTPUTS OFF")
        self.global_rf_summary_label.setAlignment(Qt.AlignCenter)
        self.global_rf_summary_label.setStyleSheet(
            "background-color: #333333; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
        )
        main_layout.addWidget(self.global_rf_summary_label)

        self.safety_summary_label = QLabel("SAFETY: OK")
        self.safety_summary_label.setAlignment(Qt.AlignCenter)
        self.safety_summary_label.setStyleSheet(
            "background-color: #444444; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
        )
        main_layout.addWidget(self.safety_summary_label)

        self.table = QTableWidget(6, 9)
        self.table.setHorizontalHeaderLabels(
            [
                "",
                "Output",
                "Internal",
                "Owner",
                "Radio",
                "Band",
                "RF Frequency",
                "VFO Output",
                "State",
            ]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.cellDoubleClicked.connect(self.on_row_double_clicked)
        self.table.cellClicked.connect(self.on_row_clicked)
        main_layout.addWidget(self.table)

        button_row = QHBoxLayout()

        self.refresh_button = QPushButton("Refresh")
        self.arrange_windows_button = QPushButton("Arrange Windows")
        self.rf_off_all_button = QPushButton("RF OFF ALL")
        self.close_button = QPushButton("Close")

        self.refresh_button.clicked.connect(self.refresh)
        self.arrange_windows_button.clicked.connect(self.arrange_windows_clicked)
        self.rf_off_all_button.clicked.connect(self.rf_off_all_clicked)
        self.close_button.clicked.connect(self.close)

        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.arrange_windows_button)
        button_row.addStretch(1)
        button_row.addWidget(self.rf_off_all_button)
        button_row.addWidget(self.close_button)

        main_layout.addLayout(button_row)

        self.manager.outputs_changed.connect(self.refresh)
        self.refresh()

    def format_frequency(self, hz):
        try:
            hz = int(hz)
        except Exception:
            hz = 0

        if hz <= 0:
            return "---"

        return f"{hz / 1_000_000:.6f} MHz"

    def make_item(self, text, align=Qt.AlignCenter):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(align)
        return item

    def state_style(self, state_text):
        if state_text == "TX":
            return QColor("#ffcccc")
        if state_text == "SPOT":
            return QColor("#ffe6b3")
        if state_text == "RF ON":
            return QColor("#ccffcc")
        return QColor("#eeeeee")

    def refresh(self):
        states = self.manager.all_states()

        for row, state in enumerate(states):
            owner = state.owner_name if state.owner_name else "---"
            radio = state.radio_name if state.radio_name else "---"
            band = state.band_name if state.band_name else "---"
            status = state.state_text()
            is_active = (
                hasattr(self.controller, "active_owner_id")
                and state.owner_id
                and state.owner_id == self.controller.active_owner_id
            )

            color_item = self.make_item("  ")
            color_item.setBackground(QColor(state.color))

            self.table.setItem(row, 0, color_item)
            self.table.setItem(row, 1, self.make_item(state.user_label))
            self.table.setItem(row, 2, self.make_item(state.internal_name))
            self.table.setItem(row, 3, self.make_item(owner))
            self.table.setItem(row, 4, self.make_item(radio))
            self.table.setItem(row, 5, self.make_item(band))
            self.table.setItem(row, 6, self.make_item(self.format_frequency(state.frequency_hz)))
            self.table.setItem(row, 7, self.make_item(self.format_frequency(state.vfo_hz)))

            state_item = self.make_item(status)
            state_item.setBackground(self.state_style(status))
            self.table.setItem(row, 8, state_item)

            if is_active:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item is not None and col != 0 and col != 8:
                        item.setBackground(QColor("#fff2cc"))

        self.refresh_global_rf_summary()
        self.refresh_safety_summary()
        self.table.resizeColumnsToContents()


    def on_row_clicked(self, row, column):
        """
        Single-click selects a row and asks the controller to bring the owning
        radio window forward.
        """
        self.focus_window_for_row(row)

    def on_row_double_clicked(self, row, column):
        """
        Double-click does the same thing, but feels natural for users who
        expect a table row to open/focus something.
        """
        self.focus_window_for_row(row)

    def focus_window_for_row(self, row):
        try:
            states = self.manager.all_states()
            if row < 0 or row >= len(states):
                return

            state = states[row]
            if not state.owner_id:
                return

            if hasattr(self.controller, "focus_window_by_owner_id"):
                self.controller.focus_window_by_owner_id(state.owner_id)

        except Exception as exc:
            if hasattr(self.controller, "log_message"):
                self.controller.log_message(f"Output Manager focus error: {exc}")



    def arrange_windows_clicked(self):
        try:
            if hasattr(self.controller, "arrange_radio_windows"):
                self.controller.arrange_radio_windows()
        except Exception as exc:
            if hasattr(self.controller, "log_message"):
                self.controller.log_message(f"Output Manager arrange error: {exc}")



    def refresh_global_rf_summary(self):
        try:
            tx_outputs = []
            spot_outputs = []
            rf_outputs = []

            for state in self.manager.all_states():
                label = state.user_label
                if state.tx_active:
                    tx_outputs.append(label)
                elif state.spot_enabled:
                    spot_outputs.append(label)
                elif state.rf_enabled:
                    rf_outputs.append(label)

            if tx_outputs:
                text = "GLOBAL RF: TX ACTIVE ON " + ", ".join(tx_outputs)
                style = "background-color: red; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
            elif spot_outputs:
                text = "GLOBAL RF: SPOT ACTIVE ON " + ", ".join(spot_outputs)
                style = "background-color: orange; color: black; font-size: 14px; font-weight: bold; padding: 3px;"
            elif rf_outputs:
                text = "GLOBAL RF: RF ON " + ", ".join(rf_outputs)
                style = "background-color: #008000; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
            else:
                text = "GLOBAL RF: ALL OUTPUTS OFF"
                style = "background-color: #333333; color: white; font-size: 14px; font-weight: bold; padding: 3px;"

            self.global_rf_summary_label.setText(text)
            self.global_rf_summary_label.setStyleSheet(style)

        except Exception:
            pass



    def refresh_safety_summary(self):
        try:
            if not hasattr(self.controller, "evaluate_safety_state"):
                return

            level, message, key = self.controller.evaluate_safety_state()

            if level == "DANGER":
                style = "background-color: red; color: white; font-size: 14px; font-weight: bold; padding: 3px;"
            elif level == "CAUTION":
                style = "background-color: #E69F00; color: black; font-size: 14px; font-weight: bold; padding: 3px;"
            else:
                message = "SAFETY: OK"
                style = "background-color: #444444; color: white; font-size: 14px; font-weight: bold; padding: 3px;"

            self.safety_summary_label.setText(message)
            self.safety_summary_label.setStyleSheet(style)

        except Exception:
            pass


    def rf_off_all_clicked(self):
        if not self.controller.link.is_connected():
            QMessageBox.information(
                self,
                "RF OFF ALL",
                "Serial port is not connected.\n\nInternal RF state will be cleared.",
            )
            self.manager.force_all_rf_off()
            return

        errors = []

        for i in range(6):
            try:
                self.controller.link.send_output_enable(f"OUT{i}", False)
            except Exception as exc:
                errors.append(f"Output {i + 1}: {exc}")

        self.manager.force_all_rf_off()
        if hasattr(self.controller, "update_global_rf_indicator"):
            self.controller.update_global_rf_indicator()

        if errors:
            QMessageBox.warning(
                self,
                "RF OFF ALL",
                "Some outputs could not be commanded OFF:\n\n" + "\n".join(errors),
            )
