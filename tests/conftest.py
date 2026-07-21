"""Shared fixtures.

The suite must run on a fresh checkout, with no Claude Code login. CI caught the
opposite on 2026-07-21: every test that built a neutralized HOME copied the real
credentials file and failed on a runner that has none.
"""

from pathlib import Path

import pytest


@pytest.fixture
def fake_credentials(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A stand-in credentials file, so tests never need a real login."""
    path = tmp_path_factory.mktemp("creds") / ".credentials.json"
    path.write_text('{"stub": true}\n')
    return path
