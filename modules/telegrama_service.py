"""
Telegrama Service — local, private, two-way "paper telegram" dispatches for family and OFWs.

A family member opens the phone page, writes a short loving reminder, and it appears on the
desktop as a telegram card. The desktop can send a quick reply back, and the sender sees
live delivery receipts:  queued -> delivered -> read -> replied.

Security model (this used to be an always-on, unauthenticated 0.0.0.0 server with CORS *)
-------------------------------------------------------------------------------------
* The service is **opt-in** and binds to **127.0.0.1** unless "allow_lan" is enabled.
* Same-machine clients (the overlay) need no token but must pass Origin + Host checks, so a
  random website or DNS-rebinding trick cannot talk to it.
* Phones on the LAN need the pairing token (``?t=...`` / ``X-Telegrama-Token``), compared in
  constant time, and may only use: the mobile page, /api/health, POST /api/dispatch and
  GET /api/status. They can never read the desktop's inbox, history, or reply as the desktop.
* Request bodies are capped, JSON content-type is required (forces a CORS preflight), field
  lengths are capped, remote senders are rate limited, and SSE connections are bounded.

History is persisted (capped) so messages and receipts survive restarts.
"""

from __future__ import annotations

import hmac
import ipaddress
import json
import os
import re
import secrets
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

from utils.logger import logger
from utils.paths import resource_path

API_VERSION = 2
DEFAULT_PORT = 54321

MAX_BODY_BYTES = 8 * 1024
MAX_MESSAGE_CHARS = 280
MAX_SENDER_CHARS = 32
MAX_REPLY_CHARS = 280
MAX_LOCATION_CHARS = 40
MAX_EMOJI_CHARS = 8
MAX_HISTORY = 200
MAX_SSE_CLIENTS = 8
SSE_HEARTBEAT_SECONDS = 15.0
UNREAD_MAX_AGE_SECONDS = 24 * 3600

ALLOWED_TAGS = {"love", "medicine", "food", "break", "meeting", "sleep", "general"}
STATE_ORDER = {"queued": 0, "delivered": 1, "read": 2, "replied": 3}
_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}


# ─────────────────────────────── helpers ───────────────────────────────

def get_local_ip() -> str:
    """Detect the local machine LAN IP address (no packets are sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def sanitize_text(value, max_len: int, *, single_line: bool = True) -> str:
    """Coerce to a clean, length-capped string (never raises on odd JSON types)."""
    if value is None:
        return ""
    text = str(value)
    text = _CONTROL_RE.sub("", text)
    if single_line:
        text = " ".join(text.split())
    else:
        text = text.strip()
    return text[:max_len]


def is_loopback_address(addr: str) -> bool:
    try:
        return ipaddress.ip_address(addr.split("%")[0]).is_loopback
    except ValueError:
        return False


class RateLimiter:
    """Sliding-window limiter keyed by client address."""

    def __init__(self, max_events: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.max_events = max_events
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> float:
        """Return 0 if allowed, else seconds until the next slot frees up."""
        now = self._clock()
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if now - t < self.window]
            if len(hits) >= self.max_events:
                self._hits[key] = hits
                return max(0.1, self.window - (now - hits[0]))
            hits.append(now)
            self._hits[key] = hits
            if len(self._hits) > 512:  # bound memory against many distinct clients
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
                    self._hits.pop(k, None)
            return 0.0


# ─────────────────────────────── store ───────────────────────────────

class TelegramaStore:
    """Thread-safe, optionally persisted store of dispatches, receipts and replies."""

    def __init__(self, path: Optional[str] = None, max_history: int = MAX_HISTORY):
        self._lock = threading.Lock()
        self._path = path
        self._max = max(10, int(max_history))
        self._entries: list[dict] = []
        self._by_id: dict[str, dict] = {}
        self._seq = 0
        self._subscribers: list[threading.Event] = []
        self._load()

    # ---- persistence
    def _load(self):
        if not self._path or not os.path.exists(self._path):
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = data.get("entries", []) if isinstance(data, dict) else []
            for entry in entries:
                if isinstance(entry, dict) and _ID_RE.match(str(entry.get("id", ""))):
                    self._entries.append(entry)
                    self._by_id[entry["id"]] = entry
                    self._seq = max(self._seq, int(entry.get("seq", 0)))
        except Exception as exc:
            logger.warning(f"Telegrama history unreadable ({exc}); starting fresh")
            try:
                os.replace(self._path, self._path + ".corrupt")
            except OSError:
                pass

    def _save_locked(self):
        if not self._path:
            return
        try:
            tmp = self._path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"version": API_VERSION, "entries": self._entries}, f, ensure_ascii=False)
            os.replace(tmp, self._path)
        except Exception as exc:
            logger.error(f"Telegrama history save failed: {exc}")

    # ---- mutations
    def add_dispatch(self, data: dict) -> tuple[Optional[dict], bool]:
        """Validate + store a dispatch. Returns (entry, created). Idempotent on a repeated id."""
        message = sanitize_text(data.get("message"), MAX_MESSAGE_CHARS)
        if not message:
            return None, False

        raw_id = str(data.get("id") or "")
        msg_id = raw_id if _ID_RE.match(raw_id) else f"tg_{secrets.token_hex(6)}"

        with self._lock:
            existing = self._by_id.get(msg_id)
            if existing is not None:
                return dict(existing), False  # a flaky phone retrying must not double-deliver

            tag = sanitize_text(data.get("tag"), 16).lower()
            self._seq += 1
            now_ms = int(time.time() * 1000)
            entry = {
                "id": msg_id,
                "seq": self._seq,
                "number": self._seq,
                "sender": sanitize_text(data.get("sender"), MAX_SENDER_CHARS) or "Mahal Ko",
                "message": message,
                "tag": tag if tag in ALLOWED_TAGS else "general",
                "emoji": sanitize_text(data.get("emoji"), MAX_EMOJI_CHARS) or "❤️",
                "location": sanitize_text(data.get("location"), MAX_LOCATION_CHARS) or "FAMILY DISPATCH",
                "timestamp": now_ms,
                "state": "queued",
                "delivered_at": None,
                "read_at": None,
                "reply": None,
                "reply_at": None,
            }
            self._entries.append(entry)
            self._by_id[msg_id] = entry
            while len(self._entries) > self._max:
                dropped = self._entries.pop(0)
                self._by_id.pop(dropped["id"], None)
            self._save_locked()
            snapshot = dict(entry)
            waiters = list(self._subscribers)
        for ev in waiters:
            ev.set()
        return snapshot, True

    def mark(self, msg_id: str, state: str) -> Optional[dict]:
        """Advance delivery state (never backwards). Returns the entry or None if unknown."""
        if state not in ("delivered", "read"):
            return None
        with self._lock:
            entry = self._by_id.get(msg_id)
            if entry is None:
                return None
            now_ms = int(time.time() * 1000)
            if STATE_ORDER[state] > STATE_ORDER[entry["state"]]:
                entry["state"] = state
            if state == "delivered" and not entry["delivered_at"]:
                entry["delivered_at"] = now_ms
            if state == "read":
                entry["delivered_at"] = entry["delivered_at"] or now_ms
                entry["read_at"] = entry["read_at"] or now_ms
            self._save_locked()
            return dict(entry)

    def add_reply(self, msg_id: str, reply_text: str) -> Optional[dict]:
        text = sanitize_text(reply_text, MAX_REPLY_CHARS)
        if not text:
            return None
        with self._lock:
            entry = self._by_id.get(msg_id)
            if entry is None:
                return None
            now_ms = int(time.time() * 1000)
            entry["reply"] = text
            entry["reply_at"] = now_ms
            entry["delivered_at"] = entry["delivered_at"] or now_ms
            entry["read_at"] = entry["read_at"] or now_ms
            entry["state"] = "replied"
            self._save_locked()
            return {"id": msg_id, "reply": text, "timestamp": now_ms}

    # ---- queries
    def get(self, msg_id: str) -> Optional[dict]:
        with self._lock:
            entry = self._by_id.get(msg_id)
            return dict(entry) if entry else None

    def get_latest(self) -> Optional[dict]:
        with self._lock:
            return dict(self._entries[-1]) if self._entries else None

    def last_seq(self) -> int:
        with self._lock:
            return self._seq

    def since(self, seq: int) -> list[dict]:
        with self._lock:
            return [dict(e) for e in self._entries if e["seq"] > seq]

    def unread(self, max_age_seconds: float = UNREAD_MAX_AGE_SECONDS) -> list[dict]:
        cutoff = (time.time() - max_age_seconds) * 1000
        with self._lock:
            return [dict(e) for e in self._entries
                    if STATE_ORDER[e["state"]] < STATE_ORDER["read"] and e["timestamp"] >= cutoff]

    def history(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(int(limit), self._max))
        with self._lock:
            return [dict(e) for e in reversed(self._entries[-limit:])]

    # ---- push
    def register_waiter(self) -> threading.Event:
        ev = threading.Event()
        with self._lock:
            self._subscribers.append(ev)
        return ev

    def unregister_waiter(self, ev: threading.Event):
        with self._lock:
            if ev in self._subscribers:
                self._subscribers.remove(ev)


# ─────────────────────────────── http ───────────────────────────────

# What a phone on the LAN (token holder) may do. Everything else is desktop-only.
_REMOTE_GET = {"/", "/telegrama", "/mobile", "/api/health", "/api/status"}
_REMOTE_POST = {"/api/dispatch"}


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False  # on Windows SO_REUSEADDR lets a second process hijack the port

    def server_bind(self):
        exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
        if exclusive is not None:
            self.socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        super().server_bind()


class TelegramaHTTPHandler(BaseHTTPRequestHandler):
    server_version = "OhverlayTelegrama/2"
    sys_version = ""
    timeout = 30

    @property
    def service(self) -> "TelegramaService":
        return self.server.service  # type: ignore[attr-defined]

    def log_message(self, format, *args):  # noqa: A002 - signature fixed by BaseHTTPRequestHandler
        pass

    # ---- security
    def _client_ip(self) -> str:
        return self.client_address[0]

    def _is_local(self) -> bool:
        return is_loopback_address(self._client_ip())

    def _allowed_hosts(self) -> set[str]:
        hosts = set(_LOOPBACK_HOSTS)
        if self.service.allow_lan:
            hosts.add(self.service.local_ip)
        return hosts

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin or origin == "null":  # no Origin = non-browser client; "null" = file:// overlay
            return True
        host = urlparse(origin).hostname or ""
        return host in self._allowed_hosts() or f"[{host}]" in self._allowed_hosts()

    def _host_ok(self) -> bool:
        host_header = self.headers.get("Host", "")
        if not host_header:
            return True
        host = host_header.rsplit(":", 1)[0] if not host_header.startswith("[") else host_header.split("]")[0] + "]"
        return host in self._allowed_hosts()

    def _token_ok(self, query: dict) -> bool:
        expected = self.service.token
        if not expected:
            return False
        supplied = self.headers.get("X-Telegrama-Token") or (query.get("t", [""])[0])
        return hmac.compare_digest(str(supplied).encode(), expected.encode())

    def _authorize(self, path: str, method: str, query: dict) -> bool:
        """Apply the security model; sends the error response itself when denying."""
        if self._is_local():
            if not self._host_ok() or not self._origin_ok():
                self._send_json(403, {"status": "error", "message": "Forbidden origin"})
                return False
            return True
        allowed = _REMOTE_GET if method == "GET" else _REMOTE_POST
        if not self.service.allow_lan or path not in allowed:
            self._send_json(403, {"status": "error", "message": "Not available remotely"})
            return False
        if not self._token_ok(query):
            self._send_json(401, {"status": "error", "message": "Pairing token required"})
            return False
        return True

    # ---- responses
    def _cors_headers(self):
        origin = self.headers.get("Origin")
        if origin and self._origin_ok():
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Telegrama-Token")

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")

    def _send_json(self, status: int, payload, extra_headers: Optional[dict] = None):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._security_headers()
        self._cors_headers()
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_empty(self, status: int):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self._security_headers()
        self._cors_headers()
        self.end_headers()

    def _public(self, entry: Optional[dict]) -> dict:
        return entry or {}

    # ---- verbs
    def do_OPTIONS(self):
        if self._is_local() and (not self._origin_ok() or not self._host_ok()):
            return self._send_empty(403)
        self._send_empty(204)

    def do_GET(self):
        parsed = urlparse(self.path)
        path, query = parsed.path.rstrip("/") or "/", parse_qs(parsed.query)
        if not self._authorize(path, "GET", query):
            return
        store = self.service.store

        if path in ("/", "/telegrama", "/mobile"):
            return self._serve_mobile_page()
        if path == "/api/health":
            return self._send_json(200, {"ok": True, "name": "ohverlay-telegrama", "version": API_VERSION})
        if path == "/api/latest":
            return self._send_json(200, self._public(store.get_latest()))
        if path == "/api/unread":
            return self._send_json(200, {"messages": store.unread(), "last_seq": store.last_seq()})
        if path == "/api/history":
            try:
                limit = int(query.get("limit", ["50"])[0])
            except ValueError:
                limit = 50
            return self._send_json(200, {"messages": store.history(limit)})
        if path == "/api/status":
            msg_id = query.get("id", [""])[0]
            entry = store.get(msg_id) if _ID_RE.match(msg_id) else None
            return self._send_json(200, self._status_view(entry))
        if path == "/api/events":
            return self._serve_events(query)
        self._send_json(404, {"status": "error", "message": "Not found"})

    @staticmethod
    def _status_view(entry: Optional[dict]) -> dict:
        if not entry:
            return {}
        return {k: entry.get(k) for k in
                ("id", "state", "delivered_at", "read_at", "reply", "reply_at", "timestamp")}

    def _serve_mobile_page(self):
        page = resource_path("modules/telegrama_mobile.html")
        if not os.path.exists(page):
            return self._send_json(404, {"status": "error", "message": "Mobile page missing"})
        with open(page, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                         "connect-src 'self'; img-src data:; base-uri 'none'; form-action 'none'")
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _serve_events(self, query: dict):
        service = self.service
        if not service.acquire_sse():
            return self._send_json(503, {"status": "error", "message": "Too many listeners"})
        store = service.store
        ev = store.register_waiter()
        try:
            try:
                last_seq = int(query.get("after", [self.headers.get("Last-Event-ID") or store.last_seq()])[0])
            except (ValueError, TypeError):
                last_seq = store.last_seq()

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Accel-Buffering", "no")
            self._cors_headers()
            self.end_headers()
            self.wfile.write(b"retry: 3000\n\n")
            self.wfile.flush()

            while not service.stopping.is_set():
                fresh = store.since(last_seq)
                if fresh:
                    for entry in fresh:
                        last_seq = max(last_seq, entry["seq"])
                        payload = json.dumps(entry, ensure_ascii=False)
                        self.wfile.write(f"id: {entry['seq']}\ndata: {payload}\n\n".encode("utf-8"))
                    self.wfile.flush()
                    continue
                if ev.wait(timeout=SSE_HEARTBEAT_SECONDS):
                    ev.clear()
                else:  # genuine idle timeout -> heartbeat only (the old loop re-sent the last message)
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
        except (OSError, ValueError):
            pass  # client went away
        finally:
            store.unregister_waiter(ev)
            service.release_sse()

    def _read_json_body(self) -> Optional[dict]:
        """Parse a bounded JSON object body; sends the error response itself on failure."""
        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype != "application/json":
            self._send_json(415, {"status": "error", "message": "Content-Type must be application/json"})
            return None
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            self._send_json(400, {"status": "error", "message": "Bad Content-Length"})
            return None
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"status": "error", "message": "Request too large"})
            return None
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {"status": "error", "message": "Invalid JSON"})
            return None
        if not isinstance(data, dict):
            self._send_json(400, {"status": "error", "message": "JSON object expected"})
            return None
        return data

    def do_POST(self):
        parsed = urlparse(self.path)
        path, query = parsed.path.rstrip("/") or "/", parse_qs(parsed.query)
        if not self._authorize(path, "POST", query):
            return
        if path not in ("/api/dispatch", "/api/reply", "/api/ack"):
            return self._send_json(404, {"status": "error", "message": "Not found"})

        data = self._read_json_body()
        if data is None:
            return
        service = self.service

        if path == "/api/dispatch":
            limiter = service.local_limiter if self._is_local() else service.remote_limiter
            wait = limiter.check(self._client_ip())
            if wait:
                return self._send_json(429, {"status": "error", "message": "Slow down, mahal ko — too many telegrams"},
                                       {"Retry-After": str(int(wait) + 1)})
            entry, created = service.store.add_dispatch(data)
            if entry is None:
                return self._send_json(400, {"status": "error", "message": "Missing message"})
            if created:
                logger.info(f"Telegrama dispatched [{entry['sender']}] ({len(entry['message'])} chars)")
                service._notify(entry)
            return self._send_json(200, {"status": "ok", "created": created, "entry": entry})

        msg_id = str(data.get("id", ""))
        if path == "/api/reply":
            reply = service.store.add_reply(msg_id, data.get("reply"))
            if reply is None:
                known = _ID_RE.match(msg_id) and service.store.get(msg_id)
                return self._send_json(404 if not known else 400,
                                       {"status": "error", "message": "Unknown id" if not known else "Missing reply"})
            logger.info(f"Telegrama reply recorded for {msg_id}")
            return self._send_json(200, {"status": "ok", "reply": reply})

        # /api/ack — desktop reports delivered / read
        entry = service.store.mark(msg_id, str(data.get("state", "")))
        if entry is None:
            return self._send_json(404, {"status": "error", "message": "Unknown id or state"})
        return self._send_json(200, {"status": "ok", "state": entry["state"]})


# ─────────────────────────────── service ───────────────────────────────

class TelegramaService:
    """Owns the HTTP daemon, the store, auth settings and desktop-side listeners."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = DEFAULT_PORT,
        *,
        allow_lan: bool = False,
        token: str = "",
        data_dir: Optional[str] = None,
    ):
        self.allow_lan = bool(allow_lan)
        self.host = host or ("0.0.0.0" if self.allow_lan else "127.0.0.1")
        self.port = int(port)
        self.token = token or ""
        history = os.path.join(data_dir, "telegrama_history.json") if data_dir else None
        self.store = TelegramaStore(history)
        self.server: Optional[_Server] = None
        self.thread: Optional[threading.Thread] = None
        self.stopping = threading.Event()
        self.local_limiter = RateLimiter(60, 60.0)
        self.remote_limiter = RateLimiter(6, 60.0)
        self._listeners: list[Callable[[dict], None]] = []
        self._sse_lock = threading.Lock()
        self._sse_clients = 0
        self._local_ip: Optional[str] = None

    @property
    def local_ip(self) -> str:
        if self._local_ip is None:
            self._local_ip = get_local_ip()
        return self._local_ip

    # ---- SSE accounting
    def acquire_sse(self) -> bool:
        with self._sse_lock:
            if self._sse_clients >= MAX_SSE_CLIENTS:
                return False
            self._sse_clients += 1
            return True

    def release_sse(self):
        with self._sse_lock:
            self._sse_clients = max(0, self._sse_clients - 1)

    # ---- listeners (desktop UI hooks)
    def add_listener(self, fn: Callable[[dict], None]):
        self._listeners.append(fn)

    def _notify(self, entry: dict):
        for fn in list(self._listeners):
            try:
                fn(entry)
            except Exception as exc:  # a broken listener must never break dispatching
                logger.warning(f"Telegrama listener failed: {exc}")

    # ---- lifecycle
    def start(self) -> bool:
        if self.server is not None:
            return True
        self.stopping.clear()
        base = self.port
        for p in range(base, base + 10):
            try:
                self.server = _Server((self.host, p), TelegramaHTTPHandler)
                self.port = p
                break
            except OSError:
                continue
        if self.server is None:
            logger.error(f"TelegramaService: could not bind {self.host}:{base}..{base + 9}")
            return False
        self.server.service = self  # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="TelegramaService")
        self.thread.start()
        scope = "LAN (token required)" if self.allow_lan else "this PC only"
        logger.info(f"Telegrama service listening on {self.host}:{self.port} — {scope}")
        return True

    def stop(self):
        self.stopping.set()
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
            self.server = None
            self.thread = None
            logger.info("Telegrama service stopped")

    @property
    def running(self) -> bool:
        return self.server is not None

    @property
    def api_base(self) -> str:
        """Base URL the desktop overlay should use (always loopback)."""
        return f"http://127.0.0.1:{self.port}"

    @property
    def mobile_url(self) -> str:
        """Link to open on a phone (needs LAN mode); falls back to the loopback page."""
        if self.allow_lan and self.token:
            return f"http://{self.local_ip}:{self.port}/telegrama?t={self.token}"
        return f"{self.api_base}/telegrama"

    def dispatch_message(self, sender: str, message: str, tag: str = "love", emoji: str = "❤️") -> dict:
        """Programmatically send a dispatch (tests, desktop triggers)."""
        entry, created = self.store.add_dispatch(
            {"sender": sender, "message": message, "tag": tag, "emoji": emoji}
        )
        if entry is not None and created:
            self._notify(entry)
        return entry or {}
