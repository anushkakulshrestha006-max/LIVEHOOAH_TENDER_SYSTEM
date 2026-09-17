from .base import BaseProvider

class GPTProvider(BaseProvider):
    def __init__(self, client):
        self.client = client

    def call(self, prompt: str):
        return self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        ).choices[0].message.content