"""Models group: list_models, get_model"""

import logging
from urllib.parse import quote

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas.models import ModelData, ModelListData, ModelListResult, ModelResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("gemini-mcp.tools.models")


def register_models_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="list_models",
        description=(
            "Lists the models available through the Gemini API. Returns each model's resource name, "
            "base model ID, version, token limits, supported generation methods, thinking support, "
            "and default sampling parameters, plus `nextPageToken` when more pages exist. "
            "Returns 50 models per page by default and at most 1000 per page; pass `nextPageToken` "
            "back as `page_token`, keeping `page_size` the same, to get the next page."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def list_models(
        page_size: int | None = Field(default=None, description="Maximum number of models to return per page. Omit for 50; values above 1000 return at most 1000."),
        page_token: str | None = Field(default=None, description="`nextPageToken` from a previous list_models call, to get the next page. Other parameters must match that call. Omit for the first page."),
    ) -> ModelListResult:
        tlog = ToolLogger(logger, "list_models")

        if page_size is not None and page_size < 1:
            return _err(ModelListResult, tlog, "VALIDATION_ERROR", "page_size must be at least 1", 400)

        params: dict[str, object] = {}
        if page_size is not None:
            params["pageSize"] = page_size
        if page_token:
            params["pageToken"] = page_token

        try:
            data, status, retry_after = service.api_request(
                "GET", "/v1/models", params=params or None,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                result = ModelListResult(success=True, statusCode=status, data=ModelListData(**data))
                tlog.success()
                return result
            return _upstream_err(ModelListResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(ModelListResult, tlog, exc)

    @mcp.tool(
        name="get_model",
        description=(
            "Gets metadata for one Gemini model. Returns its resource name, base model ID, version, "
            "display name, input and output token limits, supported generation methods, thinking "
            "support, and default temperature, max temperature, topP and topK. "
            "Get valid model IDs from list_models."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def get_model(
        model: str = Field(description="Model ID, e.g. `gemini-2.5-flash`, as returned in list_models `name`. The `models/` prefix is optional."),
    ) -> ModelResult:
        tlog = ToolLogger(logger, "get_model")

        # list_models returns `models/{model}`; accept either form
        model_id = model.strip().removeprefix("models/")
        if not model_id:
            return _err(ModelResult, tlog, "VALIDATION_ERROR", "model must not be empty", 400)

        try:
            data, status, retry_after = service.api_request(
                "GET", f"/v1/models/{quote(model_id, safe='')}",
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                result = ModelResult(success=True, statusCode=status, data=ModelData(**data))
                tlog.success()
                return result
            return _upstream_err(ModelResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(ModelResult, tlog, exc)
