import tkinter as tk
from tkinter import messagebox
import launcher_core
import threading
import time

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("Nimble Recorder Launcher")
        root.geometry("400x250")
        root.resizable(False, False)

        tk.Label(root, text="NR Launcher GUI", font=("Arial", 16, "bold")).pack(pady=10)

        self.status = tk.StringVar()
        self.status.set("Initializing...")
        tk.Label(root, textvariable=self.status, fg="gray", font=("Arial", 10)).pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="🔍 Scan Devices", width=15, command=self.manual_scan).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="🚀 Start Launcher", width=15, command=launcher_core.launch_batch_script).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="❌ Exit", width=15, command=self.root.quit).grid(row=2, column=0, padx=10)

        self.monitoring = True
        self.start_monitor_loop()
        self.auto_start()

    def manual_scan(self):
        summary = launcher_core.get_device_summary()
        devices = summary["All"]
        messagebox.showinfo("Device Scan", f"Found {len(devices)} device(s):\n{chr(10).join(devices) if devices else 'None'}")

    def update_status(self):
        self.status.set(launcher_core.device_status_text())

    def start_monitor_loop(self):
        def loop():
            while self.monitoring:
                self.update_status()
                time.sleep(5)
        threading.Thread(target=loop, daemon=True).start()

    def auto_start(self):
        threading.Thread(target=launcher_core.launch_batch_script, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
