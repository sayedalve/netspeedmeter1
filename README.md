# Internet Speed Meter

<p align="left">
  <strong>A hyper-focused, lightweight, and modern internet speed meter for the Windows taskbar.</strong>
</p>

Internet Speed Meter is a strictly dedicated network utility that displays live **Upload (↑)** and **Download (↓)** speeds directly on your taskbar. Built with Python and PyQt6, it is designed for users who want clean, accurate network monitoring without the bloat of heavy hardware tracking.

---

## 🙏 Acknowledgments

This project is a heavily refactored fork of the excellent NetSpeedTray originally created by **erez-c137**. While this version removes CPU, GPU, and RAM monitoring to focus exclusively on network speeds, the foundational PyQt6 architecture and Win32 taskbar integration were built upon their original work.

---

## ✨ Features

* **Pure Performance**
  Zero CPU, GPU, or RAM monitoring overhead. It does one thing and does it well.

* **Modern Aesthetic**
  Red and black dark mode styling with white values, a red upload arrow, and a green download arrow.

* **Typography Scaling**
  Fully customizable text sizes for numbers, units, and arrows directly from the settings UI.

* **Dynamic Mini Graph**
  Optional background area chart to visualize recent network history with configurable opacity.

* **Smart Positioning**
  Pin it to your taskbar, lock it in place, or enable Free Move to drag it anywhere on your screen.

* **Advanced Adapter Selection**
  Monitor your primary internet connection automatically, or explicitly select specific virtual or physical network adapters.

---

## 🚀 Getting Started

### Prerequisites

* Windows 10 or Windows 11
* Python 3.12+

### Running from Source

1. Clone the repository:

```bash
git clone https://github.com/sayedalve/netspeedmeter1.git
cd netspeedmeter1
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements-speedmeter.in
```

4. Launch the application:

```bash
python src/speedmeter.py
```

---

## 🔨 Building the Executable

To compile the project into a standalone Windows executable:

```bash
pyinstaller build\netspeedmeter.spec
```

The compiled executable will be available in:

```text
dist\NetSpeedMeter\
```

---

## ⚙️ Configuration

Right click the taskbar widget to access the Settings panel.

| Category       | Available Controls                                                                                                                    |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **General**    | Application startup behavior, polling interval, widget positioning, free move, lock position, tray offsets, and fullscreen visibility |
| **Network**    | Network adapter filtering, display units (Kbps, Mbps, KB/s, MB/s), decimal precision, and upload/download visual ordering             |
| **Appearance** | Typography scaling, mini graph options, history duration, and widget background opacity                                               |

---

## 🏗️ Architecture

This project is a streamlined and stabilized fork of NetSpeedTray. The core module (`speed_core`) has been refactored to remove heavy dependencies such as `matplotlib` and `pandas`, replacing them with a lightweight custom `QPainter` rendering engine.

```text
src/
├── speedmeter.py
└── speed_core/
    ├── constants/
    │   └── Centralized configuration and scaling settings
    ├── core/
    │   └── Background threads and single instance guards
    ├── utils/
    │   └── speed_renderer.py (Custom QPainter engine)
    └── views/
        ├── speed_widget.py
        └── speed_settings.py
```

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0), preserving the open source spirit of the upstream project.
