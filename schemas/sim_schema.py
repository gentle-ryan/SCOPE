PASSIVE_TURN1_SCHEMA = {
  "type": "object",
  "properties": {
    "agents": {
      "type": "array",
      "minItems": 0,
      "maxItems": 3,
      "items": {
        "type": "object",
        "properties": {
          "agent": {
            "type": "string",
            "description": "이벤트로 인해 영향을 받는 에이전트 (피영향자)"
          },
          "effect": {
            "type": "string",
            "description": "해당 에이전트의 상태 변화 (1~2문장)"
          }
        },
        "required": ["agent", "effect"]
      }
    }
  },
  "required": ["agents"]
}

PASSIVE_TURN23_SCHEMA = {
  "type": "object",
  "properties": {
    "selected_agent": {
      "type": "string",
      "description": "현재 단계에서 영향을 받는 에이전트"
    },
    "effect": {
      "type": "object",
      "properties": {
        "impacted_agent": {
          "type": "string"
        },
        "effect": {
          "type": "string"
        }
      },
      "required": ["impacted_agent", "effect"]
    }
  },
  "required": ["selected_agent", "effect"]
}

ACTIVE_BATCH_SCHEMA = {
  "type": "object",
  "properties": {
    "actor": {
      "type": "string",
      "description": "행동을 수행하는 에이전트"
    },
    "action": {
      "type": "string",
      "description": "단일 행동"
    }
  },
  "required": ["actor", "action"]
}

VALIDATOR_SCHEMA = {
  "type": "object",
  "properties": {
    "should_terminate": {
      "type": "boolean",
      "description": "이 branch를 종료해야 하는가"
    },
    "termination_reason": {
      "type": "string",
      "enum": ["none", "infeasible", "acausal", "concluded", "duplicate"],
      "description": "종료 사유"
    },
    "reason": {
      "type": "string",
      "maxLength": 100,
      "description": "판단 근거 (1~2문장)"
    }
  },
  "required": ["should_terminate", "termination_reason", "reason"]
}

SCENARIO_VERIFY_RAG_SCHEMA = {
    "type": "object",
    "properties": {
        "is_valid": {
            "type": "boolean",
            "description": "시나리오 유효성 여부"
        },
        "reason": {
            "type": "string",
            "minLength": 10,
            "description": "판단 근거 (간결하게)"
        },
        "evidence": {
            "type": "array",
            "description": "RAG context에서 근거로 사용된 문장 또는 요약",
            "items": {
                "type": "string"
            }
        }
    },
    "required": ["is_valid", "reason"]
}
