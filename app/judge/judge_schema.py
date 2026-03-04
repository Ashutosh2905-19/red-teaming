from pydantic import BaseModel, Field
from typing import List, Dict, Literal

Decision = Literal["SAFE", "REVIEW", "BLOCK"]

class JudgeOutput(BaseModel):
    decision: Decision
    decision_reason: str

    PV: float = Field(ge=0, le=1)
    HL: float = Field(ge=0, le=1)
    FC: float = Field(ge=0, le=1)
    SUIT: float = Field(ge=0, le=1)
    FRAUD: float = Field(ge=0, le=1)
    TX: float = Field(ge=0, le=1)
    RA: float = Field(ge=0, le=1)
    RTRI: float = Field(ge=0, le=1)

    evidence: List[str] = []
    notes: Dict[str, str] = {}