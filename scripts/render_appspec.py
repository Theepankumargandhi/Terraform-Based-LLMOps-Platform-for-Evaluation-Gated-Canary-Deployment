from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a CodeDeploy AppSpec for ECS.")
    parser.add_argument("--task-definition-arn", required=True)
    parser.add_argument("--container-name", required=True)
    parser.add_argument("--container-port", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = {
        "version": 1,
        "Resources": [
            {
                "TargetService": {
                    "Type": "AWS::ECS::Service",
                    "Properties": {
                        "TaskDefinition": args.task_definition_arn,
                        "LoadBalancerInfo": {
                            "ContainerName": args.container_name,
                            "ContainerPort": args.container_port,
                        },
                    },
                }
            }
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
