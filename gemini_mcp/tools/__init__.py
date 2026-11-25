"""MewCP Gemini tool registration."""

from fastmcp import FastMCP

from .interactions_tools import register_interactions_tools
from .models_tools import register_models_tools
from .tokens_tools import register_tokens_tools
from .embeddings_tools import register_embeddings_tools
from .decisions_tools import register_decisions_tools


def register_tools(mcp: FastMCP) -> None:
    register_interactions_tools(mcp)
    register_models_tools(mcp)
    register_tokens_tools(mcp)
    register_embeddings_tools(mcp)
    register_decisions_tools(mcp)
