"""Schemas for the interactions group."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ._base import ToolResult


class InteractionContent(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str | None = Field(default=None, description="Content block kind: `text`, `image`, `audio`, `video`, `document`, `thought`, ...")
    text: str | None = None
    annotations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Citation information for model-generated text (e.g. `url_citation` items with `url`, `title`, `start_index`, `end_index`).",
    )
    data: str | None = Field(default=None, description="Base64 media content, when delivered inline.")
    mime_type: str | None = None
    uri: str | None = None


class StepArguments(BaseModel):
    model_config = ConfigDict(extra="allow")
    queries: list[str] | None = Field(default=None, description="(`google_search_call` step) Web search queries the model ran.")
    code: str | None = Field(default=None, description="(`code_execution_call` step) The code to be executed.")
    language: str | None = None


class InteractionStep(BaseModel):
    model_config = ConfigDict(extra="allow")
    type: str | None = Field(
        default=None,
        description="Step kind, e.g. `user_input`, `thought`, `model_output`, `code_execution_call`, `code_execution_result`, `google_search_call`, `google_search_result`.",
    )
    content: list[InteractionContent] | None = None
    arguments: StepArguments | None = None
    call_id: str | None = Field(default=None, description="(`*_result` steps) Matches the `id` of the call step.")
    is_error: bool | None = None
    result: list[dict[str, Any]] | str | None = Field(
        default=None,
        description="(`google_search_result`) items with `search_suggestions` HTML; (`code_execution_result`) the code output.",
    )


class InteractionUsage(BaseModel):
    model_config = ConfigDict(extra="allow")
    total_input_tokens: int | None = None
    initial_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_thought_tokens: int | None = None
    total_cached_tokens: int | None = None
    total_tool_use_tokens: int | None = None
    total_tokens: int | None = None
    input_tokens_by_modality: list[dict[str, Any]] | None = None
    output_tokens_by_modality: list[dict[str, Any]] | None = None
    cached_tokens_by_modality: list[dict[str, Any]] | None = None
    tool_use_tokens_by_modality: list[dict[str, Any]] | None = None
    grounding_tool_count: list[dict[str, Any]] | None = None


class InteractionData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    status: str = Field(
        description="`in_progress`, `requires_action`, `completed`, `failed`, `cancelled`, `incomplete` (completed but cut short, e.g. by max tokens) or `requires_continuation`.",
    )
    created: str | None = None
    updated: str | None = None
    steps: list[InteractionStep] | None = None
    model: str | None = None
    agent: str | None = None
    previous_interaction_id: str | None = None
    system_instruction: str | None = None
    tools: list[dict[str, Any]] | None = None
    input: str | list[dict[str, Any]] | dict[str, Any] | None = None
    continuation_token: str | None = None
    errors: list[dict[str, Any]] | None = None
    usage: InteractionUsage | None = None


# create_interaction

class CreateInteractionData(InteractionData):
    pass


class CreateInteractionResult(ToolResult):
    data: CreateInteractionData | None = None


# start_deep_research

class StartDeepResearchData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    status: str = Field(description="`in_progress` at start; later `completed` or `failed`.")
    agent: str | None = None
    created: str | None = None


class StartDeepResearchResult(ToolResult):
    data: StartDeepResearchData | None = None


# get_interaction

class GetInteractionData(InteractionData):
    pass


class GetInteractionResult(ToolResult):
    data: GetInteractionData | None = None


# cancel_interaction

class CancelInteractionData(BaseModel):
    model_config = ConfigDict(extra="allow")
    before: InteractionData
    after: InteractionData


class CancelInteractionResult(ToolResult):
    data: CancelInteractionData | None = None


# delete_interaction

class DeleteInteractionData(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str
    deleted: bool


class DeleteInteractionResult(ToolResult):
    data: DeleteInteractionData | None = None
