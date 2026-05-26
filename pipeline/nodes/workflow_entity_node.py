import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from google.genai import types

from config import OUTPUTS_DIR
from pipeline.state import AIAState
from prompts.base_prompts import GENERIC_CRITIQUE_PROMPT, GENERIC_REFINE_PROMPT
from prompts.workflow_entity_prompts import WORKFLOW_DESCRIPTION_PROMPT, ENTITY_EXTRACT_PROMPT
from schemas.workflow_entity_schema import get_workflow_only_schema, ENTITY_EXTRACT_SCHEMA
from services.llm_client import FLASH_MODEL, LLMClient, call_with_retry
from services.rag_service import ensure_index


def workflow_entity_node(state: AIAState) -> dict:
    run_id = state["run_id"]
    parsed_markdown = state["parsed_markdown"]
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id

    ensure_index(run_id, parsed_markdown)

    workflows_path = run_dir / "workflows.json"
    entities_path = run_dir / "entities.json"

    # ── 워크플로우 추출 (3단계 self-refine) ──────────────────────
    if workflows_path.exists() and entities_path.exists():
        print("  [체크포인트] workflows.json + entities.json 존재 → 스킵")
        workflows = json.loads(workflows_path.read_text(encoding="utf-8"))
        workflow_entities = json.loads(entities_path.read_text(encoding="utf-8"))
    else:
        lang = state.get("language", "ko")
        workflow_schema = get_workflow_only_schema(lang)
        # Call 1: 초안 생성
        print("  [워크플로우] 초안 생성 중...")
        resp1 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=WORKFLOW_DESCRIPTION_PROMPT(parsed_markdown, lang=lang),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=workflow_schema,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        draft_workflows = json.loads(resp1.text).get("workflows", [])

        # Call 2: 검토
        print("  [워크플로우] 검토 중...")
        draft_json = json.dumps(draft_workflows, ensure_ascii=False, indent=2)
        resp2 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=GENERIC_CRITIQUE_PROMPT(
                "workflow", lang=lang,
                draft_workflows=draft_json,
                document=parsed_markdown,
            ),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        critique = resp2.text

        # Call 3: 최종 수정
        print("  [워크플로우] 최종 수정 중...")
        resp3 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=GENERIC_REFINE_PROMPT(
                "workflow", lang=lang,
                draft_workflows=draft_json,
                critique=critique,
                document=parsed_markdown,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=workflow_schema,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        final_workflows = json.loads(resp3.text).get("workflows", [])

        workflows = [
            {"id": wf["id"], "type": wf["type"], "description": wf["description"]}
            for wf in final_workflows
        ]
        workflows_path.write_text(json.dumps(workflows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  워크플로우 {len(workflows)}개 추출 완료")

        # Calls 4-18: entity 추출 (5 workflows × 4 runs 병렬)
        N_ENTITY_RUNS = 4
        print(f"  [엔티티] 5개 워크플로우 × {N_ENTITY_RUNS}회 병렬 entity 추출 중...")

        def _names_match(a: str, b: str) -> bool:
            a, b = a.strip(), b.strip()
            return a == b or a in b or b in a

        def _entity_in_list(name: str, lst: list[dict]) -> bool:
            return any(_names_match(name, e["name"]) for e in lst)

        def _union_entities(runs: list[list[dict]]) -> list[dict]:
            """여러 run의 entity 목록을 합집합(name 기반 dedup)으로 합산."""
            merged: list[dict] = []
            for run in runs:
                for entity in run:
                    if not _entity_in_list(entity["name"], merged):
                        merged.append(entity)
            return merged

        def extract_entities_once(wf: dict) -> tuple[int, list, list]:
            resp = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=ENTITY_EXTRACT_PROMPT(
                    wf["id"], wf["type"], wf["description"], parsed_markdown, lang=lang,
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ENTITY_EXTRACT_SCHEMA,
                    temperature=0,
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            result = json.loads(resp.text)
            return wf["id"], result.get("agents", []), result.get("objects", [])

        tasks = [(wf, run_idx) for wf in workflows for run_idx in range(N_ENTITY_RUNS)]
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(extract_entities_once, wf) for wf, _ in tasks]
            raw_results = [f.result() for f in futures]

        # workflow별로 run 결과를 모아 union
        agents_by_wf: dict[int, list[list]] = defaultdict(list)
        objects_by_wf: dict[int, list[list]] = defaultdict(list)
        for wf_id, agents, objects in raw_results:
            agents_by_wf[wf_id].append(agents)
            objects_by_wf[wf_id].append(objects)

        workflow_entities = []
        for wf in sorted(workflows, key=lambda w: w["id"]):
            wf_id = wf["id"]
            merged_agents = _union_entities(agents_by_wf[wf_id])
            merged_objects = _union_entities(objects_by_wf[wf_id])
            for i, a in enumerate(merged_agents, start=1):
                a["agent_id"] = i
            for i, o in enumerate(merged_objects, start=1):
                o["object_id"] = i
            workflow_entities.append({"workflow_id": wf_id, "agents": merged_agents, "objects": merged_objects})

        entities_path.write_text(json.dumps(workflow_entities, ensure_ascii=False, indent=2), encoding="utf-8")
        total_agents = sum(len(we["agents"]) for we in workflow_entities)
        total_objects = sum(len(we["objects"]) for we in workflow_entities)
        print(f"  에이전트 {total_agents}개 | 오브젝트 {total_objects}개 추출 완료")

    return {
        "workflows": workflows,
        "workflow_entities": workflow_entities,
    }
