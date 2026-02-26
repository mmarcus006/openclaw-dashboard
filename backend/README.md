# OpenClaw Dashboard — Backend

FastAPI backend for the OpenClaw Agent Fleet Management Dashboard.

## Quick Start

```bash
uv sync --all-extras   # Install all dependencies
uv run openclaw-dashboard   # Start the server (localhost:8400)
```

## Development

```bash
uv sync --all-extras
TESTING=1 uv run pytest -q          # Run tests
uv run ruff check app/ tests/       # Lint
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DASHBOARD_HOST` | `127.0.0.1` | Bind address |
| `DASHBOARD_PORT` | `8400` | Port |
| `DASHBOARD_ALLOWED_HOSTS` | `["localhost","127.0.0.1"]` | JSON array of allowed Host headers |
| `DASHBOARD_OPENCLAW_HOME` | `~/.openclaw` | OpenClaw installation directory |
| `DASHBOARD_LOG_LEVEL` | `INFO` | Log level |
| `TESTING` | — | Set to `1` to disable rate limiting |
