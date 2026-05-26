_IMPACT_GENERATE_KO = """\
당신은 고도화된 AI 윤리 영향 평가 전문가입니다.
윤리 코드 {code} ({name})와 관련된 영향을 식별하십시오.

━━━━━━━━━━━━━━━━━━
[입력]

전체 시나리오:
{merged_scenarios}

---

윤리 코드 {code} — {name}
{ethics_definition}

---

관련 법규 및 기준:
{regulation_context}

━━━━━━━━━━━━━━━━━━
[분석 범위 — 반드시 준수]

이 평가는 오직 윤리 코드 {code} ({name})에 한정됩니다.
모든 영향·키워드·판단은 {name}의 정의와 체크리스트에 명시된 원칙에 직접 근거해야 합니다.

━━━━━━━━━━━━━━━━━━
[분석 지침]

1. 개별 시나리오를 단순 요약하지 말고 반복적으로 나타나는 위험 패턴을 식별하라.
2. 시나리오 간 공통된 문제를 포괄할 수 있는 상위 수준의 영향 키워드를 생성하라.
3. 시나리오 내용에 근거한 인과관계만 도출하며, 과도한 추론이나 비현실적인 결과는 생성하지 말라.

4. 영향 도출 방향
   - 긍정적 영향: {name}의 원칙에 부합하는 사례를 다양하게 도출하십시오.
   - 부정적 영향: {name}의 원칙을 위반하거나 저해하는 사례를 다양하게 도출하십시오.
   - 영향 작성이 끝나면, {name}의 체크리스트 항목을 번호 순서대로 하나씩 검토하십시오. 누락된 영향이 있으면 추가로 작성하십시오.
   - 여러 영향을 하나의 항목으로 묶지 마십시오. 각 영향은 독립된 항목으로 개별 서술하십시오.
   - 관련 법규 및 기준이 있으면 해당 영향 도출에 반영하십시오.

5. 근거 시나리오 표기: 시나리오 번호만 기재. 예) Scenario#113

6. 키워드 작성 규칙:
   - {name}의 체크리스트 항목명 또는 핵심 원칙어를 그대로 사용하여 명사구로 작성.
   - 동일 윤리 코드 내 키워드는 서로 중복되지 않을 것

━━━━━━━━━━━━━━━━━━
[피영향자 분류]

각 영향에 대해 아래 기준으로 판단하십시오.
명확한 근거가 있을 때만 작성하십시오. 불확실하면 null.

1. 직접적 (Primary): AI 시스템과 직접 상호작용하는 대상
2. 간접적 (Secondary): Primary 대상에게 발생한 영향으로 연쇄적으로 영향을 받는 대상
3. 의도치 않은 (Unintended): 설계·예측 범위를 벗어나 비의도적으로 영향을 받는 대상

━━━━━━━━━━━━━━━━━━
[출력]
JSON 형식으로만 출력
"""

_IMPACT_GENERATE_EN = """\
You are a highly advanced AI ethics impact assessment expert.
Identify impacts related to Ethics Code {code} ({name}).

━━━━━━━━━━━━━━━━━━
[Input]

Full scenarios:
{merged_scenarios}

---

Ethics Code {code} — {name}
{ethics_definition}

---

Relevant laws and standards:
{regulation_context}

━━━━━━━━━━━━━━━━━━
[Analysis Scope — Must be strictly followed]

This assessment is limited solely to Ethics Code {code} ({name}).
All impacts, keywords, and judgments must be directly grounded in the definition and checklist principles of {name}.

━━━━━━━━━━━━━━━━━━
[Analysis Guidelines]

1. Do not simply summarize individual scenarios; identify recurring risk patterns.
2. Generate higher-level impact keywords that can encompass common issues across scenarios.
3. Derive only causal relationships grounded in scenario content; do not generate excessive inferences or unrealistic outcomes.

4. Impact derivation direction
   - Positive impacts: Identify diverse instances consistent with the principles of {name}.
   - Negative impacts: Identify diverse instances that violate or impede the principles of {name}.
   - After drafting impacts, review each checklist item of {name} in order. Add any missing impacts.
   - Do not bundle multiple impacts into one item; each impact must be described as a separate, independent item.
   - If relevant laws and standards are provided, reflect them in the impact derivation.

5. Evidence scenario notation: Record scenario number only. Example: Scenario#113

6. Keyword writing rules:
   - Use the checklist item name or core principle term of {name} directly as a noun phrase.
   - Keywords within the same ethics code must not overlap with each other.

━━━━━━━━━━━━━━━━━━
[Affected Party Classification]

For each impact, judge based on the criteria below.
Write only when there is clear evidence; if uncertain, use null.

1. Primary: Parties who directly interact with the AI system
2. Secondary: Parties who are indirectly affected as a downstream consequence of impacts on primary parties
3. Unintended: Parties who are non-intentionally affected in ways beyond the design or prediction scope

━━━━━━━━━━━━━━━━━━
[Output]
Output in JSON format only
"""


def IMPACT_GENERATE_PROMPT(code: str, name: str, ethics_definition: str,
                            merged_scenarios: str, regulation_context: str, lang: str = "ko") -> str:
    template = _IMPACT_GENERATE_EN if lang == "en" else _IMPACT_GENERATE_KO
    return template.format(
        code=code, name=name, ethics_definition=ethics_definition,
        merged_scenarios=merged_scenarios, regulation_context=regulation_context,
    )


_IMPACT_CRITIQUE_KO = """\
당신은 AI 윤리 영향평가 검토 전문가입니다.
아래 윤리 코드 {code} ({name})에 대한 영향 평가 초안을 검토하고, 개선 사항을 지적하십시오.

━━━━━━━━━━━━━━━━━━
[윤리 코드 정의]

{ethics_definition}

━━━━━━━━━━━━━━━━━━
[참조 시나리오]

{referenced_scenarios}

━━━━━━━━━━━━━━━━━━
[영향 평가 초안]

{draft_impacts}

━━━━━━━━━━━━━━━━━━
[검토 항목]

1. 누락된 영향: {name}의 체크리스트 항목 중 아직 다루어지지 않은 원칙
2. 과장된 영향: 시나리오나 법규 근거 없이 과도하게 주장된 영향
3. 중복 키워드: positives 또는 negatives 내에서 실질적으로 동일한 키워드가 중복 사용된 경우
4. 잘못된 분류: 긍정으로 분류했지만 부정에 가까운 영향, 또는 반대의 경우
5. {name} 범위 이탈: 이 윤리 코드와 무관한 다른 윤리 기준의 영향이 포함된 경우
6. 시나리오→윤리 도출 타당성: 각 영향 항목의 evidence_scenario 번호를 위 [참조 시나리오]에서 확인하고, 해당 시나리오가 실제로 이 윤리 원칙에 대한 영향을 지지하는지 판단하십시오.

━━━━━━━━━━━━━━━━━━
[출력 형식]

지적 사항 목록 (없으면 "이상 없음")
"""

_IMPACT_CRITIQUE_EN = """\
You are an expert reviewer of AI ethics impact assessment.
Review the draft impact assessment for Ethics Code {code} ({name}) below and identify areas for improvement.

━━━━━━━━━━━━━━━━━━
[Ethics Code Definition]

{ethics_definition}

━━━━━━━━━━━━━━━━━━
[Reference Scenarios]

{referenced_scenarios}

━━━━━━━━━━━━━━━━━━
[Impact Assessment Draft]

{draft_impacts}

━━━━━━━━━━━━━━━━━━
[Review Criteria]

1. Missing impacts: Principles in the {name} checklist not yet addressed
2. Overstated impacts: Impacts claimed without grounding in scenarios or regulations
3. Duplicate keywords: Keywords within positives or negatives that are substantively identical
4. Misclassification: Impacts classified as positive that are closer to negative, or vice versa
5. Out-of-scope for {name}: Impacts from other ethics criteria unrelated to this ethics code
6. Scenario → ethics derivation validity: For each impact item, check the evidence_scenario numbers against the [Reference Scenarios] above and determine whether those scenarios actually support an impact on this ethical principle. Flag any logical leaps or weak connections.

━━━━━━━━━━━━━━━━━━
[Output Format]

List of issues found (write "No issues" if none)
"""


def IMPACT_CRITIQUE_PROMPT(code: str, name: str, ethics_definition: str,
                            referenced_scenarios: str, draft_impacts: str, lang: str = "ko") -> str:
    template = _IMPACT_CRITIQUE_EN if lang == "en" else _IMPACT_CRITIQUE_KO
    return template.format(
        code=code, name=name, ethics_definition=ethics_definition,
        referenced_scenarios=referenced_scenarios, draft_impacts=draft_impacts,
    )


_IMPACT_REFINE_GENERATE_KO = """\
당신은 고도화된 AI 윤리 영향 평가 전문가입니다.
아래 검토 의견을 반영하여 윤리 코드 {code} ({name})의 영향 평가를 최종 수정하십시오.

━━━━━━━━━━━━━━━━━━
[윤리 코드 정의]

{ethics_definition}

---

관련 법규 및 기준:
{regulation_context}

━━━━━━━━━━━━━━━━━━
[검토 의견]

{critique}

━━━━━━━━━━━━━━━━━━
[영향 평가 초안]

{draft_impacts}

━━━━━━━━━━━━━━━━━━
[수정 규칙]

- 검토 의견의 누락 항목 보완
- 과장된 영향 삭제 또는 완화
- 중복 키워드 통합 또는 제거
- 잘못 분류된 영향 수정
- {name} 범위 이탈 항목 제거
- 초안에서 문제 없는 항목은 그대로 유지
- 등급(scale/scope/likelihood/resolvability) 및 not_found는 작성하지 마십시오.

━━━━━━━━━━━━━━━━━━
[출력]
JSON 형식으로만 출력
"""

_IMPACT_REFINE_GENERATE_EN = """\
You are a highly advanced AI ethics impact assessment expert.
Revise the impact assessment for Ethics Code {code} ({name}) by incorporating the review feedback below.

━━━━━━━━━━━━━━━━━━
[Ethics Code Definition]

{ethics_definition}

---

Relevant laws and standards:
{regulation_context}

━━━━━━━━━━━━━━━━━━
[Review Feedback]

{critique}

━━━━━━━━━━━━━━━━━━
[Impact Assessment Draft]

{draft_impacts}

━━━━━━━━━━━━━━━━━━
[Revision Rules]

- Address missing items identified in the review.
- Delete or moderate overstated impacts.
- Merge or remove duplicate keywords.
- Correct misclassified impacts.
- Remove items out of scope for {name}.
- Retain items from the draft that have no issues.
- Do not write grades (scale/scope/likelihood/resolvability) or not_found.

━━━━━━━━━━━━━━━━━━
[Output]
Output in JSON format only
"""


def IMPACT_REFINE_GENERATE_PROMPT(code: str, name: str, ethics_definition: str,
                                   regulation_context: str, critique: str, draft_impacts: str,
                                   lang: str = "ko") -> str:
    template = _IMPACT_REFINE_GENERATE_EN if lang == "en" else _IMPACT_REFINE_GENERATE_KO
    return template.format(
        code=code, name=name, ethics_definition=ethics_definition,
        regulation_context=regulation_context, critique=critique, draft_impacts=draft_impacts,
    )


_IMPACT_NOT_FOUND_KO = """\
당신은 AI 윤리 영향평가 전문가입니다.
아래 10개 윤리 코드별 정의와 평가 결과를 검토하여, 각 코드의 체크리스트에서 요구하지만 시나리오 및 문서에서 확인되지 않는 제도적·기술적·절차적 요소를 식별하십시오.

━━━━━━━━━━━━━━━━━━
[시나리오]

{merged_scenarios}

━━━━━━━━━━━━━━━━━━
[10개 윤리 코드 정의 및 현재 평가 결과]

{all_codes_with_impacts}

━━━━━━━━━━━━━━━━━━
[not_found 작성 기준]

각 코드의 체크리스트에서 요구하지만, 시나리오 및 제공 문서 어디에서도 확인되지 않는 제도적·기술적·절차적 요소를 식별하십시오.

각 항목은 아래 3가지를 모두 포함해야 합니다:

1. item: 누락된 요건의 명칭 (구체적으로)
2. description: 무엇이 없는지 + 이 시스템에서 특히 중요한 이유 (2~3문장)
3. recommendation: 실행 가능한 구체적 이행 방안

주의:
- 해당 코드의 체크리스트에서 요구하는 원칙에 한정하여 작성
- 시나리오에서 이미 다뤄진 문제는 not_found가 아닌 negatives에 해당
- 시스템 설계·운영 문서에 아예 존재하지 않는 요건만 포함
- 불확실한 경우 작성하지 말 것

━━━━━━━━━━━━━━━━━━
[출력]
JSON 형식으로만 출력
not_found_by_code: [{{"code": "1", "items": [...]}}, {{"code": "2", "items": [...]}}, ...]
"""

_IMPACT_NOT_FOUND_EN = """\
You are an AI ethics impact assessment expert.
Review the definitions and assessment results for the 10 ethics codes below, and identify institutional, technical, and procedural elements required by each code's checklist but not confirmed in the scenarios or document.

━━━━━━━━━━━━━━━━━━
[Scenarios]

{merged_scenarios}

━━━━━━━━━━━━━━━━━━
[Definitions and Current Assessment Results for 10 Ethics Codes]

{all_codes_with_impacts}

━━━━━━━━━━━━━━━━━━
[not_found Writing Criteria]

Identify elements required by each code's checklist that are not confirmed anywhere in the scenarios or provided document.

Each item must include all 3 of the following:

1. item: The name of the missing requirement (specifically)
   Example: "Grievance procedure for algorithmic decisions" (Good) / "Remedy procedure" (Too abstract)

2. description: What is missing + why it is particularly important for this system (2–3 sentences)

3. recommendation: A concrete, actionable implementation measure

Notes:
- Limit to principles required by that code's checklist
- Problems already addressed in scenarios belong in negatives, not not_found
- Include only requirements completely absent from the system design and operational documents
- Do not write if uncertain

━━━━━━━━━━━━━━━━━━
[Output]
Output in JSON format only
not_found_by_code: [{{"code": "1", "items": [...]}}, {{"code": "2", "items": [...]}}, ...]
"""


def IMPACT_NOT_FOUND_PROMPT(merged_scenarios: str, all_codes_with_impacts: str, lang: str = "ko") -> str:
    template = _IMPACT_NOT_FOUND_EN if lang == "en" else _IMPACT_NOT_FOUND_KO
    return template.format(merged_scenarios=merged_scenarios, all_codes_with_impacts=all_codes_with_impacts)


_IMPACT_GRADE_POSITIVE_KO = """\
당신은 AI 윤리 영향평가 등급 평가 전문가입니다.
아래 긍정적 영향 항목에 대해 등급을 부여하십시오.

[평가 대상]
- 윤리 코드: {code} ({name})
- 키워드: {keyword}
- 영향 설명: {impact}
- 근거 시나리오: {evidence_scenario}

[윤리 코드]
{ethics_brief}

[등급 기준]

■ 규모 (Scale): 이 긍정적 영향의 크기
- "매우 큼": 인권·존엄성 실질적 강화 또는 사회 구조적 개선
- "큼": 복지·신뢰 향상, 지속적 긍정 효과
- "중간": 일부 집단에 의미 있는 긍정 변화
- "보통/경미한": 제한적·단기적 효과

■ 범위 (Scope): 영향 지속 기간
- "단기" / "중기" / "장기" / "세대 간"

■ 가능성 (Likelihood): 실제 발생 가능성
- "높음" / "중간" / "낮음"

[출력]
JSON 형식으로만 출력. 각 reason은 50자 이내.
"""

_IMPACT_GRADE_POSITIVE_EN = """\
You are an expert in AI ethics impact assessment grading.
Assign grades to the positive impact item below.

[Assessment Target]
- Ethics code: {code} ({name})
- Keyword: {keyword}
- Impact description: {impact}
- Evidence scenarios: {evidence_scenario}

[Ethics Code]
{ethics_brief}

[Grading Criteria]

■ Scale: The magnitude of this positive impact
- "Very Large": Substantial enhancement of human rights/dignity or structural social improvement
- "Large": Improvement in welfare/trust, sustained positive effect
- "Moderate": Meaningful positive change for some groups
- "Minor": Limited or short-term effect

■ Scope: Duration of impact
- "Short-term" / "Medium-term" / "Long-term" / "Intergenerational"

■ Likelihood: Probability of actual occurrence
- "High" / "Moderate" / "Low"

[Output]
Output in JSON format only. Each reason within 50 characters.
"""

_IMPACT_GRADE_NEGATIVE_KO = """\
당신은 AI 윤리 영향평가 등급 평가 전문가입니다.
아래 부정적 영향 항목에 대해 등급을 부여하십시오.

[평가 대상]
- 윤리 코드: {code} ({name})
- 키워드: {keyword}
- 영향 설명: {impact}
- 근거 시나리오: {evidence_scenario}

[윤리 코드]
{ethics_brief}

[등급 기준]

■ 규모 (Scale): 이 부정적 영향의 심각성
- "재앙적": 생명권 박탈, 민주주의 훼손 등 회복 불가 수준
- "치명적": 심각한 신체·심리·법적 피해
- "심각한": 존엄성·자율성·프라이버시 중대 침해
- "보통": 제한적 피해, 단기 불편

■ 범위 (Scope): 영향 지속 기간
- "단기" / "중기" / "장기" / "세대 간"

■ 가능성 (Likelihood): 실제 발생 가능성
- "높음" / "중간" / "낮음"

■ 해결 가능성 (Resolvability)
- "높음": 기술 수정만으로 단기 해결 가능
- "중간": 정책·프로세스 개선 필요
- "낮음": 법률·제도 변화 필요
- "매우 낮음": 구조적으로 해결 불가능

[출력]
JSON 형식으로만 출력. 각 reason은 50자 이내.
"""

_IMPACT_GRADE_NEGATIVE_EN = """\
You are an expert in AI ethics impact assessment grading.
Assign grades to the negative impact item below.

[Assessment Target]
- Ethics code: {code} ({name})
- Keyword: {keyword}
- Impact description: {impact}
- Evidence scenarios: {evidence_scenario}

[Ethics Code]
{ethics_brief}

[Grading Criteria]

■ Scale: The severity of this negative impact
- "Catastrophic": Loss of the right to life, undermining of democracy — irreversible level
- "Critical": Serious physical, psychological, or legal harm
- "Severe": Significant violation of dignity, autonomy, or privacy
- "Moderate": Limited harm, short-term inconvenience

■ Scope: Duration of impact
- "Short-term" / "Medium-term" / "Long-term" / "Intergenerational"

■ Likelihood: Probability of actual occurrence
- "High" / "Moderate" / "Low"

■ Resolvability
- "High": Resolvable in the short term through technical fixes alone
- "Moderate": Policy or process improvements required
- "Low": Legal or institutional changes required
- "Very Low": Structurally irresolvable

[Output]
Output in JSON format only. Each reason within 50 characters.
"""


def IMPACT_GRADE_PROMPT(impact_type: str, code: str, name: str, keyword: str,
                         impact: str, evidence_scenario: str, ethics_brief: str,
                         lang: str = "ko") -> str:
    """Unified impact grade prompt for positive and negative impacts."""
    if lang == "en":
        template = _IMPACT_GRADE_POSITIVE_EN if impact_type == "positive" else _IMPACT_GRADE_NEGATIVE_EN
    else:
        template = _IMPACT_GRADE_POSITIVE_KO if impact_type == "positive" else _IMPACT_GRADE_NEGATIVE_KO
    return template.format(
        code=code, name=name, keyword=keyword,
        impact=impact, evidence_scenario=evidence_scenario, ethics_brief=ethics_brief,
    )


_IMPACT_REFINE_KO = """\
당신은 AI 윤리 영향평가 보고서 편집 전문가입니다.
아래 10개 윤리 코드별 영향평가 결과(JSON)에 대해 다음 두 작업을 수행하십시오.

━━━━━━━━━━━━━━━━━━
[작업 1: 중복 키워드 제거]

각 윤리 코드의 keyword 목록에 대해 아래 절차를 순서대로 수행하십시오.

1단계: 중복 식별 — 전체 10개 코드의 keyword를 비교하여, 2개 이상의 코드에 동일하게 등장하는 keyword를 식별하십시오.
2단계: 귀속 판단 — 중복 식별된 keyword에 대해 "이 keyword는 해당 윤리 코드의 고유 원칙을 직접적으로 반영하는가?"를 판단하십시오. Yes → 유지, No → 제거
3단계: 제거 실행 — No로 판단된 keyword를 해당 코드의 목록에서 제거하십시오. 단, 동일 keyword라도 코드마다 판단을 독립적으로 수행하십시오.

━━━━━━━━━━━━━━━━━━
[작업 2: 어투 통일]

모든 영향의 impact 필드를 아래 규칙에 맞게 수정하십시오:
- 3인칭 서술, 현재형
- 전문 행정·기술 보고서 어조, 영향은 자세하게 작성할 것
- "[시스템 기능/조건]에 의해 [직접적인 변화]가 발생할 가능성이 있으며, 이는 [이해관계자 수준의 영향]으로 이어질 수 있습니다."
- 상황 → 윤리적 영향의 인과 구조를 문장 안에 포함
- 과장 및 단정적 표현 금지

수정 금지 필드: keyword, evidence_scenario, affected_parties, scale, scope, likelihood, resolvability, not_found

━━━━━━━━━━━━━━━━━━
[입력]
{ethics_assessment}
"""

_IMPACT_REFINE_EN = """\
You are an expert editor for AI ethics impact assessment reports.
Perform the following two tasks on the assessment results (JSON) for the 10 ethics codes below.

━━━━━━━━━━━━━━━━━━
[Task 1: Remove Duplicate Keywords]

For the keyword list of each ethics code, perform the following in order:

Step 1: Identify duplicates — Compare keywords across all 10 codes and identify any keyword that appears identically in 2 or more codes.
Step 2: Attribution judgment — For each identified duplicate keyword, judge: "Does this keyword directly reflect the unique principles of this ethics code?" Yes → Retain, No → Remove.
Step 3: Execute removal — Remove keywords judged No from the code's list. Perform this judgment independently for each code even if the same keyword appears in multiple codes.

━━━━━━━━━━━━━━━━━━
[Task 2: Tone Unification]

Revise all impact fields in all impacts according to the following rules:
- Third-person narration, present tense
- Professional administrative/technical report tone; impacts should be described in detail
- "Due to [system function/condition], there is a possibility that [direct change] will occur, which may lead to [impact at the stakeholder level]."
- Include the causal structure of situation → ethical impact within the sentence
- No exaggerated or assertive expressions

Do not modify the following fields: keyword, evidence_scenario, affected_parties, scale, scope, likelihood, resolvability, not_found

━━━━━━━━━━━━━━━━━━
[Input]
{ethics_assessment}
"""


def IMPACT_REFINE_PROMPT(ethics_assessment: str, lang: str = "ko") -> str:
    template = _IMPACT_REFINE_EN if lang == "en" else _IMPACT_REFINE_KO
    return template.format(ethics_assessment=ethics_assessment)
