from pydantic import BaseModel, ConfigDict, Field

from ._base import ToolResult


class DecisionAnswer(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str | None = Field(default=None, description="`noul`, `choice` or `score`, matching the question.")
    confidence: float | None = None
    noul: float | None = Field(default=None, description="(`noul`) Probability that the statement is true.")
    choice: str | None = Field(default=None, description="(`choice`) The selected option key.")
    probabilities: dict[str, float] | None = Field(
        default=None,
        description="(`choice`, `score`) Probability per option key (`choice`) or per level index as a string (`score`).",
    )
    score: float | None = Field(default=None, description="(`score`) Expected score on the level scale (e.g. 1.8).")
    legend: dict[str, str] | None = Field(
        default=None,
        description="(`score`) Level index (as a string) to the level description from `criteria`.",
    )


class ModalityTokens(BaseModel):
    model_config = ConfigDict(extra="allow")

    modality: str | None = None
    tokens: int | None = None


class Usage(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_input_tokens: int | None = None
    total_output_tokens: int | None = None
    total_tokens: int | None = None
    input_tokens_by_modality: list[ModalityTokens] | None = None


class PromptFeedback(BaseModel):
    model_config = ConfigDict(extra="allow")

    block_reason: str | None = Field(
        default=None,
        description="If set, the input was blocked and no answers are returned: "
                    "`safety`, `other`, `blocklist`, `prohibited_content`, `image_safety`.",
    )
    block_reason_message: str | None = None


class CreateDecisionData(BaseModel):
    model_config = ConfigDict(extra="allow")

    answers: dict[str, DecisionAnswer] = Field(
        default_factory=dict,
        description="Decision answers keyed by the question identifiers from `questions`.",
    )
    usage: Usage | None = None
    prompt_feedback: PromptFeedback | None = None


class CreateDecisionResult(ToolResult):
    data: CreateDecisionData | None = None
