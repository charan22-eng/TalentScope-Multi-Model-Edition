"""JSON schemas for structured LLM verdict output.

Inlined cited-item schema (do not rely on $ref, as some local runtimes fail to resolve $ref).
"""

CITED_SCHEMA = {
    "type": "object",
    "required": ["text", "fact_ids"],
    "properties": {
        "text": {"type": "string", "maxLength": 280},
        "fact_ids": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string"},
        },
    },
}

VERDICT_SCHEMA = {
    "type": "object",
    "required": ["headline", "recommendation", "claims", "tradeoffs", "caveats"],
    "properties": {
        "headline": {"type": "string", "maxLength": 200},
        "recommendation": {
            "type": "object",
            "required": ["model_key", "confidence", "agreement"],
            "properties": {
                "model_key": {"type": "string"},
                "confidence": {"enum": ["clear", "marginal", "none"]},
                "agreement": {"enum": ["agree", "disagree"]},
            },
        },
        "claims": {
            "type": "array",
            "minItems": 2,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": ["text", "fact_ids"],
                "properties": {
                    "text": {"type": "string", "maxLength": 280},
                    "fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "tradeoffs": {
            "type": "array",
            "maxItems": 4,
            "items": {
                "type": "object",
                "required": ["text", "fact_ids"],
                "properties": {
                    "text": {"type": "string", "maxLength": 280},
                    "fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "caveats": {
            "type": "array",
            "minItems": 1,
            "maxItems": 4,
            "items": {
                "type": "object",
                "required": ["text", "fact_ids"],
                "properties": {
                    "text": {"type": "string", "maxLength": 280},
                    "fact_ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
            },
        },
    },
}
