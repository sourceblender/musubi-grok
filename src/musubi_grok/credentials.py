"""Read only the two transport values needed by the bundled Musubi client."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from musubi_harness.plugin_runtime import RuntimeConfigError
from musubi_harness.tokens import identity_refusal, scope_allows, token_claims, validity_refusal


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
        if not hasattr(os, "O_NOFOLLOW"):
            raise RuntimeConfigError("credential_file_nofollow_unavailable")
        descriptor = -1
        try:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise RuntimeConfigError("credential_file_permissions_invalid")
            with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
                descriptor = -1
                lines = stream.read().splitlines()
        except (OSError, UnicodeError) as exc:
            raise RuntimeConfigError("credential_file_unavailable") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
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
    claims = token_claims(token)
    if claims is not None and (
        claims.get("sub") != presence
        or not scope_allows(claims.get("scope"), f"{presence}/episodic", "w")
        or validity_refusal(claims)
        or identity_refusal(claims)
    ):
        raise RuntimeConfigError("transport_token_identity_invalid")
    os.environ["MUSUBI_API_URL"] = url
    os.environ["MUSUBI_TOKEN"] = token
