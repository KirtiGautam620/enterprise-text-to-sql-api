import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

app_logger = logging.getLogger("text_to_sql_logger")
app_logger.setLevel(logging.INFO)
app_logger.propagate = False

if not app_logger.handlers:
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    app_logger.addHandler(file_handler)


def log_event(event_type: str, data: Dict[str, Any]) -> None:
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "data": data
    }

    app_logger.info(json.dumps(log_entry, default=str))