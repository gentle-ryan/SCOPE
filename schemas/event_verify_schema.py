# Step 4: 이벤트 생성 스키마
EVENT_SCHEMA = {
    "type": "array",
    "minItems": 1,
    "items": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "integer",
                "description": "이벤트 고유 ID (정수, 중복 금지)"
            },
            "workflow_id": {
                "type": "integer",
                "description": "속한 워크플로우 단계 ID"
            },
            "entity_name": {
                "type": "string",
                "description": "Agent 또는 Object 이름"
            },
            "property": {
                "type": "string",
                "description": "적용된 안전공학 속성 (정의된 용어 그대로)"
            },
            "event_description": {
                "type": "string",
                "minLength": 20,
                "description": "1~2문장의 사건 설명 (관찰 가능한 변화 중심)"
            }
        },
        "required": [
            "event_id",
            "workflow_id",
            "entity_name",
            "property",
            "event_description"
        ],
    }
}

# Step 4: 이벤트 RAG 검증 스키마 (이벤트 1개씩 개별 검증)
EVENT_VERIFY_RAG_SCHEMA = {
    "type": "object",
    "properties": {
        "event_id": {
            "type": "integer",
            "description": "검증 대상 이벤트 ID"
        },
        "is_valid": {
            "type": "boolean",
            "description": "이벤트 유효성 여부"
        },
        "reason": {
            "type": "string",
            "maxLength": 40,
            "description": "최종 판단 요약"
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "RAG context에서 event를 뒷받침하는 핵심 문장들"
        },
        "failed_criteria": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "no_evidence",
                    "invalid_workflow",
                    "invalid_actor",
                    "property_mismatch",
                    "no_impact",
                    "duplicate_event",
                    "system_impossible"
                ]
            },
            "description": "검증 실패한 기준 목록 (is_valid=false일 때 필수)"
        },
        "impact_detected": {
            "type": "boolean",
            "description": "event가 실제로 downstream 영향 발생 여부"
        }
    },
    "required": [
        "event_id",
        "is_valid",
        "reason",
        "impact_detected"
    ]
}

EVENT_LLM_DEDUP_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "representative": {
                "type": "string",
                "description": "고유 event를 대표하는 가장 명확한 description"
            }
        },
        "required": ["representative"]
    }
}