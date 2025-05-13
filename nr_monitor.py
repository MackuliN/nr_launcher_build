import subprocess
import threading
import time

status_flag = {"running": False}

def is_nr_running():
    """Check if NimbleRecorder is running based on 'Main loop running...' console log."""
    return status_flag["running"]

def monitor_console_for_ready_flag():
    """Watches all cmd.exe consoles for 'Main loop running...' indicating NR is ready."""
    while True:
        try:
            output = subprocess.check_output("tasklist /FI \"IMAGENAME eq cmd.exe\" /FO CSV", shell=True).decode()
            if "cmd.exe" not in output:
                status_flag["running"] = False
                time.sleep(1)
                continue

            consoles = output.strip().splitlines()[1:]
            for line in consoles:
                pid = line.split(",")[1].strip().strip('"')
                try:
                    out = subprocess.check_output(f"powershell Get-Content -Path (Get-Process -Id {pid}).Path -Tail 20", shell=True)
                    if b"Main loop running..." in out:
                        status_flag["running"] = True
                        break
                except:
                    continue
            else:
                status_flag["running"] = False

        except:
            status_flag["running"] = False

        time.sleep(2)

# Start monitoring in background when this module is imported
threading.Thread(target=monitor_console_for_ready_flag, daemon=True).start()
