"""
Telegrama controller — glues the network service to the desktop app.

Responsibilities
* Start/stop the service from user settings (it is **off** until the user opts in).
* Marshal incoming dispatches from the HTTP threads onto the Qt UI thread.
* Open the Telegrama overlay + show a tray notification when a message arrives.
* Persist history/receipts in the user data dir and expose the phone pairing URL.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from config.settings import DEFAULT_TELEGRAMA_PORT, get_app_data_dir
from modules.telegrama_service import TelegramaService
from utils.logger import logger


class TelegramaController(QObject):
    #: emitted on the UI thread for every new inbound dispatch
    message_received = Signal(dict)
    #: emitted whenever enabled / LAN / running state changes (dialogs refresh from this)
    state_changed = Signal()

    def __init__(self, config, overlay_manager=None, tray=None, data_dir: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.overlay_manager = overlay_manager
        self.tray = tray
        self._data_dir = data_dir if data_dir is not None else get_app_data_dir()
        self.service: Optional[TelegramaService] = None
        self.message_received.connect(self._on_message_ui)
        if overlay_manager is not None:
            overlay_manager.set_param_provider("telegrama", self._overlay_params)

    # ---- settings accessors
    @property
    def enabled(self) -> bool:
        return bool(self.config.get("telegrama", "enabled"))

    @property
    def allow_lan(self) -> bool:
        return bool(self.config.get("telegrama", "allow_lan"))

    @property
    def notify(self) -> bool:
        return bool(self.config.get("telegrama", "notify"))

    @property
    def running(self) -> bool:
        return self.service is not None and self.service.running

    @property
    def phone_url(self) -> str:
        return self.service.mobile_url if self.service else ""

    # ---- lifecycle
    def start_if_enabled(self):
        if self.enabled:
            self._start()

    def _start(self) -> bool:
        self.stop(emit=False)
        token = self.config.ensure_telegrama_token() if self.allow_lan else (self.config.get("telegrama", "token") or "")
        port = int(self.config.get("telegrama", "port") or DEFAULT_TELEGRAMA_PORT)
        service = TelegramaService(port=port, allow_lan=self.allow_lan, token=token, data_dir=self._data_dir)
        service.add_listener(self._on_message_thread)
        if not service.start():
            logger.error("Telegrama could not start (port busy?)")
            self.service = None
            self.state_changed.emit()
            return False
        self.service = service
        self.state_changed.emit()
        return True

    def stop(self, emit: bool = True):
        if self.service is not None:
            self.service.stop()
            self.service = None
        if emit:
            self.state_changed.emit()

    def set_enabled(self, enabled: bool):
        self.config.set("telegrama", "enabled", bool(enabled))
        if enabled:
            self._start()
        else:
            self.stop()

    def set_allow_lan(self, allow: bool):
        self.config.set("telegrama", "allow_lan", bool(allow))
        if allow:
            self.config.ensure_telegrama_token()
        if self.enabled:
            self._start()  # rebind to the new interface
        else:
            self.state_changed.emit()

    def set_notify(self, notify: bool):
        self.config.set("telegrama", "notify", bool(notify))
        self.state_changed.emit()

    def regenerate_token(self):
        """Invalidate every previously paired phone."""
        self.config.set("telegrama", "token", "")
        self.config.ensure_telegrama_token()
        if self.enabled:
            self._start()
        else:
            self.state_changed.emit()

    # ---- overlay integration
    def _overlay_params(self) -> dict:
        return {"api": self.service.api_base} if self.running else {}

    def _on_message_thread(self, entry: dict):
        # Called from an HTTP worker thread; the queued signal hops to the UI thread.
        self.message_received.emit(entry)

    def _on_message_ui(self, entry: dict):
        om = self.overlay_manager
        if om is not None and om.available and not om.is_active("telegrama"):
            om.open_overlay("telegrama", save_state=False)
        if self.notify and self.tray is not None:
            try:
                from PySide6.QtWidgets import QSystemTrayIcon

                self.tray.showMessage(
                    f"{entry.get('emoji', '')} Telegrama from {entry.get('sender', 'someone')}".strip(),
                    entry.get("message", ""),
                    QSystemTrayIcon.Information,
                    6000,
                )
            except Exception as exc:  # notifications are best-effort
                logger.debug(f"Tray notification failed: {exc}")
