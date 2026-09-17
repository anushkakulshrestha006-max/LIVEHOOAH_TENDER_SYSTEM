from llm.router import LLMRouter
from llm.token_guard import TokenGuard


class FakeProvider:
    def __init__(self, should_fail=False, response="OK"):
        self.should_fail = should_fail
        self.response = response

    def call(self, prompt: str):
        if self.should_fail:
            raise Exception("Fake provider failure")

        return self.response
def build_fake_router():
    providers = {
        "primary": FakeProvider(should_fail=True),
        "backup": FakeProvider(should_fail=False, response="fallback success"),
    }

    return LLMRouter(
        providers=providers,
        fallback_chain=["primary", "backup"],
        token_guard=TokenGuard(max_tokens=8000)
    )