"""Contracts shared by the API, model adapter and scoring policy."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

Category = Literal['Operations', 'Security', 'Compliance', 'Financial', 'Delivery', 'Reputation']
Note = Annotated[str, Field(min_length=5, max_length=1500)]

class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Brief(Contract):
    title: str = Field(min_length=5, max_length=120)
    decision: str = Field(min_length=30, max_length=12000)
    constraints: str = Field(default='', max_length=6000)
    owner: str = Field(default='', max_length=80)
    category: Category = 'Operations'
    appetite: Literal['Cautious', 'Balanced', 'Flexible'] = 'Balanced'

class AssessmentRequest(Brief):
    mode: Literal['live', 'sample'] = 'live'
    sample_id: str | None = None

class Risk(Contract):
    title: str = Field(min_length=5, max_length=160)
    category: Category
    likelihood: int = Field(strict=True, ge=1, le=5)
    impact: int = Field(strict=True, ge=1, le=5)
    rationale: str = Field(min_length=15, max_length=1500)
    evidence: str = Field(max_length=1500, description='Exact quotation from the brief, or empty if inferred.')
    mitigation: str = Field(min_length=10, max_length=1500)
    monitoring_signal: str = Field(min_length=5, max_length=500)

class Outlook(Contract):
    best_case: str = Field(min_length=10, max_length=1500)
    base_case: str = Field(min_length=10, max_length=1500)
    worst_case: str = Field(min_length=10, max_length=1500)

class ModelAssessment(Contract):
    executive_summary: str = Field(min_length=30, max_length=3000)
    risks: list[Risk] = Field(min_length=1, max_length=8)
    assumptions: list[Note] = Field(min_length=1, max_length=8)
    open_questions: list[Note] = Field(min_length=1, max_length=8)
    next_steps: list[Note] = Field(min_length=1, max_length=8)
    outlook: Outlook


class ConditionalAssumption(Contract):
    condition: str = Field(min_length=10, max_length=650,
        description='An UNVERIFIED prerequisite relevant to this brief, written as a requirement rather than an existing fact. Natural wording is allowed. Do not invent safeguards or repeat known facts.')
    verification: str = Field(min_length=10, max_length=650,
        description='A concrete check that can establish whether the prerequisite is met. Never request secrets.')


class LiveAssessment(ModelAssessment):
    """Live generation contract; stored legacy/sample reports retain their original schema."""
    assumptions: list[ConditionalAssumption] = Field(min_length=1, max_length=3,
        description='Unverified prerequisites and how to verify them. Not supplied facts or predictions. Never contradict explicit constraints by assuming them resolved.')

class ReviewRequest(Contract):
    action: Literal['APPROVED', 'REVISION_REQUESTED', 'BLOCKED']
    reviewer: str = Field(min_length=2, max_length=80)
    note: str = Field(min_length=10, max_length=2500)
    expected_version: int = Field(strict=True, ge=0)
    checks_completed: list[Literal['source_facts', 'contradictions', 'actionability']] = Field(default_factory=list)
