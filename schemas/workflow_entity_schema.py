_WORKFLOW_ITEMS_KO = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "description": "워크플로우 단계 고유 식별자 (1~5 순차)",
        },
        "type": {
            "type": "string",
            "enum": [
                "데이터 수집·전처리·검증",
                "모델 개발·학습",
                "결과 생성·예측",
                "사용 및 연계 업무",
                "데이터·모델 관리 및 모니터링",
            ],
        },
        "description": {"type": "string", "minLength": 500},
    },
    "required": ["id", "type", "description"],
}

_WORKFLOW_ITEMS_EN = {
    "type": "object",
    "properties": {
        "id": {
            "type": "integer",
            "description": "Workflow stage unique identifier (sequential 1–5)",
        },
        "type": {
            "type": "string",
            "enum": [
                "Data Collection, Preprocessing & Validation",
                "Model Development & Training",
                "Result Generation & Prediction",
                "Deployment & Integration",
                "Data, Model Management & Monitoring",
            ],
        },
        "description": {"type": "string", "minLength": 500},
    },
    "required": ["id", "type", "description"],
}


def get_workflow_only_schema(lang: str = "ko") -> dict:
    items = _WORKFLOW_ITEMS_EN if lang == "en" else _WORKFLOW_ITEMS_KO
    return {
        "type": "object",
        "properties": {
            "workflows": {
                "type": "array",
                "minItems": 5,
                "maxItems": 5,
                "items": items,
            }
        },
        "required": ["workflows"],
    }


WORKFLOW_ONLY_SCHEMA = get_workflow_only_schema("ko")

ENTITY_VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "is_valid": {
            "type": "boolean",
            "description": "문서 내 실존 여부 + 워크플로우 적합성 여부",
        },
        "duplicate_of": {
            "type": "string",
            "nullable": True,
            "description": "동일 단계 내 중복 entity 이름. 중복 아니면 null",
        },
        "reason": {
            "type": "string",
            "maxLength": 150,
            "description": "판단 근거 1~2문장",
        },
    },
    "required": ["is_valid", "reason"],
}

ENTITY_EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "agents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["name", "role"],
            },
        },
        "objects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                },
                "required": ["name", "role"],
            },
        },
    },
    "required": ["agents", "objects"],
}
