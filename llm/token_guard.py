class TokenGuard:
    def __init__(self, max_tokens=8000):
        self.max_tokens = max_tokens

    def estimate(self, text: str):
        return len(text) // 4

    def enforce(self, text: str):
        if self.estimate(text) <= self.max_tokens:
            return text

        return text[: self.max_tokens * 4]
    