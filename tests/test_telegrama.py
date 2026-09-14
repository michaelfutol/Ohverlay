"""
Tests for the Ohverlay Telegrama service and overlay configuration.
"""

import time
import urllib.request
import json
import pytest

from modules.telegrama_service import TelegramaService
from modules.overlay_manager import OVERLAY_REGISTRY
from config.settings import Settings


@pytest.fixture
def telegrama_service():
    """Start and stop a test instance of TelegramaService."""
    service = TelegramaService(port=54330)
    assert service.start() is True
    time.sleep(0.1)
    yield service
    service.stop()


def test_telegrama_registry_and_settings():
    """Verify telegrama is in OVERLAY_REGISTRY and Settings."""
    entry = next((o for o in OVERLAY_REGISTRY if o["id"] == "telegrama"), None)
    assert entry is not None
    assert entry["interactive"] is True
    assert entry["file"] == "telegrama-overlay.html"

    settings = Settings()
    assert "telegrama" in settings.data["overlays"]
    assert "telegrama_count" in settings.data["overlays"]


def test_telegrama_dispatch_and_reply_flow(telegrama_service):
    """Test dispatching a caring telegram and receiving a 2-way reply."""
    port = telegrama_service.port
    base_url = f"http://127.0.0.1:{port}"

    # 1. Dispatch a telegram
    payload = {
        "id": "test_msg_001",
        "sender": "Mahal Ko",
        "message": "Uy inom ka na ng gamot at 1:00 PM ha ❤️",
        "tag": "medicine",
        "emoji": "💊",
    }
    req = urllib.request.Request(
        f"{base_url}/api/dispatch",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "ok"
        assert data["entry"]["id"] == "test_msg_001"

    # 2. Query latest message
    with urllib.request.urlopen(f"{base_url}/api/latest") as resp:
        assert resp.status == 200
        latest = json.loads(resp.read().decode("utf-8"))
        assert latest["id"] == "test_msg_001"
        assert "inom ka na ng gamot" in latest["message"]

    # 3. Send a 2-way reply from desktop
    reply_payload = {
        "id": "test_msg_001",
        "reply": "Nainom ko na po! 💊 Salamat mahal ko ❤️"
    }
    req_reply = urllib.request.Request(
        f"{base_url}/api/reply",
        data=json.dumps(reply_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req_reply) as resp:
        assert resp.status == 200
        reply_res = json.loads(resp.read().decode("utf-8"))
        assert reply_res["status"] == "ok"
        assert reply_res["reply"]["id"] == "test_msg_001"

    # 4. Check status from mobile viewpoint
    with urllib.request.urlopen(f"{base_url}/api/status?id=test_msg_001") as resp:
        assert resp.status == 200
        status_res = json.loads(resp.read().decode("utf-8"))
        assert "Nainom ko na po!" in status_res["reply"]


def test_telegrama_mobile_page_served(telegrama_service):
    """Test that the mobile web dispatcher HTML is served."""
    port = telegrama_service.port
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/telegrama") as resp:
        assert resp.status == 200
        html = resp.read().decode("utf-8")
        assert "Telegrama" in html
        assert "Mula Kay" in html
