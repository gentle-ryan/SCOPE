STEP3_SCHEMA = {
    "type": "object",
    "properties": {
        "detailed_role": {
            "type": "string",
            "description": "엔티티의 상세 역할 서술",
            "minLength": 50,
        }
    },
    "required": ["detailed_role"],
}

STAKEHOLDER_SCHEMA = {
    "type": "object",
    "properties": {
        "stakeholder_agents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "이해관계자 명칭 (역할·직무 기반, 실명 금지)",
                    },
                    "role": {
                        "type": "string",
                        "description": "AI 시스템과의 관계 (1~2문장)",
                    },
                    "detailed_role": {
                        "type": "string",
                        "minLength": 100,
                        "description": "AI 시스템으로부터 받는 영향 또는 상호작용 상세 서술 (최소 5문장)",
                    },
                    "impact_type": {
                        "type": "string",
                        "enum": ["primary", "secondary", "unintended"],
                        "description": "영향 유형",
                    },
                },
                "required": ["name", "role", "detailed_role", "impact_type"],
            },
        }
    },
    "required": ["stakeholder_agents"],
}
