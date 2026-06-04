import json
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), "resource_history.json")

def log_action(action: str, resource_type: str, resource_name: str, status: str, attempts: int = 1, terraform_code: str = "", error: str = ""):
    # Load existing logs
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    # Append new log entry
    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "resource_type": resource_type,
        "resource_name": resource_name,
        "status": status,
        "attempts": attempts,
        "terraform_code": terraform_code,
        "error": error
    })

    # Save back to file
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def get_history():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)