"""
Tests for native Sticky Notes, AuditStore, and Master Dashboard.
"""

import os
import shutil
import tempfile
import unittest
from PySide6.QtWidgets import QApplication

from config.settings import Settings
from modules.audit_store import AuditStore
from modules.card_themes import list_note_themes, list_font_presets
from modules.sticky_notes import StickyNoteManager
from ui.master_dashboard import MasterDashboard


class TestStickyNotesAndMasterDashboard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.settings = Settings(config_path=os.path.join(self.temp_dir, "config.json"))
        self.audit_store = AuditStore(config_dir=self.temp_dir)
        self.sticky_manager = StickyNoteManager(config=self.settings, audit_store=self.audit_store)

    def tearDown(self):
        self.sticky_manager.clear_all()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_theme_and_font_presets_availability(self):
        themes = list_note_themes()
        self.assertGreaterEqual(len(themes), 5)
        presets = list_font_presets()
        self.assertGreaterEqual(len(presets), 5)

    def test_create_and_manage_sticky_note(self):
        note = self.sticky_manager.create_note()
        self.assertIsNotNone(note)
        note_id = note.state.get("id")
        self.assertTrue(self.sticky_manager.has_note(note_id))

        # Test text update
        note.text_edit.setPlainText("Test reminder content")
        self.assertEqual(note.state["text"], "Test reminder content")

        # Test timer modes
        note._set_timer_elapsed()
        self.assertEqual(note.state["timer_mode"], "elapsed")

        note._set_countdown_minutes(45)
        self.assertEqual(note.state["timer_mode"], "countdown")
        self.assertTrue(bool(note.state["deadline_at"]))

        # Test locking
        locked_note = self.sticky_manager.set_note_locked(note_id, True)
        self.assertTrue(locked_note.state["locked"])

        unlocked_note = self.sticky_manager.set_note_locked(note_id, False)
        self.assertFalse(unlocked_note.state["locked"])

    def test_audit_store_logging_and_metrics(self):
        self.audit_store.record_event("sticky_created", note_id="n1", title="Task 1")
        self.audit_store.record_event("job_done", note_id="n1", title="Task 1")
        self.audit_store.record_event("sticky_overdue", note_id="n2", title="Task 2")

        metrics = self.audit_store.get_summary_metrics(active_notes_count=2)
        self.assertEqual(metrics["total_created"], 1)
        self.assertEqual(metrics["total_completed"], 1)
        self.assertEqual(metrics["total_overdue"], 1)
        self.assertEqual(metrics["active_count"], 2)

    def test_master_dashboard_ui(self):
        dashboard = MasterDashboard(sticky_manager=self.sticky_manager, audit_store=self.audit_store)
        self.assertIsNotNone(dashboard)

        # Create note and verify it shows in dashboard
        note = self.sticky_manager.create_note()
        note.title_label.setText("Meeting Prep")
        note._set_countdown_minutes(30)

        dashboard.show()
        dashboard.refresh_active_table()
        self.assertEqual(dashboard.active_table.rowCount(), 1)

        dashboard.refresh_history_table()
        self.assertGreaterEqual(dashboard.history_table.rowCount(), 1)
        dashboard.close()

    def test_realistic_sticky_features(self):
        note = self.sticky_manager.create_note()
        self.assertIsNotNone(note)

        # 1. Test Neon Post-it themes
        for neon_theme in [
            "neon_postit_pink",
            "neon_postit_orange",
            "neon_postit_yellow",
            "neon_postit_lime",
            "neon_postit_cyan",
            "neon_postit_purple",
        ]:
            note._set_theme(neon_theme)
            self.assertEqual(note.state["theme_id"], neon_theme)

        # 2. Test Font Presets (15 presets)
        font_presets = list_font_presets()
        self.assertEqual(len(font_presets), 15)
        for preset in font_presets:
            note._set_font_preset(preset.preset_id)
            self.assertEqual(note.state["font_preset"], preset.preset_id)

        # 3. Test Text Size up to 36px and 48px
        note._set_font_size_px(36)
        self.assertEqual(note.state["font_size_px"], 36)
        note._set_font_size_px(48)
        self.assertEqual(note.state["font_size_px"], 48)

        # 4. Test Transparency / Opacity down to 15%
        note._set_opacity(0.30)
        self.assertAlmostEqual(note.state["opacity"], 0.30, places=2)
        note._set_opacity(0.15)
        self.assertAlmostEqual(note.state["opacity"], 0.15, places=2)

        # 5. Test Resizing height smaller (down to 50px)
        note.resize(160, 55)
        self.assertLessEqual(note.height(), 65)
        self.assertGreaterEqual(note.height(), 50)

        # 6. Test StickyFrame custom painting frame exists
        self.assertTrue(hasattr(note, "frame"))
        self.assertEqual(note.frame.objectName(), "stickyFrame")


if __name__ == "__main__":
    unittest.main()

