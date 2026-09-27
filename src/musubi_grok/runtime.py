"""Resolve Grok's private state root without borrowing Codex's plugin locator."""

from __future__ import annotations

import os
from pathlib import Path

from musubi_harness.plugin_runtime import PluginRuntime


def plugin_runtime() -> PluginRuntime:
    # PLUGIN_DATA is the portable harness contract. Grok exposes its own data
    # directory to plugin components; the explicit value wins for seat canaries.
    if not os.environ.get("PLUGIN_DATA") and os.environ.get("GROK_PLUGIN_DATA"):
        os.environ["PLUGIN_DATA"] = os.environ["GROK_PLUGIN_DATA"]
    return PluginRuntime("musubi-grok", default_data_root=Path.home() / ".local" / "state" / "musubi-grok")
