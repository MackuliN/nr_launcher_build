import tkinter as tk
from tkinter import ttk
from launcher_core import (
    get_device_state,
    launch_batch_script,
    attach_menu
)

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NR Launcher Monitor")
        self.root.geometry("400x200")
        attach_menu(self.root)

        # Device labels
        self.vx_label = tk.Label(root, text="VX Device: ---", font=("Segoe UI", 12), fg="black")
        self.vx_label.pack(pady=10)

        self.vs_label = tk.Label(root, text="VS Device: ---", font=("Segoe UI", 12), fg="black")
        self.vs_label.pack(pady=10)

        # Scan + Launch button
        self.scan_button = ttk.Button(root, text="Scan + Launch NR", command=self.manual_scan)
        self.scan_button.pack(pady=20)

        # Begin background monitor
        self.running = True
        self.monitor_devices()

        # Launch NR immediately on start
        self.root.after(1000, self.auto_launch)

    def update_labels(self, state):
        vx_list = state["VX"]["devices"]
        vs_list = state["VS"]["devices"]

        vx_text = f"VX Device: {vx_list[0] if vx_list else '---'}"
        vs_text = f"VS Device: {vs_list[0] if vs_list else '---'}"

        self.vx_label.config(text=vx_text, fg=state["VX"]["color"])
        self.vs_label.config(text=vs_text, fg=state["VS"]["color"])

    def monitor_devices(self):
        if not self.running:
            return
        state = get_device_state()
        self.update_labels(state)
        self.root.after(5000, self.monitor_devices)

    def manual_scan(self):
        launch_batch_script()

    def auto_launch(self):
        # One-time check on startup
        state = get_device_state()
        if state["VX"]["color"] == "green" and state["VS"]["color"] == "green":
            launch_batch_script()

if __name__ == "__main__":
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
