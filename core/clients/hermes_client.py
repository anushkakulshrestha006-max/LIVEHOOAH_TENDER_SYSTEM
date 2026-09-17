import subprocess
import time

from core.parsers.hermes_parser import parse_strict_json


MODELS = [
    "deepseek/deepseek-v4-flash",
    "poolside/laguna-m.1"
]

MAX_PROMPT_LENGTH = 4000
TIMEOUT_SECONDS = 180
MAX_RETRIES = 2


class HermesClient:
    """
    Production-safe Hermes execution engine.
    """

    def run(self, prompt: str) -> dict:

        strict_prompt = f"""
Return ONLY valid JSON.

{{
  "opportunities": [
    {{
      "title": "",
      "location": "",
      "value": "",
      "deadline": "",
      "source": "",
      "source_url": ""
    }}
  ]
}}

TASK:
{prompt}
"""

        # Prevent huge prompt growth
        if len(strict_prompt) > MAX_PROMPT_LENGTH:
            print(
                f"\n⚠️ Prompt exceeded {MAX_PROMPT_LENGTH} chars. Truncating."
            )
            strict_prompt = strict_prompt[:MAX_PROMPT_LENGTH]

        last_error = ""

        for model in MODELS:

            print(f"\n🔹 Trying model: {model}")

            for attempt in range(MAX_RETRIES):

                cmd = [
                    "wsl",
                    "bash",
                    "-lc",
                    (
                        "hermes "
                        "--ignore-rules "
                        "--ignore-user-config "
                        f"-m {model} "
                        f"-z '{strict_prompt}'"
                    )
                ]

                try:

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=TIMEOUT_SECONDS
                    )

                except subprocess.TimeoutExpired:

                    print(
                        f"\n⏱ Timeout after "
                        f"{TIMEOUT_SECONDS}s using {model}"
                    )

                    last_error = (
                        f"Timeout using {model}"
                    )

                    continue

                output = result.stdout.strip()
                error = result.stderr.strip()

                print("\n========== HERMES STDOUT ==========")
                print(output[:3000])

                print("\n========== HERMES STDERR ==========")
                print(error)

                print("\n========== RETURN CODE ==========")
                print(result.returncode)

                provider_failure = any([
                    "HTTP 429" in output,
                    "HTTP 429" in error,
                    "HTTP 402" in output,
                    "HTTP 402" in error,
                    "Provider returned error" in output,
                    "Provider returned error" in error,
                ])

                if provider_failure:

                    print(
                        f"\n⚠️ Provider failure detected "
                        f"({model})"
                    )

                    last_error = (
                        output if output else error
                    )

                    break

                if not output:

                    error_lower = error.lower()

                    permanent_failure = any([
                        "context window" in error_lower,
                        "below the minimum 64,000 required" in error_lower,
                        "max_tokens" in error_lower,
                        "context length" in error_lower,
                        "valueerror" in error_lower,
                    ])

                    if permanent_failure:

                        print(
                            f"\n❌ Permanent Hermes failure detected ({model})"
                        )

                        print(
                            "Skipping this model immediately (no retries)."
                        )

                        last_error = error

                        break

                    print(
                        f"\n⚠️ Empty stdout from {model}"
                    )

                    last_error = f"Empty stdout from {model}"

                    wait_time = 15 * (attempt + 1)

                    print(
                        f"Retrying in {wait_time}s..."
                    )

                    time.sleep(wait_time)

                    continue

                try:

                    parsed = parse_strict_json(output)

                    parsed["meta"] = {
                        "model": model,
                        "prompt_preview": prompt[:80],
                        "raw_length": len(output),
                        "status": (
                            "ok"
                            if parsed.get("opportunities")
                            else "empty"
                        ),
                        "return_code": result.returncode
                    }

                    return parsed

                except Exception as e:

                    print(
                        "\n⚠️ JSON parsing failed:"
                    )

                    print(str(e))

                    last_error = str(e)

                    wait_time = 10 * (attempt + 1)

                    time.sleep(wait_time)

            print(
                f"\n❌ Model failed: {model}"
            )

        print("\n🚨 ALL MODELS FAILED")
        print(last_error)

        return {
            "opportunities": [],
            "meta": {
                "model": "fallback",
                "status": "failed",
                "error": last_error
            }
        }

    def run_json(self, prompt: str) -> dict:
        return self.run(prompt)


def call_hermes(prompt: str) -> dict:
    return HermesClient().run(prompt)