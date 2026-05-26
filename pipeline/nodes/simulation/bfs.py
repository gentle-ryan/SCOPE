import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types

from config import STEP5_MAX_TURN
from prompts.sim_prompts import SCENARIO_PROPAGATION_PROMPT, VALIDATOR_PROMPT
from schemas.sim_schema import PASSIVE_TURN1_SCHEMA, PASSIVE_TURN23_SCHEMA, ACTIVE_BATCH_SCHEMA, VALIDATOR_SCHEMA
from services.llm_client import FLASH_MODEL, LITE_MODEL, call_with_retry
from .branch_state import BranchState
from .history_formatter import format_single_history

_BFS_CONCURRENCY = 20


def safe_format(template: str, **kwargs) -> str:
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def _call_llm(client: genai.Client, prompt: str, schema: dict,
              max_output_tokens: int = 65536, thinking_level: str = "low",
              model: str = FLASH_MODEL) -> dict:
    for attempt in range(3):
        response = call_with_retry(
            client.models.generate_content,
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                max_output_tokens=max_output_tokens,
                thinking_config=types.ThinkingConfig(thinking_level=thinking_level),
            ),
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            if attempt == 2:
                raise
            print(f"  [_call_llm] JSONDecodeError (attempt {attempt+1}/3): {e} — 재시도")


def _apply_passive_turn1(
    branches: list[BranchState],
    context_map: dict[int, dict],
    client: genai.Client,
    executor: ThreadPoolExecutor,
    lang: str = "ko",
) -> list[BranchState]:
    def process_one(branch: BranchState) -> list[BranchState]:
        ctx = context_map.get(branch.wf_id, {})
        prompt = SCENARIO_PROPAGATION_PROMPT(
            "passive_initial",
            workflow_context=ctx.get("workflow_context", ""),
            entity_roles=ctx.get("entity_roles_str", ""),
            branch_history=format_single_history(branch),
            lang=lang,
        )
        result = _call_llm(client, prompt, PASSIVE_TURN1_SCHEMA, thinking_level="medium")
        new_branches = []
        for idx, agent_item in enumerate(result.get("agents", []), start=1):
            child = BranchState(
                branch_id=f"{branch.branch_id}_{idx}",
                event_id=branch.event_id,
                wf_id=branch.wf_id,
                history=branch.history + [{
                    "type": "effect",
                    "entity": agent_item.get("agent", ""),
                    "content": agent_item.get("effect", ""),
                }],
            )
            new_branches.append(child)
        return new_branches

    futures = [executor.submit(process_one, b) for b in branches]
    new_branches = []
    for f in futures:
        new_branches.extend(f.result())
    return new_branches


def _apply_active(
    branches: list[BranchState],
    context_map: dict[int, dict],
    client: genai.Client,
    executor: ThreadPoolExecutor,
    lang: str = "ko",
) -> None:
    alive = [b for b in branches if not b.is_terminated]
    if not alive:
        return

    def process_one(branch: BranchState) -> None:
        ctx = context_map.get(branch.wf_id, {})
        prompt = SCENARIO_PROPAGATION_PROMPT(
            "active",
            workflow_context=ctx.get("workflow_context", ""),
            entity_roles=ctx.get("entity_roles_str", ""),
            branch_history=format_single_history(branch),
            lang=lang,
        )
        result = _call_llm(client, prompt, ACTIVE_BATCH_SCHEMA)
        branch.history.append({
            "type": "action",
            "entity": result.get("actor", ""),
            "content": result.get("action", ""),
        })

    futures = [executor.submit(process_one, b) for b in alive]
    for f in futures:
        f.result()


def _apply_passive_turn23(
    branches: list[BranchState],
    context_map: dict[int, dict],
    client: genai.Client,
    executor: ThreadPoolExecutor,
    lang: str = "ko",
) -> None:
    alive = [b for b in branches if not b.is_terminated]
    if not alive:
        return

    def process_one(branch: BranchState) -> None:
        ctx = context_map.get(branch.wf_id, {})
        prompt = SCENARIO_PROPAGATION_PROMPT(
            "passive_continue",
            workflow_context=ctx.get("workflow_context", ""),
            entity_roles=ctx.get("entity_roles_str", ""),
            branch_history=format_single_history(branch),
            lang=lang,
        )
        result = _call_llm(client, prompt, PASSIVE_TURN23_SCHEMA)
        effect = result.get("effect", {})
        branch.history.append({
            "type": "effect",
            "entity": effect.get("impacted_agent", ""),
            "content": effect.get("effect", ""),
        })

    futures = [executor.submit(process_one, b) for b in alive]
    for f in futures:
        f.result()


def _apply_validator(
    branches: list[BranchState],
    context_map: dict[int, dict],
    client: genai.Client,
    executor: ThreadPoolExecutor,
    lang: str = "ko",
) -> None:
    alive = [b for b in branches if not b.is_terminated]
    if not alive:
        return

    def validate_one(branch: BranchState) -> None:
        if not branch.history:
            return
        last_step = branch.history[-1]
        ctx = context_map.get(branch.wf_id, {})
        prompt = safe_format(
            VALIDATOR_PROMPT(lang=lang),
            workflow_context=ctx.get("workflow_context", ""),
            entity_roles=ctx.get("entity_roles_str", ""),
            branch_history=format_single_history(branch),
            last_step_type=last_step["type"],
            last_step_content=last_step["content"],
        )
        result = _call_llm(client, prompt, VALIDATOR_SCHEMA, max_output_tokens=4096,
                           thinking_level="minimal", model=LITE_MODEL)
        if result.get("should_terminate"):
            branch.is_terminated = True
            branch.termination_reason = result.get("termination_reason", "none")

    futures = [executor.submit(validate_one, b) for b in alive]
    for f in futures:
        f.result()


def _run_single_event(
    root: BranchState,
    context_map: dict[int, dict],
    client: genai.Client,
    llm_executor: ThreadPoolExecutor,
    idx: int,
    total: int,
    lang: str = "ko",
) -> tuple[int, list[BranchState]]:
    """단일 이벤트의 전체 BFS Turn 1~N을 독립적으로 실행."""
    # Turn 1: passive → validator → active → validator
    branches = _apply_passive_turn1([root], context_map, client, llm_executor, lang=lang)
    _apply_validator(branches, context_map, client, llm_executor, lang=lang)
    _apply_active(branches, context_map, client, llm_executor, lang=lang)
    _apply_validator(branches, context_map, client, llm_executor, lang=lang)

    # Turn 2+: passive → validator [→ active → validator] (마지막 turn은 passive로 끝)
    for turn in range(2, STEP5_MAX_TURN + 1):
        alive = [b for b in branches if not b.is_terminated]
        if not alive:
            break
        _apply_passive_turn23(branches, context_map, client, llm_executor, lang=lang)
        _apply_validator(branches, context_map, client, llm_executor, lang=lang)
        if turn == STEP5_MAX_TURN:
            break
        alive = [b for b in branches if not b.is_terminated]
        if not alive:
            break
        _apply_active(branches, context_map, client, llm_executor, lang=lang)
        _apply_validator(branches, context_map, client, llm_executor, lang=lang)

    alive_count = sum(1 for b in branches if not b.is_terminated)
    terminated = sum(1 for b in branches if b.is_terminated)
    print(f"    [E{idx}/{total}] event_id={root.event_id} — branches={len(branches)}, alive={alive_count}, terminated={terminated}")
    return root.event_id, branches


def run_bfs_all_events(
    events: list[dict],
    context_map: dict[int, dict],
    client: genai.Client,
    max_workers: int = _BFS_CONCURRENCY,
    lang: str = "ko",
) -> dict[int, list[BranchState]]:
    """이벤트별 독립 병렬 BFS. 각 이벤트가 Turn1~N을 독립적으로 완주."""
    roots = []
    for event in events:
        eid = event["event_id"]
        wf_id = event.get("workflow_id", 0)
        roots.append(BranchState(
            branch_id=str(eid),
            event_id=eid,
            wf_id=wf_id,
            history=[{
                "type": "event",
                "entity": event.get("entity", {}).get("entity_name", ""),
                "content": event.get("event_description", ""),
            }],
        ))

    n = len(roots)
    print(f"    BFS 시작: {n}개 이벤트 독립 병렬 처리 (LLM worker={max_workers})")

    result: dict[int, list[BranchState]] = {}

    # llm_executor: 실제 LLM 호출 담당
    # event_executor: 이벤트별 파이프라인 실행 담당 (두 풀 분리로 데드락 방지)
    with ThreadPoolExecutor(max_workers=max_workers) as llm_executor:
        with ThreadPoolExecutor(max_workers=n) as event_executor:
            futures = {
                event_executor.submit(
                    _run_single_event, root, context_map, client, llm_executor, i + 1, n, lang
                ): root.event_id
                for i, root in enumerate(roots)
            }
            done = 0
            for fut in as_completed(futures):
                event_id, branches = fut.result()
                result[event_id] = branches
                done += 1
                if done % 5 == 0 or done == n:
                    print(f"    진행: {done}/{n} 이벤트 완료")

    return result
