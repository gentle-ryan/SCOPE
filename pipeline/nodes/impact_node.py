import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai import types

from config import OUTPUTS_DIR
from pipeline.state import AIAState
from prompts.base_prompts import GENERIC_CRITIQUE_PROMPT, GENERIC_REFINE_PROMPT
from prompts.impact_prompts import (
    IMPACT_GENERATE_PROMPT,
    IMPACT_NOT_FOUND_PROMPT,
    IMPACT_GRADE_PROMPT,
    IMPACT_REFINE_PROMPT,
)
from schemas.impact_schema import (
    IMPACT_GENERATE_SCHEMA,
    IMPACT_GRADE_POSITIVE_SCHEMA,
    IMPACT_GRADE_NEGATIVE_SCHEMA,
    IMPACT_NOT_FOUND_SCHEMA,
    REFINE_UNGRADED_SCHEMA,
    STEP6_SCHEMA,
    REFINE_SCHEMA,
)
from services.cache_service import cached_markdown
from services.llm_client import FLASH_MODEL, LITE_MODEL, LLMClient, call_with_retry
from services.rag_service import retrieve_context

ETHICS_CODES = [
    {"code": "1",
      "name": "인권보장",
      "name_en": "Human Rights Protection",
      "description": "인공지능의 개발과 활용은 모든 인간에게 동등하게 부여된 권리를 존중하고, 다양한 민주적 가치와 국제인권법 등에 명시된 권리를 보장하여야 한다.\n인공지능의 개발과 활용은 인간의 권리와 자유를 침해해서는 안 된다.",
      "description_en": "AI development and use must respect and guarantee rights equally granted to all humans, diverse democratic values, and rights specified in international human rights law. AI must not violate human rights and freedoms.",
      "checklist": [
        "인공지능시스템이 인간의 생명과 안전에 관한 권리를 침해하지 않도록 개발·운영하고 있는가?",
        "인공지능시스템이 모든 인간을 평등한 존재로 대우함으로써 성별, 연령, 지역, 종교, 인종, 민족, 경제적 수준, 성적 지향, 정치적 성향, 장애 등을 이유로 차별하지 않도록 개발·운영하고 있는가?",
        "인공지능시스템이 사용자의 자율적 행동이나 결정을 방해하지 않도록 개발·운영하고 있는가?",
        "인공지능시스템이 사용자의 언론·출판·집회·결사 등 표현의 자유를 침해하지 않도록 개발·운영하고 있는가?",
        "인공지능시스템이 사용자에게 불쾌감을 주지 않는 등 인간을 인격적으로 대우하도록 개발·운영하고 있는가?"
      ],
      "checklist_en": [
        "Is the AI system developed and operated to not violate human rights to life and safety?",
        "Is the AI system developed and operated to treat all humans as equal and not discriminate based on gender, age, region, religion, race, ethnicity, economic status, sexual orientation, political views, or disability?",
        "Is the AI system developed and operated to not interfere with users' autonomous actions or decisions?",
        "Is the AI system developed and operated to not infringe on users' freedom of expression, including press, publication, assembly, and association?",
        "Is the AI system developed and operated to treat humans with dignity, without causing discomfort to users?"
      ]
    },
    {
      "code": "2",
      "name": "프라이버시 보호",
      "name_en": "Privacy Protection",
      "description": "인공지능을 개발하고 활용하는 전 과정에서 개인의 프라이버시를 보호해야 한다.\n인공지능 전 생애주기에 걸쳐 개인정보의 오용을 최소화하도록 노력해야 한다.",
      "description_en": "Personal privacy must be protected throughout the entire process of developing and using AI. Efforts must be made to minimize misuse of personal data across the entire AI lifecycle.",
      "checklist": [
        "인공지능시스템의 개발·운영 과정에서 개인정보를 수집·활용하는 경우, 개인정보 보호법 등 관련 법령 준수를 위해 개인정보보호위원회의 「인공지능(AI) 개인정보보호 자율점검표」에 따른 점검을 수행하였는가?",
        "인공지능시스템의 개발·운영 과정에서 사생활의 비밀과 자유를 침해할 우려에 대하여 검토하고 있는가?"
      ],
      "checklist_en": [
        "If personal data is collected and used during AI system development and operation, has a review been conducted per the Personal Information Protection Commission's AI Privacy Self-Checklist to comply with the Personal Information Protection Act?",
        "Is the risk of infringing on the secrecy and freedom of individuals' private lives reviewed during AI system development and operation?"
      ]
    },
    {
      "code": "3",
      "name": "다양성 존중",
      "name_en": "Diversity & Inclusion",
      "description": "인공지능 개발 및 활용 전 단계에서 사용자의 다양성과 대표성을 반영해야 하며,\n성별·연령·장애·지역·인종·종교·국가 등 개인 특성에 따른 편향과 차별을 최소화해야 한다.\n상용화된 인공지능은 모든 사람에게 공정하게 적용되어야 한다.\n사회적 약자 및 취약 계층의 접근성을 보장하고 혜택이 골고루 분배되도록 노력해야 한다.",
      "description_en": "Diversity and representativeness of users must be reflected in all stages of AI development and use. Bias and discrimination based on personal characteristics such as gender, age, disability, region, race, religion, and nationality must be minimized.",
      "checklist": [
        "인공지능시스템 활용에 사회적 약자의 접근 가능성을 고려하고 있는가?",
        "인공지능시스템 개발에 활용되는 데이터의 성별, 인종, 민족, 국가 등 편향 가능성을 정기적으로 내부 전담부서 혹은 외부 전문가를 통해 판단하고 최소화하려 노력하고 있는가?",
        "인공지능시스템의 개발·운영 단계에서 다양한 의견을 청취·검토·평가·반영할 수 있는 절차를 마련하였는가?",
        "인공지능시스템 사용 시 편향, 차별, 소외 등이 발견될 경우 이를 내부적으로 검토·평가·반영할 수 있는 절차를 마련하였는가?",
        "인공지능시스템 개발자를 대상으로 편향성 인지·분석 능력 향상을 위한 교육훈련 기회를 제공하고 있는가?"
      ],
      "checklist_en": [
        "Is the accessibility of socially vulnerable groups considered in the use of the AI system?",
        "Are potential biases in data used for AI development (gender, race, ethnicity, nationality, etc.) regularly assessed and minimized by internal departments or external experts?",
        "Are procedures established to hear, review, evaluate, and incorporate diverse opinions during AI system development and operation?",
        "Are procedures in place to internally review, evaluate, and address bias, discrimination, or marginalization found during AI system use?",
        "Are training and education opportunities provided to AI developers to improve their ability to recognize and analyze bias?"
      ]
    },
    {
      "code": "4",
      "name": "침해금지",
      "name_en": "Non-maleficence",
      "description": "인공지능은 인간에게 직·간접적 해를 입히는 목적으로 활용해서는 안 된다.\n위험과 부정적 결과를 예방하고 대응 방안을 마련해야 한다.",
      "description_en": "AI must not be used for purposes that directly or indirectly harm humans. Risks and negative outcomes must be prevented and response measures must be prepared.",
      "checklist": [
        "인공지능시스템이 인간의 생명, 신체, 정신 또는 재산에 피해를 발생시킬 우려가 있는지를 사전에 검토하고 예방 조치를 취하였는가?",
        "목적 외 사용으로 인해 피해 발생 가능성이 확인될 경우 사용자에게 고지하는 절차가 있는가?",
        "예상치 못한 피해 발생 시 사용자가 신고하고 의견을 제시할 수 있는 절차가 있는가?",
        "중대한 피해 발생 시 확산 방지를 위해 시스템 사용중단, 리콜, 정부 보고, 사용자 고지 등의 절차를 마련하였는가?"
      ],
      "checklist_en": [
        "Has a prior review been conducted to assess whether the AI system may cause harm to human life, body, mind, or property, and have preventive measures been taken?",
        "Are there procedures to notify users if the possibility of harm from unintended use is identified?",
        "Are there procedures for users to report and provide feedback in the event of unexpected harm?",
        "In the event of serious harm, are procedures in place to prevent spread, including system suspension, recall, government reporting, and user notification?"
      ]
    },
    {
      "code": "5",
      "name": "공공성",
      "name_en": "Public Benefit",
      "description": "인공지능은 개인의 행복뿐 아니라 사회적 공공성과 인류 공동 이익을 위해 활용되어야 한다.\n긍정적 사회 변화를 이끌고 역기능 최소화를 위한 교육을 시행해야 한다.",
      "description_en": "AI must be used not only for individual happiness but also for social public interest and the common good of humanity. Education must be conducted to lead positive social change and minimize dysfunction.",
      "checklist": [
        "인공지능시스템이 특정 개인이나 집단의 이익만을 대변하여 공익을 훼손할 가능성을 고려하고 있는가?",
        "폭력성·음란성·사행성·중독성 등 부작용 발생 개연성을 고려하고 있는가?",
        "인공지능의 사회경제적 영향에 대해 내부 검토 또는 외부 전문가 의견을 청취하였는가?"
      ],
      "checklist_en": [
        "Is consideration given to the possibility that the AI system may undermine public interest by serving only the interests of specific individuals or groups?",
        "Is consideration given to the likelihood of adverse effects such as violence, obscenity, gambling, or addictive behavior?",
        "Have internal reviews or external expert opinions been sought regarding the socioeconomic impact of AI?"
      ]
    },
    {
      "code": "6",
      "name": "연대성",
      "name_en": "Solidarity",
      "description": "다양한 집단 간 연대성을 유지하며 미래세대를 배려하는 방향으로 인공지능을 활용해야 한다.\n전 주기에 걸쳐 다양한 주체의 공정한 참여 기회를 보장해야 한다.\n윤리적 인공지능 개발·활용을 위해 국제사회와 협력해야 한다.",
      "description_en": "AI must be used in a direction that maintains solidarity among various groups and considers future generations. Fair participation opportunities for diverse stakeholders must be guaranteed across the entire lifecycle.",
      "checklist": [
        "목적 범위 내에서 다양한 배경의 개발자·사용자가 의사소통할 기회를 제공하고 있는가?",
        "인공지능시스템 사용이 지역·성별·세대·계층 간 갈등을 유발하여 사회통합을 저해할 가능성을 고려하고 있는가?",
        "탄소중립을 위해 개발·운영 과정에서 탄소배출을 줄이는 방법을 고려하고 있는가?"
      ],
      "checklist_en": [
        "Are opportunities provided for developers and users from diverse backgrounds to communicate within the intended scope?",
        "Is consideration given to the possibility that AI system use may cause conflicts between regions, genders, generations, or social classes, hindering social integration?",
        "Are methods to reduce carbon emissions during development and operation considered for carbon neutrality?"
      ]
    },
    {
      "code": "7",
      "name": "데이터 관리",
      "name_en": "Data Governance",
      "description": "개인정보 등 데이터를 목적에 맞게 활용하며, 목적 외 사용을 금지해야 한다.\n데이터 수집·활용 전 과정에서 편향을 최소화하도록 품질과 위험을 관리해야 한다.",
      "description_en": "Data including personal information must be used according to its intended purpose, and unauthorized use must be prohibited. Quality and risk must be managed to minimize bias throughout data collection and use.",
      "checklist": [
        "데이터 수집·처리 업무 감독 절차를 마련하였는가?",
        "데이터의 출처 및 처리 주요 과정을 기록하고 있는가?",
        "데이터 분석·관리 업무를 위한 기술적·물리적 통제방안을 마련하였는가?"
      ],
      "checklist_en": [
        "Are supervision procedures established for data collection and processing operations?",
        "Are the sources and major processing steps of data being recorded?",
        "Are technical and physical controls in place for data analysis and management tasks?"
      ]
    },
    {
      "code": "8",
      "name": "책임성",
      "name_en": "Accountability",
      "description": "AI 개발·활용 과정에서 책임 주체를 명확히 해 피해를 최소화해야 한다.\n설계자·개발자·서비스 제공자·사용자의 책임을 분명히 해야 한다.",
      "description_en": "Responsible parties must be clearly identified in AI development and use to minimize harm. The responsibilities of designers, developers, service providers, and users must be clearly defined.",
      "checklist": [
        "윤리기준 준수 보장을 위한 담당자 지정 등 적절한 방안을 마련하였는가?",
        "개발자는 다음 역량을 향상하고 있는가?\n    - 활용 분야 적합성 및 위험성 판단 능력\n    - 산출물과 결정을 해석하는 능력",
        "개발·운영 과정에서 발생하는 손해의 책임 소재를 명확히 하고 있는가?",
        "피해 발생 시 합리적 배상·보상(배상책임보험·유보금 등)을 위한 방안이 준비되어 있는가?"
      ],
      "checklist_en": [
        "Are appropriate measures, including designation of responsible personnel, in place to ensure compliance with ethical standards?",
        "Is the developer improving the following competencies: ability to assess suitability and risk for the application domain; ability to interpret outputs and decisions?",
        "Is the responsibility for damages arising during development and operation clearly identified?",
        "Are plans in place for reasonable compensation (liability insurance, reserve funds, etc.) in the event of harm?"
      ]
    },
    {
      "code": "9",
      "name": "사용자 안전성",
      "name_en": "User Safety",
      "description": "AI 개발·활용 과정에서 잠재적 위험을 방지하고 안전을 확보해야 한다.\n오류 발생 시 사용자가 작동을 제어할 수 있는 기능도 갖추어야 한다.",
      "description_en": "Potential risks must be prevented and safety must be secured during AI development and use. Users must be able to control operation in the event of errors.",
      "checklist": [
        "비정상 동작·예기치 못한 오류 대비 안전조치 기능과 그 한계를 사용자에게 충분히 제공하고 있는가?",
        "감시·중독·과의존 등 인간–AI 상호작용 중 발생 가능한 위험을 사전에 평가하고 완화 노력 중인가?",
        "결과의 안전성을 지속적으로 평가하기 위한 절차(전문가 평가, 사용자 피드백 등)를 마련하였는가?"
      ],
      "checklist_en": [
        "Are safety measure capabilities for abnormal operations and unexpected errors, along with their limitations, sufficiently provided to users?",
        "Are risks that may arise during human–AI interaction, such as surveillance, addiction, or over-dependency, assessed in advance and efforts made to mitigate them?",
        "Are procedures (expert evaluation, user feedback, etc.) in place to continuously evaluate the safety of results?"
      ]
    },
    {
      "code": "10",
      "name": "투명성",
      "name_en": "Transparency",
      "description": "사회적 신뢰 형성을 위해 적절한 수준의 투명성과 설명 가능성을 확보해야 한다.\nAI 기반 제품·서비스 제공 시 활용 내용과 위험 요소를 사전에 고지해야 한다.",
      "description_en": "Appropriate levels of transparency and explainability must be secured to build social trust. Users must be informed in advance about usage details and risk factors when AI-based products and services are provided.",
      "checklist": [
        "AI 알고리즘 기반의 결정이 이루어진다는 사실과 사용자와 AI가 상호작용 중임을 고지하고 있는가?",
        "목적에 맞는 사용을 위해 가이드북·매뉴얼 등 정보를 제공하고 있는가?",
        "데이터 수집 내용, 의사결정 영향 요인 등 사용자의 설명 요청에 응할 수 있는 절차를 마련하였는가?"
      ],
      "checklist_en": [
        "Are users notified that AI algorithm-based decisions are being made and that they are interacting with AI?",
        "Is information such as guidebooks and manuals provided for appropriate use according to the intended purpose?",
        "Are procedures in place to respond to users' requests for explanation regarding data collection contents, factors influencing decisions, etc.?"
      ]
    }
]


def _format_ethics_code(c: dict, lang: str = "ko") -> str:
    if lang == "en":
        name = c.get("name_en", c["name"])
        description = c.get("description_en", c["description"])
        checklist_items = c.get("checklist_en", c["checklist"])
        checklist = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(checklist_items))
        return f"{name}\n\n{description}\n\n[Checklist]\n{checklist}"
    checklist = "\n".join(f"  {i+1}. {item}" for i, item in enumerate(c.get("checklist", [])))
    return f"{c['name']}\n\n{c['description']}\n\n[체크리스트]\n{checklist}"


def _format_ethics_code_brief(c: dict, lang: str = "ko") -> str:
    if lang == "en":
        name = c.get("name_en", c["name"])
        description = c.get("description_en", c["description"])
        return f"{c['code']}. {name}\n{description}"
    return f"{c['code']}. {c['name']}\n{c['description']}"


def _extract_referenced_scenarios(merged_scenarios: str, draft: dict) -> str:
    refs = set()
    for item in draft.get("positives", []) + draft.get("negatives", []):
        ev = item.get("evidence_scenario", "")
        for m in re.findall(r"Scenario#(\d+)", ev):
            refs.add(m)
    if not refs:
        return "(참조 시나리오 없음)"
    results = []
    for num in sorted(refs, key=int):
        pattern = rf"(Scenario#{num}: .+?)(?=\n\nScenario#|\Z)"
        match = re.search(pattern, merged_scenarios, re.DOTALL)
        if match:
            results.append(match.group(1).strip())
    return "\n\n".join(results) if results else "(해당 시나리오 없음)"


def _preprocess_regulation_context(chunks: list[str]) -> str:
    """HTML tag removal + fragment filtering"""
    cleaned = []
    for chunk in chunks:
        text = re.sub(r"<[^>]+>", " ", chunk)
        text = re.sub(r"&\w+;", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or len(text) < 20:
            continue
        cleaned.append(text)
    return "\n".join(cleaned) if cleaned else ""


def _retrieve_regulation_context(run_id: str, code_info: dict) -> str:
    """ethics code 관련 regulation 청크 검색 및 전처리"""
    queries = [code_info["name"]] + code_info.get("checklist", [])[:3]
    # 영어 쿼리도 추가 (bilingual DB 대응)
    if code_info.get("description_en"):
        queries.append(code_info["description_en"][:100])

    all_chunks: list[str] = []
    seen: set[str] = set()
    for q in queries:
        chunks = retrieve_context(run_id, q)
        for c in chunks:
            if c not in seen:
                seen.add(c)
                all_chunks.append(c)

    return _preprocess_regulation_context(all_chunks[:10])


def impact_node(state: AIAState) -> dict:
    run_id = state["run_id"]
    merged_scenarios = state["merged_scenarios"]
    parsed_markdown = state["parsed_markdown"]
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id

    checkpoint = run_dir / "impact_report.json"
    if checkpoint.exists():
        print("  [체크포인트] impact_report.json 존재 → 스킵")
        return {"impact_report": json.loads(checkpoint.read_text(encoding="utf-8"))}

    with cached_markdown(client, parsed_markdown, f"aia_{run_id}_impact", model=FLASH_MODEL) as flash_cache_name:
        # Phase 1a→1b→1c: 코드별로 순차 처리, 10개 코드는 병렬
        # 1a가 끝난 코드는 barrier 없이 즉시 1b→1c로 진행
        print("  [Phase 1a→1b→1c] 코드별 파이프라인 (10개 병렬)...")

        lang = state.get("language", "ko")

        no_reg_fallback = "No relevant regulations found." if lang == "en" else "해당 법규 정보 없음"

        def process_code(code_info: dict, cache_name: str) -> tuple[str, dict]:
            code = code_info["code"]
            name = code_info.get("name_en", code_info["name"]) if lang == "en" else code_info["name"]
            regulation_context = _retrieve_regulation_context(run_id, code_info)
            ethics_definition = _format_ethics_code(code_info, lang=lang)

            # 1a: generate
            generate_prompt = IMPACT_GENERATE_PROMPT(
                code=code,
                name=name,
                ethics_definition=ethics_definition,
                merged_scenarios=merged_scenarios,
                regulation_context=regulation_context if regulation_context else no_reg_fallback,
                lang=lang,
            )
            resp_1a = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=generate_prompt,
                config=types.GenerateContentConfig(
                    cached_content=cache_name,
                    response_mime_type="application/json",
                    response_schema=IMPACT_GENERATE_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_level="high"),
                ),
            )
            draft = json.loads(resp_1a.text)

            # 1b: critique
            referenced_scenarios = _extract_referenced_scenarios(merged_scenarios, draft)
            critique_prompt = GENERIC_CRITIQUE_PROMPT(
                "impact", lang=lang,
                code=code, name=name,
                ethics_definition=ethics_definition,
                draft_impacts=json.dumps(draft, ensure_ascii=False, indent=2),
                referenced_scenarios=referenced_scenarios,
            )
            resp_1b = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=critique_prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="medium"),
                ),
            )
            critique = resp_1b.text

            # 1c: refine generate
            refine_prompt = GENERIC_REFINE_PROMPT(
                "impact", lang=lang,
                code=code, name=name,
                ethics_definition=ethics_definition,
                regulation_context=regulation_context if regulation_context else no_reg_fallback,
                critique=critique,
                draft_impacts=json.dumps(draft, ensure_ascii=False, indent=2),
            )
            resp_1c = call_with_retry(
                client.models.generate_content,
                model=FLASH_MODEL,
                contents=refine_prompt,
                config=types.GenerateContentConfig(
                    cached_content=cache_name,
                    response_mime_type="application/json",
                    response_schema=IMPACT_GENERATE_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_level="medium"),
                ),
            )
            return code, json.loads(resp_1c.text)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_code, c, flash_cache_name): c["code"] for c in ETHICS_CODES}
            refined_by_code: dict[str, dict] = {}
            for future in futures:
                code, result = future.result()
                refined_by_code[code] = result

    # ── Phase 3 + Phase 2a 병렬 실행 ────────────────────────────
    # Phase 3: 어투 통일 + 키워드 중복 제거 (등급 없이) — 메인 스레드
    # Phase 2a: not_found 식별 — 백그라운드 스레드
    print("  [Phase 3+2a] 어투 통일/키워드 정제 + not_found 병렬 시작...")

    code_def_map = {c["code"]: _format_ethics_code(c, lang=lang) for c in ETHICS_CODES}

    def _code_name(c: dict) -> str:
        return c.get("name_en", c["name"]) if lang == "en" else c["name"]

    def run_phase2a() -> dict[str, list]:
        all_codes_with_impacts = json.dumps(
            [
                {
                    "code": c["code"],
                    "name": _code_name(c),
                    "ethics_definition": code_def_map[c["code"]],
                    "current_impacts": refined_by_code.get(c["code"], {}),
                }
                for c in ETHICS_CODES
            ],
            ensure_ascii=False,
            indent=2,
        )
        resp = call_with_retry(
            client.models.generate_content,
            model=FLASH_MODEL,
            contents=IMPACT_NOT_FOUND_PROMPT(
                merged_scenarios=merged_scenarios,
                all_codes_with_impacts=all_codes_with_impacts,
                lang=lang,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IMPACT_NOT_FOUND_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_level="high"),
            ),
        )
        raw = json.loads(resp.text).get("not_found_by_code", [])
        return {entry["code"]: entry.get("items", []) for entry in raw}

    ethics_assessment_ungraded = [
        {
            "code": c["code"],
            "name": _code_name(c),
            "positives": refined_by_code.get(c["code"], {}).get("positives", []),
            "negatives": refined_by_code.get(c["code"], {}).get("negatives", []),
        }
        for c in ETHICS_CODES
    ]

    phase2a_executor = ThreadPoolExecutor(max_workers=1)
    future_2a = phase2a_executor.submit(run_phase2a)

    # Phase 3: 메인 스레드에서 실행 (Phase 2a와 병렬)
    refine_input = json.dumps(
        {"ethics_codes_definitions": ETHICS_CODES, "ethics_assessment": ethics_assessment_ungraded},
        ensure_ascii=False, indent=2,
    )
    refine_resp = call_with_retry(
        client.models.generate_content,
        model=FLASH_MODEL,
        contents=IMPACT_REFINE_PROMPT(ethics_assessment=refine_input, lang=lang),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=REFINE_UNGRADED_SCHEMA,
            thinking_config=types.ThinkingConfig(thinking_level="medium"),
        ),
    )
    refined_assessment = json.loads(refine_resp.text).get(
        "ethics_assessment", ethics_assessment_ungraded
    )
    print("  [Phase 3] 완료 — Phase 2b 즉시 시작 (Phase 2a 병렬 진행 중)")

    # ── Phase 2b: 등급 평가 (refined 결과 기반) ──────────────────
    refined_map = {item["code"]: item for item in refined_assessment}

    grade_tasks: list[tuple] = []
    for c in ETHICS_CODES:
        code = c["code"]
        refined_item = refined_map.get(code, {})
        for item in refined_item.get("positives", []):
            grade_tasks.append((c, "positive", item))
        for item in refined_item.get("negatives", []):
            grade_tasks.append((c, "negative", item))

    total_grade = len(grade_tasks)
    completed_grade = 0
    grade_lock = threading.Lock()

    def grade_one(code_info: dict, impact_type: str, item: dict) -> dict:
        nonlocal completed_grade
        ethics_brief = _format_ethics_code_brief(code_info, lang=lang)
        grade_schema = (
            IMPACT_GRADE_POSITIVE_SCHEMA if impact_type == "positive"
            else IMPACT_GRADE_NEGATIVE_SCHEMA
        )
        prompt = IMPACT_GRADE_PROMPT(
            impact_type,
            code=code_info["code"],
            name=_code_name(code_info),
            keyword=item.get("keyword", ""),
            impact=item.get("impact", ""),
            evidence_scenario=item.get("evidence_scenario", ""),
            ethics_brief=ethics_brief,
            lang=lang,
        )
        response = call_with_retry(
            client.models.generate_content,
            model=LITE_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=grade_schema,
                temperature=0.0,
                thinking_config=types.ThinkingConfig(thinking_level="minimal"),
            ),
        )
        grades = json.loads(response.text)
        result = dict(item)
        result["scale"]      = grades.get("scale", {})
        result["scope"]      = grades.get("scope", {})
        result["likelihood"] = grades.get("likelihood", {})
        if impact_type == "negative":
            result["resolvability"] = grades.get("resolvability", {})

        with grade_lock:
            completed_grade += 1
            cnt = completed_grade
        if cnt % 5 == 0:
            print(f"  [Phase 2b] {cnt}/{total_grade} 완료")
        return result

    max_workers = min(total_grade, 20) if total_grade > 0 else 1
    print(f"  [Phase 2b] 등급 평가: {total_grade}개 항목 (동시 {max_workers})")
    graded_pos: dict[str, list] = {c["code"]: [] for c in ETHICS_CODES}
    graded_neg: dict[str, list] = {c["code"]: [] for c in ETHICS_CODES}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(grade_one, code_info, impact_type, item): (code_info["code"], impact_type, item)
            for code_info, impact_type, item in grade_tasks
        }
        for future in as_completed(futures):
            code, impact_type, original_item = futures[future]
            try:
                graded_item = future.result()
            except Exception as e:
                print(f"  [Phase 2b] 오류 ({code} {impact_type}): {e} — 원본 유지")
                graded_item = dict(original_item)
            if impact_type == "positive":
                graded_pos[code].append(graded_item)
            else:
                graded_neg[code].append(graded_item)
    print(f"  [Phase 2b] 완료 ({total_grade}개)")

    # Phase 2a 결과 수집 (Phase 2b와 병렬로 실행 중이었음)
    not_found_by_code: dict[str, list] = future_2a.result()
    phase2a_executor.shutdown(wait=False)
    print("  [Phase 2a] 완료")

    # ── 최종 조립 ──────────────────────────────────────────────
    final_assessment = [
        {
            "code": c["code"],
            "name": _code_name(c),
            "not_found":  not_found_by_code.get(c["code"], []),
            "positives":  graded_pos[c["code"]],
            "negatives":  graded_neg[c["code"]],
        }
        for c in ETHICS_CODES
    ]

    impact_report = {
        "total_system_report": {
            "report_title": "AI 영향평가 보고서",
            "ethics_assessment": final_assessment,
        }
    }


    (run_dir / "impact_report.json").write_text(
        json.dumps(impact_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("  impact_report.json 저장 완료")

    return {"impact_report": impact_report}
