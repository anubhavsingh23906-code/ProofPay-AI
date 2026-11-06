
from pydantic import BaseModel, Field
from typing import Literal


class TaskCreate(BaseModel):
    title: str = Field(min_length=5, max_length=100)
    description: str = Field(min_length=20, max_length=2000)

    budget: float = Field(gt=0, le=100000)
    currency: Literal["INR"] = "INR"

    deadline_days: int = Field(gt=0, le=30)


class TaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    budget: float
    currency: str
    deadline_days: int
    status: str

class Agreement(BaseModel):
    deliverables: list[str] = Field(
        description="Specific items the freelancer must deliver"
    )

    acceptance_criteria: list[str] = Field(
        description="Measurable conditions for accepting the work"
    )

    client_must_provide: list[str] = Field(
        description="Information, content, or files the client must provide"
    )

    assumptions_or_questions: list[str] = Field(
        description="Missing details that require client confirmation"
    )

    revision_count: int = Field(
        ge=0,
        le=5,
        description="Number of included revisions; use 0 if unspecified"
    )

class AgreementDecision(BaseModel):
    approved: bool

    feedback: str | None = Field(
        default=None,
        max_length=1000,
        description="Client feedback when requesting changes"
    )

class WorkSubmission(BaseModel):
    submission_text: str = Field(
        min_length=10,
        max_length=3000,
        description="Description of the completed work"
    )

    file_names: list[str] = Field(
        default_factory=list,
        description="Names of submitted deliverable files"
    )

class VerificationResult(BaseModel):
    completed_requirements: list[str] = Field(
        description="Requirements supported by the submitted evidence"
    )

    missing_requirements: list[str] = Field(
        description="Requirements not demonstrated by the submission"
    )

    unclear_requirements: list[str] = Field(
        description="Requirements that cannot be verified from available evidence"
    )

    feedback: str = Field(
        description="Clear explanation of the verification result"
    )

    recommendation: Literal[
        "accept",
        "request_revision",
        "manual_review"
    ] = Field(
        description="AI recommendation for the client"
    )

class ClientWorkDecision(BaseModel):

    decision: Literal[
        "accept",
        "request_revision"
    ]

    feedback: str | None = Field(
        default=None,
        max_length=1000,
        description="Client feedback when requesting revisions"
    )


class CapturePaymentRequest(BaseModel):
    order_id: str | None = Field(
        default=None,
        description="PayPal order ID returned after buyer approval. If omitted, the stored order is used.",
    )
