"""Configuration for MewCP Gemini MCP Server."""

import logging
import os

SERVER_VERSION = "v2.0.0"
BREAKING_CHANGES: list[dict] = [
    {
        "version": "v2.0.0",
        "change": "Server rebuilt on the Gemini Interactions API; tool 'generate_text' removed (use 'create_interaction')",
    },
]

# Bare host: each tool's endpoint carries its own version segment (/v1 or /v1beta).
GEMINI_API_BASE = "https://generativelanguage.googleapis.com"

CONNECT_TIMEOUT = 5    # TCP connection — fixed across all servers
READ_TIMEOUT = 120     # LLM generation upper bound: thinking-model and long-output calls routinely exceed 60s
POLL_TIMEOUT = 30      # background interactions: job-start and status-poll responses return immediately


def configure_logging() -> None:
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    try:
        from pythonjsonlogger.json import JsonFormatter
        handler = logging.StreamHandler()
        handler.setFormatter(
            JsonFormatter(fmt="%(asctime)s %(name)s %(levelname)s %(message)s")
        )
    except ImportError:
        handler = logging.StreamHandler()
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(log_level)
