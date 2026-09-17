from llm.token_guard import TokenGuard

class LLMRouter:
    def __init__(self, providers, fallback_chain, token_guard):
        self.providers = providers
        self.fallback_chain = fallback_chain
        self.token_guard = token_guard

    def generate(self, prompt: str, task="default"):
        prompt = self.token_guard.enforce(prompt)

        for name in self.fallback_chain:
            if name not in self.providers:
                continue

            provider = self.providers[name]

            try:
                response = provider.call(prompt)

                if self._valid(response):
                    return self._normalize(response)

            except Exception:
                continue

        return self._degraded(task)

    def _valid(self, response):
        return response is not None and str(response).strip() != ""

    def _normalize(self, response):
        if hasattr(response, "content"):
            return response.content
        return str(response)

    def _degraded(self, task):
        return {
            "status": "degraded_mode",
            "task": task,
            "opportunities": []
        }