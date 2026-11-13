from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class BidStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    won = "won"
    lost = "lost"


# --- Client schemas ---


class ClientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str = Field(min_length=1, max_length=100)
    past_bids_won: int = Field(default=0, ge=0)
    past_bids_lost: int = Field(default=0, ge=0)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = Field(default=None, min_length=1, max_length=100)
    past_bids_won: int | None = Field(default=None, ge=0)
    past_bids_lost: int | None = Field(default=None, ge=0)


class ClientResponse(BaseModel):
    id: int
    name: str
    industry: str
    past_bids_won: int
    past_bids_lost: int

    model_config = {"from_attributes": True}


# --- Bid schemas ---


class BidCreate(BaseModel):
    client_id: int
    title: str = Field(min_length=1, max_length=300)
    value: float = Field(gt=0)
    estimated_cost: float = Field(gt=0)
    deadline: date
    status: BidStatus = BidStatus.draft
    notes: str | None = None


class BidUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    value: float | None = Field(default=None, gt=0)
    estimated_cost: float | None = Field(default=None, gt=0)
    deadline: date | None = None
    status: BidStatus | None = None
    notes: str | None = None


class BidResponse(BaseModel):
    id: int
    client_id: int
    title: str
    value: float
    estimated_cost: float
    deadline: date
    status: BidStatus
    notes: str | None

    model_config = {"from_attributes": True}


# --- Risk assessment schemas ---


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RiskReport(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    reasons: list[str]
    recommendation: str = Field(default="")


class AssessmentResponse(BaseModel):
    id: int
    bid_id: int
    score: int
    level: RiskLevel
    reasons: list[str]
    recommendation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RiskSummaryItem(BaseModel):
    bid_id: int
    bid_title: str
    client_name: str
    score: int
    level: RiskLevel
    reasons: list[str]


class RiskSummaryResponse(BaseModel):
    top_risks: list[RiskSummaryItem]
    total_open_bids: int
