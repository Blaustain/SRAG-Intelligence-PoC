import json, logging, os
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(os.getenv("AUDIT_LOG", "logs/audit.jsonl"))

def audit(event, details=None):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "event": event, "details": details or {}}
    with LOG_PATH.open("a", encoding="utf-8") as f: f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
