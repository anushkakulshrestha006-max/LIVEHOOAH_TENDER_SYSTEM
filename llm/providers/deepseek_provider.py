from .base import BaseProvider

class DeepSeekProvider(BaseProvider):
    def __init__(self, client):
        self.client = client

    def call(self, prompt: str):
        return self.client.generate(prompt)