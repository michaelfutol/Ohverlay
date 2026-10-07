"""Shared pytest configuration.

* Forces the offscreen Qt platform so tests run headless (CI + local).
* Points ``OHVERLAY_HOME`` at a throw-away directory so no test can read or modify the
  developer's real ``~/.ohverlay`` (config, notes, sticky history).
"""

import os
import sys
import tempfile

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_TEST_HOME = tempfile.mkdtemp(prefix="ohverlay-test-home-")
os.environ["OHVERLAY_HOME"] = _TEST_HOME

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
