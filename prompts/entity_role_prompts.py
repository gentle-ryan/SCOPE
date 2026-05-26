_AGENT_ROLE_KO = """\
당신은 AI 시스템 내 에이전트의 역할을 분석하는 전문가입니다.
주어진 정보를 바탕으로 해당 에이전트의 역할을 구체적으로 정제하십시오.

────────────────────────────────
[입력]

- 에이전트 명칭: {entity_name}
- 기본 역할: {original_role}
- 워크플로우 설명: {workflow_description}
- 관련 문서 컨텍스트: {rag_context}

────────────────────────────────
[작성 방향]

original_role을 기반으로, workflow_description과 rag_context에서 확인되는 내용만을 근거로 역할을 구체화하라.

- {entity_name}이 해당 워크플로우 단계에서 취하는 행동과 수행하는 작업
- {entity_name}이 시스템 또는 다른 에이전트에게 제출·제공하는 데이터와 정보
- {entity_name}이 AI 시스템으로부터 받는 영향과 결과
- {entity_name}의 의사결정 참여 방식과 권한 범위
- rag_context에 {entity_name} 관련 내용이 있으면 반드시 반영하되, 직접 확인된 사실만 사용

────────────────────────────────
[제약]

- original_role을 벗어난 새로운 역할 생성 금지
- workflow_description 또는 rag_context에 근거 없는 내용 추가 금지
- 추측 표현("가능하다", "추정된다") 금지
- 최소 5문장, 불필요한 장황한 설명 금지
"""

_AGENT_ROLE_EN = """\
You are an expert in analyzing the roles of agents within AI systems.
Based on the provided information, elaborate and refine the role of the given agent in detail.

────────────────────────────────
[Input]

- Agent name: {entity_name}
- Base role: {original_role}
- Workflow description: {workflow_description}
- Relevant document context: {rag_context}

────────────────────────────────
[Writing Direction]

Based on original_role, elaborate the role using only information confirmed in workflow_description and rag_context:

- Actions taken and tasks performed by {entity_name} at this workflow stage
- Data and information that {entity_name} submits or provides to the system or other agents
- The impacts and outcomes that {entity_name} receives from the AI system
- How {entity_name} participates in decision-making and the scope of their authority
- If rag_context contains information about {entity_name}, it must be reflected — use only directly confirmed facts

────────────────────────────────
[Constraints]

- Do not create new roles beyond original_role.
- Do not add content not grounded in workflow_description or rag_context.
- Do not use speculative expressions ("may be possible", "is estimated to").
- Minimum 5 sentences; avoid unnecessary verbosity.
"""

_OBJECT_ROLE_KO = """\
당신은 AI 시스템 내 오브젝트의 역할을 분석하는 전문가입니다.
주어진 정보를 바탕으로 해당 오브젝트의 역할을 구체적으로 정제하십시오.

────────────────────────────────
[입력]

- 오브젝트 명칭: {entity_name}
- 기본 역할: {original_role}
- 워크플로우 설명: {workflow_description}
- 관련 문서 컨텍스트: {rag_context}

────────────────────────────────
[작성 방향]

original_role을 기반으로, workflow_description과 rag_context에서 확인되는 내용만을 근거로 역할을 구체화하라.

- {entity_name}이 생성·수집되는 단계와 방식
- {entity_name}이 거치는 처리 과정 (정제, 변환, 검증, 분석 등)
- {entity_name}의 사용 목적과 최종 활용 방식
- {entity_name}의 품질 조건 또는 요구 사항 (형식, 정확도, 완전성 등)
- {entity_name}이 AI 모델 또는 의사결정에 미치는 영향
- rag_context에 {entity_name} 관련 내용이 있으면 반드시 반영하되, 직접 확인된 사실만 사용

────────────────────────────────
[제약]

- original_role을 벗어난 새로운 역할 생성 금지
- workflow_description 또는 rag_context에 근거 없는 내용 추가 금지
- 추측 표현("가능하다", "추정된다") 금지
- 최소 5문장, 불필요한 장황한 설명 금지
"""

_OBJECT_ROLE_EN = """\
You are an expert in analyzing the roles of objects within AI systems.
Based on the provided information, elaborate and refine the role of the given object in detail.

────────────────────────────────
[Input]

- Object name: {entity_name}
- Base role: {original_role}
- Workflow description: {workflow_description}
- Relevant document context: {rag_context}

────────────────────────────────
[Writing Direction]

Based on original_role, elaborate the role using only information confirmed in workflow_description and rag_context:

- The stage and method by which {entity_name} is generated or collected
- The processing stages {entity_name} undergoes (refinement, transformation, validation, analysis, etc.)
- The purpose of use and final application of {entity_name}
- Quality conditions or requirements for {entity_name} (format, accuracy, completeness, etc.)
- The impact of {entity_name} on the AI model or decision-making
- If rag_context contains information about {entity_name}, it must be reflected — use only directly confirmed facts

────────────────────────────────
[Constraints]

- Do not create new roles beyond original_role.
- Do not add content not grounded in workflow_description or rag_context.
- Do not use speculative expressions ("may be possible", "is estimated to").
- Minimum 5 sentences; avoid unnecessary verbosity.
"""


def ROLE_REFINE_PROMPT(entity_type: str, entity_name: str, original_role: str,
                       workflow_description: str, rag_context: str, lang: str = "ko") -> str:
    """Unified role refinement for agents and objects."""
    if lang == "en":
        template = _AGENT_ROLE_EN if entity_type == "agent" else _OBJECT_ROLE_EN
    else:
        template = _AGENT_ROLE_KO if entity_type == "agent" else _OBJECT_ROLE_KO
    return template.format(
        entity_name=entity_name,
        original_role=original_role,
        workflow_description=workflow_description,
        rag_context=rag_context,
    )


# ── Stakeholder prompts ──────────────────────────────────────────────────────

_STAKEHOLDER_BASE_KO = """\
────────────────────────────────
[이미 식별된 에이전트 — 중복 금지]
{existing_agents}

────────────────────────────────
[이해관계자 유형 정의]

1. 직접적 (Primary)
AI 시스템의 개발, 배포, 사용에 직접적으로 관여하거나 상호작용하는 대상
- 최종 사용자 (서비스 이용자, 민원인, 수혜자 등)
- 시스템 운영자, 관리자
- AI 입력을 제공하는 사람/객체
- AI의 직접적인 처리·판단 대상
판단 기준: 해당 영향이 AI와 직접 상호작용하는 과정에서 발생하는가?

2. 간접적 (Secondary)
Primary 대상에게 발생한 영향으로 인해 연쇄적으로 영향을 받는 대상
- Primary 대상에 의존하는 사람 (가족, 고객, 협력사 등)
- Primary 대상의 결과물을 소비하거나 영향을 받는 집단
판단 기준: 영향이 "직접 대상 → 간접 대상"의 경로를 통해 전달되는가?

3. 의도치 않은 (Unintended)
설계나 예측 범위를 벗어나 비의도적으로 영향을 받는 대상
- 사전 설계에서 고려되지 않은 제3자
- 낮은 확률이지만 발생 가능한 극단적 상황의 대상
판단 기준: 이 영향이 설계 목적이나 주요 사용자 흐름과 무관하게 발생하는가?

────────────────────────────────
[작성 규칙]

- name: 역할·직무 기반 명칭 (실명·고유 식별자 금지)
- role: 해당 이해관계자와 AI 시스템의 관계 (1~2문장)
- detailed_role: AI 시스템으로부터 받는 영향 또는 상호작용을 구체적으로 서술
- impact_type: "primary" / "secondary" / "unintended"
- 이미 식별된 에이전트와 중복되는 대상 포함 금지
- 추측 표현("가능하다", "추정된다") 금지

────────────────────────────────
[수량 기준]

- primary: 최소 3명 이상
- secondary: 최소 3명 이상
- unintended: 최소 2명 이상
"""

_STAKEHOLDER_BASE_EN = """\
────────────────────────────────
[Already Identified Agents — Do Not Duplicate]
{existing_agents}

────────────────────────────────
[Stakeholder Type Definitions]

1. Primary
Parties who directly engage with, interact with, or are directly involved in the development, deployment, or use of the AI system.
- End users (service users, applicants, beneficiaries, etc.)
- System operators and administrators
- Individuals or entities providing inputs to the AI
- Direct subjects of AI processing or judgment
Judgment criterion: Does this impact occur in the course of direct interaction with the AI?

2. Secondary
Parties who are indirectly affected as a downstream consequence of impacts on Primary parties.
- Individuals depending on Primary parties (family members, customers, business partners, etc.)
- Groups who consume or are affected by the outcomes of Primary parties
Judgment criterion: Is the impact delivered through a "primary → secondary" pathway?

3. Unintended
Parties who are non-intentionally affected in ways beyond the design or prediction scope of the system.
- Third parties not considered in the original design
- Parties in extreme or low-probability scenarios that could nonetheless occur
Judgment criterion: Does this impact occur independently of the design intent or primary use flow?

────────────────────────────────
[Writing Rules]

- name: Role- or function-based names (no proper names or unique identifiers)
- role: The relationship between this stakeholder and the AI system (1–2 sentences)
- detailed_role: Specific description of the impacts or interactions this party experiences with the AI system
- impact_type: "primary" / "secondary" / "unintended"
- Do not include parties that overlap with already-identified agents.
- Do not use speculative expressions ("may be possible", "is estimated to").

────────────────────────────────
[Quantity Guidelines]

- primary: At least 3
- secondary: At least 3
- unintended: At least 2
"""

_STAKEHOLDER_GENERATE_KO = """\
당신은 AI 영향평가 이해관계자 분석 전문가입니다.
제공된 문서를 바탕으로 아래 3가지 유형에 해당하는 이해관계자를 식별하라.
""" + _STAKEHOLDER_BASE_KO + """\
────────────────────────────────
[식별 절차]

STEP 1. primary 이해관계자를 가능한 한 모두 열거하라.
STEP 2. primary 각각으로부터 파생되는 secondary 이해관계자를 열거하라.
STEP 3. 설계 목적과 무관하게 비의도적으로 영향받을 수 있는 unintended 이해관계자를 탐색하라.
STEP 4. 전체 목록에서 이미 식별된 에이전트와 기능적으로 중복되는 대상을 제거하라.
"""

_STAKEHOLDER_GENERATE_EN = """\
You are an expert in AI impact assessment stakeholder analysis.
Based on the provided document, identify stakeholders belonging to the 3 types below.
""" + _STAKEHOLDER_BASE_EN + """\
────────────────────────────────
[Identification Procedure]

STEP 1. Enumerate all primary stakeholders comprehensively.
STEP 2. For each primary party, enumerate secondary stakeholders derived from them.
STEP 3. Explore unintended stakeholders who may be non-intentionally impacted outside the design scope.
STEP 4. From the full list, remove any parties that functionally overlap with already-identified agents.
"""


def STAKEHOLDER_GENERATE_PROMPT(existing_agents: str, lang: str = "ko") -> str:
    template = _STAKEHOLDER_GENERATE_EN if lang == "en" else _STAKEHOLDER_GENERATE_KO
    return template.format(existing_agents=existing_agents)


_STAKEHOLDER_CRITIQUE_KO = """\
당신은 AI 영향평가 이해관계자 분석 검토 전문가입니다.
아래 이해관계자 식별 초안을 검토하고, 누락·오류·중복을 지적하라.

────────────────────────────────
[이미 식별된 에이전트 — 중복 금지]
{existing_agents}

────────────────────────────────
[이해관계자 초안]

{draft_stakeholders}

────────────────────────────────
[검토 항목]

1. 누락된 이해관계자: AI 영향평가 맥락상 반드시 포함해야 하나 빠진 유형
2. 중복 식별: 동일한 대상이 다른 이름으로 중복 포함된 경우
3. 유형 오분류: primary/secondary/unintended 분류가 부적절한 경우
4. 에이전트 중복: 이미 식별된 에이전트와 기능적으로 동일한 대상이 포함된 경우
5. detailed_role 불충분: 최소 5문장 미만이거나 AI 시스템과의 상호작용이 구체적으로 기술되지 않은 경우

────────────────────────────────
[출력 형식]

지적 사항 목록 (없으면 "이상 없음")
"""

_STAKEHOLDER_CRITIQUE_EN = """\
You are an expert reviewer of AI impact assessment stakeholder analysis.
Review the draft stakeholder identification below and identify omissions, errors, and duplicates.

────────────────────────────────
[Already Identified Agents — Do Not Duplicate]
{existing_agents}

────────────────────────────────
[Stakeholder Draft]

{draft_stakeholders}

────────────────────────────────
[Review Criteria]

1. Missing stakeholders: Types that must be included in an AI impact assessment context but are absent
2. Duplicate identification: The same party included under different names
3. Type misclassification: Cases where primary/secondary/unintended classification is inappropriate
4. Agent overlap: Parties already identified as agents that are functionally identical to included stakeholders
5. Insufficient detailed_role: Fewer than 5 sentences, or AI system interaction not specifically described

────────────────────────────────
[Output Format]

List of issues found (write "No issues" if none)
"""


def STAKEHOLDER_CRITIQUE_PROMPT(existing_agents: str, draft_stakeholders: str, lang: str = "ko") -> str:
    template = _STAKEHOLDER_CRITIQUE_EN if lang == "en" else _STAKEHOLDER_CRITIQUE_KO
    return template.format(existing_agents=existing_agents, draft_stakeholders=draft_stakeholders)


_STAKEHOLDER_REFINE_KO = """\
당신은 AI 영향평가 이해관계자 분석 전문가입니다.
아래 검토 의견을 반영하여 이해관계자 목록을 최종 수정하라.

────────────────────────────────
[검토 의견]

{critique}

────────────────────────────────
[이해관계자 초안]

{draft_stakeholders}

""" + _STAKEHOLDER_BASE_KO + """\
────────────────────────────────
[수정 규칙]

- 검토 의견의 누락 항목 보완
- 오분류 항목 유형 수정
- 중복 항목 제거
- 에이전트 중복 항목 반드시 제거
- 초안에서 문제 없는 항목은 그대로 유지
"""

_STAKEHOLDER_REFINE_EN = """\
You are an expert in AI impact assessment stakeholder analysis.
Revise the stakeholder list to reflect the review feedback below.

────────────────────────────────
[Review Feedback]

{critique}

────────────────────────────────
[Stakeholder Draft]

{draft_stakeholders}

""" + _STAKEHOLDER_BASE_EN + """\
────────────────────────────────
[Revision Rules]

- Address omissions flagged in the review.
- Correct type misclassifications.
- Remove duplicates.
- Remove any items that overlap with already-identified agents.
- Retain items from the draft that have no issues.
"""


def STAKEHOLDER_REFINE_PROMPT(critique: str, draft_stakeholders: str,
                               existing_agents: str, lang: str = "ko") -> str:
    template = _STAKEHOLDER_REFINE_EN if lang == "en" else _STAKEHOLDER_REFINE_KO
    return template.format(
        critique=critique,
        draft_stakeholders=draft_stakeholders,
        existing_agents=existing_agents,
    )
