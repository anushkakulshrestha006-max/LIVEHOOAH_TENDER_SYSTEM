def safe_fail(error_msg: str):
    return {
        "status": "failed_safe_mode",
        "error": error_msg,
        "opportunities": []
    }