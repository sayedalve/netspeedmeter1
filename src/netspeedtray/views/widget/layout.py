import logging
import math
from typing import TYPE_CHECKING, Dict, Any, Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QWidget

from netspeedtray import constants
from netspeedtray.utils.taskbar_utils import is_small_taskbar, get_taskbar_info

if TYPE_CHECKING:
    from netspeedtray.views.widget.main import NetworkSpeedWidget

class WidgetLayoutManager:
    """
    Manages layout, font, and window properties for the NetworkSpeedWidget.
    Extracts sizing and property logic from the main widget class.
    """

    def __init__(self, widget: "NetworkSpeedWidget"):
        self.widget = widget
        self.logger = logging.getLogger(f"{constants.app.APP_NAME}.LayoutManager")
        self.metrics: Optional[QFontMetrics] = None
        self.arrow_metrics: Optional[QFontMetrics] = None

    def setup_window_properties(self) -> None:
        """Set Qt window flags and attributes for proper Windows integration."""
        self.logger.debug("Setting window properties...")
        self.widget.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.widget.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.widget.setMouseTracking(True)
        self.logger.debug("Window properties set")

    def init_font(self) -> None:
        """Initialize the font and set initial widget size."""
        self.logger.debug("Initializing font...")
        self.set_font(resize=False)

    def set_font(self, resize: bool = True) -> None:
        """Apply font settings from config."""
        self.logger.debug("Setting font...")
        config = self.widget.config
        
        font_family = config.get("font_family", constants.config.defaults.DEFAULT_FONT_FAMILY)
        font_size = config.get("font_size", constants.config.defaults.DEFAULT_FONT_SIZE)
        font_weight_val = config.get("font_weight", constants.config.defaults.DEFAULT_FONT_WEIGHT)
        
        if isinstance(font_weight_val, int):
             font_weight = font_weight_val
        elif isinstance(font_weight_val, str):
            font_weight = {
                "normal": QFont.Weight.Normal, 
                "bold": QFont.Weight.Bold
            }.get(font_weight_val.lower(), QFont.Weight.Normal)
        else:
            font_weight = QFont.Weight.Normal

        font = QFont(font_family, font_size, font_weight)
        self.widget.setFont(font)
        self.widget.current_font = font 
        
        self.metrics = QFontMetrics(font)
        self.widget.current_metrics = self.metrics 
        
        # Arrow font handling
        if config.get("use_separate_arrow_font", False):
            arrow_family = config.get("arrow_font_family", font_family)
            arrow_size = config.get("arrow_font_size", font_size)
            arrow_weight_raw = config.get("arrow_font_weight", font_weight_val)
            
            if isinstance(arrow_weight_raw, int):
                arrow_weight = arrow_weight_raw
            else:
                arrow_weight = {
                    "normal": QFont.Weight.Normal, 
                    "bold": QFont.Weight.Bold
                }.get(str(arrow_weight_raw).lower(), QFont.Weight.Normal)
                
            arrow_font = QFont(arrow_family, arrow_size, arrow_weight)
        else:
            arrow_font = font
            
        self.arrow_metrics = QFontMetrics(arrow_font)
        
        self.logger.debug(f"Font set: {font_family}, {font_size}px, Weight: {font_weight}")
        
        if resize:
            self.resize_widget_for_font()

    def resize_widget_for_font(self) -> None:
        """Calculates and sets the widget's fixed dimensions."""
        self.logger.debug("Resizing widget based on layout...")
        if not self.metrics:
            raise RuntimeError("FontMetrics not initialized.")
        if not hasattr(self.widget, 'renderer'):
            raise RuntimeError("Renderer not initialized before resizing.")

        try:
            taskbar_info = get_taskbar_info()
            edge = taskbar_info.get_edge_position()
            is_horizontal = edge in (constants.TaskbarEdge.TOP, constants.TaskbarEdge.BOTTOM)
            dpi_scale = taskbar_info.dpi_scale if taskbar_info.dpi_scale > 0 else 1.0
            
            is_small = is_small_taskbar(taskbar_info)
            self.logger.debug(f"Taskbar edge: {edge}, Small: {is_small}")

            precision = self.widget.config.get("decimal_places", constants.config.defaults.DEFAULT_DECIMAL_PLACES)
            margin = 4  # Replaced constants.renderer.TEXT_MARGIN
            hide_arrows = self.widget.config.get("hide_arrows", False)
            hide_units = self.widget.config.get("hide_unit_suffix", False)
            short_labels = self.widget.config.get("short_unit_labels", constants.config.defaults.DEFAULT_SHORT_UNIT_LABELS)
            
            if is_horizontal:
                # --- HORIZONTAL TASKBAR (TOP/BOTTOM) ---
                if is_small:
                    unit_type = self.widget.config.get("unit_type", constants.config.defaults.DEFAULT_UNIT_TYPE)
                    always_mbps = self.widget.config.get("speed_display_mode", constants.config.defaults.DEFAULT_SPEED_DISPLAY_MODE) == "always_mbps"

                    from netspeedtray.utils.helpers import get_reference_value_string, get_unit_labels_for_type
                    ref_val_str = get_reference_value_string(always_mbps, precision, unit_type)
                    unit_labels = get_unit_labels_for_type(self.widget.i18n, unit_type, short_labels)
                    ref_unit = unit_labels[2]

                    def get_part_width(arrow_char, val, unit):
                        w = 0
                        if not hide_arrows:
                            w += self.arrow_metrics.horizontalAdvance(arrow_char) + self.arrow_metrics.horizontalAdvance(" ")
                        w += self.metrics.horizontalAdvance(val)
                        if not hide_units:
                            w += self.metrics.horizontalAdvance(" ") + self.metrics.horizontalAdvance(unit)
                        return w

                    up_width = get_part_width(self.widget.i18n.UPLOAD_ARROW, ref_val_str, ref_unit)
                    down_width = get_part_width(self.widget.i18n.DOWNLOAD_ARROW, ref_val_str, ref_unit)
                    sep_width = self.metrics.horizontalAdvance(constants.layout.HORIZONTAL_LAYOUT_SEPARATOR)

                    calculated_width = up_width + sep_width + down_width + (margin * 2)
                else:
                    always_mbps = self.widget.config.get("speed_display_mode", constants.config.defaults.DEFAULT_SPEED_DISPLAY_MODE) == "always_mbps"
                    
                    from netspeedtray.utils.helpers import get_all_possible_unit_labels, get_reference_value_string

                    unit_type = self.widget.config.get("unit_type", constants.config.defaults.DEFAULT_UNIT_TYPE)
                    ref_str = get_reference_value_string(always_mbps, precision, unit_type)
                    max_number_width = self.metrics.horizontalAdvance(ref_str)

                    possible_units = get_all_possible_unit_labels(self.widget.i18n, short_labels=short_labels)
                    max_unit_width = max(self.metrics.horizontalAdvance(unit) for unit in possible_units) if not hide_units else 0
                    
                    arrow_width = self.metrics.horizontalAdvance(self.widget.i18n.UPLOAD_ARROW) if not hide_arrows else 0
                    arrow_gap = 3 if not hide_arrows else 0  # Replaced constants.renderer.ARROW_NUMBER_GAP
                    unit_gap = 3 if not hide_units else 0    # Replaced constants.renderer.VALUE_UNIT_GAP

                    calculated_width = (margin + arrow_width + arrow_gap +
                                        max_number_width + unit_gap +
                                        max_unit_width + margin)

                self._network_width = calculated_width

                # --- SIDE-BY-SIDE MODE ADJUSTMENT ---
                display_mode = self.widget.config.get("widget_display_mode", "network_only")
                monitor_ram = self.widget.config.get("monitor_ram_enabled", False)
                monitor_vram = self.widget.config.get("monitor_vram_enabled", False)
                if display_mode == "side_by_side":
                    active_segments = 0
                    monitor_cpu = self.widget.config.get("monitor_cpu_enabled", False)
                    monitor_gpu = self.widget.config.get("monitor_gpu_enabled", False)
                    stack_hw = self.widget.config.get("stack_hardware_stats", False)
                    
                    display_order = self.widget.config.get("widget_display_order", ["network", "cpu", "gpu"])
                    if "network" in display_order: active_segments += 1
                    
                    if stack_hw and monitor_cpu and monitor_gpu:
                        active_segments += 1
                    else:
                        if "cpu" in display_order and monitor_cpu: active_segments += 1
                        if "gpu" in display_order and monitor_gpu: active_segments += 1
                    
                    active_segments = max(1, active_segments)
                    
                    calculated_width_accum = 0
                    if "network" in display_order:
                        calculated_width_accum += calculated_width
                        
                    style = self.widget.config.get('hardware_label_style', 'icons_colored')
                    label_offset = self.metrics.horizontalAdvance("CPU ") if style == "text" else 14
                    show_temps = bool(self.widget.config.get("show_hardware_temps", False))
                    show_power = bool(self.widget.config.get("show_hardware_power", False))

                    if show_temps and show_power:
                        hw_suffix_width = self.metrics.horizontalAdvance(" (99°C, 250.0W)")
                    elif show_power:
                        hw_suffix_width = self.metrics.horizontalAdvance(" (250.0W)")
                    elif show_temps:
                        hw_suffix_width = self.metrics.horizontalAdvance(" (99°C)")
                    else:
                        hw_suffix_width = 0

                    cpu_width = 0
                    if "cpu" in display_order and monitor_cpu:
                        cpu_val = int(getattr(self.widget, 'cpu_usage', 0))
                        cpu_width = label_offset + self.metrics.horizontalAdvance(" 100%")
                        if hw_suffix_width:
                            cpu_width += hw_suffix_width
                        if monitor_ram and getattr(self.widget, 'ram_used', None) is not None:
                            used = getattr(self.widget, 'ram_used', 0)
                            total = getattr(self.widget, 'ram_total', -1.0)
                            mem_text = f"{used:.1f}/{total:.1f}G" if total and total > 0 else f"{used:.1f}G"
                            if stack_hw: 
                                cpu_width += self.metrics.horizontalAdvance(f" | {mem_text}")
                            else:
                                cpu_width = max(cpu_width, self.metrics.horizontalAdvance(mem_text))
                        cpu_width += margin 
                                
                    gpu_width = 0
                    if "gpu" in display_order and monitor_gpu:
                        gpu_val = int(getattr(self.widget, 'gpu_usage', 0))
                        gpu_width = label_offset + self.metrics.horizontalAdvance(" 100%")
                        if hw_suffix_width:
                            gpu_width += hw_suffix_width
                        if monitor_vram and getattr(self.widget, 'vram_used', None) is not None:
                            used = getattr(self.widget, 'vram_used', 0)
                            total = getattr(self.widget, 'vram_total', -1.0)
                            mem_text = f"{used:.1f}/{total:.1f}G" if total and total > 0 else f"{used:.1f}G"
                            if stack_hw:
                                gpu_width += self.metrics.horizontalAdvance(f" | {mem_text}")
                            else:
                                gpu_width = max(gpu_width, self.metrics.horizontalAdvance(mem_text))
                        gpu_width += margin
                            
                    if stack_hw and monitor_cpu and monitor_gpu:
                        calculated_width_accum += max(cpu_width, gpu_width)
                    else:
                        calculated_width_accum += cpu_width + gpu_width
                        
                    calculated_width_accum += margin 
                        
                    gaps = 0
                    if "network" in display_order and (monitor_cpu or monitor_gpu):
                        gaps += constants.layout.WIDGET_SEGMENT_GAP_AFTER_NETWORK_PX
                    if monitor_cpu and monitor_gpu and not stack_hw:
                        gaps += constants.layout.WIDGET_SEGMENT_GAP_BETWEEN_HARDWARE_PX
                    calculated_width = calculated_width_accum + gaps
                elif display_mode in ["cpu_only", "gpu_only", "combined"]:
                    calculated_width = 0
                    show_temps = bool(self.widget.config.get("show_hardware_temps", False))
                    show_power = bool(self.widget.config.get("show_hardware_power", False))
                    if show_temps and show_power:
                        hw_suffix_w = self.metrics.horizontalAdvance(" (99°C, 250.0W)")
                    elif show_power:
                        hw_suffix_w = self.metrics.horizontalAdvance(" (250.0W)")
                    elif show_temps:
                        hw_suffix_w = self.metrics.horizontalAdvance(" (99°C)")
                    else:
                        hw_suffix_w = 0

                    if display_mode in ["cpu_only", "combined"]:
                        cpu_width = label_offset + self.metrics.horizontalAdvance(" 100%")
                        if hw_suffix_w:
                            cpu_width += hw_suffix_w
                        if monitor_ram and getattr(self.widget, 'ram_used', None) is not None:
                            cpu_width += self.metrics.horizontalAdvance(" | 16.0/16.0G")
                        calculated_width = max(calculated_width, cpu_width)

                    if display_mode in ["gpu_only", "combined"]:
                        gpu_width = label_offset + self.metrics.horizontalAdvance(" 100%")
                        if hw_suffix_w:
                            gpu_width += hw_suffix_w
                        if monitor_vram and getattr(self.widget, 'vram_used', None) is not None:
                            gpu_width += self.metrics.horizontalAdvance(" | 16.0/16.0G")
                        calculated_width = max(calculated_width, gpu_width)
                
                screen = taskbar_info.get_screen()
                full_geom = screen.geometry()
                avail_geom = screen.availableGeometry()
                
                if edge == constants.TaskbarEdge.BOTTOM:
                    visible_tb_height = full_geom.bottom() - avail_geom.bottom()
                elif edge == constants.TaskbarEdge.TOP:
                    visible_tb_height = avail_geom.top() - full_geom.top()
                else:
                    visible_tb_height = (taskbar_info.rect[3] - taskbar_info.rect[1]) / dpi_scale

                calculated_height = visible_tb_height

            else:
                screen = taskbar_info.get_screen()
                full_geom = screen.geometry()
                avail_geom = screen.availableGeometry()
                
                if edge == constants.TaskbarEdge.RIGHT:
                    visible_tb_width = full_geom.right() - avail_geom.right()
                else: 
                    visible_tb_width = avail_geom.left() - full_geom.left()

                calculated_width = visible_tb_width
                calculated_height = self.metrics.height() * 2 + (margin * 4)

            final_width = max(calculated_width, 50) 
            final_height = max(calculated_height, 20)

            self.widget.setFixedSize(math.ceil(final_width), math.ceil(final_height))
            self.logger.debug(f"Widget resized to: {self.widget.width()}x{self.widget.height()}px")
            
            if hasattr(self.widget, 'update_position'):
                self.widget.update_position()

        except Exception as e:
            self.logger.error(f"Failed to resize widget: {e}", exc_info=True)
            self.widget.setFixedSize(150, 40)
            self.logger.warning("Applied fallback widget size: 150x40px")