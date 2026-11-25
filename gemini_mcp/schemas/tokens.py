"""Schemas for the tokens group."""

from pydantic import BaseModel, ConfigDict, Field

from ._base import ToolResult


class ModalityTokenCount(BaseModel):
    model_config = ConfigDict(extra="allow")

    modality: str | None = Field(
        default=None,
        description="One of MODALITY_UNSPECIFIED, TEXT, IMAGE, VIDEO, AUDIO, DOCUMENT (e.g. PDF).",
    )
    tokenCount: int | None = None


class CountTokensData(BaseModel):
    model_config = ConfigDict(extra="allow")

    totalTokens: int | None = None
    promptTokensDetails: list[ModalityTokenCount] | None = Field(
        default=None, description="Token counts per modality in the request input.",
    )
    cacheTokensDetails: list[ModalityTokenCount] | None = Field(
        default=None, description="Token counts per modality in the cached content.",
    )


class CountTokensResult(ToolResult):
    data: CountTokensData | None = None
