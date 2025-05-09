import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import ctypes
import sys
import os
import json

from launcher_core import (
    get_device_state,
    launch_batch_script_with_tracking,
    is_nr_ready
)

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "scan_interval": 5,
    "skip_device_check": False
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

        self.skip_var = tk.BooleanVar(value=settings["skip_device_check"])
        self.skip_check = tk.Checkbutton(self, text="Skip Device Check", variable=self.skip_var)
        self.skip_check.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

        save_btn = ttk.Button(self, text="Save", command=self.save)
        save_btn.grid(row=2, column=0, columnspan=2, pady=10)

    def save(self):
        self.settings["scan_interval"] = self.interval_var.get()
        self.settings["skip_device_check"] = self.skip_var.get()
        save_settings(self.settings)
        self.on_save()
        self.destroy()

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NR Launcher Monitor")
        self.root.geometry("400x230")

        self.settings = load_settings()

        self.attach_menu()

        self.vx_label = tk.Label(root, text="VX Device: ---", font=("Segoe UI", 12), fg="black")
        self.vx_label.pack(pady=5)

        self.vs_label = tk.Label(root, text="VS Device: ---", font=("Segoe UI", 12), fg="black")
        self.vs_label.pack(pady=5)

        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=10)

        self.scan_button = ttk.Button(self.button_frame, text="Scan Devices", command=self.manual_scan)
        self.scan_button.pack(side=tk.LEFT, padx=10)

        self.launch_button = ttk.Button(self.button_frame, text="Launch NR", command=self.guard_before_launch)
        self.launch_button.pack(side=tk.LEFT, padx=10)

        self.status_label = tk.Label(root, text="NR Status: Not Ready", font=("Segoe UI", 10), fg="red")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.running = True
        self.monitor_devices()
        self.root.after(3000, self.update_nr_status)
        self.root.after(1000, self.auto_launch)

    def attach_menu(self):
        menu_bar = tk.Menu(self.root)
        function_menu = tk.Menu(menu_bar, tearoff=0)
        function_menu.add_command(label="Config Settings", command=self.open_config)
        function_menu.add_command(
            label="App Info",
            command=lambda: messagebox.showinfo(
                "App Info",
                f"NR Launcher {get_launcher_version()}\nBuilt by A. Mackulin"
            )
        )
        menu_bar.add_cascade(label="Menu", menu=function_menu)
        self.root.config(menu=menu_bar)

    def open_config(self):
        ConfigDialog(self.root, self.settings, self.reload_settings)

    def reload_settings(self):
        self.settings = load_settings()

    def manual_scan(self):
        state = get_device_state()
        self.update_labels(state)

    def update_labels(self, state):
        vx_list = state["VX"]["devices"]
        vs_list = state["VS"]["devices"]

        self.vx_label.config(
            text=f"VX Device: {vx_list[0] if vx_list else '---'}",
            fg=state["VX"]["color"]
        )
        self.vs_label.config(
            text=f"VS Device: {vs_list[0] if vs_list else '---'}",
            fg=state["VS"]["color"]
        )

    def monitor_devices(self):
        if not self.running:
            return
        self.update_labels(get_device_state())
        interval = self.settings.get("scan_interval", 5)
        self.root.after(interval * 1000, self.monitor_devices)

    def auto_launch(self):
        if self.settings.get("skip_device_check", False):
            return
        state = get_device_state()
        if state["VX"]["color"] == "green" and state["VS"]["color"] == "green":
            launch_batch_script_with_tracking()

    def guard_before_launch(self):
        if self.settings.get("skip_device_check", False):
            launch_batch_script_with_tracking()
            return

        state = get_device_state()
        if not (state["VX"]["devices"] and state["VS"]["devices"]):
            messagebox.showerror("Device Check Failed", "Required devices not connected. Cannot launch NR.")
            return

        if self.is_process_running("NimbleRecorderREST.exe"):
            response = messagebox.askokcancel(
                "NR Already Running",
                "NimbleRecorder is already running.\nClose all instances of NR, Microsoft Edge, and the most recent Command Prompt?"
            )
            if response:
                self.kill_process("msedge.exe")
                self.kill_most_recent_cmd()
                self.kill_process("NimbleRecorderREST.exe")

        launch_batch_script_with_tracking()

    def update_nr_status(self):
        if is_nr_ready(timeout=3):
            self.status_label.config(text="NR Status: Ready", fg="green")
        else:
            self.status_label.config(text="NR Status: Not Ready", fg="red")
        self.root.after(5000, self.update_nr_status)

    def is_process_running(self, name):
        try:
            output = subprocess.check_output("tasklist", shell=True).decode()
            return name.lower() in output.lower()
        except:
            return False

    def kill_process(self, name):
        try:
            subprocess.call(f"taskkill /F /IM {name}", shell=True)
        except:
            pass

    def kill_most_recent_cmd(self):
        try:
            output = subprocess.check_output("wmic process where (name='cmd.exe') get ProcessId,CreationDate /format:csv", shell=True).decode()
            lines = [line for line in output.strip().splitlines() if line and "CreationDate" not in line]
            if not lines:
                return
            lines.sort(key=lambda l: l.split(",")[1])
            pid = lines[-1].split(",")[2]
            subprocess.call(f"taskkill /F /PID {pid}", shell=True)
        except:
            pass

if __name__ == "__main__":
    elevate_if_needed()
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
