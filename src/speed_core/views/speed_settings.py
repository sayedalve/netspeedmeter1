"""
Internet Speed Meter — Settings Dialog.

Exposes only the controls relevant to a focused network speed meter:
  • Network adapter selection
  • Speed units & decimal places
  • Startup behaviour
  • Widget position / offset
  • Mini-graph toggle + opacity
  • Typography Scaling

Red & Black theme throughout. Hardware monitoring controls removed.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from speed_core import constants
from speed_core.core.startup_manager import StartupManager

logger = logging.getLogger("InternetSpeedMeter.SpeedSettings")

# ── Design tokens ─────────────────────────────────────────────────────────────
_RED      = "#E53935"
_RED_DIM  = "#B71C1C"
_RED_BRIG = "#FF1744"
_BG_BASE  = "#0D0D0D"
_BG_SURF  = "#1A1A1A"
_BG_CARD  = "#242424"
_BORDER   = "#3A0000"
_TEXT     = "#F5F5F5"
_SUBTEXT  = "#9E9E9E"
_ACCENT   = _RED

# ── Global QSS for the entire dialog ──────────────────────────────────────────
_DIALOG_QSS = f"""
    QDialog {{
        background-color: {_BG_BASE};
        color: {_TEXT};
        font-family: "Segoe UI", "Segoe UI Variable";
    }}

    /* ── Tab bar ── */
    QTabWidget::pane {{
        border: 1px solid {_BORDER};
        background-color: {_BG_SURF};
    }}
    QTabBar::tab {{
        background-color: {_BG_BASE};
        color: {_SUBTEXT};
        padding: 8px 20px;
        font-size: 12px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        color: {_RED};
        font-weight: 700;
        border-bottom: 2px solid {_RED};
        background-color: {_BG_SURF};
    }}
    QTabBar::tab:hover:!selected {{
        color: {_TEXT};
        background-color: {_BG_CARD};
    }}

    /* ── Section / GroupBox ── */
    QGroupBox {{
        color: {_RED};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        border: 1px solid {_BORDER};
        border-radius: 6px;
        margin-top: 14px;
        padding-top: 8px;
        background-color: {_BG_SURF};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 6px;
        background-color: {_BG_SURF};
    }}

    /* ── Labels ── */
    QLabel {{
        color: {_TEXT};
        background-color: transparent;
        font-size: 12px;
    }}

    /* ── CheckBox & RadioButton ── */
    QCheckBox, QRadioButton {{
        color: {_TEXT};
        font-size: 12px;
        spacing: 8px;
        background-color: transparent;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid #5A0000;
        border-radius: 3px;
        background-color: {_BG_CARD};
    }}
    QRadioButton::indicator {{
        border-radius: 8px;
    }}
    QCheckBox::indicator:checked {{
        background-color: {_RED};
        border-color: {_RED};
        image: none;
    }}
    QRadioButton::indicator:checked {{
        background-color: {_TEXT};
        border: 4px solid {_RED};
        border-radius: 8px;
    }}
    QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
        border-color: {_RED_BRIG};
    }}

    /* ── Spin boxes ── */
    QSpinBox, QDoubleSpinBox {{
        background-color: {_BG_CARD};
        color: {_TEXT};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        padding: 3px 6px;
        font-size: 12px;
        selection-background-color: {_RED_DIM};
    }}
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QSpinBox::down-button, QDoubleSpinBox::down-button {{
        background-color: {_BG_SURF};
        border: none;
        width: 16px;
    }}
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
        background-color: {_RED_DIM};
    }}

    /* ── ComboBox ── */
    QComboBox {{
        background-color: {_BG_CARD};
        color: {_TEXT};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        selection-background-color: {_RED_DIM};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {_BG_CARD};
        color: {_TEXT};
        border: 1px solid {_BORDER};
        selection-background-color: {_RED_DIM};
        outline: none;
    }}

    /* ── Slider ── */
    QSlider::groove:horizontal {{
        height: 4px;
        background-color: #3A0000;
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background-color: {_RED};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background-color: {_RED};
        border: none;
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}
    QSlider::handle:horizontal:hover {{
        background-color: {_RED_BRIG};
    }}

    /* ── Buttons ── */
    QPushButton {{
        background-color: {_BG_CARD};
        color: {_TEXT};
        border: 1px solid {_BORDER};
        border-radius: 4px;
        padding: 5px 16px;
        font-size: 12px;
        min-height: 22px;
    }}
    QPushButton:hover {{
        background-color: {_RED_DIM};
        border-color: {_RED};
    }}
    QPushButton:pressed {{
        background-color: {_RED};
    }}

    /* ── Dialog button box OK button gets accent styling ── */
    QDialogButtonBox QPushButton[text="OK"] {{
        background-color: {_RED};
        color: #FFFFFF;
        border-color: {_RED_DIM};
        font-weight: 600;
    }}
    QDialogButtonBox QPushButton[text="OK"]:hover {{
        background-color: {_RED_BRIG};
    }}

    /* ── ScrollArea ── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background-color: {_BG_BASE};
        width: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: #5A0000;
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {_RED};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Tab: General  (startup, update rate, position)
# ─────────────────────────────────────────────────────────────────────────────

class _GeneralTab(QWidget):
    def __init__(self, cfg: Dict[str, Any], startup_enabled: bool, on_change: Callable):
        super().__init__()
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # ── Startup ─────────────────────────────────────────────────────
        startup_sec = QGroupBox("STARTUP")
        startup_layout = QFormLayout(startup_sec)
        startup_layout.setContentsMargins(10, 6, 10, 10)

        self.start_with_windows = QCheckBox("Launch with Windows")
        self.start_with_windows.setChecked(startup_enabled)
        self.start_with_windows.toggled.connect(self._on_change)
        startup_layout.addRow(self.start_with_windows)
        layout.addWidget(startup_sec)

        # ── Update Rate ──────────────────────────────────────────────────
        rate_sec = QGroupBox("UPDATE RATE")
        rate_layout = QFormLayout(rate_sec)
        rate_layout.setContentsMargins(10, 6, 10, 10)

        self.update_rate = QDoubleSpinBox()
        self.update_rate.setRange(0.25, 5.0)
        self.update_rate.setSingleStep(0.25)
        self.update_rate.setDecimals(2)
        self.update_rate.setSuffix(" s")
        self.update_rate.setValue(float(cfg.get("update_rate", 1.0)))
        self.update_rate.valueChanged.connect(self._on_change)
        rate_layout.addRow("Polling interval:", self.update_rate)
        layout.addWidget(rate_sec)

        # ── Widget Position ──────────────────────────────────────────────
        pos_sec = QGroupBox("WIDGET POSITION")
        pos_layout = QFormLayout(pos_sec)
        pos_layout.setContentsMargins(10, 6, 10, 10)

        self.free_move = QCheckBox("Free move  (drag widget anywhere)")
        self.free_move.setChecked(bool(cfg.get("free_move", False)))
        self.free_move.toggled.connect(self._toggle_free_move)
        pos_layout.addRow(self.free_move)

        self.lock_position = QCheckBox("Lock position  (remember last spot)")
        self.lock_position.setChecked(bool(cfg.get("lock_position", False)))
        self.lock_position.toggled.connect(self._on_change)
        pos_layout.addRow(self.lock_position)

        self.keep_visible_fullscreen = QCheckBox("Keep visible in fullscreen apps")
        self.keep_visible_fullscreen.setChecked(bool(cfg.get("keep_visible_fullscreen", False)))
        self.keep_visible_fullscreen.toggled.connect(self._on_change)
        pos_layout.addRow(self.keep_visible_fullscreen)

        offset_row = QHBoxLayout()
        self.tray_offset_x = QSpinBox()
        self.tray_offset_x.setRange(0, 500)
        self.tray_offset_x.setValue(int(cfg.get("tray_offset_x", 0)))
        self.tray_offset_x.setSuffix(" px")
        self.tray_offset_x.valueChanged.connect(self._on_change)

        self.tray_offset_y = QSpinBox()
        self.tray_offset_y.setRange(0, 500)
        self.tray_offset_y.setValue(int(cfg.get("tray_offset_y", 3)))
        self.tray_offset_y.setSuffix(" px")
        self.tray_offset_y.valueChanged.connect(self._on_change)

        offset_row.addWidget(QLabel("X:"))
        offset_row.addWidget(self.tray_offset_x)
        offset_row.addSpacing(14)
        offset_row.addWidget(QLabel("Y:"))
        offset_row.addWidget(self.tray_offset_y)
        offset_row.addStretch()
        pos_layout.addRow("Tray offset:", offset_row)

        layout.addWidget(pos_sec)
        layout.addStretch()

    def _toggle_free_move(self, checked: bool):
        if checked:
            self.lock_position.setChecked(False)
        self._on_change()

    def collect(self) -> Dict[str, Any]:
        return {
            "update_rate":             self.update_rate.value(),
            "free_move":               self.free_move.isChecked(),
            "lock_position":           self.lock_position.isChecked(),
            "keep_visible_fullscreen": self.keep_visible_fullscreen.isChecked(),
            "tray_offset_x":           self.tray_offset_x.value(),
            "tray_offset_y":           self.tray_offset_y.value(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab: Network  (adapter, display units)
# ─────────────────────────────────────────────────────────────────────────────

class _NetworkTab(QWidget):
    def __init__(self, cfg: Dict[str, Any], available_interfaces: List[str], on_change: Callable):
        super().__init__()
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # ── Adapter selection ────────────────────────────────────────────
        adapter_sec = QGroupBox("NETWORK ADAPTER")
        adapter_layout = QVBoxLayout(adapter_sec)
        adapter_layout.setContentsMargins(10, 6, 10, 10)
        adapter_layout.setSpacing(6)

        self._mode_auto     = QRadioButton("Auto  (primary internet adapter)")
        self._mode_physical = QRadioButton("All physical adapters")
        self._mode_all      = QRadioButton("All adapters  (including virtual)")
        self._mode_selected = QRadioButton("Specific adapter(s)")

        mode = cfg.get("interface_mode", "auto_primary")
        {
            "auto_primary": self._mode_auto,
            "all_physical": self._mode_physical,
            "all":          self._mode_all,
            "selected":     self._mode_selected,
        }.get(mode, self._mode_auto).setChecked(True)

        for rb in (self._mode_auto, self._mode_physical, self._mode_all, self._mode_selected):
            rb.toggled.connect(self._on_mode_changed)
            adapter_layout.addWidget(rb)

        # Per-adapter checkboxes (shown only in "selected" mode)
        self._interface_checks: Dict[str, QCheckBox] = {}
        self._iface_container = QWidget()
        iface_layout = QVBoxLayout(self._iface_container)
        iface_layout.setContentsMargins(20, 4, 0, 4)
        iface_layout.setSpacing(4)
        selected = set(cfg.get("selected_interfaces", []))
        for iface in available_interfaces:
            cb = QCheckBox(iface)
            cb.setChecked(iface in selected)
            cb.toggled.connect(self._on_change)
            iface_layout.addWidget(cb)
            self._interface_checks[iface] = cb

        self._iface_container.setVisible(self._mode_selected.isChecked())
        adapter_layout.addWidget(self._iface_container)
        layout.addWidget(adapter_sec)

        # ── Speed units ──────────────────────────────────────────────────
        units_sec = QGroupBox("DISPLAY UNITS")
        units_layout = QFormLayout(units_sec)
        units_layout.setContentsMargins(10, 6, 10, 10)

        self.unit_type = QComboBox()
        for value, label in [
            ("bits_decimal",  "Bits  — Kbps / Mbps  (decimal)"),
            ("bits_binary",   "Bits  — Kibps / Mibps (binary)"),
            ("bytes_decimal", "Bytes — KB/s / MB/s   (decimal)"),
            ("bytes_binary",  "Bytes — KiB/s / MiB/s (binary)"),
        ]:
            self.unit_type.addItem(label, userData=value)

        current_unit = cfg.get("unit_type", "bits_decimal")
        idx = next((i for i in range(self.unit_type.count())
                    if self.unit_type.itemData(i) == current_unit), 0)
        self.unit_type.setCurrentIndex(idx)
        self.unit_type.currentIndexChanged.connect(self._on_change)
        units_layout.addRow("Unit:", self.unit_type)

        self.decimal_places = QSpinBox()
        self.decimal_places.setRange(0, 2)
        self.decimal_places.setValue(int(cfg.get("decimal_places", 1)))
        self.decimal_places.valueChanged.connect(self._on_change)
        units_layout.addRow("Decimal places:", self.decimal_places)

        self.swap_upload_download = QCheckBox("Show download on top")
        self.swap_upload_download.setChecked(bool(cfg.get("swap_upload_download", False)))
        self.swap_upload_download.toggled.connect(self._on_change)
        units_layout.addRow(self.swap_upload_download)

        layout.addWidget(units_sec)
        layout.addStretch()

    def _on_mode_changed(self):
        self._iface_container.setVisible(self._mode_selected.isChecked())
        self._on_change()

    def _interface_mode(self) -> str:
        if self._mode_physical.isChecked(): return "all_physical"
        if self._mode_all.isChecked():      return "all"
        if self._mode_selected.isChecked(): return "selected"
        return "auto_primary"

    def update_interfaces(self, available_interfaces: List[str]) -> None:
        container_layout = self._iface_container.layout()
        while container_layout.count():
            item = container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._interface_checks.clear()
        for iface in available_interfaces:
            cb = QCheckBox(iface)
            cb.toggled.connect(self._on_change)
            container_layout.addWidget(cb)
            self._interface_checks[iface] = cb

    def collect(self) -> Dict[str, Any]:
        selected = [iface for iface, cb in self._interface_checks.items() if cb.isChecked()]
        return {
            "interface_mode":       self._interface_mode(),
            "selected_interfaces":  selected,
            "unit_type":            self.unit_type.currentData(),
            "decimal_places":       self.decimal_places.value(),
            "swap_upload_download": self.swap_upload_download.isChecked(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab: Appearance
# ─────────────────────────────────────────────────────────────────────────────

class _AppearanceTab(QWidget):
    def __init__(self, cfg: Dict[str, Any], on_change: Callable):
        super().__init__()
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # ── Typography Scaling ───────────────────────────────────────────
        typo_sec = QGroupBox("TYPOGRAPHY SCALING")
        typo_layout = QFormLayout(typo_sec)
        typo_layout.setContentsMargins(10, 6, 10, 10)

        self.font_size_speed = QSpinBox()
        self.font_size_speed.setRange(8, 36)
        self.font_size_speed.setValue(int(cfg.get("font_size_speed", 11)))
        self.font_size_speed.valueChanged.connect(self._on_change)
        typo_layout.addRow("Speed numbers size:", self.font_size_speed)

        self.font_size_unit = QSpinBox()
        self.font_size_unit.setRange(6, 24)
        self.font_size_unit.setValue(int(cfg.get("font_size_unit", 8)))
        self.font_size_unit.valueChanged.connect(self._on_change)
        typo_layout.addRow("Unit text size:", self.font_size_unit)

        layout.addWidget(typo_sec)

        # ── Mini-graph ───────────────────────────────────────────────────
        graph_sec = QGroupBox("MINI GRAPH")
        graph_layout = QFormLayout(graph_sec)
        graph_layout.setContentsMargins(10, 6, 10, 10)

        self.graph_enabled = QCheckBox("Show speed graph behind text")
        self.graph_enabled.setChecked(bool(cfg.get("graph_enabled", False)))
        self.graph_enabled.toggled.connect(self._on_change)
        graph_layout.addRow(self.graph_enabled)

        self.graph_opacity = QSlider(Qt.Orientation.Horizontal)
        self.graph_opacity.setRange(0, 100)
        self.graph_opacity.setValue(int(cfg.get("graph_opacity", 66)))
        self.graph_opacity.valueChanged.connect(self._on_change)
        self._graph_opacity_label = QLabel(f"{self.graph_opacity.value()}%")
        self._graph_opacity_label.setFixedWidth(36)
        self.graph_opacity.valueChanged.connect(
            lambda v: self._graph_opacity_label.setText(f"{v}%")
        )
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.graph_opacity)
        opacity_row.addWidget(self._graph_opacity_label)
        graph_layout.addRow("Opacity:", opacity_row)

        self.history_minutes = QSpinBox()
        self.history_minutes.setRange(1, 60)
        self.history_minutes.setSuffix(" min")
        self.history_minutes.setValue(int(cfg.get("history_minutes", 3)))
        self.history_minutes.valueChanged.connect(self._on_change)
        graph_layout.addRow("History window:", self.history_minutes)

        layout.addWidget(graph_sec)

        # ── Background ───────────────────────────────────────────────────
        bg_sec = QGroupBox("WIDGET BACKGROUND")
        bg_layout = QFormLayout(bg_sec)
        bg_layout.setContentsMargins(10, 6, 10, 10)

        self.background_opacity = QSlider(Qt.Orientation.Horizontal)
        self.background_opacity.setRange(0, 100)
        self.background_opacity.setValue(int(cfg.get("background_opacity", 0)))
        self.background_opacity.valueChanged.connect(self._on_change)
        self._bg_opacity_label = QLabel(f"{self.background_opacity.value()}%")
        self._bg_opacity_label.setFixedWidth(36)
        self.background_opacity.valueChanged.connect(
            lambda v: self._bg_opacity_label.setText(f"{v}%")
        )
        bg_row = QHBoxLayout()
        bg_row.addWidget(self.background_opacity)
        bg_row.addWidget(self._bg_opacity_label)
        bg_layout.addRow("Opacity:", bg_row)

        layout.addWidget(bg_sec)
        layout.addStretch()

    def collect(self) -> Dict[str, Any]:
        return {
            "graph_enabled":      self.graph_enabled.isChecked(),
            "graph_opacity":      self.graph_opacity.value(),
            "history_minutes":    self.history_minutes.value(),
            "background_opacity": self.background_opacity.value(),
            "font_size_speed":    self.font_size_speed.value(),
            "font_size_unit":     self.font_size_unit.value(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Main dialog
# ─────────────────────────────────────────────────────────────────────────────

class SpeedSettingsDialog(QDialog):
    """
    Focused settings dialog for Internet Speed Meter.
    Emits settings_changed(dict) on every live change for instant preview,
    then saves on OK / Apply.
    """
    settings_changed = pyqtSignal(dict)

    def __init__(
        self,
        main_widget,
        config: Dict[str, Any],
        available_interfaces: List[str],
        is_startup_enabled: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._main_widget     = main_widget
        self._config          = config.copy()
        self._startup_mgr     = StartupManager()
        self._startup_enabled = is_startup_enabled

        self.setWindowTitle("Internet Speed Meter — Settings")
        self.setMinimumWidth(440)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui(available_interfaces)
        self.setStyleSheet(_DIALOG_QSS)

    # ─────────────────────────────────────────────────────────────────── #

    def _build_ui(self, available_interfaces: List[str]) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)

        self._general_tab    = _GeneralTab(self._config, self._startup_enabled, self._on_any_change)
        self._network_tab    = _NetworkTab(self._config, available_interfaces, self._on_any_change)
        self._appearance_tab = _AppearanceTab(self._config, self._on_any_change)

        tabs.addTab(self._general_tab,    "General")
        tabs.addTab(self._network_tab,    "Network")
        tabs.addTab(self._appearance_tab, "Appearance")

        layout.addWidget(tabs)

        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        btn_box.setContentsMargins(14, 8, 14, 12)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        layout.addWidget(btn_box)

    # ─────────────────────────────────────────────────────────────────── #

    def _collect_all(self) -> Dict[str, Any]:
        cfg = {}
        cfg.update(self._general_tab.collect())
        cfg.update(self._network_tab.collect())
        cfg.update(self._appearance_tab.collect())
        return cfg

    def _on_any_change(self, *_) -> None:
        self.settings_changed.emit(self._collect_all())

    def _on_apply(self) -> None:
        collected = self._collect_all()
        new_startup = self._general_tab.start_with_windows.isChecked()
        if new_startup != self._startup_enabled:
            try:
                self._startup_mgr.toggle_startup(new_startup)
                self._startup_enabled = new_startup
            except Exception as e:
                logger.error("Could not toggle startup: %s", e)
        collected["start_with_windows"] = new_startup
        if self._main_widget:
            self._main_widget.handle_settings_changed(collected, save_to_disk=True)

    def _on_ok(self) -> None:
        self._on_apply()
        self.accept()

    # ─────────────────────────────────────────────────────────────────── #

    def reset_with_config(self, config: Dict[str, Any], is_startup_enabled: bool) -> None:
        self._config          = config.copy()
        self._startup_enabled = is_startup_enabled

    def update_interface_list(self, available_interfaces: List[str]) -> None:
        self._network_tab.update_interfaces(available_interfaces)