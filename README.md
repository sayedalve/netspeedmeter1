# NetSpeedMeter

A lightweight, dedicated **internet speed meter** for the Windows taskbar.

Displays live **↑ upload** and **↓ download** speeds — nothing else.

---

## What changed from speed_core

This is a focused rebuild of the `netspeedmeter1` project.  
The following were **removed**:

| Removed feature | Reason |
|---|---|
| CPU / GPU utilization monitoring | Out of scope |
| RAM / VRAM monitoring | Out of scope |
| CPU / GPU temperature & power | Out of scope |
| Per-app network activity window | Out of scope |
| History graph window (matplotlib) | Removed; use mini-graph overlay instead |
| Widget cycling / side-by-side hardware layout | Out of scope |
| Localization (9 languages) | Kept minimal EN strings for now |
| LibreHardwareMonitor integration | Out of scope |
| RDP session detection for GPU | Out of scope |
| Update checker | Can be re-added later |

The following were **kept and refined**:

| Feature | Notes |
|---|---|
| ↑ Upload / ↓ Download live speeds | Core feature |
| Network adapter selection | Auto / All Physical / All / Specific |
| Speed units | Kbps / Mbps / KB/s / MB/s (decimal & binary) |
| Mini-graph overlay | Background area chart, configurable opacity |
| Startup with Windows | Registry Run key |
| Widget position | Free move, lock position, tray offset |
| Color coding | Speed thresholds → green/orange |
| Auto-theme | Follows Windows light/dark |

---

## Running from source

```bash
# 1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies (much lighter than original)
pip install -r requirements-speedmeter.in

# 3. Run
python src/speedmeter.py
```

> **Note:** The original `monitor.py` entry point still works unchanged.  
> The new entry point is `src/speedmeter.py`.

---

## Building an executable

```bat
pyinstaller build\netspeedmeter.spec
```

The output will be in `dist\NetSpeedMeter\`.

---

## File overview

```
src/
  speedmeter.py                          ← NEW entry point
  speed_core/
    views/
      speed_widget.py                    ← NEW main widget (NetSpeedMeterWidget)
      speed_settings.py                  ← NEW lean settings dialog
      widget/                            ← UNCHANGED (layout, theme, position)
    utils/
      speed_renderer.py                  ← NEW focused renderer (↑↓ only)
    core/                                ← UNCHANGED (monitor thread, controller, etc.)
    constants/                           ← UNCHANGED
```

---

## Settings

Right-click the taskbar widget → Settings.

| Tab | Settings |
|---|---|
| **General** | Update rate, startup, free move, lock position, tray offset |
| **Network** | Adapter selection, speed units, decimal places, swap ↑↓ |
| **Appearance** | Mini-graph toggle/opacity/history, background opacity |

---

## License

GNU GPL v3.0 — same as the upstream project.
