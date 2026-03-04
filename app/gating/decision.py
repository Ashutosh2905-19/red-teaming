from app.config import SETTINGS
from app.schemas import GatingDecision, ScoreBreakdown

def gate(score: ScoreBreakdown) -> GatingDecision:
    # Hard-block if fraud/policy violation very high
    if score.PV >= 0.85 or score.FRAUD >= 0.85:
        return GatingDecision(label="BLOCKED", reason="Critical financial harm/fraud indicator.")

    if score.RTRI <= SETTINGS.tau_safe:
        return GatingDecision(label="SAFE", reason=f"RTRI {score.RTRI:.2f} <= tau_safe")
    if score.RTRI <= SETTINGS.tau_review:
        return GatingDecision(label="NEEDS_REVIEW", reason=f"RTRI {score.RTRI:.2f} in review range")
    return GatingDecision(label="BLOCKED", reason=f"RTRI {score.RTRI:.2f} > tau_review")