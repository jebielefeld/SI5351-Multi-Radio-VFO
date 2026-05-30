import copy
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFormLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from profile_models import BandProfile, RadioProfile

PROFILE_FILE = Path("radio_profiles.json")


RADIO_TYPES = [
    "",
    "Crystal-controlled transmitter",
    "External VFO transmitter",
    "Transceiver",
    "Receiver",
    "Converter / Transverter",
    "Bench test source",
    "Other",
]

MATH_MODES = [
    "direct",
    "multiply",
    "divide",
    "linear_map",
    "per-band",
]

TRANSLATION_MODES = [
    "direct",
    "multiply",
    "divide",
    "linear_map",
]

DEFAULT_OUTPUTS = [
    "",
    "OUT1",
    "OUT2",
    "OUT3",
    "OUT4",
    "OUT5",
    "OUT6",
]

LOGICAL_TO_DISPLAY_OUTPUT = {
    "OUT0": "OUT1",
    "OUT1": "OUT2",
    "OUT2": "OUT3",
    "OUT3": "OUT4",
    "OUT4": "OUT5",
    "OUT5": "OUT6",
}

DISPLAY_TO_LOGICAL_OUTPUT = {
    display: logical for logical, display in LOGICAL_TO_DISPLAY_OUTPUT.items()
}


class ProfileEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.base_title = "Radio Profile Editor"
        self.setWindowTitle(self.base_title)
        self.resize(1150, 760)

        self.profiles: dict[str, RadioProfile] = {}
        self.original_profiles: dict[str, RadioProfile] = {}

        self.current_profile: RadioProfile | None = None
        self.current_band_row: int | None = None

        self.is_dirty = False
        self.loading_profile_fields = False

        self.build_ui()
        self.load_profiles()
        self.set_dirty(False)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)

        left_panel = QVBoxLayout()

        left_title = QLabel("Profiles")
        left_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.profile_list = QListWidget()

        self.new_button = QPushButton("New")
        self.duplicate_button = QPushButton("Duplicate")
        self.delete_button = QPushButton("Delete")

        left_panel.addWidget(left_title)
        left_panel.addWidget(self.profile_list)
        left_panel.addWidget(self.new_button)
        left_panel.addWidget(self.duplicate_button)
        left_panel.addWidget(self.delete_button)

        right_panel = QVBoxLayout()

        self.tabs = QTabWidget()

        self.basic_tab = QWidget()
        self.band_tab = QWidget()
        self.preview_tab = QWidget()

        self.tabs.addTab(self.basic_tab, "Basic Info")
        self.tabs.addTab(self.band_tab, "Bands / Math")
        self.tabs.addTab(self.preview_tab, "Preview / Test")

        self.build_basic_tab()
        self.build_band_tab()
        self.build_preview_tab()

        right_panel.addWidget(self.tabs)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)

        self.profile_list.currentItemChanged.connect(self.on_profile_selected)
        self.new_button.clicked.connect(self.new_profile)
        self.duplicate_button.clicked.connect(self.duplicate_profile)
        self.delete_button.clicked.connect(self.delete_profile)

    def build_basic_tab(self):
        layout = QVBoxLayout(self.basic_tab)

        title = QLabel("Basic Profile Information")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        form = QFormLayout()

        self.profile_id_edit = QLineEdit()
        self.display_name_edit = QLineEdit()
        self.manufacturer_edit = QLineEdit()
        self.radio_type_combo = QComboBox()
        self.math_mode_combo = QComboBox()
        self.default_output_combo = QComboBox()
        self.description_edit = QTextEdit()
        self.notes_edit = QTextEdit()

        self.radio_type_combo.addItems(RADIO_TYPES)
        self.math_mode_combo.addItems(MATH_MODES)
        self.default_output_combo.addItems(DEFAULT_OUTPUTS)

        self.description_edit.setFixedHeight(80)
        self.notes_edit.setFixedHeight(100)

        form.addRow("Profile ID:", self.profile_id_edit)
        form.addRow("Display Name:", self.display_name_edit)
        form.addRow("Manufacturer:", self.manufacturer_edit)
        form.addRow("Radio Type:", self.radio_type_combo)
        form.addRow("Math Mode:", self.math_mode_combo)
        form.addRow("Default Output:", self.default_output_combo)
        form.addRow("Description:", self.description_edit)
        form.addRow("Notes:", self.notes_edit)

        button_row = QHBoxLayout()

        self.save_button = QPushButton("Save")
        self.revert_button = QPushButton("Revert")
        self.close_button = QPushButton("Close")

        self.save_button.setEnabled(False)
        self.revert_button.setEnabled(False)

        button_row.addStretch()
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.revert_button)
        button_row.addWidget(self.close_button)

        layout.addWidget(title)
        layout.addLayout(form)
        layout.addStretch()
        layout.addLayout(button_row)

        self.save_button.clicked.connect(self.on_save_clicked)
        self.revert_button.clicked.connect(self.on_revert_clicked)
        self.close_button.clicked.connect(self.close)

        self.profile_id_edit.textChanged.connect(self.on_basic_info_changed)
        self.display_name_edit.textChanged.connect(self.on_basic_info_changed)
        self.manufacturer_edit.textChanged.connect(self.on_basic_info_changed)
        self.radio_type_combo.currentTextChanged.connect(self.on_basic_info_changed)
        self.math_mode_combo.currentTextChanged.connect(self.on_basic_info_changed)
        self.default_output_combo.currentTextChanged.connect(self.on_basic_info_changed)
        self.description_edit.textChanged.connect(self.on_basic_info_changed)
        self.notes_edit.textChanged.connect(self.on_basic_info_changed)

    def build_band_tab(self):
        layout = QVBoxLayout(self.band_tab)

        title = QLabel("Band / Math Configuration")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.band_table = QTableWidget()
        self.band_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.band_table.setSelectionMode(QTableWidget.SingleSelection)
        self.band_table.setEditTriggers(QTableWidget.NoEditTriggers)

        table_button_row = QHBoxLayout()

        self.add_band_button = QPushButton("Add Band")
        self.delete_band_button = QPushButton("Delete Band")
        self.duplicate_band_button = QPushButton("Duplicate Band")

        table_button_row.addWidget(self.add_band_button)
        table_button_row.addWidget(self.delete_band_button)
        table_button_row.addWidget(self.duplicate_band_button)
        table_button_row.addStretch()

        self.band_status_label = QLabel("No band selected.")
        self.band_status_label.setStyleSheet("padding: 6px; border: 1px solid gray;")

        detail_title = QLabel("Selected Band Detail")
        detail_title.setStyleSheet("font-size: 15px; font-weight: bold;")

        detail_form = QFormLayout()

        self.band_id_edit = QLineEdit()
        self.band_mode_combo = QComboBox()
        self.band_rf_start_edit = QLineEdit()
        self.band_rf_end_edit = QLineEdit()
        self.band_vfo_start_edit = QLineEdit()
        self.band_vfo_end_edit = QLineEdit()
        self.band_multiplier_edit = QLineEdit()
        self.band_notes_edit = QTextEdit()

        self.band_mode_combo.addItems(TRANSLATION_MODES)
        self.band_notes_edit.setFixedHeight(70)

        detail_form.addRow("Band ID:", self.band_id_edit)
        detail_form.addRow("Translation Mode:", self.band_mode_combo)
        detail_form.addRow("RF Start MHz:", self.band_rf_start_edit)
        detail_form.addRow("RF End MHz:", self.band_rf_end_edit)
        detail_form.addRow("VFO Start MHz:", self.band_vfo_start_edit)
        detail_form.addRow("VFO End MHz:", self.band_vfo_end_edit)
        detail_form.addRow("Multiplier:", self.band_multiplier_edit)
        detail_form.addRow("Notes:", self.band_notes_edit)

        detail_button_row = QHBoxLayout()

        self.apply_band_button = QPushButton("Apply Band Changes")
        self.revert_band_button = QPushButton("Revert Band")

        self.apply_band_button.setEnabled(False)
        self.revert_band_button.setEnabled(False)

        detail_button_row.addStretch()
        detail_button_row.addWidget(self.apply_band_button)
        detail_button_row.addWidget(self.revert_band_button)

        layout.addWidget(title)
        layout.addWidget(self.band_table)
        layout.addLayout(table_button_row)
        layout.addWidget(self.band_status_label)
        layout.addWidget(detail_title)
        layout.addLayout(detail_form)
        layout.addLayout(detail_button_row)

        self.band_table.itemSelectionChanged.connect(self.on_band_selection_changed)
        self.band_mode_combo.currentTextChanged.connect(
            self.update_band_detail_enabled_state
        )
        self.apply_band_button.clicked.connect(self.apply_band_changes)
        self.revert_band_button.clicked.connect(self.revert_band_changes)
        self.add_band_button.clicked.connect(self.add_band)
        self.delete_band_button.clicked.connect(self.delete_band)
        self.duplicate_band_button.clicked.connect(self.duplicate_band)

    def build_preview_tab(self):
        layout = QVBoxLayout(self.preview_tab)

        title = QLabel("Profile Validation Warnings")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        explanation = QLabel(
            "Check all loaded profiles for common mistakes before using them in the main VFO program."
        )
        explanation.setWordWrap(True)

        self.validate_profiles_button = QPushButton("Validate Profiles")

        self.validation_report = QTextEdit()
        self.validation_report.setReadOnly(True)
        self.validation_report.setPlaceholderText(
            "Click Validate Profiles to check profile and band data."
        )

        layout.addWidget(title)
        layout.addWidget(explanation)
        layout.addWidget(self.validate_profiles_button)
        layout.addWidget(self.validation_report)

        self.validate_profiles_button.clicked.connect(self.validate_profiles)

    def load_profiles(self):
        self.profile_list.clear()
        self.profiles.clear()

        if not PROFILE_FILE.exists():
            print(f"Missing file: {PROFILE_FILE}")
            return

        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if isinstance(raw_data, dict) and "profiles" in raw_data:
            raw_profiles = raw_data["profiles"]
        else:
            raw_profiles = raw_data

        profile_items = []

        if isinstance(raw_profiles, dict):
            profile_items = list(raw_profiles.items())

        elif isinstance(raw_profiles, list):
            for profile_data in raw_profiles:
                if isinstance(profile_data, dict):
                    profile_id = profile_data.get(
                        "id",
                        profile_data.get("profile_id", "unknown"),
                    )
                    profile_items.append((profile_id, profile_data))

        for profile_id, profile_data in profile_items:
            try:
                profile = RadioProfile.from_dict(profile_id, profile_data)

                self.profiles[profile_id] = profile

                item = QListWidgetItem(profile.display_name)
                item.setData(Qt.UserRole, profile_id)

                self.profile_list.addItem(item)

            except Exception as e:
                print(f"ERROR loading profile {profile_id}: {e}")

        self.original_profiles = copy.deepcopy(self.profiles)

        print(f"Loaded {len(self.profiles)} profiles.")

        if self.profile_list.count() > 0:
            self.profile_list.setCurrentRow(0)

    def on_profile_selected(self, current, previous):
        if current is None:
            self.current_profile = None
            self.current_band_row = None

            self.clear_basic_fields()
            self.band_table.setRowCount(0)
            self.band_status_label.setText("No band selected.")
            self.clear_band_detail_fields()

            return

        profile_id = current.data(Qt.UserRole)

        profile = self.profiles.get(profile_id)

        if profile is None:
            self.current_profile = None
            self.current_band_row = None

            self.clear_basic_fields()
            self.band_table.setRowCount(0)
            self.band_status_label.setText("No band selected.")
            self.clear_band_detail_fields()

            return

        self.current_profile = profile
        self.current_band_row = None

        self.load_profile_into_basic_fields(profile)

        if self.band_table.rowCount() > 0:
            self.band_table.selectRow(0)

    def load_profile_into_basic_fields(self, profile: RadioProfile):
        self.loading_profile_fields = True

        try:
            self.profile_id_edit.setText(profile.profile_id)
            self.display_name_edit.setText(profile.display_name)
            self.manufacturer_edit.setText(profile.manufacturer)
            self.description_edit.setPlainText(profile.description)
            self.notes_edit.setPlainText(profile.notes)

            self.set_combo_text(self.radio_type_combo, profile.radio_type)

            profile_mode = profile.math_mode

            if self.profile_uses_multiple_band_modes(profile):
                profile_mode = "per-band"

            self.set_combo_text(self.math_mode_combo, profile_mode)

            display_output = LOGICAL_TO_DISPLAY_OUTPUT.get(
                profile.default_output,
                profile.default_output,
            )

            self.set_combo_text(self.default_output_combo, display_output)

            self.load_band_table(profile)

        finally:
            self.loading_profile_fields = False

    def profile_uses_multiple_band_modes(self, profile: RadioProfile) -> bool:
        modes = {band.translation_mode for band in profile.bands}

        return len(modes) > 1

    def on_basic_info_changed(self):
        if self.loading_profile_fields:
            return

        if self.current_profile is None:
            return

        self.set_dirty(True)

    def apply_basic_info_to_model(self):
        if self.current_profile is None:
            return

        old_profile_id = self.current_profile.profile_id
        new_profile_id = self.profile_id_edit.text().strip()

        if not new_profile_id:
            raise ValueError("Profile ID cannot be blank.")

        if new_profile_id != old_profile_id and new_profile_id in self.profiles:
            raise ValueError(
                f"Profile ID '{new_profile_id}' already exists. "
                "Choose a unique Profile ID."
            )

        display_name = self.display_name_edit.text().strip()

        if not display_name:
            raise ValueError("Display Name cannot be blank.")

        self.current_profile.profile_id = new_profile_id
        self.current_profile.display_name = display_name
        self.current_profile.manufacturer = self.manufacturer_edit.text().strip()
        self.current_profile.radio_type = self.radio_type_combo.currentText().strip()
        self.current_profile.math_mode = self.math_mode_combo.currentText().strip()

        selected_output = self.default_output_combo.currentText().strip()
        self.current_profile.default_output = DISPLAY_TO_LOGICAL_OUTPUT.get(
            selected_output,
            selected_output,
        )

        self.current_profile.description = self.description_edit.toPlainText().strip()
        self.current_profile.notes = self.notes_edit.toPlainText().strip()

        if new_profile_id != old_profile_id:
            self.profiles.pop(old_profile_id, None)
            self.profiles[new_profile_id] = self.current_profile

        current_item = self.profile_list.currentItem()

        if current_item is not None:
            current_item.setData(Qt.UserRole, new_profile_id)
            current_item.setText(self.current_profile.display_name)

    def configure_band_table_for_profile(self, profile: RadioProfile):
        modes = {band.translation_mode for band in profile.bands}

        has_linear_map = "linear_map" in modes
        has_multiplier = bool(modes.intersection({"multiply", "divide"}))

        headers = [
            "Band",
            "Mode",
            "RF Start MHz",
            "RF End MHz",
        ]

        if has_linear_map:
            headers.extend(["VFO Start MHz", "VFO End MHz"])

        if has_multiplier:
            headers.append("Multiplier")

        headers.append("Notes")

        self.band_table.clear()

        self.band_table.setColumnCount(len(headers))
        self.band_table.setHorizontalHeaderLabels(headers)

        header = self.band_table.horizontalHeader()

        for column in range(len(headers) - 1):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)

        header.setSectionResizeMode(len(headers) - 1, QHeaderView.Stretch)

    def load_band_table(self, profile: RadioProfile):
        self.configure_band_table_for_profile(profile)

        self.band_table.setRowCount(0)

        modes = {band.translation_mode for band in profile.bands}

        has_linear_map = "linear_map" in modes
        has_multiplier = bool(modes.intersection({"multiply", "divide"}))

        for row, band in enumerate(profile.bands):
            self.band_table.insertRow(row)

            values = [
                band.band,
                band.translation_mode,
                f"{band.rf_start_hz / 1_000_000:.6f}",
                f"{band.rf_end_hz / 1_000_000:.6f}",
            ]

            if has_linear_map:
                if band.translation_mode == "linear_map":
                    values.extend(
                        [
                            f"{band.output_start_hz / 1_000_000:.6f}",
                            f"{band.output_end_hz / 1_000_000:.6f}",
                        ]
                    )
                else:
                    values.extend(["---", "---"])

            if has_multiplier:
                if band.translation_mode in {"multiply", "divide"}:
                    values.append(str(band.multiplier))
                else:
                    values.append("---")

            values.append(band.notes)

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                self.band_table.setItem(row, column, item)

        self.band_status_label.setText("No band selected.")
        self.clear_band_detail_fields()

    def on_band_selection_changed(self):
        row = self.band_table.currentRow()

        if row < 0:
            self.current_band_row = None

            self.band_status_label.setText("No band selected.")
            self.clear_band_detail_fields()

            return

        values = []

        for column in range(self.band_table.columnCount()):
            item = self.band_table.item(row, column)

            if item:
                values.append(item.text())

        self.band_status_label.setText(" | ".join(values))

        if self.current_profile is None:
            self.current_band_row = None
            self.clear_band_detail_fields()
            return

        if row >= len(self.current_profile.bands):
            self.current_band_row = None
            self.clear_band_detail_fields()
            return

        self.current_band_row = row

        band = self.current_profile.bands[row]

        self.load_band_detail_fields(band)

    def load_band_detail_fields(self, band: BandProfile):
        self.band_id_edit.setText(band.band)
        self.set_combo_text(self.band_mode_combo, band.translation_mode)

        self.band_rf_start_edit.setText(f"{band.rf_start_hz / 1_000_000:.6f}")
        self.band_rf_end_edit.setText(f"{band.rf_end_hz / 1_000_000:.6f}")
        self.band_vfo_start_edit.setText(f"{band.output_start_hz / 1_000_000:.6f}")
        self.band_vfo_end_edit.setText(f"{band.output_end_hz / 1_000_000:.6f}")
        self.band_multiplier_edit.setText(str(band.multiplier))
        self.band_notes_edit.setPlainText(band.notes)

        self.update_band_detail_enabled_state(band.translation_mode)

        self.apply_band_button.setEnabled(True)
        self.revert_band_button.setEnabled(True)

    def update_band_detail_enabled_state(self, mode: str):
        is_linear = mode == "linear_map"
        uses_multiplier = mode in {"multiply", "divide"}

        self.band_vfo_start_edit.setEnabled(is_linear)
        self.band_vfo_end_edit.setEnabled(is_linear)
        self.band_multiplier_edit.setEnabled(uses_multiplier)

    def clear_band_detail_fields(self):
        self.band_id_edit.clear()

        self.band_mode_combo.setCurrentIndex(0)

        self.band_rf_start_edit.clear()
        self.band_rf_end_edit.clear()

        self.band_vfo_start_edit.clear()
        self.band_vfo_end_edit.clear()

        self.band_multiplier_edit.clear()
        self.band_notes_edit.clear()

        self.band_vfo_start_edit.setEnabled(False)
        self.band_vfo_end_edit.setEnabled(False)
        self.band_multiplier_edit.setEnabled(False)

        self.apply_band_button.setEnabled(False)
        self.revert_band_button.setEnabled(False)

    def new_profile(self):
        profile_id = self.make_unique_profile_id("new_radio_profile")

        default_band = BandProfile(
            band="NEW_BAND",
            translation_mode="direct",
            rf_start_hz=1_000_000,
            rf_end_hz=2_000_000,
            output_start_hz=0,
            output_end_hz=0,
            multiplier=1.0,
            notes="",
        )

        new_profile = RadioProfile(
            profile_id=profile_id,
            display_name="New Radio Profile",
            manufacturer="",
            radio_type="Other",
            description="",
            math_mode="direct",
            default_output="",
            notes="",
            bands=[default_band],
        )

        self.profiles[profile_id] = new_profile

        self.reload_profile_list_from_profiles()
        self.select_profile_by_id(profile_id)

        self.tabs.setCurrentWidget(self.basic_tab)
        self.profile_id_edit.setFocus()
        self.profile_id_edit.selectAll()

        self.set_dirty(True)

    def duplicate_profile(self):
        if self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Select a profile before duplicating it.",
            )
            return

        try:
            self.apply_basic_info_to_model()

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Profile Data",
                str(e),
            )
            return

        source_profile = self.current_profile

        duplicate_profile = copy.deepcopy(source_profile)

        base_profile_id = f"{source_profile.profile_id}_copy"
        new_profile_id = self.make_unique_profile_id(base_profile_id)

        duplicate_profile.profile_id = new_profile_id
        duplicate_profile.display_name = f"{source_profile.display_name} Copy"

        self.profiles[new_profile_id] = duplicate_profile

        self.reload_profile_list_from_profiles()
        self.select_profile_by_id(new_profile_id)

        self.tabs.setCurrentWidget(self.basic_tab)
        self.profile_id_edit.setFocus()
        self.profile_id_edit.selectAll()

        self.set_dirty(True)


    def delete_profile(self):
        current_item = self.profile_list.currentItem()

        if current_item is None or self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Select a profile before deleting it.",
            )
            return

        profile_id = current_item.data(Qt.UserRole)

        if profile_id not in self.profiles:
            QMessageBox.warning(
                self,
                "Profile Not Found",
                "The selected profile could not be found in the model.",
            )
            return

        profile = self.profiles[profile_id]

        result = QMessageBox.question(
            self,
            "Delete Profile",
            (
                f"Delete profile:\n\n"
                f"{profile.display_name}\n\n"
                f"This removes the profile from memory only. "
                f"Click Save to make the deletion permanent."
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        deleted_row = self.profile_list.currentRow()

        del self.profiles[profile_id]

        self.reload_profile_list_from_profiles()

        if self.profile_list.count() == 0:
            self.current_profile = None
            self.current_band_row = None

            self.clear_basic_fields()
            self.band_table.setRowCount(0)
            self.band_status_label.setText("No band selected.")
            self.clear_band_detail_fields()

        else:
            row_to_select = min(deleted_row, self.profile_list.count() - 1)
            self.profile_list.setCurrentRow(row_to_select)

        self.set_dirty(True)

    def make_unique_profile_id(self, base_id: str) -> str:
        existing_ids = set(self.profiles.keys())

        if base_id not in existing_ids:
            return base_id

        copy_number = 2

        while True:
            candidate = f"{base_id}_{copy_number}"

            if candidate not in existing_ids:
                return candidate

            copy_number += 1

    def select_profile_by_id(self, profile_id: str):
        for row in range(self.profile_list.count()):
            item = self.profile_list.item(row)

            if item.data(Qt.UserRole) == profile_id:
                self.profile_list.setCurrentRow(row)
                return

    def add_band(self):
        if self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Select a profile before adding a band.",
            )
            return

        new_band = BandProfile(
            band="NEW_BAND",
            translation_mode="direct",
            rf_start_hz=1_000_000,
            rf_end_hz=2_000_000,
            output_start_hz=0,
            output_end_hz=0,
            multiplier=1.0,
            notes="",
        )

        self.current_profile.bands.append(new_band)

        self.load_band_table(self.current_profile)

        new_row = len(self.current_profile.bands) - 1

        if new_row >= 0:
            self.band_table.selectRow(new_row)

        self.band_id_edit.setFocus()
        self.band_id_edit.selectAll()

        self.set_dirty(True)

        self.band_status_label.setText(
            "New band created. Edit fields and click Apply Band Changes."
        )



    def delete_band(self):
        if self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Select a profile before deleting a band.",
            )
            return

        if self.current_band_row is None:
            QMessageBox.warning(
                self,
                "No Band Selected",
                "Select a band before deleting it.",
            )
            return

        if self.current_band_row >= len(self.current_profile.bands):
            QMessageBox.warning(
                self,
                "Invalid Band Selection",
                "The selected band is no longer valid.",
            )
            return

        band_to_delete = self.current_profile.bands[self.current_band_row]

        result = QMessageBox.question(
            self,
            "Delete Band",
            f"Delete band '{band_to_delete.band}' from this profile?\n\n"
            "This change is in memory only until you click Save.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        deleted_row = self.current_band_row

        del self.current_profile.bands[deleted_row]

        self.load_band_table(self.current_profile)

        if len(self.current_profile.bands) == 0:
            self.current_band_row = None
            self.band_table.clearSelection()
            self.clear_band_detail_fields()
            self.band_status_label.setText(
                "Band deleted. No bands remain in this profile."
            )
        else:
            row_to_select = min(deleted_row, len(self.current_profile.bands) - 1)
            self.band_table.selectRow(row_to_select)
            self.band_status_label.setText(
                "Band deleted. Click Save to make this permanent."
            )

        self.set_dirty(True)

    def duplicate_band(self):
        if self.current_profile is None:
            QMessageBox.warning(
                self,
                "No Profile Selected",
                "Select a profile before duplicating a band.",
            )
            return

        if self.current_band_row is None:
            QMessageBox.warning(
                self,
                "No Band Selected",
                "Select a band before duplicating it.",
            )
            return

        if self.current_band_row >= len(self.current_profile.bands):
            QMessageBox.warning(
                self,
                "Invalid Band Selection",
                "The selected band is no longer valid.",
            )
            return

        source_band = self.current_profile.bands[self.current_band_row]

        new_band = copy.deepcopy(source_band)
        new_band.band = self.make_unique_band_copy_name(source_band.band)

        self.current_profile.bands.append(new_band)

        self.load_band_table(self.current_profile)

        new_row = len(self.current_profile.bands) - 1

        if new_row >= 0:
            self.band_table.selectRow(new_row)

        self.band_id_edit.setFocus()
        self.band_id_edit.selectAll()

        self.set_dirty(True)

        self.band_status_label.setText(
            "Band duplicated. Edit Band ID and click Apply Band Changes."
        )

    def make_unique_band_copy_name(self, base_name: str) -> str:
        if self.current_profile is None:
            return f"{base_name}_COPY"

        existing_names = {band.band for band in self.current_profile.bands}

        candidate = f"{base_name}_COPY"

        if candidate not in existing_names:
            return candidate

        copy_number = 2

        while True:
            candidate = f"{base_name}_COPY_{copy_number}"

            if candidate not in existing_names:
                return candidate

            copy_number += 1

    def apply_band_changes(self):
        if self.current_profile is None:
            return

        if self.current_band_row is None:
            return

        if self.current_band_row >= len(self.current_profile.bands):
            return

        try:
            band_id = self.band_id_edit.text().strip()
            mode = self.band_mode_combo.currentText().strip()

            rf_start_hz = self.mhz_text_to_hz(self.band_rf_start_edit.text())
            rf_end_hz = self.mhz_text_to_hz(self.band_rf_end_edit.text())

            vfo_start_hz = self.mhz_text_to_hz_or_zero(self.band_vfo_start_edit.text())

            vfo_end_hz = self.mhz_text_to_hz_or_zero(self.band_vfo_end_edit.text())

            multiplier = self.float_text_or_default(
                self.band_multiplier_edit.text(),
                1.0,
            )

            notes = self.band_notes_edit.toPlainText().strip()

            if not band_id:
                raise ValueError("Band ID cannot be blank.")

            if rf_start_hz <= 0 or rf_end_hz <= 0:
                raise ValueError("RF start/end frequencies must be greater than zero.")

            if rf_start_hz >= rf_end_hz:
                raise ValueError("RF start must be lower than RF end.")

            if mode == "linear_map":
                if vfo_start_hz <= 0 or vfo_end_hz <= 0:
                    raise ValueError("VFO start/end must be greater than zero.")

                if vfo_start_hz >= vfo_end_hz:
                    raise ValueError("VFO start must be lower than VFO end.")

            if mode in {"multiply", "divide"}:
                if multiplier <= 0:
                    raise ValueError("Multiplier must be greater than zero.")

            band = self.current_profile.bands[self.current_band_row]

            band.band = band_id
            band.translation_mode = mode

            band.rf_start_hz = rf_start_hz
            band.rf_end_hz = rf_end_hz

            band.output_start_hz = vfo_start_hz
            band.output_end_hz = vfo_end_hz

            band.multiplier = multiplier
            band.notes = notes

            row_to_restore = self.current_band_row

            self.load_band_table(self.current_profile)

            if row_to_restore < self.band_table.rowCount():
                self.band_table.selectRow(row_to_restore)

            self.set_dirty(True)

            self.band_status_label.setText("Band changes applied in memory only.")

        except ValueError as e:
            QMessageBox.warning(
                self,
                "Invalid Band Data",
                str(e),
            )

    def revert_band_changes(self):
        if self.current_profile is None:
            return

        if self.current_band_row is None:
            return

        if self.current_band_row >= len(self.current_profile.bands):
            return

        band = self.current_profile.bands[self.current_band_row]

        self.load_band_detail_fields(band)

        self.band_status_label.setText("Band detail reverted.")

    def set_dirty(self, dirty: bool):
        self.is_dirty = dirty

        if self.is_dirty:
            self.setWindowTitle(f"{self.base_title} *")
        else:
            self.setWindowTitle(self.base_title)

        self.save_button.setEnabled(self.is_dirty)
        self.revert_button.setEnabled(self.is_dirty)

    def on_save_clicked(self):
        if not self.is_dirty:
            return

        try:
            self.apply_basic_info_to_model()

            backup_path = self.create_profile_backup()
            self.write_profiles_to_json()

            self.original_profiles = copy.deepcopy(self.profiles)

            self.set_dirty(False)

            QMessageBox.information(
                self,
                "Profiles Saved",
                f"Profiles saved successfully.\n\nBackup created:\n{backup_path.name}",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Profiles were NOT saved.\n\n{e}",
            )

    def create_profile_backup(self) -> Path:
        if not PROFILE_FILE.exists():
            raise FileNotFoundError(f"Missing file: {PROFILE_FILE}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        backup_path = PROFILE_FILE.with_name(f"radio_profiles_backup_{timestamp}.json")

        shutil.copy2(PROFILE_FILE, backup_path)

        return backup_path

    def write_profiles_to_json(self):
        data = {
            "schema_version": 1,
            "profiles": [
                self.profile_to_json_dict(profile) for profile in self.profiles.values()
            ],
        }

        temp_path = PROFILE_FILE.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")

        temp_path.replace(PROFILE_FILE)

    def profile_to_json_dict(self, profile: RadioProfile) -> dict:
        default_output = DISPLAY_TO_LOGICAL_OUTPUT.get(
            profile.default_output,
            profile.default_output,
        )

        return {
            "id": profile.profile_id,
            "display_name": profile.display_name,
            "manufacturer": profile.manufacturer,
            "radio_type": profile.radio_type,
            "description": profile.description,
            "math_mode": profile.math_mode,
            "default_output": default_output,
            "notes": profile.notes,
            "bands": [self.band_to_json_dict(band) for band in profile.bands],
        }

    def band_to_json_dict(self, band: BandProfile) -> dict:
        band_data = {
            "id": band.band,
            "display_name": band.notes if band.notes else band.band,
            "rf_min_hz": band.rf_start_hz,
            "rf_max_hz": band.rf_end_hz,
            "default_rf_hz": band.rf_start_hz,
            "translation": {
                "mode": band.translation_mode,
                "rf_start_hz": band.rf_start_hz,
                "rf_end_hz": band.rf_end_hz,
            },
            "filter_band": "",
            "enabled": True,
        }

        if band.translation_mode == "linear_map":
            band_data["translation"]["vfo_start_hz"] = band.output_start_hz
            band_data["translation"]["vfo_end_hz"] = band.output_end_hz

        elif band.translation_mode in {"multiply", "divide"}:
            band_data["translation"]["multiplier"] = band.multiplier

        return band_data

    def validate_profiles(self):
        """
        Validate loaded in-memory profiles and display a readable report.

        This does not modify any profile data.
        It is intended as a pre-operation safety/sanity check before the
        main VFO program uses the profile set.
        """
        try:
            if self.current_profile is not None:
                self.apply_basic_info_to_model()

            errors, warnings = self.collect_profile_validation_messages()

            report_lines = []

            if not errors and not warnings:
                report_lines.append("PASS: No profile validation errors or warnings found.")
                report_lines.append("")
                report_lines.append("Profile data looks safe enough for normal operation.")
            else:
                if errors:
                    report_lines.append("ERRORS:")
                    for message in errors:
                        report_lines.append(f"  - {message}")
                    report_lines.append("")

                if warnings:
                    report_lines.append("WARNINGS:")
                    for message in warnings:
                        report_lines.append(f"  - {message}")
                    report_lines.append("")

                report_lines.append(
                    "Errors should be fixed before using the affected profile in the main VFO program."
                )

            self.validation_report.setPlainText("\n".join(report_lines))
            self.tabs.setCurrentWidget(self.preview_tab)

            if errors:
                QMessageBox.warning(
                    self,
                    "Profile Validation",
                    f"Validation found {len(errors)} error(s) and {len(warnings)} warning(s).",
                )
            elif warnings:
                QMessageBox.information(
                    self,
                    "Profile Validation",
                    f"Validation found {len(warnings)} warning(s), but no errors.",
                )
            else:
                QMessageBox.information(
                    self,
                    "Profile Validation",
                    "Validation passed with no errors or warnings.",
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Validation Failed",
                f"Could not complete profile validation:\n\n{e}",
            )

    def collect_profile_validation_messages(self) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []

        if not self.profiles:
            errors.append("No profiles are loaded.")
            return errors, warnings

        profile_ids_seen = set()
        profile_display_names_seen = set()

        for profile_key, profile in self.profiles.items():
            profile_label = profile.display_name or profile.profile_id or profile_key

            profile_id = str(profile.profile_id or "").strip()
            display_name = str(profile.display_name or "").strip()

            if not profile_id:
                errors.append(f"Profile '{profile_label}' has a blank Profile ID.")
            elif profile_id in profile_ids_seen:
                errors.append(f"Duplicate Profile ID: '{profile_id}'.")
            else:
                profile_ids_seen.add(profile_id)

            if not display_name:
                warnings.append(f"Profile '{profile_id or profile_key}' has a blank Display Name.")
            elif display_name in profile_display_names_seen:
                warnings.append(f"Duplicate profile Display Name: '{display_name}'.")
            else:
                profile_display_names_seen.add(display_name)

            if not getattr(profile, "bands", None):
                errors.append(f"Profile '{profile_label}' has no bands.")
                continue

            band_ids_seen = set()

            for band_index, band in enumerate(profile.bands, start=1):
                band_id = str(band.band or "").strip()
                band_label = band_id or f"band #{band_index}"
                location = f"Profile '{profile_label}', band '{band_label}'"

                if not band_id:
                    errors.append(f"{location}: blank Band ID.")
                elif band_id in band_ids_seen:
                    errors.append(
                        f"Profile '{profile_label}' has duplicate Band ID '{band_id}'."
                    )
                else:
                    band_ids_seen.add(band_id)

                mode = str(band.translation_mode or "").strip()

                if mode not in TRANSLATION_MODES:
                    errors.append(f"{location}: invalid translation mode '{mode}'.")

                if band.rf_start_hz <= 0 or band.rf_end_hz <= 0:
                    errors.append(f"{location}: RF start/end must be greater than zero.")
                elif band.rf_start_hz >= band.rf_end_hz:
                    errors.append(f"{location}: RF start must be lower than RF end.")

                if mode == "linear_map":
                    if band.output_start_hz <= 0 or band.output_end_hz <= 0:
                        errors.append(
                            f"{location}: linear_map requires VFO start/end frequencies."
                        )
                    elif band.output_start_hz >= band.output_end_hz:
                        errors.append(
                            f"{location}: VFO start must be lower than VFO end."
                        )

                if mode in {"multiply", "divide"}:
                    if band.multiplier <= 0:
                        errors.append(
                            f"{location}: multiplier must be greater than zero."
                        )

                if mode in {"direct", "multiply", "divide"}:
                    if band.output_start_hz or band.output_end_hz:
                        warnings.append(
                            f"{location}: VFO start/end values are ignored for {mode} mode."
                        )

                if mode == "linear_map" and band.multiplier != 1.0:
                    warnings.append(
                        f"{location}: multiplier is ignored for linear_map mode."
                    )

                if not str(band.notes or "").strip():
                    warnings.append(
                        f"{location}: Notes/display text is blank; band display will fall back to Band ID."
                    )

        return errors, warnings

    def on_revert_clicked(self):
        if not self.is_dirty:
            return

        result = QMessageBox.question(
            self,
            "Revert Unsaved Changes",
            "Discard all unsaved in-memory changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        self.profiles = copy.deepcopy(self.original_profiles)

        self.reload_profile_list_from_profiles()

        self.set_dirty(False)

    def reload_profile_list_from_profiles(self):
        current_id = None

        current_item = self.profile_list.currentItem()

        if current_item is not None:
            current_id = current_item.data(Qt.UserRole)

        self.profile_list.blockSignals(True)
        self.band_table.blockSignals(True)

        self.profile_list.clear()

        for profile_id, profile in self.profiles.items():
            item = QListWidgetItem(profile.display_name)
            item.setData(Qt.UserRole, profile_id)
            self.profile_list.addItem(item)

        self.profile_list.blockSignals(False)
        self.band_table.blockSignals(False)

        if self.profile_list.count() == 0:
            self.current_profile = None
            self.current_band_row = None

            self.clear_basic_fields()

            self.band_table.setRowCount(0)

            self.clear_band_detail_fields()

            return

        row_to_select = 0

        if current_id is not None:
            for row in range(self.profile_list.count()):
                item = self.profile_list.item(row)

                if item.data(Qt.UserRole) == current_id:
                    row_to_select = row
                    break

        self.profile_list.setCurrentRow(row_to_select)

        self.current_band_row = None

        self.band_table.clearSelection()

        if self.band_table.rowCount() > 0:
            self.band_table.selectRow(0)

    def closeEvent(self, event):
        if not self.is_dirty:
            event.accept()
            return

        result = QMessageBox.question(
            self,
            "Unsaved Changes",
            "You have unsaved in-memory changes. Close anyway?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def mhz_text_to_hz(self, text: str) -> int:
        value = float(text.strip())

        return int(round(value * 1_000_000))

    def mhz_text_to_hz_or_zero(self, text: str) -> int:
        clean = text.strip()

        if not clean or clean == "---":
            return 0

        return self.mhz_text_to_hz(clean)

    def float_text_or_default(
        self,
        text: str,
        default: float,
    ) -> float:
        clean = text.strip()

        if not clean or clean == "---":
            return default

        return float(clean)

    def clear_basic_fields(self):
        self.profile_id_edit.clear()
        self.display_name_edit.clear()
        self.manufacturer_edit.clear()

        self.description_edit.clear()
        self.notes_edit.clear()

        self.radio_type_combo.setCurrentIndex(0)
        self.math_mode_combo.setCurrentIndex(0)
        self.default_output_combo.setCurrentIndex(0)

    def set_combo_text(
        self,
        combo: QComboBox,
        value: str,
    ):
        index = combo.findText(value)

        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            combo.addItem(value)
            combo.setCurrentText(value)


def main():
    app = QApplication(sys.argv)

    window = ProfileEditorWindow()

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
