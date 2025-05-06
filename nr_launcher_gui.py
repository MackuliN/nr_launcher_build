
import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import tempfile

BATCH_CONTENT = r"""@echo off
setlocal enabledelayedexpansion
set "POPUP_TITLE=Device Check"
set "POPUP_VBS=%TEMP%\popup.vbs"
set "EXPECTED_VX=1"
set "EXPECTED_VS=1"
echo msg = WScript.Arguments.Item(0) > "%POPUP_VBS%"
echo title = WScript.Arguments.Item(1) >> "%POPUP_VBS%"
echo style = CInt(WScript.Arguments.Item(2)) >> "%POPUP_VBS%"
echo result = MsgBox(msg, style, title) >> "%POPUP_VBS%"
echo If result = 2 Then WScript.Quit(1) >> "%POPUP_VBS%"
if not exist "%POPUP_VBS%" (
    echo Failed to create popup.vbs at %%POPUP_VBS%%
    pause
    exit /b
)
:CHECK_DEVICES
cscript //nologo "%POPUP_VBS%" "Scanning for devices. Make sure only one VX and one VS device are connected." "%POPUP_TITLE%" 64
set "VX_SERIAL="
set "VS_SERIAL="
set VX_COUNT=0
set VS_COUNT=0
set OTHER_COUNT=0
for /f "skip=1 tokens=1,2" %%A in ('adb devices') do (
    set "serial=%%A"
    set "status=%%B"
    if "!status!"=="device" (
        if /i "!serial:~0,2!"=="VX" (
            set /a VX_COUNT+=1
            set "VX_SERIAL=!serial!"
        ) else if /i "!serial:~0,2!"=="VS" (
            set /a VS_COUNT+=1
            set "VS_SERIAL=!serial!"
        ) else (
            set /a OTHER_COUNT+=1
        )
    )
)
if not !VX_COUNT! EQU %%EXPECTED_VX%% (
    cscript //nologo "%POPUP_VBS%" "Expected %%EXPECTED_VX%% VX device(s), found !VX_COUNT!. Retry or Cancel?" "VX Device Error" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto CHECK_DEVICES
)
if not !VS_COUNT! EQU %%EXPECTED_VS%% (
    cscript //nologo "%POPUP_VBS%" "Expected %%EXPECTED_VS%% VS device(s), found !VS_COUNT!. Retry or Cancel?" "VS Device Error" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto CHECK_DEVICES
)
if !OTHER_COUNT! GTR 0 (
    cscript //nologo "%POPUP_VBS%" "Unexpected devices detected (!OTHER_COUNT!). Retry or Cancel?" "Extra Devices Warning" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto CHECK_DEVICES
)
cscript //nologo "%POPUP_VBS%" "Devices detected successfully. Proceeding with commands." "Success" 64
start /WAIT adb -s device:eureka shell am broadcast -a com.oculus.vrpowermanager.prox_close
start /WAIT adb -s device:eureka shell setprop persist.oculus.guardian_disable 1
call "C:\Users\rift\S2\NR\startNimbleRecorderUnified.bat"
:EXIT_CLEAN
if exist "%POPUP_VBS%" del "%POPUP_VBS%" >nul 2>&1
exit /b
"""

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("Nimble Recorder Launcher")
        root.geometry("400x250")
        root.resizable(False, False)
        tk.Label(root, text="NR Launcher GUI", font=("Arial", 16, "bold")).pack(pady=10)
        self.status = tk.StringVar()
        self.status.set("Idle. Ready to scan.")
        tk.Label(root, textvariable=self.status, fg="gray", font=("Arial", 10)).pack()
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="🔍 Scan Devices", width=15, command=self.scan_devices).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="🚀 Start Launcher", width=15, command=self.run_launcher).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="❌ Exit", width=15, command=self.root.quit).grid(row=2, column=0, padx=10)

    def scan_devices(self):
        self.status.set("Scanning for devices...")
        try:
            output = subprocess.check_output(["adb", "devices"], stderr=subprocess.STDOUT, text=True)
            lines = output.strip().splitlines()[1:]
            devices = [line.split()[0] for line in lines if "device" in line]
            self.status.set(f"Detected devices: {devices if devices else 'None'}")
            messagebox.showinfo("Device Scan", f"Found {len(devices)} device(s):\n{chr(10).join(devices) if devices else 'None'}")
        except subprocess.CalledProcessError as e:
            self.status.set("ADB error during scan")
            messagebox.showerror("Scan Failed", f"Error:\n{e.output}")

    def run_launcher(self):
        self.status.set("Writing launcher script...")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".bat", mode="w", encoding="utf-8") as f:
                f.write(BATCH_CONTENT)
                batch_path = f.name
            self.status.set("Launching NR script...")
            subprocess.call(["cmd.exe", "/c", batch_path])
            self.status.set("Launcher completed.")
        except Exception as e:
            self.status.set("Failed to launch")
            messagebox.showerror("Launcher Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
