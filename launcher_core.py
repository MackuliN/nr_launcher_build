import subprocess
import tempfile
import os
import sys
import psutil
from datetime import datetime

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
set VX_COUNT=0
set VS_COUNT=0
set OTHER_COUNT=0
for /f "skip=1 tokens=1,2" %%A in ('adb devices') do (
    set "serial=%%A"
    set "status=%%B"
    if "!status!"=="device" (
        if /i "!serial:~0,2!"=="VX" (
            set /a VX_COUNT+=1
        ) else if /i "!serial:~0,2!"=="VS" (
            set /a VS_COUNT+=1
        ) else (
            set /a OTHER_COUNT+=1
        )
    )
)
if !VX_COUNT! EQU !EXPECTED_VX! if !VS_COUNT! EQU !EXPECTED_VS! goto SUCCESS
:SHOW_PROMPT
cscript //nologo "%POPUP_VBS%" "Scanning for devices. Make sure only one VX and one VS device are connected." "%POPUP_TITLE%" 64
set VX_COUNT=0
set VS_COUNT=0
set OTHER_COUNT=0
for /f "skip=1 tokens=1,2" %%A in ('adb devices') do (
    set "serial=%%A"
    set "status=%%B"
    if "!status!"=="device" (
        if /i "!serial:~0,2!"=="VX" (
            set /a VX_COUNT+=1
        ) else if /i "!serial:~0,2!"=="VS" (
            set /a VS_COUNT+=1
        ) else (
            set /a OTHER_COUNT+=1
        )
    )
)
if not !VX_COUNT! EQU !EXPECTED_VX! (
    cscript //nologo "%POPUP_VBS%" "Expected !EXPECTED_VX! VX device(s), found !VX_COUNT!. Retry or Cancel?" "VX Device Error" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto SHOW_PROMPT
)
if not !VS_COUNT! EQU !EXPECTED_VS! (
    cscript //nologo "%POPUP_VBS%" "Expected !EXPECTED_VS! VS device(s), found !VS_COUNT!. Retry or Cancel?" "VS Device Error" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto SHOW_PROMPT
)
if !OTHER_COUNT! GTR 0 (
    cscript //nologo "%POPUP_VBS%" "Unexpected devices detected (!OTHER_COUNT!). Retry or Cancel?" "Extra Devices Warning" 21
    if errorlevel 1 goto EXIT_CLEAN
    goto SHOW_PROMPT
)
:SUCCESS
start /WAIT adb -s device:eureka shell am broadcast -a com.oculus.vrpowermanager.prox_close
start /WAIT adb -s device:eureka shell setprop persist.oculus.guardian_disable 1
call "C:\Users\rift\S2\NR\startNimbleRecorderUnified.bat"
:EXIT_CLEAN
if exist "%POPUP_VBS%" del "%POPUP_VBS%" >nul 2>&1
exit /b
"""

def scan_devices():
    try:
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        output = subprocess.check_output(
            ["adb", "devices"],
            stderr=subprocess.STDOUT,
            text=True,
            startupinfo=startupinfo
        )
        lines = output.strip().splitlines()[1:]
        devices = [line.split()[0] for line in lines if "device" in line]
        return devices
    except subprocess.CalledProcessError:
        return []

def get_device_summary():
    devices = scan_devices()
    vx = [d for d in devices if d.startswith("VX")]
    vs = [d for d in devices if d.startswith("VS")]
    return {
        "VX": vx,
        "VS": vs,
        "All": devices
    }

def get_device_state():
    summary = get_device_summary()
    state = {
        "VX": {"devices": summary["VX"], "color": "black"},
        "VS": {"devices": summary["VS"], "color": "black"}
    }
    if summary["VX"] and summary["VS"]:
        state["VX"]["color"] = "green"
        state["VS"]["color"] = "green"
    elif not summary["VX"]:
        state["VX"]["color"] = "red"
    elif not summary["VS"]:
        state["VS"]["color"] = "red"
    return state

def launch_batch_script_with_tracking():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bat", mode="w", encoding="utf-8") as f:
        f.write(BATCH_CONTENT)
        batch_path = f.name

    proc = subprocess.Popen(["cmd.exe", "/c", batch_path])
    parent = psutil.Process(proc.pid)

    import time
    time.sleep(3)

    children = parent.children(recursive=True)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("nr_process_log.txt", "a", encoding="utf-8") as log:
        log.write(f"\n[{timestamp}] NR Launcher spawned processes:\n")
        for c in children:
            try:
                log.write(f"- {c.name()} (PID {c.pid})\n")
            except:
                continue

def check_adb_streaming():
    found_vx, found_vs = False, False
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'] and 'adb.exe' in proc.info['name'].lower():
            cmd = ' '.join(proc.info['cmdline']).lower()
            if 'nakasendo-streaming-server' in cmd:
                if 'vx' in cmd:
                    found_vx = True
                elif 'vs' in cmd:
                    found_vs = True
    return found_vx and found_vs

def check_rest_backend():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] and 'NimbleRecorderREST.exe' in proc.info['name']:
            return True
    return False

def is_nr_ready(timeout=10):
    import time
    start = time.time()
    while time.time() - start < timeout:
        if check_adb_streaming() and check_rest_backend():
            time.sleep(3)
            if check_adb_streaming() and check_rest_backend():
                return True
        time.sleep(1)
    return False

def attach_menu(root, label="Menu"):
    import tkinter as tk
    from tkinter import messagebox

    menu_bar = tk.Menu(root)
    function_menu = tk.Menu(menu_bar, tearoff=0)
    function_menu.add_command(label="Config Settings", command=lambda: messagebox.showinfo("Config", "Settings dialog coming soon."))
    function_menu.add_command(label="App Info", command=lambda: messagebox.showinfo("App Info", "NR Launcher v2.0\nBuilt by A. Mackulin"))
    menu_bar.add_cascade(label=label, menu=function_menu)
    root.config(menu=menu_bar)
