LLM_CONFIG = {
    "providers": {
        "deepseek": {
            "type": "openrouter",
            "model": "deepseek-chat"
        },
        "gpt": {
            "type": "openai",
            "model": "gpt-4o-mini"
        },
        "laguna": {
            "type": "local",
            "model": "laguna-m1"
        }
    },

    "fallback_chain": [
        "deepseek",
        "gpt",
        "laguna",
        "rule_based"
    ],

    "token_limits": {
        "max_tokens": 8000
    }
}