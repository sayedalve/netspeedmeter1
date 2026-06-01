"""
SpeedRenderer — minimal, focused renderer for upload/download speeds only.
Replaces the bloated WidgetRenderer for the focused internet speed meter.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen

from speed_core.constants.fonts import fonts

logger = logging.getLogger("InternetSpeedMeter.SpeedRenderer")

UNIT_DIVISORS = {
    "bits_decimal":  {"mb": 1_000_000, "kb": 1_000,  "label_mb": "Mbps", "label_kb": "Kbps", "label_b": "bps"},
    "bits_binary":   {"mb": 1_048_576, "kb": 1_024,  "label_mb": "Mibps","label_kb": "Kibps","label_b": "bps"},
    "bytes_decimal": {"mb": 1_000_000, "kb": 1_000,  "label_mb": "MB/s", "label_kb": "KB/s", "label_b": "B/s"},
    "bytes_binary":  {"mb": 1_048_576, "kb": 1_024,  "label_mb": "MiB/s","label_kb": "KiB/s","label_b": "B/s"},
}

# Red & Black theme palette (mirrors constants/color.py Batch 1 values)
_RED_PRIMARY = "#E53935"

@dataclass
class SpeedRenderConfig:
    unit_type: str = "bits_decimal"
    default_color: str = _RED_PRIMARY
    font_family: str = "Segoe UI"
    font_size: int = 9
    font_weight: int = 400
    decimal_places: int = 1
    swap_upload_download: bool = False
    color_coding: bool = False
    high_speed_threshold: float = 10.0
    low_speed_threshold: float = 1.0
    high_speed_color: str = "#FF1744"
    low_speed_color: str = "#B71C1C"
    background_color: str = "#000000"
    background_opacity: float = 0.0
    graph_enabled: bool = False
    graph_opacity: float = 0.66
    history_minutes: int = 3
    update_rate: float = 1.0

    @classmethod
    def from_dict(cls, cfg: Dict[str, Any]) -> "SpeedRenderConfig":
        raw_bg_opacity = cfg.get("background_opacity", 0)
        raw_graph_opacity = cfg.get("graph_opacity", 66)
        return cls(
            unit_type=str(cfg.get("unit_type", "bits_decimal")),
            default_color=str(cfg.get("default_color", _RED_PRIMARY)),
            font_family=str(cfg.get("font_family", "Segoe UI")),
            font_size=int(cfg.get("font_size", 9)),
            font_weight=int(cfg.get("font_weight", 400)),
            decimal_places=int(cfg.get("decimal_places", 1)),
            swap_upload_download=bool(cfg.get("swap_upload_download", False)),
            color_coding=bool(cfg.get("color_coding", False)),
            high_speed_threshold=float(cfg.get("high_speed_threshold", 10.0)),
            low_speed_threshold=float(cfg.get("low_speed_threshold", 1.0)),
            high_speed_color=str(cfg.get("high_speed_color", "#FF1744")),
            low_speed_color=str(cfg.get("low_speed_color", "#B71C1C")),
            background_color=str(cfg.get("background_color", "#000000")),
            background_opacity=max(0.0, min(1.0, float(raw_bg_opacity) / 100.0)),
            graph_enabled=bool(cfg.get("graph_enabled", False)),
            graph_opacity=max(0.0, min(1.0, float(raw_graph_opacity) / 100.0)),
            history_minutes=int(cfg.get("history_minutes", 3)),
            update_rate=max(0.1, float(cfg.get("update_rate", 1.0))),
        )

def _format_speed_value(bytes_per_sec: float, unit_type: str, decimal_places: int) -> tuple[str, str]:
    """Returns (value_str, unit_label) for the given bytes/sec."""
    spec = UNIT_DIVISORS.get(unit_type, UNIT_DIVISORS["bits_decimal"])
    is_bits = unit_type.startswith("bits")
    speed = bytes_per_sec * 8 if is_bits else bytes_per_sec

    # Always floor to KB/s (or Kbps) to eliminate the B/s bouncing bug
    if speed >= spec["mb"]:
        val = speed / spec["mb"]
        label = spec["label_mb"]
    else:
        val = speed / spec["kb"]
        label = spec["label_kb"]

    fmt = f"{val:.{decimal_places}f}"
    return fmt, label

class SpeedRenderer:
    """
    Renders only upload and download speeds on the taskbar widget.
    Two compact rows: ↑ upload  and  ↓ download.
    """

    UP_ARROW = "↑"
    DOWN_ARROW = "↓"

    def __init__(self, config: Dict[str, Any]) -> None:
        self.logger = logger
        self.cfg = SpeedRenderConfig.from_dict(config)
        self._build_fonts()
        self._speed_history: List[float] = []
        self._max_samples: int = max(60, int((self.cfg.history_minutes * 60) / max(self.cfg.update_rate, 0.1)))

    def update_config(self, config: Dict[str, Any]) -> None:
        self.cfg = SpeedRenderConfig.from_dict(config)
        self._build_fonts()
        self._max_samples = max(60, int((self.cfg.history_minutes * 60) / max(self.cfg.update_rate, 0.1)))

    def push_history(self, upload_bytes: float, download_bytes: float) -> None:
        self._speed_history.append(upload_bytes + download_bytes)
        if len(self._speed_history) > self._max_samples:
            self._speed_history = self._speed_history[-self._max_samples:]

    def preferred_size(self) -> tuple[int, int]:
        sample_up,   _ = _format_speed_value(12_345_678, self.cfg.unit_type, self.cfg.decimal_places)
        sample_down, _ = _format_speed_value(12_345_678, self.cfg.unit_type, self.cfg.decimal_places)
        arrow_w = self._arrow_metrics.horizontalAdvance(self.UP_ARROW)
        
        # Calculate width using our new specific font sizes
        val_w   = max(
            self._speed_metrics.horizontalAdvance(sample_up),
            self._speed_metrics.horizontalAdvance(sample_down),
        )
        unit_w  = self._unit_metrics.horizontalAdvance("Mbps")
        
        total_w = arrow_w + 3 + val_w + 3 + unit_w + 8
        row_h   = self._speed_metrics.height() + 1
        total_h = row_h * 2 + 2
        return total_w, total_h

    def draw(
        self,
        painter: QPainter,
        width: int,
        height: int,
        upload_bytes: float,
        download_bytes: float,
    ) -> None:
        cfg = self.cfg

        if cfg.background_opacity > 0.005:
            bg = QColor(cfg.background_color)
            bg.setAlphaF(cfg.background_opacity)
            painter.fillRect(0, 0, width, height, bg)

        if cfg.graph_enabled and len(self._speed_history) >= 2:
            self._draw_graph(painter, width, height)

        if cfg.swap_upload_download:
            top_bytes, bot_bytes = download_bytes, upload_bytes
            top_arrow, bot_arrow = self.DOWN_ARROW, self.UP_ARROW
        else:
            top_bytes, bot_bytes = upload_bytes, download_bytes
            top_arrow, bot_arrow = self.UP_ARROW, self.DOWN_ARROW

        row_h = self._speed_metrics.height()
        line_spacing = -1  
        total_block_h = (row_h * 2) + line_spacing
        
        start_y = (height - total_block_h) // 2
        
        top_baseline = start_y + self._speed_metrics.ascent()
        bot_baseline = top_baseline + row_h + line_spacing

        self._draw_row_at(painter, width, top_baseline, top_arrow, top_bytes, not cfg.swap_upload_download)
        self._draw_row_at(painter, width, bot_baseline, bot_arrow, bot_bytes, cfg.swap_upload_download)

    def _build_fonts(self) -> None:
        """Construct distinct fonts for numbers, units, and arrows from central constants."""
        cfg = self.cfg
        
        # 1. Main Speed Values Font
        self._speed_font = QFont(cfg.font_family, fonts.SIZE_SPEED_LARGE, cfg.font_weight)
        self._speed_metrics = QFontMetrics(self._speed_font)
        
        # 2. Units Font (Smaller, normal weight)
        self._unit_font = QFont(cfg.font_family, fonts.SIZE_UNIT_MEDIUM, fonts.WEIGHT_NORMAL)
        self._unit_metrics = QFontMetrics(self._unit_font)
        
        # 3. Arrow Font
        arrow_weight = min(cfg.font_weight + 200, 900)
        self._arrow_font = QFont(cfg.font_family, fonts.SIZE_ARROW, arrow_weight)
        self._arrow_metrics = QFontMetrics(self._arrow_font)

    def _speed_color(self, bytes_per_sec: float, is_upload: bool) -> QColor:
        cfg = self.cfg
        if not cfg.color_coding:
            return QColor(cfg.default_color)
        is_bits = cfg.unit_type.startswith("bits")
        speed_mbps = (bytes_per_sec * 8 if is_bits else bytes_per_sec) / 1_000_000
        if speed_mbps >= cfg.high_speed_threshold:
            return QColor(cfg.high_speed_color)
        elif speed_mbps >= cfg.low_speed_threshold:
            return QColor(cfg.default_color)
        else:
            return QColor(cfg.low_speed_color)

    def _draw_row_at(
        self,
        painter: QPainter,
        widget_w: int,
        baseline_y: int,
        arrow: str,
        bytes_per_sec: float,
        is_upload: bool,
    ) -> None:
        cfg = self.cfg
        val_str, unit_str = _format_speed_value(bytes_per_sec, cfg.unit_type, cfg.decimal_places)
        
        # Upload arrow gets the Red theme color, Download arrow gets forced to Green
        if is_upload:
            arrow_color = self._speed_color(bytes_per_sec, is_upload)
        else:
            arrow_color = QColor("#4ade80") # Bright, modern green
            
        # Text and Units stay pure white for readability
        text_color = QColor("#FFFFFF")

        arrow_w = self._arrow_metrics.horizontalAdvance(arrow)
        val_w   = self._speed_metrics.horizontalAdvance(val_str)
        unit_w  = self._unit_metrics.horizontalAdvance(unit_str)

        gap      = 3
        total_w  = arrow_w + gap + val_w + gap + unit_w
        x_start  = (widget_w - total_w) // 2
        
        # 1. Draw Arrow (Red for Up, Green for Down)
        painter.setPen(arrow_color)
        painter.setFont(self._arrow_font)
        painter.drawText(x_start, baseline_y, arrow)

        # 2. Draw Value (White, Custom Size)
        painter.setPen(text_color)
        painter.setFont(self._speed_font)
        painter.drawText(x_start + arrow_w + gap, baseline_y, val_str)

        # 3. Draw Units (White, Custom Size)
        painter.setFont(self._unit_font)
        painter.drawText(x_start + arrow_w + gap + val_w + gap, baseline_y, unit_str)

    def _draw_graph(self, painter: QPainter, width: int, height: int) -> None:
        history = self._speed_history
        if len(history) < 2:
            return

        peak = max(history) or 1.0
        pts  = len(history)

        path = QPainterPath()
        path.moveTo(0, height)

        for i, val in enumerate(history):
            x = i / (pts - 1) * width
            y = height - (val / peak) * height * 0.85
            if i == 0:
                path.lineTo(x, y)
            else:
                path.lineTo(x, y)

        path.lineTo(width, height)
        path.closeSubpath()

        # Red fill: use the configured color (red by default) with dampened alpha
        fill_color = QColor(self.cfg.default_color)
        fill_color.setAlphaF(self.cfg.graph_opacity * 0.35)
        painter.fillPath(path, fill_color)

        # Red line: slightly more opaque than the fill
        line_color = QColor(self.cfg.default_color)
        line_color.setAlphaF(self.cfg.graph_opacity * 0.75)
        pen = QPen(line_color)
        pen.setWidthF(1.0)
        painter.setPen(pen)

        line_path = QPainterPath()
        for i, val in enumerate(history):
            x = i / (pts - 1) * width
            y = height - (val / peak) * height * 0.85
            if i == 0:
                line_path.moveTo(x, y)
            else:
                line_path.lineTo(x, y)
        painter.drawPath(line_path)

    def get_last_text_rect(self) -> QRect:
        """Dummy rect to satisfy the legacy tray manager right-click menu positioning."""
        return QRect(0, 0, 50, 20)