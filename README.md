# 🚀 NR Launcher GUI

A graphical launcher for Nimble Recorder device initialization, now upgraded into a **real-time device monitoring system** with embedded launcher logic, built using Python + Tkinter + PyInstaller.

---

## 🖥 Features

- Graphical launcher for Windows
- Real-time device scan (every 5 seconds)
- Auto-detects ADB-connected VX + VS devices
- Auto-launches Nimble Recorder once both are connected
- Status label updates live in GUI
- Embedded logic from `START_NR - MACKV2_1.bat`
- Executes `startNimbleRecorderUnified.bat`
- Packaged as a single `.exe` via GitHub Actions
- Auto-tagged GitHub Releases (e.g., `v1.0.1`, `v1.0.2`, ...)

---

## 🧪 Usage

1. Download the latest `.exe` from the [Releases](../../releases/latest)
2. Double-click to launch
3. GUI instantly begins scanning & launching if valid devices found
4. Manual controls:
   - 🔍 Scan Devices
   - 🚀 Start Launcher
   - ❌ Exit

---

## 📦 Building Locally (Optional)

> Requires Python 3.10+ and [PyInstaller](https://www.pyinstaller.org/)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed launcher_gui.py
```

Output will be in `dist/launcher_gui.exe`

---

## 🔄 Auto Build & Tag via GitHub Actions

Every push to `main` triggers:

- PyInstaller build
- Auto-incremented GitHub Release
- `.exe` + `.zip` uploaded with tag `v1.0.<run_number>`

### 🧙‍♂️ Example Workflow:

```yaml
- name: 🚀 Auto-tag Release Build
  uses: softprops/action-gh-release@v1
  with:
    tag_name: v1.0.${{ github.run_number }}
    name: NR Launcher Build ${{ github.run_number }}
    files: "launcher.zip\nlauncher_gui.exe"
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 📁 Folder Structure

```
📦 nr-launcher
├── launcher_gui.py         # Frontend GUI (Tkinter)
├── launcher_core.py        # Backend: device scan & NR logic
├── requirements.txt
└── .github/
    └── workflows/
        └── build.yml
```

---

## 🛠 Maintainers
Built by 🧙 **Grimoire** in service of your NR Launcher quests.
