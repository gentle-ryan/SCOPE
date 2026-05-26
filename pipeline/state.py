import operator
from typing import Annotated, Optional, TypedDict


class AIAState(TypedDict, total=False):
    # 메타
    run_id: str
    pdf_path: str
    language: str  # "ko" | "en"
    step_status: dict[str, str]
    errors: list[str]
    cache_name: str

    # Step 1
    parsed_markdown: str

    # Step 2
    workflows: list[dict]
    workflow_entities: list[dict]

    # Step 3
    entity_roles: list[dict]
    stakeholder_agents: list[dict]

    # Step 4
    events: list[dict]
    verified_events: list[dict]
    verify_fail_rate: float

    # A/B 테스트 플래그
    event_use_cache: bool

    # Step 5
    simulation_paths: Annotated[dict[int, list], operator.or_]
    scenarios_text: str
    merged_scenarios: str
    feasibility_pruned: int

    # Step 6
    impact_report: dict
