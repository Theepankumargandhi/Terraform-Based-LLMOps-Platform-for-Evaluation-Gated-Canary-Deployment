from llmops_platform.metrics import compute_groundedness_proxy, compute_keyword_recall


def test_keyword_recall_uses_expected_keywords() -> None:
    recall = compute_keyword_recall(
        "Rollback the deployment to reduce latency and timeouts.",
        ["rollback", "deployment", "database", "latency"],
    )
    assert recall == 0.75


def test_groundedness_proxy_rewards_evidence_overlap() -> None:
    groundedness = compute_groundedness_proxy(
        "Rollback the deployment because logs show timeout errors.",
        ["Recent changes: deployment 2026.03.08-1", "Logs: timeout while calling service"],
    )
    assert groundedness > 0
