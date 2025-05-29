import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import ctypes
import sys
import os
import json
import threading

from launcher_core import (
    get_device_state,
    launch_batch_script_with_tracking,
)

from nr_monitor import is_nr_running

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "scan_interval": 5,
    "auto_launch_disable": False,
    "edge_autolaunch_disable": False,
    "launch_all_server_disable": False,
    "hmd_prefix": "VX",
    "scylla_prefix": "VS"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def elevate_if_needed():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}"', None, 1)
        sys.exit(0)

def get_launcher_version():
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(base_path, "version.txt"), "r") as f:
            return f.read().strip()
    except:
        return "v2.0"

def get_battery_level(device_id="eureka"):
    try:
        cmd = ["adb", "-s", f"device:{device_id}", "shell", "dumpsys", "battery"]
        result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=subprocess.STARTUPINFO())
        output = result.stdout
        for line in output.splitlines():
            if "level" in line:
                return line.strip().split(":")[-1].strip()
    except:
        return "?"
    return "?"

class ConfigDialog(tk.Toplevel):
    def __init__(self, master, settings, on_save):
        super().__init__(master)
        self.title("Configuration")
        self.resizable(False, False)

        self.settings = settings
        self.on_save = on_save

        tk.Label(self, text="Scan Interval (seconds):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.interval_var = tk.IntVar(value=settings["scan_interval"])
        self.interval_spin = tk.Spinbox(self, from_=1, to=60, textvariable=self.interval_var, width=5)
        self.interval_spin.grid(row=0, column=1, padx=10, pady=10)

        self.auto_launch_var = tk.BooleanVar(value=settings.get("auto_launch_disable", False))
        self.auto_launch_check = tk.Checkbutton(self, text="Disable Auto-Launch", variable=self.auto_launch_var)
        self.auto_launch_check.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        self.edge_launch_var = tk.BooleanVar(value=settings.get("edge_autolaunch_disable", False))
        self.edge_launch_check = tk.Checkbutton(self, text="Disable Edge Auto-Launch", variable=self.edge_launch_var)
        self.edge_launch_check.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        self.server_launch_var = tk.BooleanVar(value=settings.get("launch_all_server_disable", False))
        self.server_launch_check = tk.Checkbutton(self, text="Disable Auto Launch of Server Scripts", variable=self.server_launch_var)
        self.server_launch_check.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        tk.Label(self, text="HMD Serial Prefix:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.hmd_var = tk.StringVar(value=settings.get("hmd_prefix", "VX"))
        self.hmd_entry = tk.Entry(self, textvariable=self.hmd_var)
        self.hmd_entry.grid(row=4, column=1, padx=10, pady=10)

        tk.Label(self, text="Scylla Serial Prefix:").grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.scylla_var = tk.StringVar(value=settings.get("scylla_prefix", "VS"))
        self.scylla_entry = tk.Entry(self, textvariable=self.scylla_var)
        self.scylla_entry.grid(row=5, column=1, padx=10, pady=10)

        save_btn = ttk.Button(self, text="Save", command=self.save)
        save_btn.grid(row=6, column=0, columnspan=2, pady=10)

    def save(self):
        self.settings["scan_interval"] = self.interval_var.get()
        self.settings["auto_launch_disable"] = self.auto_launch_var.get()
        self.settings["edge_autolaunch_disable"] = self.edge_launch_var.get()
        self.settings["launch_all_server_disable"] = self.server_launch_var.get()
        self.settings["hmd_prefix"] = self.hmd_var.get()
        self.settings["scylla_prefix"] = self.scylla_var.get()
        save_settings(self.settings)
        self.on_save()
        self.destroy()

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NR Launcher Monitor")
        self.root.geometry("400x260")

        self.settings = load_settings()

        self.attach_menu()

        self.hmd_label = tk.Label(root, text="HMD Device: ---", font=("Segoe UI", 12), fg="black")
        self.hmd_label.pack(pady=5)

        self.scylla_label = tk.Label(root, text="Scylla Device: ---", font=("Segoe UI", 12), fg="black")
        self.scylla_label.pack(pady=5)

        self.battery_label = tk.Label(root, text="Battery (Eureka): ---", font=("Segoe UI", 10))
        self.battery_label.pack(pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.scan_button = ttk.Button(self.button_frame, text="Scan Devices", command=self.manual_scan)
        self.scan_button.pack(side=tk.LEFT, padx=10)

        self.launch_button = ttk.Button(self.button_frame, text="Launch NR", command=self.guard_before_launch)
        self.launch_button.pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(root, text="NR Status: Not Ready", font=("Segoe UI", 10), fg="red")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.edge_started = False
        self.running = True
        self.monitor_devices()
        self.root.after(3000, self.update_nr_status)
        self.root.after(10000, self.update_battery_status)
        self.root.after(1000, self.auto_launch)

    def attach_menu(self):
        menu_bar = tk.Menu(self.root)
        function_menu = tk.Menu(menu_bar, tearoff=0)
        function_menu.add_command(label="Config Settings", command=self.open_config)
        function_menu.add_command(label="Force Launch NR", command=self.force_launch_nr)
        function_menu.add_command(label="App Info", command=lambda: messagebox.showinfo("App Info", f"NR Launcher {get_launcher_version()}\nBuilt by A. Mackulin"))
        menu_bar.add_cascade(label="Menu", menu=function_menu)
        self.root.config(menu=menu_bar)

    def open_config(self):
        ConfigDialog(self.root, self.settings, self.reload_settings)

    def reload_settings(self):
        self.settings = load_settings()

    def force_launch_nr(self):
        response = messagebox.askokcancel("Force Launch", "Are you sure you want to launch NR directly without checking for connected devices?")
        if not response:
            return
        user_home = os.path.expanduser("~")
        bat_path = os.path.join(user_home, "S2", "NR", "startNimbleRecorderUnified.bat")
        if os.path.exists(bat_path):
            subprocess.Popen(["cmd", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            messagebox.showerror("File Not Found", f"Could not locate:\n{bat_path}")

    def manual_scan(self):
        state = get_device_state(self.settings)
        self.update_labels(state)

    def update_labels(self, state):
        hmd_list = state["HMD"]["devices"]
        scylla_list = state["Scylla"]["devices"]

        self.hmd_label.config(text=f"HMD Device: {hmd_list[0] if hmd_list else '---'}", fg=state["HMD"]["color"])
        self.scylla_label.config(text=f"Scylla Device: {scylla_list[0] if scylla_list else '---'}", fg=state["Scylla"]["color"])

    def monitor_devices(self):
        if not self.running:
            return
        threading.Thread(target=lambda: self.update_labels(get_device_state(self.settings)), daemon=True).start()
        interval = self.settings.get("scan_interval", 5)
        self.root.after(interval * 1000, self.monitor_devices)

    def update_battery_status(self):
        threading.Thread(target=self._fetch_battery_status, daemon=True).start()
        self.root.after(10000, self.update_battery_status)

    def _fetch_battery_status(self):
        level = get_battery_level()
        self.battery_label.config(text=f"Battery (Eureka): {level}%")

    def auto_launch(self):
        if self.settings.get("auto_launch_disable", False):
            return
        if is_nr_running():
            return
        state = get_device_state(self.settings)
        if state["HMD"]["color"] == "green" and state["Scylla"]["color"] == "green":
            launch_batch_script_with_tracking(skip_check=False)

    def launch_all_server(self):
        script = (
            "set PYTHONPATH=%PYTHONPATH%;C:\\Users\\rift\\schroedinger_control\\EFReCalSolution && "
            "echo %PYTHONPATH% && "
            "cd C:\\Users\\rift\\S2\\ && "
            "start C:\\python38\\python.exe .\\s2_chassis_server.py -o .\\ && "
            "timeout /t 2 && "
            "start C:\\tools\\fb-python310\\python.exe .\\launch_s2_server.par -o .\\"
        )
        subprocess.Popen(script, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

    def guard_before_launch(self):
        if is_nr_running():
            messagebox.showinfo("NR Already Running", "NimbleRecorder is already running.\nPlease close all instances before launching again.")
            return
        state = get_device_state(self.settings)
        if not (state["HMD"]["devices"] and state["Scylla"]["devices"]):
            messagebox.showerror("Device Check Failed", "Required devices not connected. Cannot launch NR.")
            return
        launch_batch_script_with_tracking(skip_check=False)

    def update_nr_status(self):
        if is_nr_running():
            self.status_label.config(text="NR Status: Ready", fg="green")
            if not self.settings.get("edge_autolaunch_disable", False) and not self.edge_started:
                subprocess.Popen(["cmd", "/c", "start", "msedge"], shell=True)
                self.edge_started = True
                if not self.settings.get("launch_all_server_disable", False):
                    self.launch_all_server()
        else:
            self.status_label.config(text="NR Status: Not Ready", fg="red")
            self.edge_started = False
        self.root.after(1500, self.update_nr_status)

if __name__ == "__main__":
    elevate_if_needed()
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
