from pydantic import BaseModel, ConfigDict, Field

from ._base import ToolResult


class ContentEmbedding(BaseModel):
    model_config = ConfigDict(extra="allow")

    values: list[float] | None = None
    shape: list[int] | None = Field(
        default=None,
        description="Soft tokens tensor frame shape (e.g. [1, 1, 256, 2048]).",
    )


class ModalityTokenCount(BaseModel):
    model_config = ConfigDict(extra="allow")

    modality: str | None = Field(
        default=None,
        description="One of MODALITY_UNSPECIFIED, TEXT, IMAGE, VIDEO, AUDIO, DOCUMENT.",
    )
    tokenCount: int | None = None


class EmbeddingUsageMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")

    promptTokenCount: int | None = None
    promptTokenDetails: list[ModalityTokenCount] | None = None


class EmbedContentData(BaseModel):
    model_config = ConfigDict(extra="allow")

    embedding: ContentEmbedding
    usageMetadata: EmbeddingUsageMetadata | None = None


class EmbedContentResult(ToolResult):
    data: EmbedContentData | None = None
