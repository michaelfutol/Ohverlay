"""
Ohverlay Master Task & Sticky Notes Dashboard.
Comprehensive master control and monitoring center for all active sticky notes,
running elapsed/countdown task timers, overdue alerts, and task history.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modules.card_themes import list_note_themes


class MasterDashboard(QWidget):
    """Master Control & Monitoring Dashboard for all Ohverlay sticky notes and task timers."""

    def __init__(self, sticky_manager, audit_store=None, parent=None):
        super().__init__(parent)
        self.sticky_manager = sticky_manager
        self.audit_store = audit_store

        self.setWindowTitle("Ohverlay — Master Task & Sticky Notes Dashboard")
        self.resize(1060, 680)
        self.setMinimumSize(850, 520)

        self._build_ui()

        # Real-time ticker for live countdown and elapsed times (1-second tick)
        self._live_timer = QTimer(self)
        self._live_timer.timeout.connect(self._tick_live_timers)
        self._live_timer.start(1000)

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #121916;
                color: #e6dcb8;
                font-family: 'Book Antiqua', 'Georgia', serif;
            }
            QTabWidget::pane {
                border: 1px solid #cfa062;
                background-color: #1a2421;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #23312c;
                color: #cfa062;
                border: 1px solid #3c4d46;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1a2421;
                color: #ffefcc;
                border-color: #cfa062;
                border-bottom: 2px solid #1a2421;
            }
            QTabBar::tab:hover {
                background-color: #2f4039;
                color: #dfb880;
            }
            QTableWidget {
                background-color: #151d1a;
                border: 1px solid #2d3d36;
                color: #e6dcb8;
                gridline-color: #23312c;
                selection-background-color: #4a3820;
                selection-color: #fff4d9;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #202b26;
                color: #cfa062;
                border: none;
                border-bottom: 2px solid #cfa062;
                padding: 6px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton {
                background-color: #2b3934;
                color: #e6dcb8;
                border: 1px solid #cfa062;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3c4d46;
                border-color: #dfb880;
            }
            QPushButton:pressed {
                background-color: #5c4424;
                color: #ffefcc;
            }
            QLineEdit, QComboBox {
                background-color: #1e2925;
                color: #e6dcb8;
                border: 1px solid #4a5c54;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #cfa062;
            }
            QComboBox QAbstractItemView {
                background-color: #1a2421;
                color: #e6dcb8;
                border: 1px solid #cfa062;
                selection-background-color: #4a3820;
            }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(10)

        # ── Header Banner ──
        header_frame = QFrame(self)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1a2421;
                border: 1px solid #cfa062;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(10, 6, 10, 6)

        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        title_lbl = QLabel("MASTER TASK & STICKY NOTES DASHBOARD", header_frame)
        title_lbl.setFont(QFont("Book Antiqua", 15, int(QFont.Bold)))
        title_lbl.setStyleSheet("color: #dfb880; border: none; background: transparent;")

        sub_lbl = QLabel("Real-time monitoring for desktop sticky notes, elapsed timers, countdown tasks, and history.", header_frame)
        dash_sub_font = QFont("Book Antiqua", 9)
        dash_sub_font.setItalic(True)
        sub_lbl.setFont(dash_sub_font)
        sub_lbl.setStyleSheet("color: #a89c7c; border: none; background: transparent;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)

        h_layout.addStretch()

        new_note_btn = QPushButton("➕ New Sticky Note", header_frame)
        new_note_btn.setFont(QFont("Book Antiqua", 11, QFont.Bold))
        new_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c4424;
                color: #ffefcc;
                border: 1px solid #dfb880;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #73552e;
            }
        """)
        new_note_btn.clicked.connect(self._create_new_sticky)
        h_layout.addWidget(new_note_btn)

        root_layout.addWidget(header_frame)

        # ── KPI Metrics Cards ──
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(8)

        self.card_active = self._make_kpi_card("ACTIVE NOTES", "0", "#6be585")
        self.card_countdowns = self._make_kpi_card("COUNTDOWNS", "0", "#62c4ff")
        self.card_elapsed = self._make_kpi_card("RUNNING ELAPSED", "0", "#dfb880")
        self.card_overdue = self._make_kpi_card("OVERDUE TASKS", "0", "#ff7b7b")
        self.card_locked = self._make_kpi_card("LOCKED OVERLAYS", "0", "#cfa062")

        self.kpi_layout.addWidget(self.card_active)
        self.kpi_layout.addWidget(self.card_countdowns)
        self.kpi_layout.addWidget(self.card_elapsed)
        self.kpi_layout.addWidget(self.card_overdue)
        self.kpi_layout.addWidget(self.card_locked)
        root_layout.addLayout(self.kpi_layout)

        # ── Tabs ──
        self.tabs = QTabWidget(self)
        self.tab_active = QWidget()
        self.tab_history = QWidget()

        self._build_active_tab()
        self._build_history_tab()

        self.tabs.addTab(self.tab_active, "📌 Active Notes & Running Timers")
        self.tabs.addTab(self.tab_history, "📜 Task History & Audit Log")

        root_layout.addWidget(self.tabs, 1)

    def _make_kpi_card(self, label: str, value: str, color_hex: str) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #1a2421;
                border: 1px solid #2d3d36;
                border-radius: 5px;
                padding: 4px;
            }}
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(8, 4, 8, 4)
        vbox.setSpacing(1)

        lbl = QLabel(label, frame)
        lbl.setFont(QFont("Book Antiqua", 8, QFont.Bold))
        lbl.setStyleSheet("color: #8c8369; border: none; background: transparent;")

        val = QLabel(value, frame)
        val.setFont(QFont("Book Antiqua", 14, QFont.Bold))
        val.setStyleSheet(f"color: {color_hex}; border: none; background: transparent;")
        val.setObjectName("kpiVal")

        vbox.addWidget(lbl)
        vbox.addWidget(val)
        return frame

    def _build_active_tab(self):
        layout = QVBoxLayout(self.tab_active)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Toolbar row
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Search / Filter:"))
        self.active_search_input = QLineEdit(self.tab_active)
        self.active_search_input.setPlaceholderText("Filter by title or note text…")
        self.active_search_input.textChanged.connect(self.refresh_active_table)
        toolbar.addWidget(self.active_search_input, 2)

        toolbar.addWidget(QLabel("Timer Mode:"))
        self.timer_filter_combo = QComboBox(self.tab_active)
        self.timer_filter_combo.addItems(["All Timers", "Countdown Only", "Elapsed Only", "Overdue Only", "No Timer"])
        self.timer_filter_combo.currentIndexChanged.connect(self.refresh_active_table)
        toolbar.addWidget(self.timer_filter_combo)

        toolbar.addStretch()

        show_all_btn = QPushButton("👁️ Show All", self.tab_active)
        show_all_btn.clicked.connect(lambda: self.sticky_manager.show_all())
        toolbar.addWidget(show_all_btn)

        hide_all_btn = QPushButton("🙈 Hide All", self.tab_active)
        hide_all_btn.clicked.connect(lambda: self.sticky_manager.hide_all())
        toolbar.addWidget(hide_all_btn)

        refresh_btn = QPushButton("🔄 Refresh", self.tab_active)
        refresh_btn.clicked.connect(self.refresh_active_table)
        toolbar.addWidget(refresh_btn)

        layout.addLayout(toolbar)

        # Active Notes Table
        self.active_table = QTableWidget(0, 8, self.tab_active)
        self.active_table.setHorizontalHeaderLabels([
            "NOTE ID", "TITLE", "CONTENT PREVIEW", "TIMER MODE", "LIVE TIMER", "DEADLINE", "THEME", "LOCKED"
        ])
        self.active_table.verticalHeader().setVisible(False)
        self.active_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.active_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.active_table.horizontalHeader().setStretchLastSection(False)
        self.active_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.active_table.setColumnWidth(0, 90)
        self.active_table.setColumnWidth(1, 140)
        self.active_table.setColumnWidth(3, 110)
        self.active_table.setColumnWidth(4, 110)
        self.active_table.setColumnWidth(5, 140)
        self.active_table.setColumnWidth(6, 130)
        self.active_table.setColumnWidth(7, 80)
        layout.addWidget(self.active_table, 1)

        # Bottom actions for selected row
        btn_row = QHBoxLayout()
        btn_lock = QPushButton("🔒 / 🔓 Toggle Lock", self.tab_active)
        btn_lock.clicked.connect(self._toggle_selected_lock)
        btn_row.addWidget(btn_lock)

        btn_timer = QPushButton("⏱️ Set Countdown", self.tab_active)
        btn_timer.clicked.connect(self._set_selected_countdown)
        btn_row.addWidget(btn_timer)

        btn_extend = QPushButton("⏳ Extend (+30m)", self.tab_active)
        btn_extend.clicked.connect(self._extend_selected_countdown)
        btn_row.addWidget(btn_extend)

        btn_theme = QPushButton("🎨 Change Theme", self.tab_active)
        btn_theme.clicked.connect(self._cycle_selected_theme)
        btn_row.addWidget(btn_theme)

        btn_row.addStretch()

        btn_delete = QPushButton("🗑️ Close Note", self.tab_active)
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #4a2525;
                border: 1px solid #cfa062;
                color: #ffcccc;
            }
            QPushButton:hover {
                background-color: #6a3535;
            }
        """)
        btn_delete.clicked.connect(self._delete_selected_note)
        btn_row.addWidget(btn_delete)

        layout.addLayout(btn_row)

    def _build_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Filter row
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Search History:"))
        self.history_search_input = QLineEdit(self.tab_history)
        self.history_search_input.setPlaceholderText("Filter events, titles, details…")
        self.history_search_input.textChanged.connect(self.refresh_history_table)
        toolbar.addWidget(self.history_search_input, 2)

        toolbar.addStretch()

        export_btn = QPushButton("💾 Export History", self.tab_history)
        export_btn.clicked.connect(self._export_history)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("🧹 Clear History", self.tab_history)
        clear_btn.clicked.connect(self._clear_history)
        toolbar.addWidget(clear_btn)

        refresh_h_btn = QPushButton("🔄 Refresh", self.tab_history)
        refresh_h_btn.clicked.connect(self.refresh_history_table)
        toolbar.addWidget(refresh_h_btn)

        layout.addLayout(toolbar)

        # History Table
        self.history_table = QTableWidget(0, 6, self.tab_history)
        self.history_table.setHorizontalHeaderLabels([
            "TIMESTAMP", "EVENT TYPE", "NOTE ID", "TITLE", "ACTION / STATUS", "DETAILS"
        ])
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.history_table.setColumnWidth(0, 150)
        self.history_table.setColumnWidth(1, 130)
        self.history_table.setColumnWidth(2, 90)
        self.history_table.setColumnWidth(3, 150)
        self.history_table.setColumnWidth(4, 130)
        layout.addWidget(self.history_table, 1)

    # ── Live Tickers & Data Refresh ──

    def _tick_live_timers(self):
        if not self.isVisible():
            return
        self._update_kpi_cards()
        self.refresh_active_table(preserve_selection=True)

    def _update_kpi_cards(self):
        if not self.sticky_manager:
            return
        rows = self.sticky_manager.dashboard_rows()
        active_count = len(rows)
        countdowns = sum(1 for r in rows if r.get("timer_mode") == "countdown")
        elapsed = sum(1 for r in rows if r.get("timer_mode") == "elapsed")
        overdue = sum(1 for r in rows if r.get("is_overdue"))
        locked = sum(1 for r in rows if r.get("locked"))

        self.card_active.findChild(QLabel, "kpiVal").setText(str(active_count))
        self.card_countdowns.findChild(QLabel, "kpiVal").setText(str(countdowns))
        self.card_elapsed.findChild(QLabel, "kpiVal").setText(str(elapsed))
        self.card_overdue.findChild(QLabel, "kpiVal").setText(str(overdue))
        self.card_locked.findChild(QLabel, "kpiVal").setText(str(locked))

    def refresh_active_table(self, preserve_selection: bool = False):
        if not self.sticky_manager:
            return

        selected_id = ""
        if preserve_selection and self.active_table.currentRow() >= 0:
            item = self.active_table.item(self.active_table.currentRow(), 0)
            if item:
                selected_id = item.text()

        search_query = self.active_search_input.text().strip().lower()
        timer_filter = self.timer_filter_combo.currentText()

        all_rows = self.sticky_manager.dashboard_rows()
        filtered_rows = []

        for r in all_rows:
            note_id = r.get("note_id", "")
            widget = self.sticky_manager.get_note(note_id)
            text_preview = widget.text_edit.toPlainText() if widget else ""

            # Search filter
            if search_query:
                combined = f"{r.get('title', '')} {text_preview} {note_id}".lower()
                if search_query not in combined:
                    continue

            # Timer filter
            t_mode = r.get("timer_mode", "off")
            is_overdue = r.get("is_overdue", False)
            if timer_filter == "Countdown Only" and t_mode != "countdown":
                continue
            elif timer_filter == "Elapsed Only" and t_mode != "elapsed":
                continue
            elif timer_filter == "Overdue Only" and not is_overdue:
                continue
            elif timer_filter == "No Timer" and t_mode != "off":
                continue

            filtered_rows.append((r, text_preview))

        self.active_table.setRowCount(len(filtered_rows))
        restore_row_index = -1

        for row_idx, (r, text_preview) in enumerate(filtered_rows):
            note_id = r.get("note_id", "")
            title = r.get("title", "Sticky Note")
            t_mode = r.get("timer_mode", "off")
            t_label = r.get("timer_label", "--:--:--")
            deadline = r.get("deadline_at", "")
            theme_id = r.get("theme_id", "")
            locked = "🔒 Yes" if r.get("locked") else "🔓 No"
            is_overdue = r.get("is_overdue", False)

            if note_id == selected_id:
                restore_row_index = row_idx

            clean_preview = text_preview.replace("\n", " ")[:60]

            item_id = QTableWidgetItem(note_id)
            item_title = QTableWidgetItem(title)
            item_preview = QTableWidgetItem(clean_preview)
            item_mode = QTableWidgetItem(t_mode.upper())
            item_timer = QTableWidgetItem(t_label)
            item_deadline = QTableWidgetItem(deadline.replace("T", " ") if deadline else "—")
            item_theme = QTableWidgetItem(theme_id)
            item_locked = QTableWidgetItem(locked)

            # Highlighting for timers
            if is_overdue:
                item_timer.setForeground(QColor("#ff6b6b"))
                item_mode.setForeground(QColor("#ff6b6b"))
            elif t_mode == "countdown":
                item_timer.setForeground(QColor("#62c4ff"))
            elif t_mode == "elapsed":
                item_timer.setForeground(QColor("#dfb880"))

            self.active_table.setItem(row_idx, 0, item_id)
            self.active_table.setItem(row_idx, 1, item_title)
            self.active_table.setItem(row_idx, 2, item_preview)
            self.active_table.setItem(row_idx, 3, item_mode)
            self.active_table.setItem(row_idx, 4, item_timer)
            self.active_table.setItem(row_idx, 5, item_deadline)
            self.active_table.setItem(row_idx, 6, item_theme)
            self.active_table.setItem(row_idx, 7, item_locked)

        if restore_row_index >= 0:
            self.active_table.selectRow(restore_row_index)

    def refresh_history_table(self):
        if not self.audit_store:
            return

        query = self.history_search_input.text().strip().lower()
        events = self.audit_store.fetch_recent(limit=150)

        filtered = []
        for e in events:
            if query:
                combined = f"{e.get('timestamp', '')} {e.get('event', '')} {e.get('title', '')} {json.dumps(e.get('details', {}))}".lower()
                if query not in combined:
                    continue
            filtered.append(e)

        self.history_table.setRowCount(len(filtered))
        for row_idx, e in enumerate(filtered):
            ts = e.get("timestamp", "").replace("T", " ")
            event_type = e.get("event", "")
            note_id = e.get("note_id", "")
            title = e.get("title", "")
            action = e.get("action", "") or e.get("event", "")
            details = json.dumps(e.get("details", {}))

            self.history_table.setItem(row_idx, 0, QTableWidgetItem(ts))
            self.history_table.setItem(row_idx, 1, QTableWidgetItem(event_type))
            self.history_table.setItem(row_idx, 2, QTableWidgetItem(note_id))
            self.history_table.setItem(row_idx, 3, QTableWidgetItem(title))
            self.history_table.setItem(row_idx, 4, QTableWidgetItem(action))
            self.history_table.setItem(row_idx, 5, QTableWidgetItem(details))

    # ── User Actions ──

    def _create_new_sticky(self):
        if self.sticky_manager:
            note = self.sticky_manager.create_note()
            note.show()
            note.raise_()
            note.activateWindow()
            self._update_kpi_cards()
            self.refresh_active_table()
            self.refresh_history_table()

    def _get_selected_note_widget(self):
        row = self.active_table.currentRow()
        if row < 0:
            return None
        item = self.active_table.item(row, 0)
        if not item:
            return None
        note_id = item.text()
        return self.sticky_manager.get_note(note_id)

    def _toggle_selected_lock(self):
        widget = self._get_selected_note_widget()
        if not widget:
            QMessageBox.information(self, "Select Note", "Please select a sticky note row first.")
            return
        is_locked = widget.state.get("locked", False)
        self.sticky_manager.set_note_locked(widget.state.get("id"), not is_locked)
        self.refresh_active_table()

    def _set_selected_countdown(self):
        widget = self._get_selected_note_widget()
        if not widget:
            QMessageBox.information(self, "Select Note", "Please select a sticky note row first.")
            return

        text, ok = QInputDialog.getText(
            self,
            "Set Task Countdown",
            "Enter duration (e.g. 15m, 30m, 1h, 2h, 01:30:00):",
            text="30m",
        )
        if ok and text.strip():
            from modules.sticky_notes import _parse_duration_input
            seconds = _parse_duration_input(text)
            if seconds:
                widget._set_countdown_seconds(seconds)
                self.sticky_manager.record_note_event("timer_countdown_set", widget)
                self.refresh_active_table()
                self.refresh_history_table()

    def _extend_selected_countdown(self):
        widget = self._get_selected_note_widget()
        if not widget:
            QMessageBox.information(self, "Select Note", "Please select a sticky note row first.")
            return
        widget._set_countdown_minutes(30)
        self.sticky_manager.record_note_event("timer_extended", widget)
        self.refresh_active_table()
        self.refresh_history_table()

    def _cycle_selected_theme(self):
        widget = self._get_selected_note_widget()
        if not widget:
            QMessageBox.information(self, "Select Note", "Please select a sticky note row first.")
            return
        themes = list_note_themes()
        current = widget.state.get("theme_id")
        current_idx = next((i for i, t in enumerate(themes) if t.theme_id == current), 0)
        next_theme = themes[(current_idx + 1) % len(themes)]
        widget._set_theme(next_theme.theme_id)
        self.refresh_active_table()

    def _delete_selected_note(self):
        widget = self._get_selected_note_widget()
        if not widget:
            QMessageBox.information(self, "Select Note", "Please select a sticky note row first.")
            return
        title = widget.state.get("title", "Sticky Note")
        reply = QMessageBox.question(
            self,
            "Close Sticky Note",
            f"Are you sure you want to close and remove '{title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            widget._close_note()
            self._update_kpi_cards()
            self.refresh_active_table()
            self.refresh_history_table()

    def _export_history(self):
        if not self.audit_store:
            return
        events = self.audit_store.fetch_all()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Task History",
            f"ohverlay_sticky_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(events, f, indent=2)
                QMessageBox.information(self, "Export Successful", f"Saved {len(events)} events to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error exporting history: {e}")

    def _clear_history(self):
        if not self.audit_store:
            return
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the task and timer history log?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.audit_store.clear_history()
            self.refresh_history_table()

    def showEvent(self, event):
        self._update_kpi_cards()
        self.refresh_active_table()
        self.refresh_history_table()
        super().showEvent(event)
