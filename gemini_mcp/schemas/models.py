"""Models group schemas: list_models, get_model."""

from pydantic import BaseModel, ConfigDict, Field

from ._base import ToolResult


class ModelData(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Resource name, format `models/{model}`. Strip the `models/` prefix to get the `model` value other tools take.")
    baseModelId: str | None = Field(default=None, description="Name of the base model, without version, e.g. `gemini-1.5-flash`.")
    version: str | None = None
    displayName: str | None = None
    description: str | None = None
    inputTokenLimit: int | None = None
    outputTokenLimit: int | None = None
    supportedGenerationMethods: list[str] | None = Field(default=None, description="Supported API method names, e.g. `generateContent`.")
    thinking: bool | None = None
    temperature: float | None = Field(default=None, description="Default temperature used by the backend; range `[0.0, maxTemperature]`.")
    maxTemperature: float | None = None
    topP: float | None = Field(default=None, description="Default nucleus-sampling value used by the backend.")
    topK: int | None = Field(default=None, description="Default top-k value used by the backend. Empty means the model doesn't use top-k sampling.")


class ModelResult(ToolResult):
    data: ModelData | None = None


class ModelListData(BaseModel):
    model_config = ConfigDict(extra="allow")

    models: list[ModelData] = []
    nextPageToken: str | None = Field(default=None, description="Pass as `page_token` to get the next page. Omitted when there are no more pages.")


class ModelListResult(ToolResult):
    data: ModelListData | None = None
