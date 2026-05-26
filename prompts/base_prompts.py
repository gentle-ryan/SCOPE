"""Cross-cutting prompt functions with language support.

Provides GENERIC_CRITIQUE_PROMPT, GENERIC_REFINE_PROMPT, and RAG_VERIFY_PROMPT
that dispatch to task-type-specific content while supporting `lang` parameter.
"""

from prompts.workflow_entity_prompts import WORKFLOW_CRITIQUE_PROMPT, WORKFLOW_REFINE_PROMPT
from prompts.entity_role_prompts import STAKEHOLDER_CRITIQUE_PROMPT, STAKEHOLDER_REFINE_PROMPT
from prompts.impact_prompts import IMPACT_CRITIQUE_PROMPT, IMPACT_REFINE_GENERATE_PROMPT

_ENTITY_VERIFY_KO = """\
당신은 AI 시스템 영향평가 전문가입니다.
주어진 entity가 원본 문서에 실제로 존재하는지, 그리고 동일 단계 내 다른 entity와 중복인지 검증하십시오.

────────────────────────────────
[입력]

- Entity 이름: {entity_name}
- Entity 유형: {entity_type}
- Entity 역할: {entity_role}
- 워크플로우 컨텍스트: {workflow_context}
- RAG 컨텍스트 (원본 문서 발췌): {rag_context}
- 동일 단계 내 다른 Entity 목록: {other_entities}

────────────────────────────────
[검증 기준]

1. 문서 존재성 (is_valid)
   - RAG 컨텍스트에 해당 entity의 이름 또는 동일한 역할이 명시적으로 확인된다
   - 워크플로우 해당 단계에서 실제로 참여·사용·처리되는 대상이다
   - 위 두 조건 중 하나라도 불충분하면 is_valid = false

2. 중복 탐지 (duplicate_of)
   - 다른 entity 목록과 비교하여, 이름·역할이 사실상 동일한 entity가 있으면 해당 이름 기재
   - 표현만 다르고 실질적으로 동일한 대상을 가리키는 경우 중복으로 판정
   - 중복이 아니면 null

────────────────────────────────
[판정 규칙]

- is_valid=false: RAG에서 근거 확인 불가하거나 워크플로우상 불가
- duplicate_of: 중복 대상의 이름 (없으면 null)
- reason: 판단 근거 1~2문장
"""

_ENTITY_VERIFY_EN = """\
You are an expert in AI system impact assessment.
Verify whether the given entity actually exists in the original document, and whether it duplicates another entity within the same workflow stage.

────────────────────────────────
[Input]

- Entity name: {entity_name}
- Entity type: {entity_type}
- Entity role: {entity_role}
- Workflow context: {workflow_context}
- RAG context (excerpts from original document): {rag_context}
- Other entities in the same stage: {other_entities}

────────────────────────────────
[Verification Criteria]

1. Document existence (is_valid)
   - The entity's name or equivalent role is explicitly confirmed in the RAG context.
   - The entity actually participates in, is used by, or is processed at this workflow stage.
   - If either condition is insufficient, is_valid = false.

2. Duplicate detection (duplicate_of)
   - Compare against other entities: if another entity has essentially the same name and role, record that entity's name.
   - If the wording differs but they refer to the same subject, classify as a duplicate.
   - If not a duplicate, return null.

────────────────────────────────
[Decision Rules]

- is_valid=false: Cannot confirm evidence in RAG, or structurally impossible in the workflow.
- duplicate_of: Name of the duplicate entity (null if none).
- reason: 1–2 sentences of justification.
"""

_EVENT_VERIFY_KO = """\
당신은 AI 시스템 영향평가 검증 전문가입니다.
주어진 event가 유효한지 판단하십시오.

────────────────────────────────
[입력]

- Workflow Context: {workflow_context}
- Entity 이름: {entity_name}
- Entity 상세 역할: {entity_detailed_role}
- Event: {event}
- RAG Context: {rag_context}

────────────────────────────────
[검증 기준 — 아래 조건을 모두 만족해야 유효]

1. event의 핵심 명사/행위가 rag context 내에 명시적으로 존재해야 한다.
2. workflow context 상 자연스럽게 발생 가능하다.
3. Entity의 상세 역할 범위 내에서 수행 가능한 행동이다.
4. property가 event에 실제로 반영되어 있다.
5. 다른 entity·데이터 흐름·결과에 영향을 미친다.

────────────────────────────────
[무효 조건 — 하나라도 해당하면 is_valid = false]

- RAG에서 근거 확인 불가
- workflow 상 불가능한 행동
- Entity 역할상 불가능한 행동
- property가 실제로 반영되지 않음
- 시스템 설계상 구조적으로 불가능한 이벤트: 해당 AI 시스템의 아키텍처·처리 흐름·운영 범위상 원천적으로 발생할 수 없는 사건
"""

_EVENT_VERIFY_EN = """\
You are an expert in AI system impact assessment verification.
Determine whether the given event is valid.

────────────────────────────────
[Input]

- Workflow Context: {workflow_context}
- Entity name: {entity_name}
- Entity detailed role: {entity_detailed_role}
- Event: {event}
- RAG Context: {rag_context}

────────────────────────────────
[Validity Criteria — all conditions must be satisfied]

1. The key nouns and actions of the event must be explicitly present in the RAG context.
2. The event can naturally occur within the workflow context.
3. The action is within the scope of what the entity's detailed role can perform.
4. The property is actually reflected in the event.
5. The event affects other entities, data flows, or system outcomes.

────────────────────────────────
[Invalidity Conditions — is_valid = false if any apply]

- Cannot confirm evidence in RAG context.
- Action is impossible given the workflow.
- Action is outside the entity's role.
- The property is not actually reflected in the event.
- Structurally impossible event: an occurrence that cannot happen given this AI system's architecture, processing flow, or operational scope.
"""

_SCENARIO_VERIFY_KO = """\
당신은 AI 시스템 영향평가 시나리오 검증 전문가입니다.
주어진 시나리오가 유효한 영향 전파 시나리오인지 판단하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

워크플로우 (현재 ~ 이후 단계): {workflow_context}
시나리오: {scenario}
RAG 근거: {rag_context}
Agent Role: {agent_role}

━━━━━━━━━━━━━━━━━━
[검증 기준 — 모두 만족해야 유효]

1. 인과 흐름 일관성: 각 단계가 이전 단계의 결과로부터 자연스럽게 이어진다.
2. 현실성: workflow 및 entity_roles 상 실제 발생 가능한 흐름이다.
3. RAG 근거성: 주요 단계별 행동과 영향의 근거가 RAG context에서 확인된다.
4. 의미 있는 영향: 단순 상태 변화가 아니라, 다른 entity·프로세스·시스템 결과에 영향을 준다.

━━━━━━━━━━━━━━━━━━
[무효 조건 — 하나라도 해당하면 is_valid = false]

- 동일 패턴 반복 (의미 없는 반복)
- 인과적으로 단절된 단계 존재
- 실제 시스템에서 발생 불가능한 흐름
- RAG에서 핵심 흐름 근거 미확인
"""

_SCENARIO_VERIFY_EN = """\
You are an expert in validating impact propagation scenarios for AI system impact assessment.
Determine whether the given scenario is a valid impact propagation scenario.

━━━━━━━━━━━━━━━━━━
[Input]

Workflow (current and subsequent stages): {workflow_context}
Scenario: {scenario}
RAG Evidence: {rag_context}
Agent Role: {agent_role}

━━━━━━━━━━━━━━━━━━
[Validity Criteria — all must be satisfied]

1. Causal flow consistency: each step follows naturally from the result of the previous step.
2. Realism: the flow is realistically possible given the workflow and entity roles.
3. RAG grounding: the key actions and impacts at each step are confirmed in the RAG context.
4. Meaningful impact: this is not a mere state change — it affects other entities, processes, or system outcomes.

━━━━━━━━━━━━━━━━━━
[Invalidity Conditions — is_valid = false if any apply]

- Repetition of identical patterns (meaningless repetition).
- A step exists that is causally disconnected from the prior step.
- A flow that cannot occur in the actual system.
- Key flow steps cannot be confirmed in RAG.
"""


def _safe_format(template: str, **kwargs) -> str:
    """String substitution that handles values containing curly braces (e.g. JSON)."""
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


def GENERIC_CRITIQUE_PROMPT(task_type: str, lang: str = "ko", **kwargs) -> str:
    """Critique prompt for workflow / stakeholder / impact task types."""
    if task_type == "workflow":
        return WORKFLOW_CRITIQUE_PROMPT(
            document=kwargs["document"],
            draft_workflows=kwargs["draft_workflows"],
            lang=lang,
        )
    elif task_type == "stakeholder":
        return STAKEHOLDER_CRITIQUE_PROMPT(
            existing_agents=kwargs["existing_agents"],
            draft_stakeholders=kwargs["draft_stakeholders"],
            lang=lang,
        )
    elif task_type == "impact":
        return IMPACT_CRITIQUE_PROMPT(
            code=kwargs["code"],
            name=kwargs["name"],
            ethics_definition=kwargs["ethics_definition"],
            referenced_scenarios=kwargs["referenced_scenarios"],
            draft_impacts=kwargs["draft_impacts"],
            lang=lang,
        )
    else:
        raise ValueError(f"Unknown task_type for GENERIC_CRITIQUE_PROMPT: {task_type!r}")


def GENERIC_REFINE_PROMPT(task_type: str, lang: str = "ko", **kwargs) -> str:
    """Refinement prompt for workflow / stakeholder / impact task types."""
    if task_type == "workflow":
        return WORKFLOW_REFINE_PROMPT(
            document=kwargs["document"],
            draft_workflows=kwargs["draft_workflows"],
            critique=kwargs["critique"],
            lang=lang,
        )
    elif task_type == "stakeholder":
        return STAKEHOLDER_REFINE_PROMPT(
            draft_stakeholders=kwargs["draft_stakeholders"],
            critique=kwargs["critique"],
            existing_agents=kwargs["existing_agents"],
            lang=lang,
        )
    elif task_type == "impact":
        return IMPACT_REFINE_GENERATE_PROMPT(
            code=kwargs["code"],
            name=kwargs["name"],
            ethics_definition=kwargs["ethics_definition"],
            regulation_context=kwargs["regulation_context"],
            critique=kwargs["critique"],
            draft_impacts=kwargs["draft_impacts"],
            lang=lang,
        )
    else:
        raise ValueError(f"Unknown task_type for GENERIC_REFINE_PROMPT: {task_type!r}")


def RAG_VERIFY_PROMPT(task_type: str, lang: str = "ko", **kwargs) -> str:
    """RAG-grounded verification prompt for event / scenario / entity task types."""
    if task_type == "event":
        template = _EVENT_VERIFY_EN if lang == "en" else _EVENT_VERIFY_KO
        return _safe_format(
            template,
            workflow_context=kwargs["workflow_context"],
            entity_name=kwargs["entity_name"],
            entity_detailed_role=kwargs["entity_detailed_role"],
            event=kwargs["event"],
            rag_context=kwargs["rag_context"],
        )
    elif task_type == "scenario":
        template = _SCENARIO_VERIFY_EN if lang == "en" else _SCENARIO_VERIFY_KO
        return _safe_format(
            template,
            workflow_context=kwargs["workflow_context"],
            scenario=kwargs["scenario"],
            rag_context=kwargs["rag_context"],
            agent_role=kwargs["agent_role"],
        )
    elif task_type == "entity":
        template = _ENTITY_VERIFY_EN if lang == "en" else _ENTITY_VERIFY_KO
        return _safe_format(
            template,
            entity_name=kwargs["entity_name"],
            entity_type=kwargs["entity_type"],
            entity_role=kwargs["entity_role"],
            workflow_context=kwargs["workflow_context"],
            rag_context=kwargs["rag_context"],
            other_entities=kwargs.get("other_entities", "(없음)" if lang == "ko" else "(none)"),
        )
    else:
        raise ValueError(f"Unknown task_type for RAG_VERIFY_PROMPT: {task_type!r}")
