import psutil
import subprocess

def is_nr_running():
    """Dynamically checks if NimbleRecorder process is running and logs show 'Main loop running...'."""
    for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
        if proc.info['name'] == 'cmd.exe':
            try:
                with proc.oneshot():
                    pid = proc.info['pid']
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'startNimbleRecorderUnified.bat' in cmdline.lower():
                        result = subprocess.run(
                            f'powershell Get-Content -Path (Get-Process -Id {pid}).Path -Tail 30',
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        if "Main loop running..." in result.stdout:
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    return False
