from pathlib import Path

from llmops_platform.releases import load_release_config


def test_load_release_config() -> None:
    config = load_release_config(Path("configs/releases/stable.yaml"))
    assert config.name == "stable"
    assert config.evaluation.min_keyword_recall >= 0.7
