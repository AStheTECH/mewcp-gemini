"""Embeddings group: embed_content"""

import logging
from typing import Any

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from .. import service
from ..config import CONNECT_TIMEOUT, READ_TIMEOUT
from ..logging_utils import ToolLogger
from ..schemas.embeddings import EmbedContentData, EmbedContentResult
from ._helpers import _err, _handle_request_exc, _upstream_err

logger = logging.getLogger("gemini-mcp.tools.embeddings")

_ROLES = {"user", "model"}
_TASK_TYPES = {
    "TASK_TYPE_UNSPECIFIED", "RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT",
    "SEMANTIC_SIMILARITY", "CLASSIFICATION", "CLUSTERING",
    "QUESTION_ANSWERING", "FACT_VERIFICATION", "CODE_RETRIEVAL_QUERY",
}
# gemini-embedding-001 ignores these inside embedContentConfig; top-level works on all models.
_TOP_LEVEL_CONFIG = ("taskType", "title", "outputDimensionality")


def register_embeddings_tools(mcp: FastMCP) -> None:

    @mcp.tool(
        name="embed_content",
        description=(
            "Generates an embedding vector for one piece of content using a Gemini embedding model "
            "(e.g. `gemini-embedding-001`, `gemini-embedding-2`; generation models are not supported), "
            "for semantic search, classification, and clustering. Returns the vector in "
            "`embedding.values` plus prompt token usage per modality (`gemini-embedding-001` returns no "
            "usage). Only `parts[].text` is counted. Task type changes the vector, so for retrieval with "
            "`gemini-embedding-001` embed queries with taskType RETRIEVAL_QUERY and corpus text with "
            "RETRIEVAL_DOCUMENT, and use the same choice every time you embed the same kind of text. "
            "`gemini-embedding-2` does not use taskType: put the task in the text instead, e.g. "
            "`task: search result | query: <text>` for queries and `title: none | text: <text>` for "
            "documents. Default size is 3072 dimensions; set `outputDimensionality` (768, 1536 or 3072 "
            "recommended) to shrink it. `gemini-embedding-001` vectors below 3072 are not normalized, so "
            "normalize them yourself before comparing. Use list_models to find models whose "
            "supportedGenerationMethods include embedContent."
        ),
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=True),
    )
    def embed_content(
        model: str = Field(
            description=(
                "Embedding model ID, for example `gemini-embedding-001`. Bare ID; a leading "
                "`models/` prefix is stripped. Sent in the path and as the body resource name "
                "`models/{model}`."
            ),
        ),
        content: dict[str, Any] = Field(
            description=(
                "The content to embed, a Gemini Content object. Only the `parts[].text` fields are "
                "counted. Fields: `parts` (array): ordered Parts making up a single message; parts "
                "may have different MIME types. Each part sets one of `text` (string, inline text), "
                "`inlineData` (object: `mimeType`, `data` as base64 bytes), or `fileData` (object: "
                "`fileUri` required, `mimeType` optional). `role` (string, optional): the producer "
                "of the content, `user` or `model`. Example: "
                "{\"parts\": [{\"text\": \"What is the meaning of life?\"}]}."
            ),
        ),
        embedContentConfig: dict[str, Any] | None = Field(
            default=None,
            description=(
                "Optional EmbedContentConfig object. Fields: `title` (string): title for the text. "
                "`taskType` (string): one of TASK_TYPE_UNSPECIFIED (defaults to one of the others), "
                "RETRIEVAL_QUERY (query in a search/retrieval setting), RETRIEVAL_DOCUMENT (document "
                "from the corpus being searched), SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, "
                "QUESTION_ANSWERING, FACT_VERIFICATION, CODE_RETRIEVAL_QUERY. `autoTruncate` "
                "(boolean): silently truncate input longer than the maximum sequence length. "
                "`outputDimensionality` (integer): reduced output dimension; extra values are "
                "truncated from the end. `documentOcr` (boolean): enable OCR for document content. "
                "`audioTrackExtraction` (boolean): extract audio from video content. "
                "Omit to use the model defaults."
            ),
        ),
    ) -> EmbedContentResult:
        tlog = ToolLogger(logger, "embed_content")

        model_id = model.strip().removeprefix("models/")
        if not model_id:
            return _err(EmbedContentResult, tlog, "VALIDATION_ERROR", "model must not be empty", 400)
        if not content:
            return _err(EmbedContentResult, tlog, "VALIDATION_ERROR", "content must not be empty", 400)
        parts = content.get("parts")
        if parts is not None and not isinstance(parts, list):
            return _err(EmbedContentResult, tlog, "VALIDATION_ERROR", "content.parts must be an array", 400)
        role = content.get("role")
        if role is not None and role not in _ROLES:
            return _err(EmbedContentResult, tlog, "VALIDATION_ERROR",
                        "content.role must be 'user' or 'model'", 400)
        if embedContentConfig:
            task_type = embedContentConfig.get("taskType")
            if task_type is not None and task_type not in _TASK_TYPES:
                return _err(EmbedContentResult, tlog, "VALIDATION_ERROR",
                            f"embedContentConfig.taskType must be one of {sorted(_TASK_TYPES)}", 400)

        body: dict[str, Any] = {"model": f"models/{model_id}", "content": content}
        if embedContentConfig:
            config = dict(embedContentConfig)
            for key in _TOP_LEVEL_CONFIG:
                if key in config:
                    body[key] = config.pop(key)
            if config:
                body["embedContentConfig"] = config

        try:
            data, status, retry_after = service.api_request(
                "POST", f"/v1/models/{model_id}:embedContent", body=body,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
            )
            if 200 <= status < 300:
                result = EmbedContentResult(success=True, statusCode=status,
                                            data=EmbedContentData(**data))
                tlog.success()
                return result
            return _upstream_err(EmbedContentResult, tlog, status, data, retry_after)
        except Exception as exc:
            return _handle_request_exc(EmbedContentResult, tlog, exc)
