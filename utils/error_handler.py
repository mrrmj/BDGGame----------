import traceback
from datetime import datetime

def log_error(error, context=""):
    """Centralized error logging"""
    tb = traceback.format_exc()
    entry = f"\n[{datetime.now()}] {context}\n{error}\n{tb}\n"
    
    with open("error_log.txt", "a") as f:
        f.write(entry)
    return entry