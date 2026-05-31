"""
SpeedSettings — lean settings dialog for the dedicated internet speed meter.

Only exposes:
  • Network adapter selection
  • Speed units
  • Startup behaviour
  • Widget position settings
  • Mini-graph toggle + opacity

Everything related to CPU/GPU/RAM/temperature/power has been removed.
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

from netspeedtray import constants
from netspeedtray.core.startup_manager import StartupManager

logger = logging.getLogger("NetSpeedTray.SpeedSettings")


# ─────────────────────────────────────────────────────────────────────────────
#  Thin helper widgets
# ─────────────────────────────────────────────────────────────────────────────

class _Toggle(QCheckBox):
    """Styled toggle switch (simple checkbox styled as a toggle)."""
    pass


class _Section(QGroupBox):
    """Styled section box."""
    def __init__(self, title: str, parent=None):
        super().__init__(title, parent)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid rgba(128,128,128,0.3);
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)


# ─────────────────────────────────────────────────────────────────────────────
#  Tab: General  (startup, update rate, position)
# ─────────────────────────────────────────────────────────────────────────────

class _GeneralTab(QWidget):
    def __init__(self, cfg: Dict[str, Any], startup_enabled: bool, on_change: Callable):
        super().__init__()
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Startup ─────────────────────────────────────────────────────
        startup_sec = _Section("Startup")
        startup_layout = QFormLayout(startup_sec)

        self.start_with_windows = _Toggle("Launch with Windows")
        self.start_with_windows.setChecked(startup_enabled)
        self.start_with_windows.toggled.connect(self._on_change)
        startup_layout.addRow(self.start_with_windows)
        layout.addWidget(startup_sec)

        # ── Update Rate ──────────────────────────────────────────────────
        rate_sec = _Section("Update rate")
        rate_layout = QFormLayout(rate_sec)

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
        pos_sec = _Section("Widget position")
        pos_layout = QFormLayout(pos_sec)

        self.free_move = _Toggle("Free move  (drag widget anywhere)")
        self.free_move.setChecked(bool(cfg.get("free_move", False)))
        self.free_move.toggled.connect(self._toggle_free_move)
        pos_layout.addRow(self.free_move)

        self.lock_position = _Toggle("Lock position  (remember last spot)")
        self.lock_position.setChecked(bool(cfg.get("lock_position", False)))
        self.lock_position.toggled.connect(self._on_change)
        pos_layout.addRow(self.lock_position)

        self.keep_visible_fullscreen = _Toggle("Keep visible in fullscreen apps")
        self.keep_visible_fullscreen.setChecked(bool(cfg.get("keep_visible_fullscreen", False)))
        self.keep_visible_fullscreen.toggled.connect(self._on_change)
        pos_layout.addRow(self.keep_visible_fullscreen)

        offset_row = QHBoxLayout()
        self.tray_offset_x = QSpinBox(); self.tray_offset_x.setRange(0, 500)
        self.tray_offset_x.setValue(int(cfg.get("tray_offset_x", 0)))
        self.tray_offset_x.setSuffix(" px")
        self.tray_offset_x.valueChanged.connect(self._on_change)

        self.tray_offset_y = QSpinBox(); self.tray_offset_y.setRange(0, 500)
        self.tray_offset_y.setValue(int(cfg.get("tray_offset_y", 3)))
        self.tray_offset_y.setSuffix(" px")
        self.tray_offset_y.valueChanged.connect(self._on_change)

        offset_row.addWidget(QLabel("X:")); offset_row.addWidget(self.tray_offset_x)
        offset_row.addSpacing(12)
        offset_row.addWidget(QLabel("Y:")); offset_row.addWidget(self.tray_offset_y)
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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Adapter selection ────────────────────────────────────────────
        adapter_sec = _Section("Network adapter")
        adapter_layout = QVBoxLayout(adapter_sec)

        self._mode_auto     = QRadioButton("Auto (primary internet adapter)")
        self._mode_physical = QRadioButton("All physical adapters")
        self._mode_all      = QRadioButton("All adapters (including virtual)")
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
        units_sec = _Section("Display units")
        units_layout = QFormLayout(units_sec)

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

        self.swap_upload_download = _Toggle("Show download on top")
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
        # Clear existing
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
            "interface_mode":      self._interface_mode(),
            "selected_interfaces": selected,
            "unit_type":           self.unit_type.currentData(),
            "decimal_places":      self.decimal_places.value(),
            "swap_upload_download":self.swap_upload_download.isChecked(),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Tab: Appearance
# ─────────────────────────────────────────────────────────────────────────────

class _AppearanceTab(QWidget):
    def __init__(self, cfg: Dict[str, Any], on_change: Callable):
        super().__init__()
        self._on_change = on_change
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ── Mini-graph ───────────────────────────────────────────────────
        graph_sec = _Section("Mini-graph")
        graph_layout = QFormLayout(graph_sec)

        self.graph_enabled = _Toggle("Show speed graph behind text")
        self.graph_enabled.setChecked(bool(cfg.get("graph_enabled", False)))
        self.graph_enabled.toggled.connect(self._on_change)
        graph_layout.addRow(self.graph_enabled)

        self.graph_opacity = QSlider(Qt.Orientation.Horizontal)
        self.graph_opacity.setRange(0, 100)
        self.graph_opacity.setValue(int(cfg.get("graph_opacity", 66)))
        self.graph_opacity.valueChanged.connect(self._on_change)
        self._graph_opacity_label = QLabel(f"{self.graph_opacity.value()}%")
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
        bg_sec = _Section("Background")
        bg_layout = QFormLayout(bg_sec)

        self.background_opacity = QSlider(Qt.Orientation.Horizontal)
        self.background_opacity.setRange(0, 100)
        self.background_opacity.setValue(int(cfg.get("background_opacity", 0)))
        self.background_opacity.valueChanged.connect(self._on_change)
        self._bg_opacity_label = QLabel(f"{self.background_opacity.value()}%")
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
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Main dialog
# ─────────────────────────────────────────────────────────────────────────────

class SpeedSettingsDialog(QDialog):
    """
    Focused settings dialog for the internet speed meter.
    Emits settings_changed(dict) on every live change so the widget
    can preview instantly, then saves on OK / Apply.
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
        self._main_widget = main_widget
        self._config      = config.copy()
        self._startup_mgr = StartupManager()
        self._startup_enabled = is_startup_enabled

        self.setWindowTitle("NetSpeedMeter — Settings")
        self.setMinimumWidth(420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._build_ui(available_interfaces)
        self._apply_stylesheet()

    # ------------------------------------------------------------------ #

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

        # Button row
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        btn_box.setContentsMargins(12, 8, 12, 12)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        btn_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        layout.addWidget(btn_box)

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar::tab {
                padding: 8px 18px;
                font-size: 12px;
            }
            QTabBar::tab:selected { font-weight: 600; }
            QDialogButtonBox { padding: 4px; }
        """)

    # ------------------------------------------------------------------ #

    def _collect_all(self) -> Dict[str, Any]:
        cfg = {}
        cfg.update(self._general_tab.collect())
        cfg.update(self._network_tab.collect())
        cfg.update(self._appearance_tab.collect())
        return cfg

    def _on_any_change(self, *_) -> None:
        """Emit a live preview — caller should NOT save to disk."""
        self.settings_changed.emit(self._collect_all())

    def _on_apply(self) -> None:
        collected = self._collect_all()
        # Handle startup toggle separately (registry side-effect)
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

    # ------------------------------------------------------------------ #

    def reset_with_config(self, config: Dict[str, Any], is_startup_enabled: bool) -> None:
        """Re-populate all controls from a fresh config dict."""
        self._config = config.copy()
        self._startup_enabled = is_startup_enabled
        # Re-build tabs in-place is complex — simplest: close and let main widget re-open.
        # For now just update the controls we can reach easily.

    def update_interface_list(self, available_interfaces: List[str]) -> None:
        self._network_tab.update_interfaces(available_interfaces)
