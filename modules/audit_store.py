"""
Audit & History Store for Ohverlay Sticky Notes and Task Management.
Tracks live events, timer durations, history, and completions in a local JSON file.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils.logger import logger

# Task completions power the time analytics, so they are never pruned.
# Everything else (created/closed/overdue/share...) is capped to keep the file small and fast.
DEFAULT_MAX_EVENTS = 5000
_PROTECTED_EVENTS = {"task_completed"}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class AuditStore:
    """Stores history of sticky notes, timers, completions, and edits."""

    def __init__(self, config_dir: Optional[str] = None, max_events: int = DEFAULT_MAX_EVENTS):
        if config_dir is None:
            from config.settings import get_app_data_dir
            config_dir = get_app_data_dir()
        self.config_dir = os.path.abspath(config_dir)
        os.makedirs(self.config_dir, exist_ok=True)
        self.history_file = os.path.join(self.config_dir, "sticky_history.json")
        self.max_events = max(100, int(max_events))
        self._lock = threading.RLock()
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
                try:  # keep the unreadable file instead of overwriting it on the next save
                    os.replace(self.history_file, self.history_file + ".corrupt")
                except OSError:
                    pass
                self._events = []
        else:
            self._events = []

    def _prune(self):
        overflow = len(self._events) - self.max_events
        if overflow <= 0:
            return
        kept, dropped = [], 0
        for event in self._events:  # oldest first
            if dropped < overflow and event.get("event") not in _PROTECTED_EVENTS:
                dropped += 1
                continue
            kept.append(event)
        self._events = kept

    def _save(self):
        try:
            tmp_path = self.history_file + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._events, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, self.history_file)
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
            "id": f"evt_{uuid.uuid4().hex[:12]}",
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
        with self._lock:
            self._events.append(record)
            self._prune()
            self._save()
        return record

    def fetch_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._events)

    def fetch_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._lock:
            return list(reversed(self._events[-limit:]))

    def clear_history(self):
        with self._lock:
            self._events = []
            self._save()


    def record_task_completion(
        self,
        *,
        note_id: str,
        title: str,
        task_name: str,
        start_time: str,
        finish_time: str,
        duration_seconds: int,
        timer_active: bool = True,
    ):
        duration_formatted = self._format_duration(duration_seconds)
        details = {
            "note_id": note_id,
            "task_name": task_name,
            "start_time": start_time,
            "finish_time": finish_time,
            "duration_seconds": duration_seconds,
            "duration_formatted": duration_formatted,
            "timer_active": timer_active,
        }
        return self.record_event(
            "task_completed",
            note_id=note_id,
            title=title,
            action=f"Completed '{task_name}' in {duration_formatted}",
            details=details,
        )

    def get_time_analytics(self) -> Dict[str, Any]:
        """Aggregate time tracking analytics across all completed tasks."""
        task_events = [e for e in self._events if e.get("event") == "task_completed"]

        total_seconds = 0
        tasks = []
        project_durations = {}

        today_str = datetime.now().strftime("%Y-%m-%d")
        tasks_today = 0

        for e in task_events:
            dtl = e.get("details", {})
            dur = int(dtl.get("duration_seconds", 0) or 0)
            total_seconds += dur

            ts = e.get("timestamp", "")
            if ts.startswith(today_str):
                tasks_today += 1

            project = e.get("title", "Sticky Note") or "Sticky Note"
            project_durations[project] = project_durations.get(project, 0) + dur

            tasks.append({
                "id": e.get("id"),
                "timestamp": ts,
                "note_id": e.get("note_id", ""),
                "project": project,
                "task_name": dtl.get("task_name", e.get("title", "")),
                "start_time": dtl.get("start_time", ""),
                "finish_time": dtl.get("finish_time", ts),
                "duration_seconds": dur,
                "duration_formatted": dtl.get("duration_formatted") or self._format_duration(dur),
                "status": "COMPLETED",
            })

        avg_seconds = (total_seconds // len(tasks)) if tasks else 0

        return {
            "total_compounded_seconds": total_seconds,
            "total_compounded_formatted": self._format_duration(total_seconds),
            "completed_tasks_count": len(tasks),
            "tasks_today_count": tasks_today,
            "average_duration_seconds": avg_seconds,
            "average_duration_formatted": self._format_duration(avg_seconds),
            "project_durations": project_durations,
            "tasks": list(reversed(tasks)),
        }

    @staticmethod
    def _format_duration(total_seconds: int) -> str:
        seconds = abs(int(total_seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        elif minutes > 0:
            return f"{minutes}m {secs:02d}s"
        else:
            return f"{secs}s"

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
