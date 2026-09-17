from tests.helpers.test_llm_fakes import build_fake_router


def test_router_fallback():
    router = build_fake_router()

    result = router.generate("test prompt", task="discovery")

    assert result is not None
    assert result == "fallback success"