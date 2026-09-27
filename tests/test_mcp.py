"""A real stdio server loads with Grok's direct, seat-owned data root."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import base64
import time
from pathlib import Path

from musubi_grok.runtime import plugin_runtime
from musubi_grok.credentials import load_transport
from musubi_harness.plugin_runtime import RuntimeConfigError
import pytest


def _test_token(presence: str, *, exp: int | None = None) -> str:
    def part(value: dict[str, object]) -> str:
        return base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip("=")

    claims: dict[str, object] = {'iss': 'https://example.test', 'aud': 'musubi', 'sub': presence, 'presence': presence, 'scope': presence + '/*:rw'}
    if exp is not None:
        claims['exp'] = exp
    return f"{part({'alg': 'none'})}.{part(claims)}.sig"


def test_owner_only_credential_file_reads_only_transport(monkeypatch, tmp_path: Path) -> None:
    secret_file = tmp_path / "musubi.env"
    secret_file.write_text(
        "MUSUBI_API_URL=https://musubi.example.test/v1\n"
        f"MUSUBI_TOKEN={_test_token('yua/command-chair')}\n"
        "JWT_SIGNING_KEY=must-not-be-imported\n"
    )
    secret_file.chmod(0o600)
    monkeypatch.delenv("MUSUBI_API_URL", raising=False)
    monkeypatch.delenv("MUSUBI_TOKEN", raising=False)
    monkeypatch.delenv("JWT_SIGNING_KEY", raising=False)
    monkeypatch.setenv("MUSUBI_GROK_CREDENTIAL_FILE", str(secret_file))
    load_transport("yua/command-chair")
    assert os.environ["MUSUBI_API_URL"] == "https://musubi.example.test/v1"
    assert "JWT_SIGNING_KEY" not in os.environ
    with pytest.raises(RuntimeConfigError, match="transport_token_identity_invalid"):
        load_transport("tama/command-chair")
    monkeypatch.delenv("MUSUBI_API_URL")
    monkeypatch.delenv("MUSUBI_TOKEN")
    secret_file.chmod(0o644)
    with pytest.raises(RuntimeConfigError, match="credential_file_permissions_invalid"):
        load_transport("yua/command-chair")


def test_credential_file_refuses_symlink_and_invalid_utf8(monkeypatch, tmp_path: Path) -> None:
    secret_file = tmp_path / "musubi.env"
    secret_file.write_bytes(b"\xff")
    secret_file.chmod(0o600)
    monkeypatch.delenv("MUSUBI_API_URL", raising=False)
    monkeypatch.delenv("MUSUBI_TOKEN", raising=False)
    monkeypatch.setenv("MUSUBI_GROK_CREDENTIAL_FILE", str(secret_file))
    with pytest.raises(RuntimeConfigError, match="credential_file_unavailable"):
        load_transport("yua/command-chair")
    link = tmp_path / "link.env"
    link.symlink_to(secret_file)
    monkeypatch.setenv("MUSUBI_GROK_CREDENTIAL_FILE", str(link))
    with pytest.raises(RuntimeConfigError, match="credential_file_unavailable"):
        load_transport("yua/command-chair")


def test_approaching_expiry_is_not_a_startup_refusal(monkeypatch) -> None:
    monkeypatch.setenv("MUSUBI_API_URL", "https://musubi.example.test/v1")
    monkeypatch.setenv("MUSUBI_TOKEN", _test_token("yua/command-chair", exp=int(time.time()) + 7 * 86400))
    load_transport("yua/command-chair")


def test_grok_data_root_and_explicit_override(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("PLUGIN_DATA", raising=False)
    monkeypatch.setenv("GROK_PLUGIN_DATA", str(tmp_path / "grok"))
    assert plugin_runtime().data_root() == tmp_path / "grok"
    monkeypatch.setenv("PLUGIN_DATA", str(tmp_path / "seat"))
    assert plugin_runtime().data_root() == tmp_path / "seat"


def test_real_stdio_lists_tools_and_refuses_partial_identity(tmp_path: Path) -> None:
    env = os.environ.copy()
    for key in ("MUSUBI_API_URL", "MUSUBI_TOKEN", "MUSUBI_GROK_CREDENTIAL_FILE", "GROK_PLUGIN_DATA"):
        env.pop(key, None)
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
