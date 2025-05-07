# 🚀 NR Launcher GUI

A graphical launcher for Nimble Recorder device initialization, wrapped in a single `.exe` file using Python + Tkinter + PyInstaller.

---

## 🖥 Features

- Graphical launcher for Windows
- Detects and validates ADB-connected VX + VS devices
- Embeds `START_NR - MACKV2_1.bat` logic
- Executes `startNimbleRecorderUnified.bat`
- Packaged as a single `.exe` via GitHub Actions

---

## 🧪 Usage

1. Download the latest `.exe` from the [Releases](../../releases/latest)
2. Double-click to launch
3. Use GUI:
   - 🔍 Scan Devices
   - 🚀 Start Launcher
   - ❌ Exit

---

## 📦 Building Locally (Optional)

> Requires Python 3.10+ and [PyInstaller](https://www.pyinstaller.org/)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed nr_launcher_gui.py
```

Output will be in `dist/nr_launcher_gui.exe`

---

## 🔄 Auto Build via GitHub Actions

Every push to `main` triggers:

- PyInstaller build
- Auto-versioned GitHub Release
- `.exe` + `.zip` uploaded

### 🧙‍♂️ Example Workflow:

```yaml
- name: 🚀 Release Build
  uses: softprops/action-gh-release@v1
  with:
    tag_name: v1.0.${{ github.run_number }}
    name: NR Launcher Build ${{ github.run_number }}
    files: "launcher.zip\nnr_launcher_gui.exe"
```

---

## 📁 Folder Structure

```
📦 nr-launcher
├── nr_launcher_gui.py
├── requirements.txt
└── .github/
    └── workflows/
        └── build.yml
```

---

## 🛠 Maintainers
Built by 🧙 **Grimoire** in service of your NR Launcher quests.
