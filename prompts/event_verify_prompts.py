_EVENT_AGENT_KO = """\
당신은 AI 시스템 안전공학 전문가입니다.
아래 에이전트(Agent)에 대해, 인적 오류 속성을 기반으로 실제 발생 가능한 사건(event)을 생성하십시오.

────────────────────────────────
[분석 대상]

- 에이전트 명칭: {entity_name}
- 상세 역할: {detailed_role}

────────────────────────────────
[분석 지침]

1. 속성 적용
- 각 property 중, 해당 에이전트의 역할 범위 내에서 다른 entity·데이터 흐름·결과에 실제 영향을 미치는 경우에만 event를 생성하라.
- 하나의 event에는 하나의 property만 적용한다.

2. event 생성
- 1~2문장으로 간결하게 기술한다.
- 에이전트의 상세 역할에 근거해야 하며, 실제 수행 가능한 행동만 포함한다.
- property와 직접 연관된 결과만 기술한다.
- event_id는 고유해야 한다.
- property는 아래 정의의 한국어 용어 그대로 사용한다. 예) 정상, 실수/망각, 규칙 기반 착오, 지식 기반 착오, 위반

────────────────────────────────
[Agent Property 정의]

- 정상 (Normal): 에이전트가 의도한 계획을 정확히 수행하며, 절차·규칙·시간 요구사항을 모두 준수한 상태.
- 실수/망각 (Slip/Lapse): 계획이나 의도는 올바르나, 수행 과정에서 실수가 발생하거나 일부 절차를 망각하여 수행하지 못한 상태. 예: "3단계 중 2단계만 수행하고 종료함"
- 규칙 기반 착오 (Rule-based Mistake): 상황을 잘못 분류하거나 오판하여, 올바르지 않은 규칙이나 절차를 적용한 상태. 예: "긴급 문의를 일반 문의로 잘못 분류하여 잘못된 절차 적용"
- 지식 기반 착오 (Knowledge-based Mistake): 시스템 또는 도메인 지식 부족 혹은 과신으로 인해 잘못된 판단이나 결정을 내린 상태. 예: "존재하지 않는 논문을 사실처럼 인용함"
- 위반 (Violation): 절차나 규칙을 인지하고 있음에도, 효율·편의·시간 압박·자원 부족 등을 이유로 의도적으로 따르지 않은 행위. 예: "비용 절감을 위해 필수 검증 단계를 생략함"

────────────────────────────────
[출력 형식]
event_schema.py를 정확히 따르는 JSON만 출력
"""

_EVENT_AGENT_EN = """\
You are an expert in AI system safety engineering.
For the Agent below, generate plausible events based on human error properties.

────────────────────────────────
[Subject]

- Agent name: {entity_name}
- Detailed role: {detailed_role}

────────────────────────────────
[Analysis Guidelines]

1. Property application
- Generate events only for properties where the agent's actions within their role scope actually affect other entities, data flows, or outcomes.
- Apply only one property per event.

2. Event generation
- Describe in 1–2 sentences concisely.
- Must be grounded in the agent's detailed role and include only actions that can actually be performed.
- Describe only outcomes directly related to the property.
- Each event_id must be unique.
- The property field must use the English terms as defined below (e.g., Normal, Slip/Lapse, Rule-based Mistake, Knowledge-based Mistake, Violation).

────────────────────────────────
[Agent Property Definitions]

- Normal: The agent executes the intended plan accurately, fully complying with all procedures, rules, and time requirements.
- Slip/Lapse: The plan or intention is correct, but an error occurs during execution or certain steps are forgotten and not carried out. Example: "Completed only 2 of 3 steps and terminated."
- Rule-based Mistake: The situation is misclassified or misjudged, leading to the application of an incorrect rule or procedure. Example: "An urgent inquiry is misclassified as a general inquiry, resulting in the wrong procedure being applied."
- Knowledge-based Mistake: Insufficient domain or system knowledge, or overconfidence, leads to an incorrect judgment or decision. Example: "A non-existent paper is cited as a fact."
- Violation: A procedure or rule is known but deliberately not followed due to efficiency, convenience, time pressure, or resource constraints. Example: "A mandatory validation step is skipped to reduce costs."

────────────────────────────────
[Output Format]
Output only valid JSON conforming to event_schema.py
"""

_EVENT_OBJECT_KO = """\
당신은 AI 시스템 안전공학 전문가입니다.
아래 오브젝트(Object)에 대해, 상태 변화 속성을 기반으로 실제 발생 가능한 사건(event)을 생성하십시오.

────────────────────────────────
[분석 대상]

- 오브젝트 명칭: {entity_name}
- 상세 역할: {detailed_role}

────────────────────────────────
[분석 지침]

1. 속성 적용
- 각 property 중, 해당 오브젝트의 역할 범위 내에서 다른 entity·데이터 흐름·결과에 실제 영향을 미치는 경우에만 event를 생성하라.
- 하나의 event에는 하나의 property만 적용한다.

2. event 생성
- 1~2문장으로 간결하게 기술한다.
- 오브젝트의 상세 역할에 근거해야 하며, 실제 발생 가능한 상태만 포함한다.
- property와 직접 연관된 결과만 기술한다.
- event_id는 고유해야 한다.
- property는 아래 정의의 한국어 용어 그대로 사용한다. 예) 정상, 과다/과소, 추가 포함
- 윤리 용어 사용 금지.

────────────────────────────────
[Object Property 정의]

- 정상 (Normal): 오브젝트가 설계된 목적과 정책에 부합하게 생성·처리되며, 결과가 의도된 기능과 영향 범위 내에서 안정적으로 유지되는 상태.
- 과다/과소 (More or Less): 오브젝트의 양·빈도·강도 또는 확률값이 의도된 수준을 벗어나, 영향이 과도하게 확대되거나 충분히 발현되지 않는 상태.
- 역전 (Reverse): 오브젝트의 의미·판단 결과·영향 방향이 설계 의도와 반대로 나타나 기대와 상반된 결과를 유발하는 상태.
- 추가 포함 (As Well As): 의도된 결과 외에 불필요하거나 부적절한 요소가 함께 포함되어 추가적인 리스크를 유발하는 상태.
- 부분적 생성 (Part Of): 오브젝트가 일부만 생성·전달되어 전체 맥락을 충분히 반영하지 못하고 불완전한 판단을 초래하는 상태.
- 대체 (Other Than): 오브젝트가 의도한 의미나 대상과 다른 것으로 생성·판단되어 잘못된 영향이 발생하는 상태.
- 없음 (No): 오브젝트가 생성·검출·반영되어야 함에도 존재하지 않아 필요한 영향 평가가 이루어지지 않는 상태.

────────────────────────────────
[출력 형식]
event_schema.py를 정확히 따르는 JSON만 출력
"""

_EVENT_OBJECT_EN = """\
You are an expert in AI system safety engineering.
For the Object below, generate plausible events based on state-change properties.

────────────────────────────────
[Subject]

- Object name: {entity_name}
- Detailed role: {detailed_role}

────────────────────────────────
[Analysis Guidelines]

1. Property application
- Generate events only for properties where the object's state changes within its role scope actually affect other entities, data flows, or outcomes.
- Apply only one property per event.

2. Event generation
- Describe in 1–2 sentences concisely.
- Must be grounded in the object's detailed role and include only states that can actually occur.
- Describe only outcomes directly related to the property.
- Each event_id must be unique.
- The property field must use the English terms as defined below (e.g., Normal, More or Less, Reverse, etc.).
- Do not use ethics terminology.

────────────────────────────────
[Object Property Definitions]

- Normal: The object is generated and processed in accordance with its designed purpose and policy, with outcomes remaining stable within the intended functional and impact scope.
- More or Less: The quantity, frequency, intensity, or probability value of the object exceeds or falls short of the intended level, causing impacts to be excessively amplified or insufficiently manifested. Example: overexposure to certain results, underdetection causing impact to be unaccounted for.
- Reverse: The meaning, judgment outcome, or direction of impact of the object appears opposite to the design intent, producing results contrary to expectations. Example: positive/negative judgment reversed, hazard signal classified as safe.
- As Well As: Unnecessary or inappropriate elements are included alongside the intended output, introducing additional risk. Example: biased information included, unnecessary personal data exposed.
- Part Of: The object is generated or delivered only partially, failing to sufficiently reflect the full context and leading to incomplete judgment. Example: some attributes missing.
- Other Than: The object is generated or judged as something other than the intended meaning or target, causing incorrect impacts. Example: misclassification, judgment applied to the wrong subject.
- No: The object should have been generated, detected, or reflected but does not exist, resulting in necessary impact assessment not taking place. Example: hazard signal undetected, result not generated.

────────────────────────────────
[Output Format]
Output only valid JSON conforming to event_schema.py
"""


def EVENT_GENERATE_PROMPT(entity_type: str, entity_name: str, detailed_role: str, lang: str = "ko") -> str:
    """Unified event generation for agents and objects."""
    if lang == "en":
        template = _EVENT_AGENT_EN if entity_type == "agent" else _EVENT_OBJECT_EN
    else:
        template = _EVENT_AGENT_KO if entity_type == "agent" else _EVENT_OBJECT_KO
    return template.format(entity_name=entity_name, detailed_role=detailed_role)


_EVENT_LLM_DEDUP_KO = """\
당신은 안전공학 이벤트 분석 전문가입니다.

아래는 동일한 entity/property 조합에서 여러 번 추출된 event descriptions입니다.

────────────────────────────────
[입력]

Entity: {entity_name}
Property: {property}

[Event descriptions]
{descriptions}

────────────────────────────────
[목표]

문장 표현 차이가 아닌 사건의 실질적 의미를 기준으로
동일 사건을 그룹화하라.

동일한 의미를 가진 사건이 여러 문장으로 반복되는 경우
하나로 통합해야 한다.

────────────────────────────────
[사건 의미 비교 기준]

사건은 다음 요소들의 조합으로 판단한다.

1. 수행 행동 (Action) — 해당 entity가 실제 수행한 행동
2. 원인 (Cause) — 행동이 발생한 직접 원인
3. 결과 영향 (Impact) — 다른 entity, 데이터 흐름, 시스템 결과에 미친 영향

────────────────────────────────
[동일 사건 판정 규칙]

수행 행동 / 직접 원인 / 결과 영향 이 동일하면 같은 사건.
문장 표현 / 길이 / 단어 차이 / 문장 구조 차이는 동일성 판단 기준이 아니다.

────────────────────────────────
[대표 이벤트 선택 기준]

1. 수행 행동이 명확함
2. 원인이 명확함
3. 결과 영향이 명확함
4. 가장 긴 문장이 아니라 정보량이 가장 많은 설명
"""

_EVENT_LLM_DEDUP_EN = """\
You are an expert in safety engineering event analysis.

The following are event descriptions extracted multiple times from the same entity/property combination.

────────────────────────────────
[Input]

Entity: {entity_name}
Property: {property}

[Event Descriptions]
{descriptions}

────────────────────────────────
[Objective]

Group events based on the substantive meaning of the incident — not surface differences in wording — and consolidate identical incidents into one.

────────────────────────────────
[Incident Meaning Comparison Criteria]

An incident is judged by the combination of:

1. Action — the actual action performed by the entity
2. Cause — the direct cause of the action
3. Impact — the effect on other entities, data flows, or system outcomes

────────────────────────────────
[Same-Incident Criteria]

Two incidents are considered identical when: Action, Cause, and Impact are all the same.
Differences in wording, length, word choice, or sentence structure are not criteria for distinctness.

────────────────────────────────
[Representative Event Selection]

Priority:
1. Action is clearly stated
2. Cause is clearly stated
3. Impact is clearly stated
4. Most informative description (not necessarily the longest)
"""


def EVENT_LLM_DEDUP_PROMPT(entity_name: str, property: str, descriptions: str, lang: str = "ko") -> str:
    template = _EVENT_LLM_DEDUP_EN if lang == "en" else _EVENT_LLM_DEDUP_KO
    return template.format(entity_name=entity_name, property=property, descriptions=descriptions)
