# File: output_manager.py
#
# SI5351 Multi-Radio VFO Control Platform
# Output Manager backend.
#
# Purpose:
#   - Central authority for Output 1 through Output 6 ownership.
#   - Internally maps user-facing Output 1-6 to firmware OUT0-OUT5.
#   - Tracks RF state, SPOT state, TX/RX state, radio, band, and frequency.
#
# Important:
#   Operators see Output 1-6.
#   Firmware and serial protocol still use OUT0-OUT5.

from dataclasses import dataclass
from typing import Optional, Dict, List

from PySide6.QtCore import QObject, Signal


OUTPUT_COUNT = 6

# Operator-facing color hints used by the GUI.
# These are intentionally simple and high-contrast.
OUTPUT_COLORS = [
    "#0072B2",  # Output 1 - blue
    "#E69F00",  # Output 2 - amber
    "#56B4E9",  # Output 3 - light blue
    "#CC79A7",  # Output 4 - magenta
    "#D55E00",  # Output 5 - burnt orange
    "#999999",  # Output 6 - gray
]


def index_to_color(index: int) -> str:
    if index < 0 or index >= OUTPUT_COUNT:
        raise ValueError(f"Output index out of range: {index}")
    return OUTPUT_COLORS[index]



def output_name_to_index(output_name: str) -> int:
    """
    Convert internal output name OUT0..OUT5 to integer index 0..5.
    """
    text = str(output_name).upper().strip().replace("CLK", "OUT")
    if not text.startswith("OUT"):
        raise ValueError(f"Invalid output name: {output_name}")

    try:
        index = int(text[3:])
    except ValueError as exc:
        raise ValueError(f"Invalid output name: {output_name}") from exc

    if index < 0 or index >= OUTPUT_COUNT:
        raise ValueError(f"Output out of range: {output_name}")

    return index


def index_to_output_name(index: int) -> str:
    """
    Convert index 0..5 to internal firmware name OUT0..OUT5.
    """
    if index < 0 or index >= OUTPUT_COUNT:
        raise ValueError(f"Output index out of range: {index}")
    return f"OUT{index}"


def index_to_user_label(index: int) -> str:
    """
    Convert index 0..5 to operator-facing physical connector label.

    Operators see:
      Output 1 (BNC 1)
      ...
      Output 6 (BNC 6)

    Firmware still uses OUT0..OUT5 internally.
    """
    if index < 0 or index >= OUTPUT_COUNT:
        raise ValueError(f"Output index out of range: {index}")
    return f"Output {index + 1} (BNC {index + 1})"


def output_name_to_user_label(output_name: str) -> str:
    return index_to_user_label(output_name_to_index(output_name))


@dataclass
class OutputState:
    index: int
    owner_id: Optional[str] = None
    owner_name: str = ""
    radio_name: str = ""
    band_name: str = ""
    frequency_hz: int = 0
    vfo_hz: int = 0
    step_hz: int = 100
    rf_enabled: bool = False
    spot_enabled: bool = False
    tx_active: bool = False

    @property
    def internal_name(self) -> str:
        return index_to_output_name(self.index)

    @property
    def user_label(self) -> str:
        return index_to_user_label(self.index)

    @property
    def color(self) -> str:
        return index_to_color(self.index)

    @property
    def is_free(self) -> bool:
        return self.owner_id is None

    def state_text(self) -> str:
        if self.tx_active:
            return "TX"
        if self.spot_enabled:
            return "SPOT"
        if self.rf_enabled:
            return "RF ON"
        return "OFF"

    def clear(self) -> None:
        self.owner_id = None
        self.owner_name = ""
        self.radio_name = ""
        self.band_name = ""
        self.frequency_hz = 0
        self.vfo_hz = 0
        self.step_hz = 100
        self.rf_enabled = False
        self.spot_enabled = False
        self.tx_active = False


class OutputManager(QObject):
    """
    Central ownership and state manager for all VFO outputs.

    Rules:
      - One output may have only one owner.
      - One owner may hold only one output.
      - Output claims are explicit.
      - Startup RF state must always be OFF.
    """

    outputs_changed = Signal()
    conflict_detected = Signal(str)

    def __init__(self):
        super().__init__()
        self.outputs: Dict[int, OutputState] = {
            i: OutputState(index=i) for i in range(OUTPUT_COUNT)
        }

    def all_states(self) -> List[OutputState]:
        return [self.outputs[i] for i in range(OUTPUT_COUNT)]

    def find_free_output_name(self) -> Optional[str]:
        for state in self.all_states():
            if state.is_free:
                return state.internal_name
        return None

    def owner_for_output(self, output_name: str) -> Optional[str]:
        index = output_name_to_index(output_name)
        return self.outputs[index].owner_id

    def output_for_owner(self, owner_id: str) -> Optional[str]:
        for state in self.all_states():
            if state.owner_id == owner_id:
                return state.internal_name
        return None

    def claim_output(self, output_name: str, owner_id: str, owner_name: str) -> bool:
        index = output_name_to_index(output_name)
        state = self.outputs[index]

        if state.owner_id is None or state.owner_id == owner_id:
            # Enforce one-output-per-owner.
            for other in self.all_states():
                if other.index != index and other.owner_id == owner_id:
                    other.clear()

            state.owner_id = owner_id
            state.owner_name = owner_name
            self.outputs_changed.emit()
            return True

        self.conflict_detected.emit(
            f"{state.user_label} is already assigned to {state.owner_name}"
        )
        return False

    def reassign_output(
        self,
        old_output_name: str,
        new_output_name: str,
        owner_id: str,
        owner_name: str,
    ) -> bool:
        old_index = output_name_to_index(old_output_name)
        new_index = output_name_to_index(new_output_name)

        if old_index == new_index:
            return True

        new_state = self.outputs[new_index]
        if new_state.owner_id not in (None, owner_id):
            self.conflict_detected.emit(
                f"{new_state.user_label} is already assigned to {new_state.owner_name}"
            )
            return False

        old_state = self.outputs[old_index]
        old_radio = old_state.radio_name
        old_band = old_state.band_name
        old_frequency = old_state.frequency_hz
        old_vfo = old_state.vfo_hz
        old_step = old_state.step_hz

        # Release any old assignment held by this owner.
        for state in self.all_states():
            if state.owner_id == owner_id:
                state.clear()

        new_state.owner_id = owner_id
        new_state.owner_name = owner_name
        new_state.radio_name = old_radio
        new_state.band_name = old_band
        new_state.frequency_hz = old_frequency
        new_state.vfo_hz = old_vfo
        new_state.step_hz = old_step
        new_state.rf_enabled = False
        new_state.spot_enabled = False
        new_state.tx_active = False

        self.outputs_changed.emit()
        return True

    def release_owner(self, owner_id: str) -> None:
        changed = False
        for state in self.all_states():
            if state.owner_id == owner_id:
                state.clear()
                changed = True
        if changed:
            self.outputs_changed.emit()

    def update_owner_name(self, owner_id: str, owner_name: str) -> None:
        for state in self.all_states():
            if state.owner_id == owner_id:
                state.owner_name = owner_name
        self.outputs_changed.emit()

    def update_radio_state(
        self,
        owner_id: str,
        radio_name: str = "",
        band_name: str = "",
        frequency_hz: int = 0,
        vfo_hz: int = 0,
        step_hz: int = 100,
    ) -> None:
        for state in self.all_states():
            if state.owner_id == owner_id:
                state.radio_name = radio_name
                state.band_name = band_name
                state.frequency_hz = int(frequency_hz or 0)
                state.vfo_hz = int(vfo_hz or 0)
                state.step_hz = int(step_hz or 100)
                self.outputs_changed.emit()
                return

    def update_rf_state_by_owner(
        self,
        owner_id: str,
        rf_enabled: bool,
        spot_enabled: bool,
        tx_active: bool,
    ) -> None:
        for state in self.all_states():
            if state.owner_id == owner_id:
                state.rf_enabled = bool(rf_enabled)
                state.spot_enabled = bool(spot_enabled)
                state.tx_active = bool(tx_active)
                self.outputs_changed.emit()
                return

    def update_tx_state_by_output(self, output_name: str, tx_active: bool) -> None:
        index = output_name_to_index(output_name)
        self.outputs[index].tx_active = bool(tx_active)
        self.outputs_changed.emit()

    def force_all_rf_off(self) -> None:
        for state in self.all_states():
            state.rf_enabled = False
            state.spot_enabled = False
            state.tx_active = False
        self.outputs_changed.emit()
