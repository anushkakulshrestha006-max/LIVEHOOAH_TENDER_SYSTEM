def fallback_response(task: str):
    if task == "discovery":
        return {"opportunities": []}

    if task == "scoring":
        return {"score": 0}

    return {
        "status": "degraded_mode",
        "message": "LLM unavailable"
    }