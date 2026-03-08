from __future__ import annotations

import uvicorn

from llmops_platform.api import create_app
from llmops_platform.settings import load_settings

app = create_app()


def run() -> None:
    settings = load_settings()
    uvicorn.run("llmops_platform.main:app", host="0.0.0.0", port=settings.app_port, reload=False)


if __name__ == "__main__":
    run()
