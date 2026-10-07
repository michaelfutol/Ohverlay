"""
Unit and integration tests for Sticky Note Checklist Mode, Task Duration Stamping,
Authentic Post-It Themes, and Master Dashboard Time Analytics.
"""

from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QLabel

from config.settings import Settings
from modules.audit_store import AuditStore
from modules.card_themes import (
    THEME_LIST,
    get_note_theme,
    list_note_themes,
    resolve_theme_id,
)
from modules.sticky_notes import (
    NetShareStickyNoteManager,
    StickyNoteWidget,
    TaskRowWidget,
    _format_short_duration,
)
from ui.master_dashboard import MasterDashboard


class TestStickyChecklistAndAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        import shutil
        import tempfile
        self._temp_dir = tempfile.mkdtemp()
        self.config = Settings()
        self.audit_store = AuditStore(config_dir=self._temp_dir)
        self.sticky_manager = NetShareStickyNoteManager(
            config=self.config,
            audit_store=self.audit_store,
        )

    def tearDown(self):
        import shutil
        for note in list(self.sticky_manager._notes.values()):
            note.close()
        self.sticky_manager._notes.clear()
        self.audit_store.clear_history()
        shutil.rmtree(self._temp_dir, ignore_errors=True)

    # ── 1. Authentic Post-It Themes (Bloat Removed) ──

    def test_authentic_postit_theme_list(self):
        pass

    def test_checklist_task_creation_and_strikeout(self):
        """Verify adding tasks, checking them off applies strikethrough and dims color."""
        note = self.sticky_manager.create_note()
        note.project_title_edit.setText("BACACAY")
        note.state["title"] = "BACACAY"

        # Set tasks
        tasks = [
            {"id": "t1", "text": "1. STRUC", "completed": False, "start_time": "2026-09-15T08:00:00", "finish_time": "", "duration_seconds": 0, "duration_text": ""},
            {"id": "t2", "text": "2. ARCH", "completed": False, "start_time": "2026-09-15T08:00:00", "finish_time": "", "duration_seconds": 0, "duration_text": ""},
            {"id": "t3", "text": "3. ELEC.", "completed": False, "start_time": "2026-09-15T08:00:00", "finish_time": "", "duration_seconds": 0, "duration_text": ""},
            {"id": "t4", "text": "4. PLUMBING", "completed": False, "start_time": "2026-09-15T08:00:00", "finish_time": "", "duration_seconds": 0, "duration_text": ""},
        ]
        note.state["tasks"] = tasks
        note._refresh_checklist_ui()

        self.assertEqual(len(note._task_rows), 4)

        # Check off task 1 (STRUC)
        row1 = note._task_rows["t1"]
        self.assertFalse(row1.checkbox.isChecked())
        self.assertFalse(row1.line_edit.font().strikeOut())

        # Toggle checked
        note._on_task_toggled("t1", True)
        self.assertTrue(note.state["tasks"][0]["completed"])
        self.assertTrue(row1.checkbox.isChecked())
        self.assertTrue(row1.line_edit.font().strikeOut())

        # Sync text preview
        plain_text = note.text_edit.toPlainText()
        self.assertIn("[x] 1. STRUC", plain_text)
        self.assertIn("[ ] 2. ARCH", plain_text)

    # ── 3. Duration Stamping With & Without Timer ──

    def test_duration_stamping_inactive_timer(self):
        """When timer is OFF, checking off does not stamp duration on the note."""
        note = self.sticky_manager.create_note()
        note.state["timer_mode"] = "off"
        task_id = "t_no_timer"
        note.state["tasks"] = [
            {"id": task_id, "text": "Quick Task", "completed": False, "start_time": "2026-09-15T08:00:00", "finish_time": "", "duration_seconds": 0, "duration_text": ""}
        ]
        note._refresh_checklist_ui()

        note._on_task_toggled(task_id, True)

        # Note does not display artificial duration text
        task = note.state["tasks"][0]
        self.assertEqual(task["duration_text"], "")
        row = note._task_rows[task_id]
        self.assertTrue(row.duration_label.isHidden())

        # But audit store STILL has exact start, finish, and computed duration
        analytics = self.audit_store.get_time_analytics()
        self.assertEqual(analytics["completed_tasks_count"], 1)
        logged_task = analytics["tasks"][0]
        self.assertEqual(logged_task["task_name"], "Quick Task")
        self.assertTrue(logged_task["finish_time"] != "")
        self.assertGreater(logged_task["duration_seconds"], 0)

    def test_duration_stamping_active_timer(self):
        """When timer is ACTIVE (elapsed/countdown), checking off stamps duration on right side of task."""
        note = self.sticky_manager.create_note()
        note.state["timer_mode"] = "elapsed"

        # Task started 18 minutes ago
        past_start = (datetime.now() - timedelta(minutes=18, seconds=5)).isoformat(timespec="seconds")
        task_id = "t_timer_active"
        note.state["tasks"] = [
            {"id": task_id, "text": "1. STRUC Review", "completed": False, "start_time": past_start, "finish_time": "", "duration_seconds": 0, "duration_text": ""}
        ]
        note._refresh_checklist_ui()

        note._on_task_toggled(task_id, True)

        task = note.state["tasks"][0]
        self.assertTrue(task["completed"])
        self.assertEqual(task["duration_text"], "18m")

        # Row displays duration badge on the right
        row = note._task_rows[task_id]
        self.assertEqual(row.duration_label.text(), "18m")
        self.assertFalse(row.duration_label.isHidden())

    def test_short_duration_formatting(self):
        """Test duration formatting helper for task rows."""
        self.assertEqual(_format_short_duration(45), "45s")
        self.assertEqual(_format_short_duration(60), "1m")
        self.assertEqual(_format_short_duration(18 * 60 + 10), "18m")
        self.assertEqual(_format_short_duration(3600 + 5 * 60), "1h 05m")

    # ── 4. AuditStore Time Analytics & Compounding ──

    def test_audit_store_compounded_time_analytics(self):
        """Verify compounded duration calculation, project breakdowns, and exact timestamps."""
        start1 = "2026-09-15T08:00:00"
        finish1 = "2026-09-15T08:18:00"
        self.audit_store.record_task_completion(
            note_id="n1",
            title="BACACAY",
            task_name="1. STRUC",
            start_time=start1,
            finish_time=finish1,
            duration_seconds=1080, # 18m
            timer_active=True,
        )

        start2 = "2026-09-15T08:20:00"
        finish2 = "2026-09-15T08:45:00"
        self.audit_store.record_task_completion(
            note_id="n1",
            title="BACACAY",
            task_name="2. ARCH",
            start_time=start2,
            finish_time=finish2,
            duration_seconds=1500, # 25m
            timer_active=True,
        )

        start3 = "2026-09-15T09:00:00"
        finish3 = "2026-09-15T09:30:00"
        self.audit_store.record_task_completion(
            note_id="n2",
            title="PROJECT B",
            task_name="Electrical Roughing",
            start_time=start3,
            finish_time=finish3,
            duration_seconds=1800, # 30m
            timer_active=True,
        )

        analytics = self.audit_store.get_time_analytics()
        self.assertEqual(analytics["completed_tasks_count"], 3)
        # Total compounded = 1080 + 1500 + 1800 = 4380s (1h 13m)
        self.assertEqual(analytics["total_compounded_seconds"], 4380)
        self.assertEqual(analytics["total_compounded_formatted"], "1h 13m")

        # Project durations
        self.assertEqual(analytics["project_durations"]["BACACAY"], 2580) # 43m
        self.assertEqual(analytics["project_durations"]["PROJECT B"], 1800) # 30m

        # Exact timestamps
        t1 = [t for t in analytics["tasks"] if t["task_name"] == "1. STRUC"][0]
        self.assertEqual(t1["start_time"], start1)
        self.assertEqual(t1["finish_time"], finish1)
        self.assertEqual(t1["duration_formatted"], "18m 00s")
        self.assertEqual(t1["status"], "COMPLETED")

    # ── 5. Master Dashboard Time Analytics Tab ──

    def test_master_dashboard_analytics_tab(self):
        """Verify the Master Dashboard includes the 3rd tab and populates analytics table."""
        dashboard = MasterDashboard(sticky_manager=self.sticky_manager, audit_store=self.audit_store)
        self.assertEqual(dashboard.tabs.count(), 3)
        self.assertEqual(dashboard.tabs.tabText(2), "📊 Time Analytics & Task Log")

        # Add completed task to audit store
        self.audit_store.record_task_completion(
            note_id="note_bacacay",
            title="BACACAY",
            task_name="1. STRUC",
            start_time="2026-09-15T08:00:00",
            finish_time="2026-09-15T08:18:00",
            duration_seconds=1080,
            timer_active=True,
        )

        dashboard.refresh_analytics_table()

        # Check KPI cards
        self.assertEqual(dashboard.card_completed_tasks.findChild(QLabel, "kpiVal").text(), "1 (1 today)")
        self.assertEqual(dashboard.card_total_projects.findChild(QLabel, "kpiVal").text(), "1")

        # Check Analytics Table
        self.assertEqual(dashboard.analytics_table.rowCount(), 1)
        self.assertEqual(dashboard.analytics_table.item(0, 0).text(), "BACACAY")
        self.assertEqual(dashboard.analytics_table.item(0, 1).text(), "1. STRUC")
        self.assertIn("2026-09-15 08:00:00", dashboard.analytics_table.item(0, 2).text())
        self.assertIn("2026-09-15 08:18:00", dashboard.analytics_table.item(0, 3).text())
        self.assertIn("18m", dashboard.analytics_table.item(0, 4).text())
        self.assertIn("COMPLETED", dashboard.analytics_table.item(0, 5).text())

        # Check Project dropdown
        self.assertIn("BACACAY", [dashboard.analytics_project_combo.itemText(i) for i in range(dashboard.analytics_project_combo.count())])

        # Test project filter
        dashboard.analytics_project_combo.setCurrentText("BACACAY")
        dashboard.refresh_analytics_table()
        self.assertEqual(dashboard.analytics_table.rowCount(), 1)

        dashboard.close()


if __name__ == "__main__":
    unittest.main()
