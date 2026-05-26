_PASSIVE_TURN1_KO = """\
당신은 AI 시스템 영향평가 시나리오 생성 전문가입니다.
입력 이벤트로 인해 영향을 받는 서로 다른 에이전트 3명을 선정하고, 각 에이전트에게 발생하는 상태 변화(effect)를 1개씩 생성하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

워크플로우 (현재 ~ 이후 단계): {workflow_context}
관련 Entity 및 Role: {entity_roles}
입력 이벤트: {branch_history}

━━━━━━━━━━━━━━━━━━
[절차]

1. 에이전트 선택 — 피영향자 최대 3명 (서로 다른 에이전트, 중복 금지)
- event의 결과로 직접 또는 간접적으로 영향을 받는 에이전트를 선택한다.
- entity_roles 목록에 존재하는 에이전트만 선택 가능하다.
- 선택된 에이전트는 반드시 서로 다른 에이전트여야 하며, 이후 workflow 흐름에 영향을 받을 수 있어야 한다.

2. Effect 생성 — 식별된 에이전트당 1개
- 각 에이전트가 event로 인해 받는 상태 변화를 기술한다.
- 3개의 effect는 각각 명확히 다른 전파 방향을 나타내야 한다 (단순 표현 변경 금지).
- 각 effect는 이후 워크플로우 단계에 영향을 줄 수 있는 변화여야 한다.
- effect는 해당 에이전트의 role 범위 내에서 발생 가능해야 한다.

━━━━━━━━━━━━━━━━━━
[Effect 작성 제약]

- 외부에서 관찰 가능한 상태 변화만 허용
- 금지: 내부 심리 상태 (감정, 인식, 판단 등), 추상적 표현, 미래 가능성("~할 수 있다"), event 재서술, 단순 상태 설명("문제가 발생", "영향이 있음")
- entity_roles 및 workflow에 근거한 실제 발생 가능한 변화만 허용

━━━━━━━━━━━━━━━━━━
[출력]
- 서로 다른 에이전트 3명, 각 에이전트에 대해 effect 1개 (총 3개)
- JSON 형식으로만 출력
"""

_PASSIVE_TURN1_EN = """\
You are an expert in scenario generation for AI system impact assessment.
From the input event, select up to 3 different affected agents and generate one state change (effect) for each.

━━━━━━━━━━━━━━━━━━
[Input]

Workflow (current and subsequent stages): {workflow_context}
Relevant Entities and Roles: {entity_roles}
Input Event: {branch_history}

━━━━━━━━━━━━━━━━━━
[Procedure]

1. Agent Selection — affected parties (up to 3, all must be different)
- Select agents who are directly or indirectly affected by the event.
- Only agents present in the entity_roles list may be selected.
- Selected agents must be distinct from each other and must be susceptible to impacts in subsequent workflow stages.

2. Effect Generation — 1 per identified agent
- Describe the state change that each agent experiences as a result of the event.
- The 3 effects must each represent clearly different propagation directions (no mere rephrasing).
- Each effect must be a change that can influence subsequent workflow stages.
- Each effect must be plausible within the agent's role scope.

━━━━━━━━━━━━━━━━━━
[Effect Writing Constraints]

- Only externally observable state changes are permitted.
- Prohibited: internal mental states (emotions, perceptions, judgments, etc.), abstract expressions, future possibilities ("could"), re-descriptions of the event, simple state descriptions ("a problem occurred", "there is an impact").
- Only plausible changes grounded in entity_roles and the workflow are permitted.

━━━━━━━━━━━━━━━━━━
[Output]
- 3 different agents, 1 effect per agent (3 effects total)
- Output in JSON format only
"""

_PASSIVE_TURN23_KO = """\
당신은 AI 시스템 영향평가 시나리오 생성 전문가입니다.
직전 단계의 결과로부터 영향이 유지되거나 다른 에이전트로 전파되는 과정을 분석하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

워크플로우 (현재 ~ 이후 단계): {workflow_context}
관련 Entity 및 Role: {entity_roles}
시나리오 history (단일 분기): {branch_history}

━━━━━━━━━━━━━━━━━━
[절차]

1. 에이전트 선택 — 피영향자 (1명)
- 직전 단계의 결과로 영향을 받는 에이전트를 선택한다.
- 동일 에이전트를 유지하거나, 새로운 에이전트로 전파될 수 있다.
- entity_roles 목록에 존재하는 에이전트만 선택 가능하다.

2. Effect 생성 — 1개
- 직전 단계(history)의 결과로부터 직접 발생하는 상태 변화를 기술한다.
- 인과 관계가 명확해야 한다. 연결되지 않으면 생성 금지.
- 해당 에이전트의 role 범위 내에서 발생 가능한 변화여야 한다.
- 외부에서 관찰 가능한 상태 변화만 허용 (내부 상태 금지).

━━━━━━━━━━━━━━━━━━
[출력]
- 하나의 에이전트(피영향자), effect 1개
- JSON 형식으로만 출력
"""

_PASSIVE_TURN23_EN = """\
You are an expert in scenario generation for AI system impact assessment.
Analyze how the impact from the immediately preceding step is sustained or propagates to another agent.

━━━━━━━━━━━━━━━━━━
[Input]

Workflow (current and subsequent stages): {workflow_context}
Relevant Entities and Roles: {entity_roles}
Scenario history (single branch): {branch_history}

━━━━━━━━━━━━━━━━━━
[Procedure]

1. Agent Selection — affected party (1)
- Select the agent affected by the result of the immediately preceding step.
- The same agent may be retained, or propagation to a new agent is possible.
- Only agents present in the entity_roles list may be selected.

2. Effect Generation — 1
- Describe the state change arising directly from the result of the preceding step (history).
- The causal relationship must be clear; do not generate if there is no connection.
- The change must be plausible within the agent's role scope.
- Only externally observable state changes are permitted (internal states prohibited).

━━━━━━━━━━━━━━━━━━
[Output]
- One agent (affected party), 1 effect
- Output in JSON format only
"""

_ACTIVE_KO = """\
당신은 AI 시스템 영향평가 시나리오 생성 전문가입니다.
현재 상태를 기반으로 행동을 수행할 에이전트와 그 action을 생성하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

워크플로우 (현재 ~ 이후 단계): {workflow_context}
관련 Entity 및 Role: {entity_roles}
시나리오 history (단일 분기): {branch_history}

※ 현재 상태는 이전 단계들의 action과 effect가 누적된 결과입니다.

━━━━━━━━━━━━━━━━━━
[절차]

1. 에이전트 선택 — 행위자 (1명)
- 현재 상태를 기반으로 실제로 행동을 수행할 수 있는 에이전트를 선택한다.
- entity_roles 또는 이해관계자 목록에 존재하는 에이전트만 선택 가능하다.

2. Action 생성 — 1개
- 선택된 에이전트가 수행하는 단일 행동을 기술한다.
- 현재 history로부터 자연스럽게 이어지는 행동이어야 한다.
- 이후 새로운 effect를 유발할 수 있는 행동이어야 한다.
- 해당 에이전트의 role 범위 내에서 수행 가능해야 한다.

⚠️ action은 반드시 문제를 해결하는 방향일 필요가 없습니다. 아래 유형을 적극 고려하십시오:
- 문제를 인식하지 못한 채 진행하는 정상적인 업무 처리
- 불완전하거나 잘못된 판단에 기반한 행동
- 의도는 올바르나 부작용을 유발하는 행동
- 문제를 지연시키거나 악화시키는 행동
- 문제를 해결

━━━━━━━━━━━━━━━━━━
[Action 작성 제약]

- 외부에서 관찰 가능한 단일 행동만 허용
- 금지: 내부 인지/판단 (검토, 고려, 분석, 인식 등), 복합 행동 ("확인 후 수정"), 상태 변화 표현 ("정상화된다" → effect임), 추상적 행동 ("대응한다", "조치한다")

━━━━━━━━━━━━━━━━━━
[출력]
- 하나의 에이전트(행위자), action 1개
- JSON 형식으로만 출력
"""

_ACTIVE_EN = """\
You are an expert in scenario generation for AI system impact assessment.
Based on the current state, generate an agent who will take action and the action they will perform.

━━━━━━━━━━━━━━━━━━
[Input]

Workflow (current and subsequent stages): {workflow_context}
Relevant Entities and Roles: {entity_roles}
Scenario history (single branch): {branch_history}

※ The current state is the accumulated result of actions and effects from preceding steps.

━━━━━━━━━━━━━━━━━━
[Procedure]

1. Agent Selection — actor (1)
- Select an agent who can realistically take action based on the current state.
- Only agents present in the entity_roles list or stakeholder list may be selected.

2. Action Generation — 1
- Describe a single action performed by the selected agent.
- The action must naturally follow from the current history.
- The action must be capable of triggering new effects.
- The action must be feasible within the agent's role scope.

⚠️ The action does not need to be problem-solving. Actively consider the following types:
- Normal task processing without awareness of the problem
- Action based on incomplete or incorrect judgment
- Action with correct intent but causing side effects
- Action that delays or worsens the problem
- Action that resolves the problem

━━━━━━━━━━━━━━━━━━
[Action Writing Constraints]

- Only a single externally observable action is permitted.
- Prohibited: internal cognition/judgment (reviewing, considering, analyzing, recognizing), compound actions ("check then modify"), state-change expressions ("normalizes" → this is an effect), abstract actions ("respond", "take measures").

━━━━━━━━━━━━━━━━━━
[Output]
- One agent (actor), 1 action
- Output in JSON format only
"""

_VALIDATOR_KO = """\
당신은 AI 시스템 영향평가 시나리오 검증 전문가입니다.
가장 최근에 추가된 단계가 시나리오 흐름상 타당한지 검증하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

워크플로우 (현재 ~ 이후 단계): {workflow_context}
관련 Entity 및 Role: {entity_roles}
시나리오 history: {branch_history}
검증 대상 유형: {last_step_type}
검증 대상 내용: {last_step_content}

━━━━━━━━━━━━━━━━━━
[검증 항목 — 아래 순서대로 판단하라]

1. is_feasible: 워크플로우 + entity role 범위 내에서 실제 발생 가능한 행동/상태인가?
   - entity_roles에 존재하는 entity인가?
   - 해당 entity의 role 범위 내 행동/상태인가?
   - workflow 흐름상 물리적·논리적으로 가능한가?
   → false이면 termination_reason: "infeasible"

2. is_causal: 직전 단계의 결과로부터 직접적으로 이어지는가?
   - history의 직전 항목과 명확한 인과 관계가 있는가?
   - 맥락 없이 갑자기 전환된 내용은 아닌가?
   → false이면 termination_reason: "acausal"

3. is_duplicate: history에 이미 동일하거나 표현만 다른 내용이 있는가?
   - 동일 entity + 동일 유형 상태 변화/행동 반복 여부
   - 표현만 바꾼 재서술 여부
   → true이면 termination_reason: "duplicate"

4. is_complete: 이 시점에서 시나리오가 자연스럽게 완결되었는가?
   - 결과가 확정되어 추가 전파가 불필요한 상태인가?
   - 상황 안정화로 의미 있는 다음 단계가 없는 상태인가?
   → true이면 termination_reason: "concluded"

━━━━━━━━━━━━━━━━━━
[종료 규칙]

- 위 4가지 중 하나라도 종료 조건이 되면 should_terminate = true
- 모두 통과하면 should_terminate = false, termination_reason = "none"
- reason: 판단 근거를 1~2문장으로 기술

━━━━━━━━━━━━━━━━━━
[출력]
JSON 형식으로만 출력
"""

_VALIDATOR_EN = """\
You are an expert in scenario validation for AI system impact assessment.
Verify whether the most recently added step is valid within the scenario flow.

━━━━━━━━━━━━━━━━━━
[Input]

Workflow (current and subsequent stages): {workflow_context}
Relevant Entities and Roles: {entity_roles}
Scenario history: {branch_history}
Type of step being validated: {last_step_type}
Content of step being validated: {last_step_content}

━━━━━━━━━━━━━━━━━━
[Validation Criteria — Evaluate in order]

1. is_feasible: Is this action/state plausible within the workflow and entity role scope?
   - Is this entity present in entity_roles?
   - Is this action/state within the entity's role scope?
   - Is this physically and logically possible within the workflow flow?
   → If false: termination_reason: "infeasible"

2. is_causal: Does this step directly follow from the result of the immediately preceding step?
   - Is there a clear causal relationship with the immediately preceding item in history?
   - Is it not an abrupt transition with no contextual connection?
   → If false: termination_reason: "acausal"

3. is_duplicate: Is there already identical or differently-worded duplicate content in history?
   - Same entity + same type of state change/action repeated
   - Re-description with different wording only
   → If true: termination_reason: "duplicate"

4. is_complete: Has the scenario naturally concluded at this point?
   - Is the outcome determined such that further propagation is unnecessary?
   - Is the situation stabilized such that no meaningful next step exists?
   → If true: termination_reason: "concluded"

━━━━━━━━━━━━━━━━━━
[Termination Rules]

- If any of the above 4 conditions triggers termination: should_terminate = true
- If all pass: should_terminate = false, termination_reason = "none"
- reason: State the basis for the judgment in 1–2 sentences.

━━━━━━━━━━━━━━━━━━
[Output]
Output in JSON format only
"""

_MERGE_KO = """\
당신은 AI 시스템 시나리오 작성 전문가입니다.
아래 시나리오 목록을 각각 자연어 문단으로 재작성하십시오.

━━━━━━━━━━━━━━━━━━
[입력 시나리오]
{scenarios}

━━━━━━━━━━━━━━━━━━
[작성 규칙]

- 각 시나리오를 "Scenario#번호: 제목" 헤더로 구분 (번호는 {start_num}부터 시작)
- 인과 관계가 드러나도록 내용이 명확하게 연결
- 3인칭 서술, 현재형, 관찰 가능한 사실 중심 (추측·해석 금지)
- 불필요하게 반복되는 서술 제거

━━━━━━━━━━━━━━━━━━
[출력 형식] — 반드시 준수, 다른 문장 절대 금지

Scenario#1: [제목]
[자연어 서술 문단]

Scenario#2: [제목]
[자연어 서술 문단]

...
"""

_MERGE_EN = """\
You are an expert in AI system scenario writing.
Rewrite each of the scenarios below as natural-language paragraphs.

━━━━━━━━━━━━━━━━━━
[Input Scenarios]
{scenarios}

━━━━━━━━━━━━━━━━━━
[Writing Rules]

- Separate each scenario with a "Scenario#[number]: [title]" header (numbers start from {start_num})
- Connect content clearly to reveal causal relationships
- Third-person narration, present tense, focused on observable facts (no speculation or interpretation)
- Remove unnecessarily repetitive descriptions

━━━━━━━━━━━━━━━━━━
[Output Format] — Must be followed strictly; no other sentences allowed

Scenario#1: [title]
[natural language paragraph]

Scenario#2: [title]
[natural language paragraph]

...
"""


def SCENARIO_PROPAGATION_PROMPT(mode: str, workflow_context: str, entity_roles: str,
                                 branch_history: str, lang: str = "ko") -> str:
    """Unified BFS scenario propagation for passive_initial / passive_continue / active modes."""
    if lang == "en":
        templates = {
            "passive_initial": _PASSIVE_TURN1_EN,
            "passive_continue": _PASSIVE_TURN23_EN,
            "active": _ACTIVE_EN,
        }
    else:
        templates = {
            "passive_initial": _PASSIVE_TURN1_KO,
            "passive_continue": _PASSIVE_TURN23_KO,
            "active": _ACTIVE_KO,
        }
    if mode not in templates:
        raise ValueError(f"Unknown mode for SCENARIO_PROPAGATION_PROMPT: {mode!r}")
    return templates[mode].format(
        workflow_context=workflow_context,
        entity_roles=entity_roles,
        branch_history=branch_history,
    )


def VALIDATOR_PROMPT(lang: str = "ko") -> str:
    return _VALIDATOR_EN if lang == "en" else _VALIDATOR_KO


def MERGE_PROMPT(scenarios: str, start_num: int, lang: str = "ko") -> str:
    template = _MERGE_EN if lang == "en" else _MERGE_KO
    return template.format(scenarios=scenarios, start_num=start_num)
