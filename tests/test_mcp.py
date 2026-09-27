"""A real stdio server loads with Grok's direct, seat-owned data root."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from musubi_grok.runtime import plugin_runtime


def test_grok_data_root_and_explicit_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PLUGIN_DATA", raising=False)
    monkeypatch.setenv("GROK_PLUGIN_DATA", str(tmp_path / "grok"))
    assert plugin_runtime().data_root() == tmp_path / "grok"
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path / "seat"))
    assert plugin_runtime().data_root() == tmp_path / "seat"


def test_real_stdio_lists_tools_and_refuses_partial_identity(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        PLUGIN_DATA=str(tmp_path),
        MUSUBI_ACTOR="yua",
        MUSUBI_PRESENCE="yua/command-chair",
        MUSUBI_ZONE="home",
    )
    command = [sys.executable, "-m", "musubi_grok.mcp"]
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n"
    completed = subprocess.run(command, input=request, text=True, capture_output=True, env=env, check=False, timeout=10)
    assert completed.returncode == 0, completed.stderr
    response = json.loads(completed.stdout)
    assert {tool["name"] for tool in response["result"]["tools"]} == {
        "musubi_recent", "musubi_search", "musubi_get", "musubi_remember", "musubi_status"
    }
    env.pop("MUSUBI_PRESENCE")
    refused = subprocess.run(command, input=request, text=True, capture_output=True, env=env, check=False, timeout=10)
    assert refused.returncode == 2
    assert "partial_identity_config_refused" in refused.stderr
