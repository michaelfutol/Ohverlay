"""
Audit & History Store for Ohverlay Sticky Notes and Task Management.
Tracks live events, timer durations, history, and completions in a local JSON file.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.logger import logger


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class AuditStore:
    """Stores history of sticky notes, timers, completions, and edits."""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            from config.settings import get_app_data_dir
            config_dir = get_app_data_dir()
        self.config_dir = os.path.abspath(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.history_file = os.path.join(self.config_dir, "sticky_history.json")
        self._events: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self._events = data
                    elif isinstance(data, dict) and "events" in data:
                        self._events = data["events"]
                logger.debug(f"Loaded {len(self._events)} audit events from {self.history_file}")
            except Exception as e:
                logger.error(f"Failed to load audit history: {e}")
                self._events = []
        else:
            self._events = []

    def _save(self):
        try:
            tmp_path = self.history_file + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._events, f, indent=2)
            shutil.move(tmp_path, self.history_file)
        except Exception as e:
            logger.error(f"Failed to save audit history: {e}")

    def record_event(
        self,
        event: str,
        *,
        note_id: str = "",
        title: str = "",
        sender: str = "local",
        recipient: str = "local",
        filename: str = "",
        file_path: str = "",
        notification_id: str = "",
        action: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        record = {
            "id": f"evt_{len(self._events) + 1}_{int(datetime.now().timestamp())}",
            "timestamp": _now_iso(),
            "event": event,
            "action": action,
            "note_id": note_id or (details.get("note_id") if details else ""),
            "title": title or filename or (details.get("title") if details else "Sticky Note"),
            "sender": sender,
            "recipient": recipient,
            "filename": filename or title,
            "file_path": file_path,
            "notification_id": notification_id,
            "details": details or {},
        }
        self._events.append(record)
        self._save()
        return record

    def fetch_all(self) -> List[Dict[str, Any]]:
        return list(self._events)

    def fetch_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(reversed(self._events[-limit:]))

    def clear_history(self):
        self._events = []
        self._save()

    def get_summary_metrics(self, active_notes_count: int = 0) -> Dict[str, Any]:
        created_count = sum(1 for e in self._events if e.get("event") in ("sticky_created", "created"))
        completed_count = sum(1 for e in self._events if e.get("event") in ("job_done", "task_completed", "completed"))
        overdue_count = sum(1 for e in self._events if e.get("event") in ("sticky_overdue", "overdue"))
        closed_count = sum(1 for e in self._events if e.get("event") in ("sticky_closed", "closed"))
        
        return {
            "total_created": created_count,
            "total_completed": completed_count,
            "total_overdue": overdue_count,
            "total_closed": closed_count,
            "active_count": active_notes_count,
        }
