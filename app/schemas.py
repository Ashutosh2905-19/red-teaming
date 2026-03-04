from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Literal, Dict, Any, List, Optional

# Finance-specific for now (later: generalize domains)
Department = Literal[
    "retail_banking","corporate_banking","lending_credit","wealth_management",
    "investment_banking","trading_markets","insurance","taxation","accounting_audit",
    "payments_cards","fintech_products","crypto_digital_assets",
    "risk_management","compliance_regulatory","aml_kyc_fraud","treasury"
]

AttackType = Literal[
    "policy_bypass","misleading_advice","guaranteed_returns","insider_trading",
    "market_manipulation","tax_evasion","fraud","privacy","prompt_injection",
    "hallucination","bias","toxicity","ambiguity","unsafe_instructions"
]

ExpectedBehavior = Literal["REFUSE", "SAFE_ANSWER", "ASK_CLARIFY", "LIMITED_ANSWER"]

class YourModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str

class TaxonomyNode(BaseModel):
    node_id: int
    parent_id: Optional[int]
    node_type: Literal["domain","department","use_case","attack_type"]
    name: str
    path: str  # e.g. finance/wealth_management/portfolio_advice/guaranteed_returns

class PromptItem(BaseModel):
    prompt_id: str
    taxonomy_node_id: int  # points to attack_type node
    domain: str = "finance"
    department: Department
    use_case: str
    attack_type: AttackType
    risk_level: Literal["low","medium","high"]
    prompt_text: str
    expected_behavior: ExpectedBehavior
    policy_tags: List[str] = Field(default_factory=list)

class ModelResponse(BaseModel):
    prompt_id: str
    model_name: str
    text: str
    latency_ms: int
    meta: Dict[str, Any] = Field(default_factory=dict)

class ScoreBreakdown(BaseModel):
    PV: float
    HL: float
    FC: float
    SUIT: float
    FRAUD: float
    TX: float
    RA: float
    RTRI: float
    weights: Dict[str, float]

class RAIReport(BaseModel):
    transparency_ok: bool = True
    suitability_ok: bool = True
    audit_notes: List[str] = Field(default_factory=list)

class GatingDecision(BaseModel):
    label: Literal["SAFE","NEEDS_REVIEW","BLOCKED"]
    reason: str