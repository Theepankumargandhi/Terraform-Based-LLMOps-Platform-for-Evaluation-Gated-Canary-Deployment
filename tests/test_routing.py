from llmops_platform.routing import CanaryRouter


def test_canary_router_is_deterministic_for_request_id() -> None:
    router = CanaryRouter(candidate_weight=25)
    first = router.choose_release("request-123")
    second = router.choose_release("request-123")
    assert first == second


def test_canary_router_respects_override() -> None:
    router = CanaryRouter(candidate_weight=0)
    assert router.choose_release("request-123", preferred_release="candidate") == "candidate"
