"""Tokens group: count_tokens"""

import logging
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas.tokens import CountTokensData, CountTokensResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("gemini-mcp.tools.tokens")


def register_tokens_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="count_tokens",
        description=(
            "Runs a model's tokenizer on input content and returns the total token count plus "
            "per-modality counts, without generating anything. Models may tokenize differently, "
            "so pass the same model you will generate with."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def count_tokens(
        model: str = Field(
            description="The model ID, for example `gemini-2.5-flash`. Forms the resource name `models/{model}`.",
        ),
        contents: list[dict[str, Any]] = Field(
            description=(
                "The input given to the model as a prompt (array of Content). Each item: `role` "
                "(str, optional, 'user' or 'model'; useful for multi-turn input), `parts` (array of Part). "
                "Each Part holds exactly one of `text` (inline text), `inlineData` {`mimeType`, "
                "`data` (base64 bytes)}, or `fileData` {`fileUri` (required within fileData; the `uri` "
                "from create_file/get_file), `mimeType` (optional)}. "
                "Example: [{\"parts\": [{\"text\": \"Hello\"}]}]."
            ),
        ),
    ) -> CountTokensResult:
        tlog = ToolLogger(logger, "count_tokens")

        model_id = model.strip().removeprefix("models/")
        if not model_id:
            return _err(CountTokensResult, tlog, "VALIDATION_ERROR", "model must not be empty", 400)
        if not contents:
            return _err(CountTokensResult, tlog, "VALIDATION_ERROR", "contents must contain at least one Content item", 400)

        try:
            data, status, retry_after = service.api_request(
                "POST", f"/v1/models/{model_id}:countTokens", body={"contents": contents},
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                tlog.success()
                return CountTokensResult(success=True, statusCode=status, data=CountTokensData(**data))
            return _upstream_err(CountTokensResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(CountTokensResult, tlog, exc)
