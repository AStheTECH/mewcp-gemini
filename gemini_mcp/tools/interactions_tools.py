"""Interactions group: create_interaction, start_deep_research, get_interaction, cancel_interaction, delete_interaction."""

import logging
from typing import Any, Literal
from urllib.parse import quote

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, POLL_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas.interactions import (
    CancelInteractionData,
    CancelInteractionResult,
    CreateInteractionData,
    CreateInteractionResult,
    DeleteInteractionData,
    DeleteInteractionResult,
    GetInteractionData,
    GetInteractionResult,
    InteractionData,
    StartDeepResearchData,
    StartDeepResearchResult,
)
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("gemini-mcp.tools.interactions")

ModelName = Literal[
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-4-argon",
    "gemini-4-carbon",
    "gemini-4-hydrogen",
    "gemini-4-neon",
]

STEP_TYPES = {
    "user_input", "thought", "model_output", "function_call", "function_result",
    "code_execution_call", "code_execution_result", "google_search_call",
    "google_search_result", "google_maps_call", "google_maps_result",
    "file_search_call", "file_search_result", "mcp_server_tool_call",
    "mcp_server_tool_result", "processing_call", "processing_result",
}

DEEP_RESEARCH_AGENT = "deep-research-preview-04-2026"
DEEP_RESEARCH_MAX_AGENT = "deep-research-max-preview-04-2026"


def _drop_images(blocks: Any) -> Any:
    if not isinstance(blocks, list):
        return blocks
    return [b for b in blocks if not (isinstance(b, dict) and b.get("type") == "image")]


def _text_only(data: dict[str, Any]) -> dict[str, Any]:
    """Drop image blocks from output steps (text output only until shared storage exists)."""
    steps = data.get("steps")
    if not isinstance(steps, list):
        return data
    out = []
    for step in steps:
        if isinstance(step, dict) and step.get("type") != "user_input":
            step = {**step}
            if "content" in step:
                step["content"] = _drop_images(step["content"])
            if "result" in step:
                step["result"] = _drop_images(step["result"])
        out.append(step)
    return {**data, "steps": out}


def _check_media_uris(blocks: list[dict[str, Any]]) -> str | None:
    for b in blocks:
        uri = b.get("uri")
        if uri is not None and not (isinstance(uri, str) and uri.lower().startswith(("https://", "http://"))):
            return "Content block `uri` must be a public HTTPS or pre-signed URL; local files and private links are not supported"
    return None


def register_interactions_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="create_interaction",
        description=(
            "Sends a prompt (text plus optional file links) to a Gemini text model and returns the finished "
            "interaction: its `id`, `status`, `steps` and token `usage`; the answer is the `text` of the "
            "`model_output` step. Pass an earlier `id` as `previous_interaction_id` to continue a conversation "
            "server-side. Files go in only as public HTTPS or pre-signed links (up to 15 MB each, no login or "
            "paywall); local files and private links are not supported. Text output only: image blocks (such as "
            "code-execution charts) are dropped from the returned steps. With `google_search` the model decides "
            "what to search (each query is billed on Gemini 3+ models after 5,000 free per month); Google's terms "
            "require you to show the answer with its `url_citation` annotations and the `search_suggestions` from "
            "the `google_search_result` step, unmodified. `code_execution` runs Python in Google's sandbox (fixed "
            "libraries, no installs, 30 s per run). Status `incomplete` means the output was cut short, e.g. by "
            "`max_output_tokens`."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def create_interaction(
        model: ModelName = Field(description="The Gemini model that generates the interaction."),
        input: str | list[dict[str, Any]] = Field(
            description=(
                "The prompt: a plain string, or a list of content blocks such as "
                "`{\"type\": \"text\", \"text\": \"...\"}` or "
                "`{\"type\": \"image\", \"uri\": \"<public https url>\", \"mime_type\": \"image/png\"}` "
                "(`document`, `audio` and `video` blocks take the same `uri` + `mime_type` shape; PDFs use "
                "`document` with `application/pdf`; a YouTube URL works as a `video` uri, preview). Content blocks "
                "are wrapped in a `user_input` step for you; a list of steps "
                "(`[{\"type\": \"user_input\", \"content\": [...]}]`) is sent as-is. Files must be public HTTPS or "
                "pre-signed links, up to 15 MB each."
            ),
        ),
        system_instruction: str | None = Field(default=None, description="System instruction for the interaction. Omit for none."),
        previous_interaction_id: str | None = Field(
            default=None,
            description="The `id` of an earlier interaction to continue the conversation server-side. Omit to start a new conversation.",
        ),
        thinking_level: Literal["minimal", "low", "medium", "high", "xhigh"] | None = Field(
            default=None,
            description="How many thought tokens the model should generate (sent as `generation_config.thinking_level`). Omit for the model default.",
        ),
        max_output_tokens: int | None = Field(
            default=None,
            description="Maximum number of tokens in the response (sent as `generation_config.max_output_tokens`). Omit for the model default.",
        ),
        google_search: bool = Field(
            default=False,
            description="Enable Google Search grounding (adds `{\"type\": \"google_search\"}` to `tools`). Default false.",
        ),
        code_execution: bool = Field(
            default=False,
            description="Enable Python code execution in Google's sandbox (adds `{\"type\": \"code_execution\"}` to `tools`). Default false.",
        ),
    ) -> CreateInteractionResult:
        tlog = ToolLogger(logger, "create_interaction")

        if isinstance(input, str):
            if not input.strip():
                return _err(CreateInteractionResult, tlog, "VALIDATION_ERROR", "input must not be empty", 400)
            api_input: str | list[dict[str, Any]] = input
        else:
            if not input or not all(isinstance(b, dict) for b in input):
                return _err(CreateInteractionResult, tlog, "VALIDATION_ERROR",
                            "input must be a non-empty string or a non-empty list of content blocks", 400)
            step_flags = [b.get("type") in STEP_TYPES for b in input]
            if all(step_flags):
                blocks = [c for s in input for c in (s.get("content") or []) if isinstance(c, dict)]
                api_input = input
            elif not any(step_flags):
                blocks = input
                api_input = [{"type": "user_input", "content": input}]
            else:
                return _err(CreateInteractionResult, tlog, "VALIDATION_ERROR",
                            "input mixes steps and content blocks; send either content blocks or steps", 400)
            uri_err = _check_media_uris(blocks)
            if uri_err:
                return _err(CreateInteractionResult, tlog, "VALIDATION_ERROR", uri_err, 400)
        if max_output_tokens is not None and max_output_tokens < 1:
            return _err(CreateInteractionResult, tlog, "VALIDATION_ERROR", "max_output_tokens must be at least 1", 400)

        body: dict[str, Any] = {"model": model, "input": api_input}
        if system_instruction is not None:
            body["system_instruction"] = system_instruction
        if previous_interaction_id is not None:
            body["previous_interaction_id"] = previous_interaction_id
        generation_config: dict[str, Any] = {}
        if thinking_level is not None:
            generation_config["thinking_level"] = thinking_level
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        if generation_config:
            body["generation_config"] = generation_config
        tools = []
        if google_search:
            tools.append({"type": "google_search"})
        if code_execution:
            tools.append({"type": "code_execution"})
        if tools:
            body["tools"] = tools

        endpoint = "/v1beta/interactions" if tools else "/v1/interactions"

        try:
            data, status, retry_after = service.api_request(
                "POST", endpoint, body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                result = CreateInteractionResult(
                    success=True, statusCode=status, data=CreateInteractionData(**_text_only(data)),
                )
                tlog.success()
                return result
            result = _upstream_err(CreateInteractionResult, tlog, status, data, retry_after)
            if status == 429 and google_search and result.error:
                result.error.message += (
                    " (Google Search grounding has its own quota; this key may have none left. "
                    "Retry later or call without google_search.)"
                )
            return result
        except Exception as exc:
            return _handle_request_exc(CreateInteractionResult, tlog, exc)

    @mcp.tool(
        name="start_deep_research",
        description=(
            "Starts Gemini's Deep Research agent (preview) in the background on a research question; the agent "
            "plans, searches the web, reads sources and writes a detailed cited report. Returns immediately with the "
            "interaction `id` and `status: in_progress`; it does not wait for the report. Poll get_interaction with "
            "that `id` every 30-60 seconds until `status` is `completed` or `failed`; most tasks finish within "
            "20 minutes, at most 60. The report is the text of the last step, with citations to show and review "
            "alongside it (Google Search terms apply). COSTLY: about $1-3 per task (`max=true`: about $3-7), so use "
            "it only for real research, not quick questions. Text only (charts are off). Stop a running task with "
            "cancel_interaction."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def start_deep_research(
        query: str = Field(description="The research question plus any context or constraints, as plain text."),
        max: bool = Field(
            default=False,
            description=(
                "Use Deep Research Max (maximum comprehensiveness, up to ~160 searches, about $3-7 per task) "
                "instead of Deep Research (speed and efficiency, about $1-3). Default false."
            ),
        ),
    ) -> StartDeepResearchResult:
        tlog = ToolLogger(logger, "start_deep_research")

        if not query.strip():
            return _err(StartDeepResearchResult, tlog, "VALIDATION_ERROR", "query must not be empty", 400)

        body = {
            "input": query,
            "agent": DEEP_RESEARCH_MAX_AGENT if max else DEEP_RESEARCH_AGENT,
            "background": True,
            "agent_config": {"type": "deep-research", "visualization": "off"},
        }

        try:
            data, status, retry_after = service.api_request(
                "POST", "/v1beta/interactions", body=body,
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                result = StartDeepResearchResult(success=True, statusCode=status, data=StartDeepResearchData(**data))
                tlog.success()
                return result
            return _upstream_err(StartDeepResearchResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(StartDeepResearchResult, tlog, exc)

    @mcp.tool(
        name="get_interaction",
        description=(
            "Retrieves a stored interaction by id and returns its `status`, `steps`, and token `usage`. Use it to "
            "poll background jobs such as start_deep_research until `status` leaves `in_progress` (`completed`, "
            "`failed` or `cancelled`); once completed, the answer or report is the text of the last `model_output` "
            "step, with citation annotations to show alongside it. Only stored interactions can be fetched. Text "
            "output only: image blocks are dropped from the returned steps."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def get_interaction(
        id: str = Field(description="The interaction `id` returned by create_interaction or start_deep_research."),
    ) -> GetInteractionResult:
        tlog = ToolLogger(logger, "get_interaction")

        if not id.strip():
            return _err(GetInteractionResult, tlog, "VALIDATION_ERROR", "id must not be empty", 400)

        try:
            data, status, retry_after = service.api_request(
                "GET", f"/v1/interactions/{quote(id.strip(), safe='')}",
                timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if 200 <= status < 300:
                result = GetInteractionResult(success=True, statusCode=status, data=GetInteractionData(**_text_only(data)))
                tlog.success()
                return result
            return _upstream_err(GetInteractionResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(GetInteractionResult, tlog, exc)

    @mcp.tool(
        name="cancel_interaction",
        description=(
            "Cancels a background interaction that is still running (e.g. a start_deep_research task) and returns "
            "the interaction as it was before and after the cancel; its `status` becomes `cancelled`. Only applies "
            "to background interactions still `in_progress`. Get the `id` from start_deep_research, or check the "
            "current status first with get_interaction. NOTE: this stops the job for good; it cannot be resumed. "
            "The response includes both the before and after state so you have a full record of what changed."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=True),
    )
    def cancel_interaction(
        id: str = Field(description="The `id` of the running background interaction to cancel."),
    ) -> CancelInteractionResult:
        tlog = ToolLogger(logger, "cancel_interaction")

        if not id.strip():
            return _err(CancelInteractionResult, tlog, "VALIDATION_ERROR", "id must not be empty", 400)
        path = f"/v1/interactions/{quote(id.strip(), safe='')}"

        try:
            before_data, status, retry_after = service.api_request(
                "GET", path, timeout=(CONNECT_TIMEOUT, POLL_TIMEOUT),
            )
            if not 200 <= status < 300:
                return _upstream_err(CancelInteractionResult, tlog, status, before_data, retry_after)
            before = InteractionData(**_text_only(before_data))

            data, status, retry_after = service.api_request(
                "POST", f"{path}/cancel", timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                result = CancelInteractionResult(
                    success=True, statusCode=status,
                    data=CancelInteractionData(before=before, after=InteractionData(**_text_only(data))),
                )
                tlog.success()
                return result
            return _upstream_err(CancelInteractionResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CancelInteractionResult, tlog, exc)

    @mcp.tool(
        name="delete_interaction",
        description=(
            "DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. "
            "Permanently deletes a stored interaction (its stored request and response) by id. "
            "This action is irreversible — the interaction's input, output and history cannot be recovered, and it "
            "can no longer be fetched or continued with previous_interaction_id. "
            "NEVER call this tool autonomously or as part of an automated flow. "
            "You MUST stop, tell the user exactly what will be deleted and that it is permanent, "
            "and wait for their explicit written confirmation before proceeding. "
            "Returns the deleted `id` and `deleted: true`."
        ),
        annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=True),
    )
    def delete_interaction(
        id: str = Field(description="The `id` of the interaction to delete."),
    ) -> DeleteInteractionResult:
        tlog = ToolLogger(logger, "delete_interaction")

        if not id.strip():
            return _err(DeleteInteractionResult, tlog, "VALIDATION_ERROR", "id must not be empty", 400)

        try:
            data, status, retry_after = service.api_request(
                "DELETE", f"/v1/interactions/{quote(id.strip(), safe='')}",
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return DeleteInteractionResult(
                    success=True, statusCode=status, data=DeleteInteractionData(id=id.strip(), deleted=True),
                )
            return _upstream_err(DeleteInteractionResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(DeleteInteractionResult, tlog, exc)
