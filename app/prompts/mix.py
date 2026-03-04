import random
from app.prompts.attack_library import ATTACK_PATTERNS, GENUINE_PATTERNS

def wrap_question(q: str, attack_type: str, jailbreak: bool, rnd: random.Random) -> str:
    if jailbreak:
        candidates = ATTACK_PATTERNS.get(attack_type, ATTACK_PATTERNS.get("prompt_injection", []))
        template = rnd.choice(candidates) if candidates else "{q}"
        return template.format(q=q)
    else:
        return rnd.choice(GENUINE_PATTERNS).format(q=q)

def mix_prompts(base_questions: list[str], attack_type: str, jailbreak_ratio: float, seed: int = 42):
    rnd = random.Random(seed)
    out = []
    for q in base_questions:
        jb = rnd.random() < jailbreak_ratio
        out.append((wrap_question(q, attack_type, jb, rnd), "JAILBREAK" if jb else "GENUINE"))
    return out