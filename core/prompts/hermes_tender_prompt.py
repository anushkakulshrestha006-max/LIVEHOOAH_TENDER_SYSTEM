def build_prompt(user_input: str):
    return f"""
You are a Tender Intelligence Engine.

Return ONLY valid JSON.

Schema:
{{
  "task": "tender_discovery",
  "opportunities": [],
  "meta": {{
    "execution_mode": "hermes_cli"
  }}
}}

Input:
{user_input}

Return ONLY JSON.
"""