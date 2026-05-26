SCALE_CHECKLIST_SCHEMA = {
    "type": "object",
    "properties": {
        "life_death_risk": {"type": "boolean"},
        "irreversible_harm": {"type": "boolean"},
        "democratic_damage": {"type": "boolean"},
        "dignity_autonomy_safety": {"type": "boolean"},
        "legal_trust_damage": {"type": "boolean"},
        "privacy_structural": {"type": "boolean"},
        "recurring": {"type": "boolean"}
    }
}

POSITIVE_SCALE_CHECKLIST_SCHEMA = {
    "type": "object",
    "properties": {
        "quality_of_life": {"type": "boolean"},
        "rights_strengthened": {"type": "boolean"},
        "social_trust": {"type": "boolean"},
        "recurring_positive": {"type": "boolean"},
        "decision_safety": {"type": "boolean"}
    }
}

# Phase 1: impact 생성 전용 (등급 필드 없음)
_IMPACT_ITEM_GENERATE = {
    "type": "object",
    "properties": {
        "keyword": {"type": "string"},
        "evidence_scenario": {"type": "string"},
        "impact": {"type": "string"},
        "affected_parties": {
            "type": "object",
            "properties": {
                "direct": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                "indirect": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                "unintended": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
            },
        },
    },
    "required": ["keyword", "evidence_scenario", "impact", "affected_parties"],
}

IMPACT_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {"type": "string"},
        "name": {"type": "string"},
        "positives": {"type": "array", "items": _IMPACT_ITEM_GENERATE},
        "negatives": {"type": "array", "items": _IMPACT_ITEM_GENERATE},
    },
    "required": ["code", "name", "positives", "negatives"],
}

# Phase 2b: 단일 impact 등급 평가
_GRADE_REASON = {"type": "string", "maxLength": 50}

_GRADE_FIELD = {
    "type": "object",
    "properties": {"grade": {"type": "string"}, "reason": _GRADE_REASON},
    "required": ["grade", "reason"],
}

IMPACT_GRADE_POSITIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "scale":      _GRADE_FIELD,
        "scope":      _GRADE_FIELD,
        "likelihood": _GRADE_FIELD,
    },
    "required": ["scale", "scope", "likelihood"],
}

IMPACT_GRADE_NEGATIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "scale":         _GRADE_FIELD,
        "scope":         _GRADE_FIELD,
        "likelihood":    _GRADE_FIELD,
        "resolvability": _GRADE_FIELD,
    },
    "required": ["scale", "scope", "likelihood", "resolvability"],
}

# Phase 2a: not_found 전용
_NOT_FOUND_ITEM = {
    "type": "object",
    "properties": {
        "item":           {"type": "string"},
        "description":    {"type": "string"},
        "recommendation": {"type": "string"},
    },
    "required": ["item", "description", "recommendation"],
}

IMPACT_NOT_FOUND_SCHEMA = {
    "type": "object",
    "properties": {
        "not_found_by_code": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code":  {"type": "string"},
                    "items": {"type": "array", "items": _NOT_FOUND_ITEM},
                },
                "required": ["code", "items"],
            },
        }
    },
    "required": ["not_found_by_code"],
}

_UNGRADED_ITEM = {
    "type": "object",
    "properties": {
        "keyword": {"type": "string"},
        "evidence_scenario": {"type": "string"},
        "impact": {"type": "string"},
        "affected_parties": {
            "type": "object",
            "properties": {
                "direct":     {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                "indirect":   {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                "unintended": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
            },
        },
    },
    "required": ["keyword", "evidence_scenario", "impact", "affected_parties"],
}

REFINE_UNGRADED_SCHEMA = {
    "type": "object",
    "properties": {
        "ethics_assessment": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code":      {"type": "string"},
                    "name":      {"type": "string"},
                    "positives": {"type": "array", "items": _UNGRADED_ITEM},
                    "negatives": {"type": "array", "items": _UNGRADED_ITEM},
                },
                "required": ["code", "name", "positives", "negatives"],
            },
        }
    },
    "required": ["ethics_assessment"],
}

REFINE_SCHEMA = {
    "type": "object",
    "properties": {
        "ethics_assessment": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "name": {"type": "string"},
                    "not_found": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {"type": "string"},
                                "description": {"type": "string"},
                                "recommendation": {"type": "string"}
                            },
                            "required": ["item", "description", "recommendation"]
                        }
                    },
                    "positives": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword": {"type": "string"},
                                "evidence_scenario": {"type": "string"},
                                "impact": {"type": "string"},
                                "affected_parties": {
                                    "type": "object",
                                    "properties": {
                                        "direct": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                                        "indirect": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                                        "unintended": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}}
                                    }
                                },
                                "scale": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]},
                                "scope": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]},
                                "likelihood": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]}
                            },
                            "required": ["keyword", "impact", "evidence_scenario", "affected_parties", "scale", "scope", "likelihood"]
                        }
                    },
                    "negatives": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "keyword": {"type": "string"},
                                "evidence_scenario": {"type": "string"},
                                "impact": {"type": "string"},
                                "affected_parties": {
                                    "type": "object",
                                    "properties": {
                                        "direct": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                                        "indirect": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}},
                                        "unintended": {"type": "object", "properties": {"target": {"type": "string"}, "impact": {"type": "string"}}}
                                    }
                                },
                                "scale": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]},
                                "scope": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]},
                                "likelihood": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]},
                                "resolvability": {"type": "object", "properties": {"grade": {"type": "string"}, "reason": {"type": "string"}}, "required": ["grade", "reason"]}
                            },
                            "required": ["keyword", "impact", "evidence_scenario", "affected_parties", "scale", "scope", "likelihood", "resolvability"]
                        }
                    }
                },
                "required": ["code", "name", "positives", "negatives"]
            }
        }
    },
    "required": ["ethics_assessment"]
}


AFFECTED_SCHEMA = {
    "type": "object",
    "properties": {
        "direct": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "impact": {"type": "string"}
            }
        },
        "indirect": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "impact": {"type": "string"}
            }
        },
        "unintended": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "impact": {"type": "string"}
            }
        }
    }
}

STEP6_SCHEMA = {
    "type": "object",
    "properties": {
        "total_system_report": {
            "type": "object",
            "properties": {
                "report_title": {"type": "string"},
                "ethics_assessment": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "name": {"type": "string"},

                            "not_found": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "item": {"type": "string"},
                                        "description": {"type": "string"},
                                        "recommendation": {"type": "string"}
                                    },
                                    "required": ["item", "description", "recommendation"]
                                }
                            },

                            "positives": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "keyword": {"type": "string"},
                                        "evidence_scenario": {"type": "string"},
                                        "impact": {"type": "string"},
                                        "affected_parties": AFFECTED_SCHEMA,
                                        "scale": {
                                            "type": "object",
                                            "properties": {
                                                "checklist": POSITIVE_SCALE_CHECKLIST_SCHEMA,
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        },
                                        "scope": {
                                            "type": "object",
                                            "properties": {
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        },
                                        "likelihood": {
                                            "type": "object",
                                            "properties": {
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        }
                                    },
                                    "required": ["keyword", "impact", "evidence_scenario", "affected_parties", "scale", "scope", "likelihood"]
                                }
                            },

                            "negatives": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "keyword": {"type": "string"},
                                        "evidence_scenario": {"type": "string"},
                                        "impact": {"type": "string"},
                                        "affected_parties": AFFECTED_SCHEMA,
                                        "scale": {
                                            "type": "object",
                                            "properties": {
                                                "checklist": SCALE_CHECKLIST_SCHEMA,
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        },
                                        "scope": {
                                            "type": "object",
                                            "properties": {
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        },
                                        "likelihood": {
                                            "type": "object",
                                            "properties": {
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        },
                                        "resolvability": {
                                            "type": "object",
                                            "properties": {
                                                "grade": {"type": "string"},
                                                "reason": {"type": "string"}
                                            },
                                            "required": ["grade", "reason"]
                                        }
                                    },
                                    "required": ["keyword", "impact", "evidence_scenario", "affected_parties", "scale", "scope", "likelihood", "resolvability"]
                                }
                            }
                        },
                        "required": ["code", "name", "positives", "negatives"]
                    }
                }
            },
            "required": ["report_title", "ethics_assessment"]
        }
    },
    "required": ["total_system_report"]
}
