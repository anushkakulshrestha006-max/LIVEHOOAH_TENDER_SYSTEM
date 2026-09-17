from llm.router import LLMRouter
from llm.token_guard import TokenGuard

from llm.providers.deepseek_provider import DeepSeekProvider
from llm.providers.gpt_provider import GPTProvider
from llm.providers.laguna_provider import LagunaProvider

from config.llm_config import LLM_CONFIG


def build_llm_router(deepseek_client, openai_client):
    providers = {
        "deepseek": DeepSeekProvider(deepseek_client),
        "gpt": GPTProvider(openai_client),
        "laguna": LagunaProvider(),
    }

    return LLMRouter(
        providers=providers,
        fallback_chain=LLM_CONFIG["fallback_chain"],
        token_guard=TokenGuard(LLM_CONFIG["token_limits"]["max_tokens"])
    )