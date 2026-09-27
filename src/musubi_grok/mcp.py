"""Native Grok MCP facade over the shared Musubi harness."""

from __future__ import annotations

from musubi_harness.plugin_mcp import PluginMcpFacade

from .runtime import plugin_runtime


def main() -> int:
    return PluginMcpFacade(
        plugin_runtime(),
        source="grok",
        event_prefix="grok",
        owner_label="grok-mcp",
        server_name="musubi-grok",
        server_version="0.1.0",
    ).serve()


if __name__ == "__main__":
    raise SystemExit(main())
