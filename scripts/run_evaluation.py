from __future__ import annotations

import argparse
import json
from pathlib import Path
from sys import exit as sys_exit

from llmops_platform.evaluation import compare_releases
from llmops_platform.service import LLMOpsService
from llmops_platform.settings import load_settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the offline release gate.")
    parser.add_argument("--stable", type=Path, required=True, help="Path to stable release YAML.")
    parser.add_argument(
        "--candidate", type=Path, required=True, help="Path to candidate release YAML."
    )
    parser.add_argument("--dataset", type=Path, required=True, help="Path to eval JSONL dataset.")
    parser.add_argument("--output", type=Path, required=True, help="Path to output report JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings(
        stable_release_path=args.stable,
        candidate_release_path=args.candidate,
    )
    service = LLMOpsService(settings)
    report = compare_releases(service=service, dataset_path=args.dataset)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(json.dumps(report.model_dump(), indent=2))

    if not report.candidate_passed_gate:
        sys_exit(1)


if __name__ == "__main__":
    main()
