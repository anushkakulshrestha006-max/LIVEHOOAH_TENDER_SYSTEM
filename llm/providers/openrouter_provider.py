from .base import BaseProvider

class OpenRouterProvider(BaseProvider):
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def call(self, prompt: str):
        return self.client.chat_completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )