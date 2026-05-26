_WORKFLOW_STAGES_KO = """\
1. 데이터 수집·전처리·검증
   AI 모델 학습·생성에 필요한 데이터를 수집하고, 결측값 처리·이상치 제거·형식 변환 등으로 모델에 적합하도록 준비하는 단계

2. 모델 개발·학습
   전처리된 데이터를 기반으로 AI 모델(예측/생성)을 학습하고 검증하는 단계

3. 결과 생성·예측
   모델이 입력 데이터를 기반으로 예측 결과를 산출하거나 새로운 데이터를 생성하는 단계

4. 사용 및 연계 업무
   AI 결과를 실제 업무 환경과 연계된 후속 프로세스에서 활용하고, 의사결정·운영·사용자 상호작용에 적용하는 단계

5. 데이터·모델 관리 및 모니터링
   학습 데이터·피드백 데이터·모델 버전·로그 등을 안전하게 관리하고, 모델 성능과 시스템 상태를 모니터링하며 필요 시 재학습·재배포를 수행하는 단계"""

_WORKFLOW_STAGES_EN = """\
1. Data Collection, Preprocessing & Validation
   The stage in which data required for AI model training or generation is collected and prepared for the model through handling missing values, removing outliers, and format conversion.

2. Model Development & Training
   The stage in which AI models (predictive/generative) are trained and validated based on preprocessed data.

3. Result Generation & Prediction
   The stage in which the model produces prediction results or generates new data based on input data.

4. Deployment & Integration
   The stage in which AI results are applied in actual work environments through subsequent processes, including decision-making, operations, and user interaction.

5. Data, Model Management & Monitoring
   The stage in which training data, feedback data, model versions, and logs are securely managed, and model performance and system status are monitored, with retraining and redeployment performed as needed."""

_WORKFLOW_DESCRIPTION_KO = """\
당신은 AI 시스템 구조 분석 전문가입니다.
제공된 문서를 기반으로 AI 시스템의 5단계 워크플로우 설명을 작성하라.

────────────────────────────────
[워크플로우 단계 — 반드시 이 순서·명칭 유지]

{stages}

────────────────────────────────
[문서]

{{document}}

────────────────────────────────
[description 작성 규칙]

- 문서에서 확인 가능한 내용만 사용하며, 없는 흐름 추가 금지
- 해당 단계에서 일어나는 모든 처리 흐름, 데이터 흐름, 결정 기준, 처리 절차, 결과물을 빠짐없이 기술
- 문장 수를 제한하지 말고 내용이 완전히 기술될 때까지 충분히 작성
- 불확실한 내용은 "문서에서 명확히 정의되지 않음"으로 명시
- 단계 간 내용 중복 금지
- 한국어로 작성, 영어 기술 용어는 괄호로 병기

────────────────────────────────
[강제 규칙]

- 정확히 5개 단계만 생성
- id는 반드시 1~5 순차 증가
- type은 지정된 5개 명칭만 사용
- agents, objects 항목 출력 금지 (description만 작성)
""".format(stages=_WORKFLOW_STAGES_KO)

_WORKFLOW_DESCRIPTION_EN = """\
You are an expert in AI system architecture analysis.
Based on the provided document, write descriptions for each of the 5 workflow stages of the AI system.

────────────────────────────────
[Workflow Stages — Maintain this exact order and naming]

{stages}

────────────────────────────────
[Document]

{{document}}

────────────────────────────────
[Description Writing Guidelines]

- Use only information verifiable from the document; do not add processes not present in the document.
- Describe all processing flows, data flows, decision criteria, procedures, and outputs occurring at each stage in full detail.
- Do not limit the number of sentences; write thoroughly until all content is fully described.
- For unclear content, explicitly state "Not clearly defined in the document."
- No duplication of content across stages.
- Write in English; Korean technical terms may be included in parentheses where appropriate.

────────────────────────────────
[Constraints]

- Generate exactly 5 stages.
- Stage IDs must be sequential from 1 to 5.
- Stage types must use only the 5 designated names.
- Do not output agents or objects fields (description only).
""".format(stages=_WORKFLOW_STAGES_EN)


def WORKFLOW_DESCRIPTION_PROMPT(document: str, lang: str = "ko") -> str:
    template = _WORKFLOW_DESCRIPTION_EN if lang == "en" else _WORKFLOW_DESCRIPTION_KO
    return template.format(document=document)


_WORKFLOW_CRITIQUE_KO = """\
당신은 AI 시스템 구조 분석 검토 전문가입니다.
아래 원본 문서와 워크플로우 설명 초안을 비교하여, 각 단계별 누락 요소와 오류를 지적하라.

────────────────────────────────
[원본 문서]

{document}

────────────────────────────────
[워크플로우 초안]

{draft_workflows}

────────────────────────────────
[검토 항목]

각 단계(1~5)에 대해 아래를 확인하라:

1. 누락된 처리 흐름: 문서에 있으나 초안에 기술되지 않은 처리 과정
2. 누락된 데이터 흐름: 문서에 있으나 초안에 설명되지 않은 입력·출력·중간 데이터
3. 누락된 결정 기준: 문서에 있으나 초안에 기술되지 않은 분기·판단 조건
4. 단계 간 중복: 다른 단계에 이미 포함된 내용이 중복으로 기술된 경우
5. 오기·불일치: 문서 내용과 다르게 기술된 항목

────────────────────────────────
[출력 형식]

각 단계별로 아래 형식으로 작성:
"단계 [id]: [type]"
- 지적 사항 목록 (없으면 "이상 없음")
"""

_WORKFLOW_CRITIQUE_EN = """\
You are an expert reviewer of AI system structure analysis.
Compare the original document below with the draft workflow description and identify missing elements and errors in each stage.

────────────────────────────────
[Original Document]

{document}

────────────────────────────────
[Workflow Draft]

{draft_workflows}

────────────────────────────────
[Review Criteria]

For each stage (1–5), check the following:

1. Missing processing flows: processes present in the document but not described in the draft
2. Missing data flows: inputs, outputs, or intermediate data present in the document but not explained
3. Missing decision criteria: branching or judgment conditions present in the document but not described
4. Cross-stage duplication: content that duplicates content already included in another stage
5. Factual errors or inconsistencies: items described differently from the document

────────────────────────────────
[Output Format]

For each stage, write in the following format:
"Stage [id]: [type]"
- List of issues found (write "No issues" if none)
"""


def WORKFLOW_CRITIQUE_PROMPT(document: str, draft_workflows: str, lang: str = "ko") -> str:
    template = _WORKFLOW_CRITIQUE_EN if lang == "en" else _WORKFLOW_CRITIQUE_KO
    return template.format(document=document, draft_workflows=draft_workflows)


_WORKFLOW_REFINE_KO = """\
당신은 AI 시스템 구조 분석 전문가입니다.
아래 원본 문서와 검토 의견을 참고하여 워크플로우 설명을 최종 수정하라.

────────────────────────────────
[원본 문서]

{document}

────────────────────────────────
[워크플로우 초안]

{draft_workflows}

────────────────────────────────
[검토 의견]

{critique}

────────────────────────────────
[수정 규칙]

- 검토 의견에서 지적된 누락 요소를 원본 문서를 참고하여 반드시 보완
- 중복으로 지적된 내용은 더 적합한 단계에만 남기고 제거
- 초안의 정확한 내용은 유지하고, 누락·오류 사항만 수정
- 문장 수를 제한하지 말고 내용이 완전히 기술될 때까지 충분히 작성
- agents, objects 항목 출력 금지

────────────────────────────────
[강제 규칙]

- 정확히 5개 단계 출력
- id는 반드시 1~5 순차
- type은 지정된 5개 명칭만 사용
"""

_WORKFLOW_REFINE_EN = """\
You are an expert in AI system architecture analysis.
Using the original document and review feedback below, finalize the workflow description.

────────────────────────────────
[Original Document]

{document}

────────────────────────────────
[Workflow Draft]

{draft_workflows}

────────────────────────────────
[Review Feedback]

{critique}

────────────────────────────────
[Revision Rules]

- Address all missing elements identified in the review by referencing the original document.
- Remove content flagged as duplicates, keeping it only in the most appropriate stage.
- Retain accurate content from the draft; revise only what is missing or incorrect.
- Do not limit the number of sentences; write thoroughly until all content is fully described.
- Do not output agents or objects fields.

────────────────────────────────
[Constraints]

- Output exactly 5 stages.
- IDs must be sequential from 1 to 5.
- Stage types must use only the 5 designated names.
"""


def WORKFLOW_REFINE_PROMPT(document: str, draft_workflows: str, critique: str, lang: str = "ko") -> str:
    template = _WORKFLOW_REFINE_EN if lang == "en" else _WORKFLOW_REFINE_KO
    return template.format(document=document, draft_workflows=draft_workflows, critique=critique)


_ENTITY_EXTRACT_KO = """\
당신은 AI 시스템 구조 분석 전문가입니다.
아래 워크플로우 단계의 에이전트(Agent)와 오브젝트(Object)를 식별하라.

────────────────────────────────
[워크플로우 단계]

- ID: {workflow_id}
- 유형: {workflow_type}
- 설명: {workflow_description}

────────────────────────────────
[참고 문서]

{document}

────────────────────────────────
[에이전트(Agent) 식별 규칙]

- 해당 단계에서 작업을 수행하거나 의사결정에 관여하는 모든 개인 또는 사람으로 구성된 조직을 개별 나열
- AI 시스템으로부터 서비스를 제공받거나 직접적인 영향을 받는 대상(수혜자, 분석 대상 인구집단 등)도 포함
- AI 시스템·소프트웨어·플랫폼·정보시스템은 에이전트가 아닌 오브젝트로 분류
- name: 문서에 등장하는 원문 표현 우선 사용, 역할·직무 기반 명칭 (실명·고유 식별자 금지)
- role: 해당 단계에서 수행하는 기능 (1~2문장)
- 문서에 등장하는 모든 에이전트를 빠짐없이 식별
- 동일 에이전트가 여러 단계에 등장할 경우 이 단계에서의 역할을 따로 작성

────────────────────────────────
[오브젝트(Object) 식별 규칙]

- 해당 단계에서 핵심적으로 사용·생성·전달되는 주요 데이터·모델·문서를 나열
- name: 문서에 등장하는 원문 표현 우선 사용
- role: 해당 단계에서의 기능적 의미 (1~2문장)
- UI·인프라(버튼, 화면, API, 서버, 데이터베이스, 로그 등) 제외
- 유사한 성격의 데이터 항목은 묶어서 하나의 오브젝트로 표현
- 동일 오브젝트가 여러 단계에 등장할 경우 이 단계에서의 역할을 따로 작성
"""

_ENTITY_EXTRACT_EN = """\
You are an expert in AI system architecture analysis.
Identify the Agents and Objects for the workflow stage below.

────────────────────────────────
[Workflow Stage]

- ID: {workflow_id}
- Type: {workflow_type}
- Description: {workflow_description}

────────────────────────────────
[Reference Document]

{document}

────────────────────────────────
[Agent Identification Rules]

- List all individuals or human-composed organizations that perform tasks or participate in decision-making at this stage.
- Also include parties who receive services from the AI system or are directly affected by it (beneficiaries, analyzed populations, etc.).
- AI systems, software, platforms, and information systems are classified as Objects, not Agents.
- name: Prefer the original expression from the document; use role- or function-based names (no proper names or unique identifiers).
- role: The function performed at this stage (1–2 sentences).
- Identify all agents appearing in the document without omission.
- If the same agent appears in multiple stages, write the role specific to this stage separately.

────────────────────────────────
[Object Identification Rules]

- List key data, models, and documents that are used, created, or transferred at this stage.
- name: Prefer the original expression from the document.
- role: The functional meaning at this stage (1–2 sentences).
- Exclude UI and infrastructure (buttons, screens, APIs, servers, databases, logs, etc.).
- Group similar data items into one object where appropriate.
- If the same object appears in multiple stages, write the role specific to this stage separately.
"""


def ENTITY_EXTRACT_PROMPT(workflow_id: int, workflow_type: str, workflow_description: str,
                           document: str, lang: str = "ko") -> str:
    template = _ENTITY_EXTRACT_EN if lang == "en" else _ENTITY_EXTRACT_KO
    return template.format(
        workflow_id=workflow_id,
        workflow_type=workflow_type,
        workflow_description=workflow_description,
        document=document,
    )
