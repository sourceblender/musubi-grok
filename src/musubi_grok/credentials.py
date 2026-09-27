"""Read only the two transport values needed by the bundled Musubi client."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from musubi_harness.plugin_runtime import RuntimeConfigError
from musubi_harness.tokens import token_presence_problems


def load_transport(presence: str) -> None:
    """Use injected credentials or one explicitly named, owner-only dotenv.

    The legacy operator dotenv contains unrelated server secrets. Never source
    it as shell code or copy any other keys into the MCP process.
    """
    url = os.environ.get("MUSUBI_API_URL", "").strip()
    token = os.environ.get("MUSUBI_TOKEN", "").strip()
    if bool(url) != bool(token):
        raise RuntimeConfigError("transport_config_partial")
    if not url:
        file_name = os.environ.get("MUSUBI_GROK_CREDENTIAL_FILE", "").strip()
        if not file_name:
            return
        path = Path(file_name).expanduser()
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise RuntimeConfigError("credential_file_permissions_invalid")
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise RuntimeConfigError("credential_file_unavailable") from exc
        found: dict[str, str] = {}
        for line in lines:
            key, sep, value = line.partition("=")
            key = key.strip()
            if sep and key in {"MUSUBI_API_URL", "MUSUBI_TOKEN"}:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                    value = value[1:-1]
                found[key] = value
        url, token = found.get("MUSUBI_API_URL", ""), found.get("MUSUBI_TOKEN", "")
        if not url or not token:
            raise RuntimeConfigError("credential_file_incomplete")
    problems = token_presence_problems(token, presence)
    if problems:
        raise RuntimeConfigError("transport_token_identity_invalid")
    os.environ["MUSUBI_API_URL"] = url
    os.environ["MUSUBI_TOKEN"] = token
