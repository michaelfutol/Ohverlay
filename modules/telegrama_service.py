"""
Telegrama Service - Lightweight background HTTP service for 2-way paper telegram dispatches.
Allows family members and OFWs to send short, loving reminders from mobile/web straight to Ohverlay desktop.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from utils.logger import logger


def get_local_ip() -> str:
    """Detect the local machine LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually establish a connection; used to query routing table
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


class TelegramaStore:
    """Thread-safe in-memory store for telegram dispatches and replies."""

    def __init__(self):
        self._lock = threading.Lock()
        self.dispatches: list[dict] = []
        self.replies: dict[str, dict] = {}
        self.latest_dispatch: dict | None = None
        self._subscribers: list[threading.Event] = []

    def add_dispatch(self, data: dict) -> dict:
        with self._lock:
            msg_id = data.get("id") or f"tg_{int(time.time() * 1000)}"
            entry = {
                "id": msg_id,
                "sender": data.get("sender", "Mahal Ko"),
                "message": data.get("message", ""),
                "tag": data.get("tag", "love"),
                "emoji": data.get("emoji", "❤️"),
                "timestamp": data.get("timestamp") or int(time.time() * 1000),
                "location": data.get("location", "FAMILY DISPATCH"),
            }
            self.dispatches.append(entry)
            self.latest_dispatch = entry
            # Wake up all SSE / waiting listeners
            for ev in self._subscribers:
                ev.set()
            return entry

    def add_reply(self, msg_id: str, reply_text: str) -> dict:
        with self._lock:
            reply_entry = {
                "id": msg_id,
                "reply": reply_text,
                "timestamp": int(time.time() * 1000),
            }
            self.replies[msg_id] = reply_entry
            return reply_entry

    def get_status(self, msg_id: str) -> dict | None:
        with self._lock:
            return self.replies.get(msg_id)

    def get_latest(self) -> dict | None:
        with self._lock:
            return self.latest_dispatch

    def register_waiter(self) -> threading.Event:
        with self._lock:
            ev = threading.Event()
            self._subscribers.append(ev)
            return ev

    def unregister_waiter(self, ev: threading.Event):
        with self._lock:
            if ev in self._subscribers:
                self._subscribers.remove(ev)


_GLOBAL_STORE = TelegramaStore()


class TelegramaHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler serving Mobile Dispatcher and REST / SSE APIs."""

    def log_message(self, format, *args):
        # Silence verbose request logs unless error
        pass

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # ─── Mobile Dispatcher Page ───
        if path in ("/", "/telegrama", "/mobile"):
            mobile_html_path = os.path.join(os.path.dirname(__file__), "telegrama_mobile.html")
            if os.path.exists(mobile_html_path):
                with open(mobile_html_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(content)
                return

        # ─── Latest message poll ───
        if path == "/api/latest":
            latest = _GLOBAL_STORE.get_latest()
            resp = json.dumps(latest or {}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        # ─── Check Reply Status ───
        if path == "/api/status":
            query = parse_qs(parsed.query)
            msg_id = query.get("id", [None])[0]
            status = _GLOBAL_STORE.get_status(msg_id) if msg_id else None
            resp = json.dumps(status or {}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        # ─── Server-Sent Events (SSE) ───
        if path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._send_cors_headers()
            self.end_headers()

            ev = _GLOBAL_STORE.register_waiter()
            try:
                # Send latest if recent (< 30s)
                latest = _GLOBAL_STORE.get_latest()
                if latest and (time.time() * 1000 - latest["timestamp"] < 30000):
                    self.wfile.write(f"data: {json.dumps(latest)}\n\n".encode("utf-8"))
                    self.wfile.flush()

                while True:
                    ev.wait(timeout=15.0)
                    ev.clear()
                    latest = _GLOBAL_STORE.get_latest()
                    if latest:
                        self.wfile.write(f"data: {json.dumps(latest)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                    else:
                        # Keep-alive heartbeat
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
            except Exception:
                pass
            finally:
                _GLOBAL_STORE.unregister_waiter(ev)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        # ─── Dispatch new telegram ───
        if path == "/api/dispatch":
            entry = _GLOBAL_STORE.add_dispatch(data)
            logger.info(f"Telegrama Dispatched: [{entry.get('sender')}] {entry.get('message')}")
            resp = json.dumps({"status": "ok", "entry": entry}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        # ─── 2-Way Reply from desktop ───
        if path == "/api/reply":
            msg_id = data.get("id", "")
            reply_text = data.get("reply", "")
            if msg_id and reply_text:
                reply_entry = _GLOBAL_STORE.add_reply(msg_id, reply_text)
                logger.info(f"Telegrama Reply: [{msg_id}] {reply_text}")
                resp = json.dumps({"status": "ok", "reply": reply_entry}).encode("utf-8")
            else:
                resp = json.dumps({"status": "error", "message": "Missing id or reply"}).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(resp)
            return

        self.send_response(404)
        self.end_headers()


class TelegramaService:
    """Manages the background HTTP daemon for Telegrama dispatches."""

    def __init__(self, host: str = "0.0.0.0", port: int = 54321):
        self.host = host
        self.port = port
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.local_ip = get_local_ip()

    def start(self) -> bool:
        if self.server is not None:
            return True

        for p in range(self.port, self.port + 10):
            try:
                self.server = ThreadingHTTPServer((self.host, p), TelegramaHTTPHandler)
                self.port = p
                break
            except OSError:
                continue

        if self.server is None:
            logger.error(f"TelegramaService: Could not bind to port {self.port}..{self.port+9}")
            return False

        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="TelegramaService")
        self.thread.start()
        logger.info(f"Telegrama Service running at http://{self.local_ip}:{self.port}/telegrama")
        return True

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
            self.thread = None
            logger.info("Telegrama Service stopped")

    @property
    def mobile_url(self) -> str:
        return f"http://{self.local_ip}:{self.port}/telegrama"

    def dispatch_message(self, sender: str, message: str, tag: str = "love", emoji: str = "❤️") -> dict:
        """Programmatically send a dispatch (e.g. from tests or desktop triggers)."""
        return _GLOBAL_STORE.add_dispatch({
            "sender": sender,
            "message": message,
            "tag": tag,
            "emoji": emoji,
        })
