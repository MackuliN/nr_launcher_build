import os
import time
import psutil
from datetime import datetime

NR_PROCESS_NAME = "NimbleRecorderREST.exe"
NR_LOG_DIR = "C:/NR/Project/logs"
READY_STRINGS = [
    "Main loop running...",
    "Creating NR_REST HTTP listener"
]

last_check_time = 0
last_check_result = False

def is_process_running():
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == NR_PROCESS_NAME:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def get_latest_log_file():
    try:
        if not os.path.exists(NR_LOG_DIR):
            return None
        files = [
            os.path.join(NR_LOG_DIR, f)
            for f in os.listdir(NR_LOG_DIR)
            if f.endswith(".log")
        ]
        if not files:
            return None
        latest_file = max(files, key=os.path.getmtime)
        return latest_file
    except Exception:
        return None

def parse_log_for_readiness(log_path):
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-300:]  # only look at the last 300 lines
        for line in reversed(lines):
            if any(s in line for s in READY_STRINGS):
                return True
        return False
    except Exception:
        return False

def is_nr_running():
    global last_check_time, last_check_result

    now = time.time()
    if now - last_check_time < 5:
        return last_check_result

    process_active = is_process_running()
    log_path = get_latest_log_file()
    log_ready = parse_log_for_readiness(log_path) if log_path else False

    result = process_active and log_ready

    last_check_time = now
    last_check_result = result
    return result
