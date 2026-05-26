import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai import types

from config import GEMINI_EMBED_MODEL, OUTPUTS_DIR
from pipeline.state import AIAState
from pipeline.nodes.simulation import run_bfs_all_events
from prompts.base_prompts import RAG_VERIFY_PROMPT, _safe_format as safe_format
from prompts.sim_prompts import MERGE_PROMPT
from schemas.sim_schema import SCENARIO_VERIFY_RAG_SCHEMA
from services.llm_client import FLASH_MODEL, LITE_MODEL, LLMClient, call_with_retry
from services.rag_service import retrieve_context

_N_GROUPS = 10
_BFS_CONCURRENCY = 1000
_VERIFY_CONCURRENCY = 1000
_PRUNE_THRESHOLD = 0.85


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return dot / mag if mag else 0.0


def _split_chunks(lst: list, n: int) -> list[list]:
    size = math.ceil(len(lst) / n) if lst else 1
    return [lst[i : i + size] for i in range(0, len(lst), size)]


def _format_entity_roles(we: dict, stakeholder_agents: list[dict] | None = None) -> str:
    lines = []
    for a in we.get("agents", []):
        lines.append(f"[에이전트] {a['name']}: {a.get('detailed_role', a.get('role', ''))}")
    for o in we.get("objects", []):
        lines.append(f"[오브젝트] {o['name']}: {o.get('detailed_role', o.get('role', ''))}")
    if stakeholder_agents:
        for impact_type, label in [("primary", "직접적"), ("secondary", "간접적"), ("unintended", "의도치 않은")]:
            filtered = [s for s in stakeholder_agents if s.get("impact_type") == impact_type]
            if filtered:
                lines.append(f"\n[{label} 이해관계자]")
                for s in filtered:
                    lines.append(f"- {s['name']}: {s.get('detailed_role', s.get('role', ''))}")
    return "\n".join(lines)


def _build_workflow_context(wf_id: int, wf_desc_map: dict) -> str:
    return "\n".join(
        f"[단계 {wid}] {desc}"
        for wid, desc in sorted(wf_desc_map.items())
        if wid >= wf_id
    )


def sim_node(state: AIAState) -> dict:
    run_id = state["run_id"]
    verified_events = state["verified_events"]
    entity_roles = state["entity_roles"]
    workflows = state["workflows"]
    stakeholder_agents = state.get("stakeholder_agents", [])
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id

    lang = state.get("language", "ko")
    wf_desc_map = {wf["id"]: wf.get("description", "") for wf in workflows}
    entity_role_map = {we["workflow_id"]: we for we in entity_roles}
    event_wf_map = {e["event_id"]: e["workflow_id"] for e in verified_events}

    # ─── Phase 1: BFS 시뮬레이션 ──────────────────────────────
    sim_paths_path = run_dir / "simulation_paths.json"
    if sim_paths_path.exists():
        print("  [Phase 1 체크포인트] simulation_paths.json 존재 → 스킵")
        simulation_paths = json.loads(sim_paths_path.read_text(encoding="utf-8"))
        feasibility_pruned = 0
    else:
        context_map = {
            wf_id: {
                "workflow_context": _build_workflow_context(wf_id, wf_desc_map),
                "entity_roles_str": _format_entity_roles(entity_role_map.get(wf_id, {}), stakeholder_agents),
            }
            for wf_id in {e.get("workflow_id", 0) for e in verified_events}
        }
        print(f"  [Phase 1] BFS: {len(verified_events)}개 이벤트 (동시 {_BFS_CONCURRENCY})")
        bfs_result = run_bfs_all_events(verified_events, context_map, client, max_workers=_BFS_CONCURRENCY, lang=state.get("language", "ko"))

        simulation_paths: dict[str, list] = {}
        feasibility_pruned = 0
        for event_id, branches in bfs_result.items():
            simulation_paths[str(event_id)] = [
                {
                    "branch_id": b.branch_id,
                    "history": b.history,
                    "is_terminated": b.is_terminated,
                    "termination_reason": b.termination_reason,
                }
                for b in branches
            ]
            feasibility_pruned += sum(1 for b in branches if b.is_terminated)

        sim_paths_path.write_text(
            json.dumps(simulation_paths, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  [Phase 1 완료] feasibility_pruned={feasibility_pruned}")

    # ─── Phase 2: 포맷 + 임베딩 중복 제거 ────────────────────
    scenarios_path = run_dir / "scenarios.json"
    raw_path = run_dir / "raw_scenarios.json"
    if scenarios_path.exists():
        print("  [Phase 2 체크포인트] scenarios.json 존재 → 스킵")
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))
    else:
        if raw_path.exists():
            print("  [Phase 2 체크포인트] raw_scenarios.json 존재 → raw 생성 스킵, embedding dedup부터 시작")
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            raw: list[dict] = []
            discard_count = 0
            for event_id_str, branches in simulation_paths.items():
                wf_id = event_wf_map.get(int(event_id_str), 0)
                for b in branches:
                    reason = b.get("termination_reason", "none")
                    if b.get("is_terminated"):
                        if reason in ("infeasible", "acausal"):
                            # 유효하지 않은 경로 — 폐기
                            discard_count += 1
                            continue
                        elif reason == "duplicate":
                            # 직전 step이 중복 원인 — 제거 후 저장
                            history = b.get("history", [])[:-1]
                        else:
                            # concluded: 자연스럽게 완결된 시나리오 — 전체 저장
                            history = b.get("history", [])
                    else:
                        # 비종료: 모든 turn을 통과한 정상 경로
                        history = b.get("history", [])
                    contents = [item["content"] for item in history if item.get("content")]
                    if contents:
                        raw.append({
                            "branch_id": b["branch_id"],
                            "paragraph": " → ".join(contents),
                            "workflow_id": wf_id,
                        })
            print(f"  [Phase 2] reason별 처리: 폐기(infeasible/acausal)={discard_count}")
            print(f"  [Phase 2] 포맷 완료: {len(raw)}개")
            raw_path.write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        if len(raw) > 1:
            texts = [s["paragraph"] for s in raw]
            batches = [texts[i : i + 100] for i in range(0, len(texts), 100)]

            def _embed_batch(batch: list[str]) -> list[list[float]]:
                result = client.models.embed_content(model=GEMINI_EMBED_MODEL, contents=batch)
                return [e.values for e in result.embeddings]

            print(f"  [Phase 2] 임베딩 {len(batches)}개 배치 병렬 요청...")
            with ThreadPoolExecutor(max_workers=len(batches)) as emb_executor:
                batch_results = list(emb_executor.map(_embed_batch, batches))
            embeddings: list[list[float]] = [emb for br in batch_results for emb in br]
            print(f"  [Phase 2] 임베딩 완료 ({len(embeddings)}개)")
            kept, kept_embs = [], []
            for idx, (scenario, emb) in enumerate(zip(raw, embeddings)):
                if any(_cosine_sim(emb, ke) > _PRUNE_THRESHOLD for ke in kept_embs):
                    continue
                kept.append(scenario)
                kept_embs.append(emb)
                if len(kept) % 100 == 0:
                    print(f"  [Phase 2] dedup 진행: {idx+1}/{len(raw)} 검사, {len(kept)}개 유지 중")
            scenarios = kept
        else:
            scenarios = raw

        print(f"  [Phase 2 완료] 중복 제거 후 {len(scenarios)}개")
        scenarios_path.write_text(json.dumps(scenarios, ensure_ascii=False, indent=2), encoding="utf-8")

    # ─── Phase 3: 시나리오 검증 ──────────────────────────────
    verified_scenarios_path = run_dir / "verified_scenarios.json"
    if verified_scenarios_path.exists():
        print("  [Phase 3 체크포인트] verified_scenarios.json 존재 → 스킵")
        verified_scenarios = json.loads(verified_scenarios_path.read_text(encoding="utf-8"))
    else:
        print(f"  [Phase 3] 검증: {len(scenarios)}개 시나리오 (동시 {_VERIFY_CONCURRENCY})")

        def verify_scenario(scenario: dict) -> bool:
            wf_id = scenario.get("workflow_id", 0)
            agent_role = _format_entity_roles(entity_role_map.get(wf_id, {}), stakeholder_agents)
            rag_chunks = retrieve_context(run_id, scenario["paragraph"])
            rag_context = "\n---\n".join(rag_chunks)
            prompt = RAG_VERIFY_PROMPT(
                "scenario", lang=lang,
                workflow_context=_build_workflow_context(wf_id, wf_desc_map),
                scenario=json.dumps(scenario, ensure_ascii=False),
                rag_context=rag_context,
                agent_role=agent_role,
            )
            response = call_with_retry(
                client.models.generate_content,
                model=LITE_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SCENARIO_VERIFY_RAG_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                ),
            )
            return json.loads(response.text).get("is_valid", False)

        total = len(scenarios)
        valid_flags = [False] * total
        with ThreadPoolExecutor(max_workers=_VERIFY_CONCURRENCY) as executor:
            future_to_idx = {executor.submit(verify_scenario, s): i for i, s in enumerate(scenarios)}
            done_count = 0
            for fut in as_completed(future_to_idx):
                idx = future_to_idx[fut]
                valid_flags[idx] = fut.result()
                done_count += 1
                if done_count % 50 == 0 or done_count == total:
                    passed = sum(valid_flags[:done_count])
                    print(f"  [Phase 3] {done_count}/{total} 검증 완료 (통과={passed})")

        verified_scenarios = [s for s, valid in zip(scenarios, valid_flags) if valid]
        print(f"  [Phase 3 완료] 검증 통과: {len(verified_scenarios)}/{len(scenarios)}")
        verified_scenarios_path.write_text(
            json.dumps(verified_scenarios, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ─── Phase 4: 시나리오 폴리싱 (MERGE_PROMPT) ──────────────
    merged_path = run_dir / "merged_scenarios.md"
    if merged_path.exists():
        print("  [Phase 4 체크포인트] merged_scenarios.md 존재 → 스킵")
        merged_scenarios = merged_path.read_text(encoding="utf-8")
    else:
        chunks = _split_chunks(verified_scenarios, _N_GROUPS)
        offsets = [sum(len(chunks[j]) for j in range(i)) for i in range(len(chunks))]
        print(f"  [Phase 4] 폴리싱: {len(verified_scenarios)}개 → {len(chunks)}개 청크 병렬")

        def _call_merge(chunk: list, offset: int) -> str:
            prompt = MERGE_PROMPT(
                scenarios=json.dumps(chunk, ensure_ascii=False),
                start_num=offset + 1,
                lang=lang,
            )
            response = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=65536,
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            return response.text

        results = [""] * len(chunks)
        with ThreadPoolExecutor(max_workers=_N_GROUPS) as executor:
            future_to_idx = {executor.submit(_call_merge, chunk, offset): i
                             for i, (chunk, offset) in enumerate(zip(chunks, offsets))}
            for fut in as_completed(future_to_idx):
                idx = future_to_idx[fut]
                results[idx] = fut.result()
                done_chunks = sum(1 for r in results if r)
                print(f"  [Phase 4] 청크 {done_chunks}/{len(chunks)} 완료")
        merged_scenarios = "\n\n".join(results)
        merged_path.write_text(merged_scenarios, encoding="utf-8")
        print(f"  [Phase 4 완료] merged_scenarios.md: {len(merged_scenarios.splitlines())}줄")

    return {
        "simulation_paths": simulation_paths,
        "scenarios_text": json.dumps(verified_scenarios, ensure_ascii=False),
        "merged_scenarios": merged_scenarios,
        "feasibility_pruned": feasibility_pruned,
    }
