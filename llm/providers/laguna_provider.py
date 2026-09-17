from .base import BaseProvider

class LagunaProvider(BaseProvider):
    def call(self, prompt: str):
        # fallback lightweight logic
        return "[]"