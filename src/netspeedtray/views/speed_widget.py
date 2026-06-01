"""
Internet Speed Meter — dedicated internet speed meter widget.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import win32api
import win32con
import win32gui
from PyQt6.QtCore import QEvent, QObject, QPoint, QRect, QSize, QTimer, Qt
from PyQt6.QtGui import (
    QCloseEvent, QColor, QContextMenuEvent, QFont, QFontMetrics,
    QHideEvent, QIcon, QMouseEvent, QPaintEvent, QPainter, QShowEvent,
)
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox, QWidget

from netspeedtray import constants
from netspeedtray.core.controller       import StatsController
from netspeedtray.core.monitor_thread   import StatsMonitorThread
from netspeedtray.core.position_manager import PositionManager, WindowState
from netspeedtray.core.startup_manager  import StartupManager
from netspeedtray.core.system_events    import SystemEventHandler
from netspeedtray.core.tray_manager     import TrayIconManager
from netspeedtray.core.widget_state     import WidgetState
from netspeedtray.core.config_controller import ConfigController
from netspeedtray.core.input_handler    import InputHandler
from netspeedtray.utils.config          import ConfigManager
from netspeedtray.utils.taskbar_utils   import (
    get_taskbar_info, is_taskbar_obstructed, is_taskbar_visible,
)
from netspeedtray.utils.speed_renderer  import SpeedRenderer
from netspeedtray.views.widget.layout   import WidgetLayoutManager
from netspeedtray.views.widget.theme    import WidgetThemeManager

logger = logging.getLogger("InternetSpeedMeter.Widget")


def _strip_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of cfg with hardware monitoring hard-disabled and free-move forced."""
    out = cfg.copy()
    out["monitor_cpu_enabled"]  = False
    out["monitor_gpu_enabled"]  = False
    out["monitor_ram_enabled"]  = False
    out["monitor_vram_enabled"] = False
    out["widget_display_mode"]  = "network_only"
    out["free_move"]            = True  # FORCE FREE MOVE to allow placing on left side
    return out


class NetSpeedMeterWidget(QWidget):
    MIN_UPDATE_INTERVAL = constants.config.defaults.MINIMUM_UPDATE_RATE

    def __init__(
        self,
        taskbar_height: int = constants.taskbar.taskbar.DEFAULT_HEIGHT,
        config: Optional[Dict[str, Any]] = None,
        i18n=None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logger
        self.i18n = i18n
        self.settings_dialog = None
        self.session_start_time = datetime.now()
        self.config_manager    = ConfigManager()
        self.config_controller = ConfigController(self, self.config_manager)

        raw_cfg = config or self.config_controller.load_initial_config(taskbar_height)
        self.config: Dict[str, Any] = _strip_config(raw_cfg)

        self.current_font:    QFont        = None
        self.current_metrics: QFontMetrics = None

        self._init_managers()
        self.theme_manager.apply_theme_aware_defaults()

        self.upload_speed:   float = 0.0
        self.download_speed: float = 0.0

        self.taskbar_height: int  = taskbar_height
        self._dragging:      bool = False
        self._drag_offset:   QPoint = QPoint()

        self.is_paused:                bool  = False
        self._taskbar_lost_count:      int   = 0
        self._will_quit_app:           bool  = False
        self._is_context_menu_visible: bool  = False
        self._cached_layout_mode:      str   = "vertical"

        self.renderer = SpeedRenderer(self.config)
        self.setVisible(False)

        try:
            self.layout_manager.setup_window_properties()
            self._init_ui_components()
            self._init_core_components()
            self.layout_manager.resize_widget_for_font()
            self._setup_connections()
            self._setup_timers()
            self.position_manager.update_position()
            self._synchronize_startup_task()
            QTimer.singleShot(0, self._delayed_initial_show)
        except Exception as e:
            self.logger.critical("Init failed: %s", e, exc_info=True)
            raise

    def _init_managers(self) -> None:
        self.layout_manager  = WidgetLayoutManager(self)
        self.theme_manager   = WidgetThemeManager(self)
        self.startup_manager = StartupManager()
        if not self.current_metrics:
            self.layout_manager.init_font()
        taskbar_info = get_taskbar_info()
        window_state = WindowState(
            config=self.config,
            widget=self,
            taskbar_info=taskbar_info,
            font_metrics=self.current_metrics,
        )
        self.position_manager = PositionManager(window_state, parent=self)

    def _init_ui_components(self) -> None:
        self.tray_manager = TrayIconManager(self, self.i18n)
        self.tray_manager.initialize()
        self.input_handler = InputHandler(
            widget=self,
            position_manager=self.position_manager,
            tray_manager=self.tray_manager,
        )
        self.system_event_handler = SystemEventHandler(self)

    def _init_core_components(self) -> None:
        self.widget_state  = WidgetState(self.config)
        cfg_rate = float(self.config.get("update_rate", constants.config.defaults.DEFAULT_UPDATE_RATE))
        effective_interval = max(
            constants.config.defaults.MINIMUM_UPDATE_RATE,
            min(cfg_rate, constants.timers.MAXIMUM_UPDATE_RATE_SECONDS),
        )
        thread_cfg = _strip_config(self.config)
        self.monitor_thread = StatsMonitorThread(interval=effective_interval, config=thread_cfg)
        self.controller = StatsController(config=self.config, widget_state=self.widget_state)
        self.controller.set_view(self)
        self._state_watcher_timer = QTimer(self)

    def _setup_connections(self) -> None:
        self.monitor_thread.stats_ready.connect(self.controller.handle_stats)
        self.controller.display_speed_updated.connect(self.update_display_speeds)
        self.monitor_thread.start()
        self.system_event_handler.foreground_app_changed.connect(self._execute_refresh)
        self.system_event_handler.taskbar_changed.connect(self.update_position)
        self.system_event_handler.theme_changed.connect(self._on_theme_changed)
        self.system_event_handler.immediate_hide_requested.connect(lambda: self.setVisible(False))
        self.system_event_handler.start()
        self._refresh_cached_layout_mode()

    def _setup_timers(self) -> None:
        self.position_manager.start_monitoring()
        self._state_watcher_timer.setInterval(constants.timeouts.STATE_WATCHER_INTERVAL_MS)
        self._state_watcher_timer.timeout.connect(self._execute_refresh)
        self._state_watcher_timer.start()

    def update_display_speeds(self, upload_mbps: float, download_mbps: float) -> None:
        mb  = constants.network.units.MEGA_DIVISOR
        bpb = constants.network.units.BITS_PER_BYTE
        self.upload_speed   = (upload_mbps   * mb) / bpb
        self.download_speed = (download_mbps * mb) / bpb
        self.renderer.push_history(self.upload_speed, self.download_speed)
        self.update()

    # --- No-op stubs: hardware signals wired by the legacy controller but unused here ---
    def update_cpu_usage(self, v):    pass
    def update_gpu_usage(self, v):    pass
    def update_cpu_temp(self, v):     pass
    def update_gpu_temp(self, v):     pass
    def update_cpu_power(self, v):    pass
    def update_gpu_power(self, v):    pass
    def update_ram_info(self, u, t):  pass
    def update_vram_info(self, u, t): pass

    def paintEvent(self, event: QPaintEvent) -> None:
        if not self.isVisible():
            return
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), QColor(0, 0, 0, 1))
            self.renderer.draw(
                painter, self.width(), self.height(),
                self.upload_speed, self.download_speed,
            )
        finally:
            if painter.isActive():
                painter.end()

    def show_settings(self) -> None:
        from netspeedtray.views.speed_settings import SpeedSettingsDialog
        if self.settings_dialog is None or not self.settings_dialog.isVisible():
            self.settings_dialog = SpeedSettingsDialog(
                main_widget=self,
                config=self.config.copy(),
                available_interfaces=self.get_unified_interface_list(),
                is_startup_enabled=self.is_startup_enabled(),
            )
            self.settings_dialog.settings_changed.connect(
                lambda cfg: self.handle_settings_changed(cfg, save_to_disk=False)
            )
            self.settings_dialog.show()
        else:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.tray_manager:
            self.tray_manager.show_context_menu()
        event.accept()

    def apply_all_settings(self) -> None:
        self.config_controller.apply_all_settings()

    def handle_settings_changed(self, updated_config: Dict[str, Any], save_to_disk: bool = True) -> None:
        safe = _strip_config(updated_config)
        self.config_controller.handle_settings_changed(safe, save_to_disk)
        self.renderer.update_config(safe)
        self.layout_manager.resize_widget_for_font()
        self.update()

    def update_config(self, updates: Dict[str, Any], save_to_disk: bool = True) -> None:
        self.config_controller.update_config(updates, save_to_disk)

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy() if self.config else {}

    def is_startup_enabled(self, force_check: bool = False) -> bool:
        return self.startup_manager.is_startup_enabled(force_check)

    def toggle_startup(self, enable: bool) -> None:
        self.startup_manager.toggle_startup(enable)
        self.update_config({"start_with_windows": enable})

    def _synchronize_startup_task(self) -> None:
        self.startup_manager.synchronize_startup_task(self.config.get("start_with_windows", False))

    def update_position(self) -> None:
        self._refresh_cached_layout_mode()
        if self.position_manager:
            self.position_manager.update_position()

    def reset_to_default_position(self) -> None:
        self.position_manager.reset_to_default()
        self.update_config({"position_x": None, "position_y": None})

    def get_widget_size(self) -> QSize:
        return self.size()

    def _refresh_cached_layout_mode(self) -> None:
        try:
            taskbar_info = get_taskbar_info()
            edge = taskbar_info.get_edge_position()
            self._cached_layout_mode = (
                "horizontal"
                if edge in (constants.TaskbarEdge.LEFT, constants.TaskbarEdge.RIGHT)
                else "vertical"
            )
        except Exception:
            pass

    def _on_display_changed(self) -> None:
        self.position_manager.update_position()
        self._ensure_win32_topmost()

    def _ensure_win32_topmost(self) -> None:
        self.position_manager.ensure_topmost()

    def get_unified_interface_list(self) -> List[str]:
        if not self.controller or not self.widget_state:
            return []
        live = set(self.controller.get_available_interfaces())
        hist = set(self.widget_state.get_distinct_interfaces())
        return sorted(list(live | hist))

    def get_active_interfaces(self) -> List[str]:
        return self.controller.get_active_interfaces() if self.controller else []

    def _execute_refresh(self, hwnd: int = 0) -> None:
        if self._is_context_menu_visible or self._dragging:
            return
        try:
            taskbar_info = get_taskbar_info()
            if taskbar_info.hwnd == 0:
                self._taskbar_lost_count += 1
            else:
                self._taskbar_lost_count = 0

            if hwnd == 0:
                hwnd = win32gui.GetForegroundWindow()
            keep_visible = self.config.get("keep_visible_fullscreen", False)
            should_be_visible = is_taskbar_visible(taskbar_info) and (
                keep_visible or not is_taskbar_obstructed(taskbar_info, hwnd)
            )

            if self.isVisible() != should_be_visible:
                self.setVisible(should_be_visible)
            if self.isVisible():
                if not self.config.get("free_move", False):
                    self.position_manager.update_position(fresh_taskbar_info=taskbar_info)
                self._ensure_win32_topmost()
        except Exception:
            pass

    def _delayed_initial_show(self) -> None:
        self._execute_refresh()

    def _on_theme_changed(self) -> None:
        self.theme_manager.on_theme_changed()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.input_handler:
            self.input_handler.handle_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.input_handler:
            self.input_handler.handle_mouse_move(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if self.input_handler:
            self.input_handler.handle_mouse_release(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if self.input_handler:
            self.input_handler.handle_double_click(event)

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)

    def hideEvent(self, event: QHideEvent) -> None:
        super().hideEvent(event)

    def fully_exit_application(self) -> None:
        self._will_quit_app = True
        self.close()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._will_quit_app:
            self.cleanup()
            event.accept()
            app = QApplication.instance()
            if app:
                app.quit()
        else:
            self.setVisible(False)
            event.ignore()

    def cleanup(self) -> None:
        if hasattr(self, "system_event_handler") and self.system_event_handler:
            self.system_event_handler.stop()
        if self.position_manager:
            self.position_manager.stop_monitoring()
        if self._state_watcher_timer.isActive():
            self._state_watcher_timer.stop()
        if hasattr(self, "monitor_thread") and self.monitor_thread:
            self.monitor_thread.stop()
        if self.widget_state:
            self.widget_state.cleanup()

        if self.config.get("free_move", False) or self.config.get("lock_position", False):
            pos = self.pos()
            self.update_config({"position_x": pos.x(), "position_y": pos.y()}, save_to_disk=False)
        else:
            self.update_config({"position_x": None, "position_y": None}, save_to_disk=False)

        self.config_manager.save(self.config)

    # --- Dead stubs retained so the legacy controller/tray can call them without error ---
    def open_graph_window(self) -> None:         pass
    def open_app_activity_window(self) -> None:  pass
    def show_support_dialog(self) -> None:       pass
    def check_for_updates(self) -> None:         pass
    def update_retention_period(self, days: int) -> None: pass
    def pause(self) -> None:   self.is_paused = True
    def resume(self) -> None:  self.is_paused = False