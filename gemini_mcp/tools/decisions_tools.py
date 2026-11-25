"""Decisions group: create_decision"""

import logging
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas.decisions import CreateDecisionData, CreateDecisionResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("gemini-mcp.tools.decisions")


def register_decisions_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="create_decision",
        description=(
            "Evaluates one or more structured decision questions (yes/no probability `noul`, "
            "multiple choice `choice`, or graded `score`) against one shared input and returns "
            "one calibrated answer per question keyed by your question IDs, plus token usage; "
            "nothing is stored. Each question is answered independently against the same input, "
            "so batch related checks into one call. If `prompt_feedback.block_reason` is set, "
            "the input was blocked by the input policy and `answers` is empty."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def create_decision(
        model: str = Field(
            description="Name of the model used to evaluate the decisions, e.g. `gemini-decision-1`.",
        ),
        input: str | list[dict[str, Any]] = Field(
            description=(
                "Shared input evaluated once across all questions. A plain string, or an array of "
                "content blocks: `{\"type\": \"text\", \"text\": ...}`, "
                "`{\"type\": \"image\", \"data\" or \"uri\", \"mime_type\"}`, and likewise "
                "`audio`, `video`, `document`."
            ),
        ),
        questions: dict[str, dict[str, Any]] = Field(
            description=(
                "Decision questions keyed by caller-chosen unique IDs (at least 1); answers come "
                "back under the same IDs. Each question is `{type, instructions, criteria}`: "
                "`type` is `noul` (probability a statement is true), `choice` (pick one named "
                "option) or `score` (graded scale); `instructions` says what to decide; `criteria` "
                "depends on `type` - `noul`: `{\"true_description\": ..., \"false_description\": ...}`; "
                "`choice`: object mapping each option key to its description; `score`: ordered "
                "array of level descriptions, lowest first (level i = array index)."
            ),
        ),
    ) -> CreateDecisionResult:
        tlog = ToolLogger(logger, "create_decision")

        if not model.strip():
            return _err(CreateDecisionResult, tlog, "VALIDATION_ERROR", "model must not be empty", 400)
        if not input:
            return _err(CreateDecisionResult, tlog, "VALIDATION_ERROR", "input must not be empty", 400)
        if not questions:
            return _err(CreateDecisionResult, tlog, "VALIDATION_ERROR",
                        "questions must contain at least one question", 400)

        body = {"model": model, "input": input, "questions": questions}
        try:
            data, status, retry_after = service.api_request(
                "POST", "/v1beta/decisions", body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CreateDecisionResult(success=True, statusCode=status,
                                            data=CreateDecisionData(**data))
            return _upstream_err(CreateDecisionResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CreateDecisionResult, tlog, exc)
