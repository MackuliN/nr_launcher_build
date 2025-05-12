import threading
import time
import subprocess

class NimbleRecorderMonitor:
    def __init__(self, on_status_change):
        self.on_status_change = on_status_change
        self.running = False
        self.monitor_thread = None
        self.current_status = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        while self.running:
            new_status = self._is_nr_running()
            if new_status != self.current_status:
                self.current_status = new_status
                self.on_status_change(self.current_status)
            time.sleep(2)

    def _is_nr_running(self):
        try:
            output = subprocess.check_output("tasklist", shell=True).decode()
            return "NimbleRecorderREST.exe".lower() in output.lower()
        except:
            return False
