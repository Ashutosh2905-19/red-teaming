import uuid
from tqdm import tqdm

from app.config import SETTINGS
from app.storage.db_tree import (
    init_db,
    upsert_taxonomy_node,
    insert_prompt,
    insert_run,
    insert_response,
    insert_result,
)

from app.finance.taxonomy import FINANCE_TAXONOMY
from app.finance.generator_finance import generate_finance_prompts
from app.models.ollama_client import OllamaClient
from app.scoring.rtri import score_finance
from app.rai.finance_checks import run_finance_rai
from app.gating.decision import gate


def build_taxonomy_tree() -> dict[str, int]:
    """
    Inserts finance taxonomy into taxonomy_nodes and returns:
    mapping: path -> node_id for attack_type leaf nodes.
    """
    mapping: dict[str, int] = {}

    root_path = "finance"
    finance_id = upsert_taxonomy_node(parent_id=None, node_type="domain", name="finance", path=root_path)

    for dept, usecases in FINANCE_TAXONOMY["finance"].items():
        dept_path = f"{root_path}/{dept}"
        dept_id = upsert_taxonomy_node(parent_id=finance_id, node_type="department", name=dept, path=dept_path)

        for use_case, attacks in usecases.items():
            use_path = f"{dept_path}/{use_case}"
            use_id = upsert_taxonomy_node(parent_id=dept_id, node_type="use_case", name=use_case, path=use_path)

            for attack in attacks:
                attack_path = f"{use_path}/{attack}"
                leaf_id = upsert_taxonomy_node(parent_id=use_id, node_type="attack_type", name=attack, path=attack_path)
                mapping[attack_path] = leaf_id

    return mapping


def get_or_create_leaf_id(dept: str, use_case: str, attack: str, attack_path: str) -> int:
    """
    Robust fallback: if a seed prompt references a taxonomy leaf path that does not exist
    in FINANCE_TAXONOMY, create it in DB so pipeline never breaks.
    """
    root_id = upsert_taxonomy_node(parent_id=None, node_type="domain", name="finance", path="finance")
    dept_id = upsert_taxonomy_node(parent_id=root_id, node_type="department", name=dept, path=f"finance/{dept}")
    use_id = upsert_taxonomy_node(parent_id=dept_id, node_type="use_case", name=use_case, path=f"finance/{dept}/{use_case}")
    leaf_id = upsert_taxonomy_node(parent_id=use_id, node_type="attack_type", name=attack, path=attack_path)
    return leaf_id


def run_finance_pipeline(n_per_seed: int = 2, seed: int = 42) -> str:
    """
    End-to-end finance red teaming pipeline:
    1) init DB
    2) build taxonomy tree
    3) generate prompts (finance seeds + mutations)
    4) run prompts through each LLM
    5) score (RTRI), run RAI checks, apply gating decision
    6) store everything in tree-based DB
    """
    init_db()

    run_id = str(uuid.uuid4())
    insert_run(run_id)

    taxonomy_leaf_map = build_taxonomy_tree()

    prompts = generate_finance_prompts(
        taxonomy_node_id_map=taxonomy_leaf_map,
        get_or_create_leaf_id=get_or_create_leaf_id,
        n_per_seed=n_per_seed,
        seed=seed,
    )

    for p in prompts:
        insert_prompt(p)

    client = OllamaClient()

    for model_name in SETTINGS.ollama_models:
        for p in tqdm(prompts, desc=f"Finance red teaming | model={model_name}"):
            text, latency_ms, meta = client.generate(model_name, p.prompt_text)
            insert_response(run_id, p.prompt_id, model_name, text, latency_ms, meta)

            score = score_finance(
                text=text,
                expected_behavior=p.expected_behavior,
                policy_tags=p.policy_tags
            )
            rai = run_finance_rai(text)
            decision = gate(score)

            insert_result(run_id, p.prompt_id, model_name, score, decision, rai)

    print("\n✅ FINANCE PIPELINE COMPLETE")
    print("DB:", SETTINGS.db_path)
    print("Run ID:", run_id)

    return run_id


if __name__ == "__main__":
    run_finance_pipeline()