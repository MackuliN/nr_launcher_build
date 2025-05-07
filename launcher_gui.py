import tkinter as tk
from tkinter import messagebox
import launcher_core
import threading
import time

class NRLauncherApp:
    def __init__(self, root):
        self.root = root
        root.title("Nimble Recorder Launcher")
        root.geometry("400x300")
        root.resizable(False, False)

        tk.Label(root, text="NR Launcher GUI", font=("Arial", 16, "bold")).pack(pady=10)

        self.vx_label = tk.Label(root, text="VX: -", font=("Arial", 10))
        self.vx_label.pack()
        self.vs_label = tk.Label(root, text="VS: -", font=("Arial", 10))
        self.vs_label.pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="🔍 Scan Devices", width=15, command=self.manual_scan).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="🚀 Start Launcher", width=15, command=launcher_core.launch_batch_script).grid(row=1, column=0, padx=10, pady=10)
        tk.Button(btn_frame, text="❌ Exit", width=15, command=self.root.quit).grid(row=2, column=0, padx=10)

        self.monitoring = True
        self.current_devices = {"VX": [], "VS": []}
        self.start_monitor_loop()
        self.auto_start()

    def manual_scan(self):
        state = launcher_core.get_device_state()
        self.current_devices = {
            "VX": state["VX"]["devices"],
            "VS": state["VS"]["devices"]
        }
        self.update_status_labels(state)
        all_devices = state["VX"]["devices"] + state["VS"]["devices"]
        messagebox.showinfo("Device Scan", f"Found {len(all_devices)} device(s):\n{chr(10).join(all_devices) if all_devices else 'None'}")

    def update_status_labels(self, state):
        vx_text = f"VX: {', '.join(state['VX']['devices']) if state['VX']['devices'] else '-'}"
        vs_text = f"VS: {', '.join(state['VS']['devices']) if state['VS']['devices'] else '-'}"
        self.vx_label.config(text=vx_text, fg=state['VX']['color'])
        self.vs_label.config(text=vs_text, fg=state['VS']['color'])

    def start_monitor_loop(self):
        def loop():
            while self.monitoring:
                state = launcher_core.get_device_state()
                # If user hasn't manually rescanned, update colors based on disappearance
                for k in ["VX", "VS"]:
                    if self.current_devices[k]:
                        if not state[k]["devices"]:
                            state[k]["color"] = "red"
                self.update_status_labels(state)
                time.sleep(5)
        threading.Thread(target=loop, daemon=True).start()

    def auto_start(self):
        threading.Thread(target=launcher_core.launch_batch_script, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = NRLauncherApp(root)
    root.mainloop()
