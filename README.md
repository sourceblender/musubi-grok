# musubi-grok

A [Grok Build](https://docs.x.ai/build/features/skills-plugins-marketplaces) plugin for Musubi memory. It supplies two skills and one stdio MCP server with `musubi_recent`, `musubi_search`, `musubi_get`, `musubi_remember`, and `musubi_status`. The [musubi-harness](https://github.com/sourceblender/musubi-harness) package owns the identity, namespace, outbox, delivery, and exact readback rules. This package is the Grok host binding.

## Install

Requirements: Grok Build, Python 3.12, and `uv`.

```sh
grok plugin install sourceblender/musubi-grok@v0.1.0
# In the installed plugin directory, run scripts/setup once.
```

For a local checkout, run `scripts/setup`, then `grok plugin install /absolute/path/to/musubi-grok`. Restart Grok after installation. `grok plugin validate /path/to/musubi-grok` checks the manifest; `grok mcp doctor musubi-grok` checks the server.

The launcher reads its Python environment from `$GROK_PLUGIN_DATA/venv`, or `$MUSUBI_GROK_PLUGIN_DATA/venv`, or `~/.local/share/musubi-grok/venv` in that order. Set `MUSUBI_GROK_PLUGIN_DATA` for a fixed setup location when the host does not export `GROK_PLUGIN_DATA` to MCP processes. Setup does not read credentials.

## Seat configuration

Supply the complete identity and transport to the MCP process, preferably from a seat launcher or a project `.grok/config.toml`:

```toml
[mcp_servers.musubi-grok]
command = "/absolute/path/to/musubi-grok/scripts/musubi-grok-run"
enabled = true
env = { PLUGIN_DATA = "/private/seat/musubi", MUSUBI_ACTOR = "alice", MUSUBI_PRESENCE = "alice/laptop", MUSUBI_ZONE = "home", MUSUBI_DELIVERY_MODE = "verified" }
```

The harness reads `MUSUBI_API_URL` and `MUSUBI_TOKEN` from the process environment when remote access is required. Use the host's secret injection, not a tracked file. With no `PLUGIN_DATA`, the MCP binding uses `GROK_PLUGIN_DATA` when Grok provides it, otherwise `~/.local/state/musubi-grok`. Identity must be complete: partial or cross actor configuration is refused. The default delivery mode is `shadow`; `verified` attempts remote delivery and exact readback. Do not delete an old outbox until its pending and dead rows have been reviewed.

The plugin currently covers deliberate recall and explicit remember. Automatic turn capture is a separate lifecycle feature and is **not** claimed by this release.

## Development

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[test]'
.venv/bin/python -m pytest -q
grok plugin validate .
```

The MCP server follows the standard stdio JSON-RPC protocol. Its five tools use the same scoped harness facade as the Claude Code and Codex plugins. `musubi_remember` goes through the local outbox and reports `verified` only after the server record is read back.

## Security

Memory can contain private context. Keep credentials in the host's secret store and keep `PLUGIN_DATA` private to one seat. The plugin never logs tokens. Report vulnerabilities privately through GitHub's security advisory channel for this repository.
