import json
from concurrent.futures import ThreadPoolExecutor, Future
from google.genai import types

from config import OUTPUTS_DIR
from pipeline.state import AIAState

from prompts.base_prompts import GENERIC_CRITIQUE_PROMPT, GENERIC_REFINE_PROMPT
from prompts.entity_role_prompts import ROLE_REFINE_PROMPT, STAKEHOLDER_GENERATE_PROMPT
from schemas.entity_role_schema import STEP3_SCHEMA, STAKEHOLDER_SCHEMA
from services.cache_service import cached_markdown
from services.llm_client import FLASH_MODEL, LLMClient, call_with_retry
from services.rag_service import retrieve_context

def entity_role_node(state: AIAState) -> dict:
    run_id = state["run_id"]
    workflow_entities = state["workflow_entities"]
    workflows = state["workflows"]
    parsed_markdown = state["parsed_markdown"]
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id

    checkpoint = run_dir / "entity_roles.json"
    stakeholders_path = run_dir / "stakeholder_agents.json"

    entity_roles_cached = checkpoint.exists()
    stakeholders_cached = stakeholders_path.exists()

    if entity_roles_cached and stakeholders_cached:
        print("  [체크포인트] entity_roles.json + stakeholder_agents.json 존재 → 스킵")
        return {
            "entity_roles": json.loads(checkpoint.read_text(encoding="utf-8")),
            "stakeholder_agents": json.loads(stakeholders_path.read_text(encoding="utf-8")),
        }

    # ── 이해관계자 파이프라인 (GENERATE → CRITIQUE → REFINE, 내부 순차) ──
    # existing_agents_str은 에이전트 이름만 필요 → workflow_entities에서 바로 구성
    existing_agents_str = "\n".join(
        f"- {a['name']}"
        for we in workflow_entities
        for a in we.get("agents", [])
    )
    def run_stakeholder_pipeline() -> list[dict]:
        lang = state.get("language", "ko")
        doc_prefix = (
            f"The following is a document about an AI service.\n\n{parsed_markdown}\n\n"
            if lang == "en"
            else f"다음은 AI 서비스에 대한 문서입니다.\n\n{parsed_markdown}\n\n"
        )
        print("  [이해관계자] 초안 생성 중...")
        resp1 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=doc_prefix + STAKEHOLDER_GENERATE_PROMPT(existing_agents_str, lang=lang),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=STAKEHOLDER_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="medium"),
            ),
        )
        draft = json.loads(resp1.text).get("stakeholder_agents", [])
        draft_json = json.dumps(draft, ensure_ascii=False, indent=2)

        print("  [이해관계자] 검토 중...")
        resp2 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=GENERIC_CRITIQUE_PROMPT(
                "stakeholder", lang=lang,
                draft_stakeholders=draft_json,
                existing_agents=existing_agents_str,
            ),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )

        print("  [이해관계자] 최종 수정 중...")
        resp3 = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=GENERIC_REFINE_PROMPT(
                "stakeholder", lang=lang,
                draft_stakeholders=draft_json,
                critique=resp2.text,
                existing_agents=existing_agents_str,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=STAKEHOLDER_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        result = json.loads(resp3.text).get("stakeholder_agents", [])
        stakeholders_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  이해관계자 {len(result)}명 식별 완료")
        return result

    # ── entity_roles 캐시 있으면 로드, 없으면 태스크 구성 ──────────
    if entity_roles_cached:
        print("  [체크포인트] entity_roles.json 존재 → entity_role 스킵")
        enriched_entities = json.loads(checkpoint.read_text(encoding="utf-8"))
        # entity_roles는 이미 있고 stakeholder만 필요 → 단독 실행
        stakeholder_agents = run_stakeholder_pipeline()
        return {"entity_roles": enriched_entities, "stakeholder_agents": stakeholder_agents}

    # ── entity_roles 미캐시: agent+object 개수대로 호출 + 이해관계자 파이프라인 병렬 ──
    wf_desc_map = {wf["id"]: wf.get("description", "") for wf in workflows}
    tasks: list[tuple] = []
    for we in workflow_entities:
        wf_id = we["workflow_id"]
        wf_desc = wf_desc_map.get(wf_id, "")
        for agent in we.get("agents", []):
            tasks.append(("agent", agent, wf_desc))
        for obj in we.get("objects", []):
            tasks.append(("object", obj, wf_desc))

    n_entity_workers = len(tasks)
    # +1: 이해관계자 파이프라인 스레드 (stakeholder 미캐시 시에만)
    n_workers = n_entity_workers + (0 if stakeholders_cached else 1)
    print(f"  병렬 실행: entity_role {len(tasks)}개 + {'이해관계자 파이프라인 1개' if not stakeholders_cached else '(이해관계자 스킵)'}")

    def enrich_one(task: tuple, cache_name: str) -> None:
        entity_type, entity, wf_desc = task
        name = entity.get("name", "")
        original_role = entity.get("role", "")
        rag_chunks = retrieve_context(run_id, f"{name}, {original_role}")
        rag_context = "\n---\n".join(rag_chunks)
        prompt = ROLE_REFINE_PROMPT(
            entity_type, name, original_role, wf_desc, rag_context,
            lang=state.get("language", "ko"),
        )
        response = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                cached_content=cache_name,
                response_mime_type="application/json",
                response_schema=STEP3_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        entity["detailed_role"] = json.loads(response.text).get("detailed_role", original_role)

    with cached_markdown(client, parsed_markdown, f"aia_{run_id}_entity_role", model=FLASH_MODEL) as cache_name:
        with ThreadPoolExecutor(max_workers=max(n_workers, 1)) as executor:
            entity_futures: list[Future] = [
                executor.submit(enrich_one, task, cache_name) for task in tasks
            ]
            sh_future: Future | None = (
                None if stakeholders_cached
                else executor.submit(run_stakeholder_pipeline)
            )

            for f in entity_futures:
                f.result()

            if sh_future is not None:
                stakeholder_agents = sh_future.result()
            else:
                print("  [체크포인트] stakeholder_agents.json 존재 → 스킵")
                stakeholder_agents = json.loads(stakeholders_path.read_text(encoding="utf-8"))

    enriched_entities = workflow_entities
    checkpoint.write_text(json.dumps(enriched_entities, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  entity_role 완료: {len(tasks)}개 detailed_role 추가")

    return {
        "entity_roles": enriched_entities,
        "stakeholder_agents": stakeholder_agents,
    }
