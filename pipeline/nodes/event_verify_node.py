import json
from concurrent.futures import ThreadPoolExecutor
from google.genai import types
import numpy as np

from config import GEMINI_EMBED_MODEL, OUTPUTS_DIR
from pipeline.state import AIAState
from prompts.base_prompts import RAG_VERIFY_PROMPT
from prompts.event_verify_prompts import EVENT_GENERATE_PROMPT, EVENT_LLM_DEDUP_PROMPT
from schemas.event_verify_schema import EVENT_SCHEMA, EVENT_VERIFY_RAG_SCHEMA, EVENT_LLM_DEDUP_SCHEMA
from services.llm_client import FLASH_MODEL, LITE_MODEL, LLMClient, call_with_retry
from services.rag_service import retrieve_context

_GEN_CONCURRENCY = 500
_VERIFY_CONCURRENCY = 500
_LLM_DEDUP_CONCURRENCY = 500
_PRUNE_THRESHOLD = 0.85
_GEN_ROUNDS = 7


_EMBED_BATCH = 100


def _deduplicate(events: list[dict], client) -> list[dict]:
    if len(events) <= 1:
        return events

    texts = [e.get("event_description", "") for e in events]
    batches = [texts[i : i + _EMBED_BATCH] for i in range(0, len(texts), _EMBED_BATCH)]

    # 임베딩 배치 병렬 요청
    def embed_batch(batch: list[str]) -> list[list[float]]:
        result = client.models.embed_content(model=GEMINI_EMBED_MODEL, contents=batch)
        return [e.values for e in result.embeddings]

    with ThreadPoolExecutor(max_workers=len(batches)) as executor:
        batch_results = list(executor.map(embed_batch, batches))

    embeddings = [emb for batch in batch_results for emb in batch]

    # numpy 행렬 연산으로 전체 pairwise cosine similarity 한 번에 계산
    mat = np.array(embeddings, dtype=np.float32)
    mat /= np.maximum(np.linalg.norm(mat, axis=1, keepdims=True), 1e-10)
    sim = mat @ mat.T  # (N, N)

    N = len(events)
    kept_mask = np.ones(N, dtype=bool)
    for i in range(N):
        if not kept_mask[i]:
            continue
        kept_mask[i + 1 :][sim[i, i + 1 :] > _PRUNE_THRESHOLD] = False

    return [events[i] for i in range(N) if kept_mask[i]]


def _llm_dedup(events: list[dict], client, lang: str = "ko") -> list[dict]:
    from collections import defaultdict
    buckets: dict[tuple, list[dict]] = defaultdict(list)
    for ev in events:
        key = (ev.get("workflow_id", 0), ev.get("entity_name", ""), ev.get("property", ""))
        buckets[key].append(ev)

    def dedup_bucket(bucket_item):
        key, evs = bucket_item
        wf_id, entity_name, property_ = key
        if len(evs) <= 1:
            return evs
        descriptions = "\n".join(f"{i+1}. {e['event_description']}" for i, e in enumerate(evs))
        prompt = EVENT_LLM_DEDUP_PROMPT(
            entity_name=entity_name, property=property_, descriptions=descriptions, lang=lang,
        )
        response = call_with_retry(
            client.models.generate_content,
            model=LITE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EVENT_LLM_DEDUP_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        )
        reps = json.loads(response.text)
        return [
            {"event_id": 0, "workflow_id": wf_id, "entity_name": entity_name,
             "property": property_, "event_description": r["representative"]}
            for r in reps
        ]

    print(f"  LLM 중복 제거: {len(buckets)}개 버킷 (동시 {_LLM_DEDUP_CONCURRENCY})")
    with ThreadPoolExecutor(max_workers=_LLM_DEDUP_CONCURRENCY) as executor:
        results = list(executor.map(dedup_bucket, buckets.items()))

    flat = [ev for bucket in results for ev in bucket]
    for i, ev in enumerate(flat, start=1):
        ev["event_id"] = i
    return flat


def event_verify_node(state: AIAState) -> dict:
    run_id = state["run_id"]
    workflows = state["workflows"]
    entity_roles = state["entity_roles"]
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id

    wf_desc_map = {wf["id"]: wf.get("description", "") for wf in workflows}

    checkpoint = run_dir / "verified_events.json"
    if checkpoint.exists():
        print("  [체크포인트] verified_events.json 존재 → 스킵")
        return {
            "verified_events": json.loads(checkpoint.read_text(encoding="utf-8")),
            "verify_fail_rate": 0.0,
        }

    # ── 이벤트 생성 ──────────────────────────────────────────────
    events_path = run_dir / "events.json"

    if events_path.exists():
        print("  [체크포인트] events.json 존재 → 이벤트 생성 스킵")
        all_events = json.loads(events_path.read_text(encoding="utf-8"))
    else:
        # entity별 (workflow_id, entity, entity_type, detailed_role) 목록 구성
        entity_tasks: list[tuple] = []
        for we in entity_roles:
            wf_id = we["workflow_id"]
            for agent in we.get("agents", []):
                entity_tasks.append((wf_id, agent, "agent"))
            for obj in we.get("objects", []):
                entity_tasks.append((wf_id, obj, "object"))

        # 각 entity × _GEN_ROUNDS회 → (task, round) 쌍
        gen_tasks: list[tuple] = []
        for wf_id, entity, entity_type in entity_tasks:
            for _ in range(_GEN_ROUNDS):
                gen_tasks.append((wf_id, entity, entity_type))

        lang = state.get("language", "ko")

        def generate_events(wf_id: int, entity: dict, entity_type: str) -> list[dict]:
            name = entity.get("name", "")
            detailed_role = entity.get("detailed_role", entity.get("role", ""))
            prompt = EVENT_GENERATE_PROMPT(entity_type, name, detailed_role, lang=lang)
            config_kwargs: dict = dict(
                response_mime_type="application/json",
                response_schema=EVENT_SCHEMA,
                temperature=0.5,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            )
            response = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            events = json.loads(response.text)
            for ev in events:
                ev["workflow_id"] = wf_id
                ev["entity_name"] = name
                ev["entity_type"] = entity_type
            return events

        print(f"  이벤트 생성: {len(gen_tasks)}개 호출 병렬 실행 (entity {len(entity_tasks)}개 × {_GEN_ROUNDS}회, 동시 {_GEN_CONCURRENCY})")
        with ThreadPoolExecutor(max_workers=_GEN_CONCURRENCY) as executor:
            futures = [executor.submit(generate_events, wf_id, entity, entity_type)
                       for wf_id, entity, entity_type in gen_tasks]
            results = [f.result() for f in futures]

        all_events: list[dict] = []
        seen_ids: set[int] = set()
        next_id = 1
        for events in results:
            for event in events:
                if event.get("event_id") in seen_ids:
                    event["event_id"] = next_id
                seen_ids.add(event["event_id"])
                next_id = max(next_id, event["event_id"]) + 1
                all_events.append(event)

        events_path.write_text(json.dumps(all_events, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  이벤트 {len(all_events)}개 생성 완료")

    # ── LLM 버킷 중복 제거 (embedding dedup 포함 체크포인트) ────────
    llm_dedup_path = run_dir / "llm_dedup_events.json"
    if llm_dedup_path.exists():
        print("  [체크포인트] llm_dedup_events.json 존재 → embedding+LLM dedup 스킵")
        all_events = json.loads(llm_dedup_path.read_text(encoding="utf-8"))
    else:
        before = len(all_events)
        all_events = _deduplicate(all_events, client)
        print(f"  임베딩 pruning: {before} → {len(all_events)}개 (-{before - len(all_events)})")
        before = len(all_events)
        all_events = _llm_dedup(all_events, client, lang=state.get("language", "ko"))
        print(f"  LLM dedup: {before} → {len(all_events)}개 (-{before - len(all_events)})")
        llm_dedup_path.write_text(json.dumps(all_events, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── entity_role 조회용 맵 ────────────────────────────────────
    # (wf_id, entity_name) → detailed_role
    entity_role_map: dict[tuple, str] = {}
    for we in entity_roles:
        wf_id = we["workflow_id"]
        for e in we.get("agents", []) + we.get("objects", []):
            entity_role_map[(wf_id, e["name"])] = e.get("detailed_role", e.get("role", ""))

    # ── 이벤트 RAG 검증 ──────────────────────────────────────────
    def verify_one(event: dict) -> bool:
        rag_chunks = retrieve_context(run_id, event.get("event_description", ""))
        rag_context = "\n---\n".join(rag_chunks)

        wf_id = event.get("workflow_id", 0)
        workflow_context = wf_desc_map.get(wf_id, "")

        entity_name = event.get("entity_name", "")
        entity_detailed_role = entity_role_map.get((wf_id, entity_name), "")

        prompt = RAG_VERIFY_PROMPT(
            "event", lang=state.get("language", "ko"),
            workflow_context=workflow_context,
            entity_name=entity_name,
            entity_detailed_role=entity_detailed_role,
            event=json.dumps(event, ensure_ascii=False),
            rag_context=rag_context,
        )
        response = call_with_retry(
            client.models.generate_content,
            model=LITE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EVENT_VERIFY_RAG_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        )
        result = json.loads(response.text)
        return result.get("is_valid", False)

    print(f"  이벤트 RAG 검증: {len(all_events)}개 (동시 {_VERIFY_CONCURRENCY})")
    with ThreadPoolExecutor(max_workers=_VERIFY_CONCURRENCY) as executor:
        valid_flags = list(executor.map(verify_one, all_events))

    verified_events = [e for e, valid in zip(all_events, valid_flags) if valid]
    fail_rate = (len(all_events) - len(verified_events)) / len(all_events) if all_events else 0.0
    print(f"  검증 통과: {len(verified_events)}/{len(all_events)} (실패율 {fail_rate:.1%})")

    # Normalize to nested entity format for consistent frontend consumption
    for ev in verified_events:
        if "entity_name" in ev:
            ev["entity"] = {
                "entity_name": ev.pop("entity_name"),
                "entity_type": ev.pop("entity_type", ""),
            }

    checkpoint.write_text(json.dumps(verified_events, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"verified_events": verified_events, "verify_fail_rate": fail_rate}
