"""Native Grok MCP facade over the shared Musubi harness."""

from __future__ import annotations

import sys

from musubi_harness.plugin_mcp import PluginMcpFacade
from musubi_harness.plugin_runtime import RuntimeConfigError

from .credentials import load_transport
from .runtime import plugin_runtime


def main() -> int:
    runtime = plugin_runtime()
    try:
        config = runtime.runtime_config()
        load_transport(config.presence)
    except RuntimeConfigError as exc:
        print(f"musubi-grok MCP refused startup: {exc}", file=sys.stderr)
        return 2
    try:
        facade = PluginMcpFacade(
            runtime,
            source="grok",
            event_prefix="grok",
            owner_label="grok-mcp",
            server_name="musubi-grok",
            server_version="0.1.0",
        )
    except ValueError:
        print("musubi-grok MCP refused startup: harness_outdated_grok_source", file=sys.stderr)
        return 78
    return facade.serve()


if __name__ == "__main__":
    raise SystemExit(main())
