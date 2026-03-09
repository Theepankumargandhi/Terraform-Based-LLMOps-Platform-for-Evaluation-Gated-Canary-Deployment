from __future__ import annotations

import asyncio
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from llmops_platform.service import LLMOpsService
from llmops_platform.settings import load_settings

DEFAULT_REMOTE_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8080")

SAMPLE_INCIDENTS: dict[str, dict[str, Any]] = {
    "Payments Latency Spike": {
        "question": "What is the likely root cause and safest next action?",
        "context": {
            "service": "payments-api",
            "severity": "high",
            "summary": "Latency spiked after a deployment and checkout errors increased.",
            "recent_changes": [
                "Deployed release 2026.03.08-1",
                "Raised outbound retry budget from 2 to 5",
            ],
            "logs": [
                "timeout while calling inventory-service",
                "retry budget exhausted",
                "upstream gateway returned 504 for /checkout",
            ],
            "metrics": {
                "cpu_utilization": 94,
                "p95_latency_ms": 2200,
                "error_rate": 6.4,
            },
            "runbook_excerpt": (
                "If latency spikes after a deploy, rollback first and validate downstream "
                "saturation before tuning retries."
            ),
        },
    },
    "Database Connection Exhaustion": {
        "question": "What evidence points to the immediate cause and what should the operator do?",
        "context": {
            "service": "orders-worker",
            "severity": "critical",
            "summary": "Background jobs are backing up and the service stopped acknowledging queue items.",
            "recent_changes": [
                "Enabled a new analytics enrichment step",
                "Queue consumer concurrency raised from 8 to 20",
            ],
            "logs": [
                "psycopg2.OperationalError: remaining connection slots are reserved",
                "job visibility timeout exceeded for order-81274",
            ],
            "metrics": {
                "db_connections_used": 99,
                "queue_backlog": 1840,
                "worker_cpu_utilization": 61,
            },
            "runbook_excerpt": (
                "If connection saturation occurs, scale down consumers or disable the last "
                "released feature before restarting workers."
            ),
        },
    },
    "Kafka Consumer Lag": {
        "question": "Summarize the probable root cause, evidence, and next checks.",
        "context": {
            "service": "fraud-detector",
            "severity": "medium",
            "summary": "Fraud scoring is delayed and downstream dashboards are stale.",
            "recent_changes": [
                "New fraud model config published",
                "Kafka broker 3 restarted for maintenance",
            ],
            "logs": [
                "consumer lag breached threshold on partition 7",
                "rebalance in progress for consumer group fraud-detector-v2",
            ],
            "metrics": {
                "consumer_lag": 125000,
                "messages_per_second": 4800,
                "broker_disk_utilization": 88,
            },
            "runbook_excerpt": (
                "If lag rises after a broker event, confirm partition leadership stability and "
                "avoid scaling before consumer rebalances settle."
            ),
        },
    },
}


def apply_page_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --demo-bg: #07111f;
                --demo-panel: rgba(15, 23, 42, 0.78);
                --demo-panel-border: rgba(148, 163, 184, 0.14);
                --demo-text: #e2e8f0;
                --demo-muted: #94a3b8;
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(16, 185, 129, 0.16), transparent 24%),
                    radial-gradient(circle at top right, rgba(14, 165, 233, 0.18), transparent 20%),
                    linear-gradient(180deg, #08101d 0%, #0b1322 55%, #07111f 100%);
                color: var(--demo-text);
            }
            [data-testid="stAppViewContainer"] {
                background: transparent;
            }
            [data-testid="stMainBlockContainer"] {
                background: transparent;
            }
            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(11, 19, 34, 0.98), rgba(15, 23, 42, 0.96));
                border-right: 1px solid rgba(148, 163, 184, 0.12);
            }
            [data-testid="stHeader"] {
                background: rgba(7, 17, 31, 0.82);
            }
            h1, h2, h3, label, p, li, span, div {
                color: inherit;
            }
            .stMarkdown, .stCaption, .stSelectbox label, .stTextInput label, .stTextArea label {
                color: var(--demo-text);
            }
            [data-testid="stForm"] {
                background: rgba(15, 23, 42, 0.3);
                border: 1px solid var(--demo-panel-border);
                border-radius: 18px;
                padding: 1rem 1rem 0.2rem 1rem;
            }
            [data-testid="stMetric"] {
                background: var(--demo-panel);
                border: 1px solid var(--demo-panel-border);
                border-radius: 16px;
                padding: 0.8rem 1rem;
            }
            [data-testid="stExpander"] {
                background: rgba(15, 23, 42, 0.42);
                border: 1px solid var(--demo-panel-border);
                border-radius: 16px;
            }
            .stAlert {
                border-radius: 14px;
            }
            .demo-hero {
                padding: 1.2rem 1.4rem;
                border-radius: 18px;
                background: linear-gradient(135deg, #0f172a, #164e63);
                color: #f8fafc;
                border: 1px solid rgba(255, 255, 255, 0.08);
                margin-bottom: 1rem;
            }
            .demo-note {
                padding: 0.85rem 1rem;
                border-radius: 14px;
                background: rgba(15, 23, 42, 0.46);
                border: 1px solid rgba(148, 163, 184, 0.12);
                color: var(--demo-muted);
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def ensure_default_state() -> None:
    if "question" in st.session_state:
        return
    load_sample_into_state("Payments Latency Spike")


def load_sample_into_state(sample_name: str) -> None:
    sample = SAMPLE_INCIDENTS[sample_name]
    context = sample["context"]
    st.session_state.question = sample["question"]
    st.session_state.service_name = context["service"]
    st.session_state.severity = context["severity"]
    st.session_state.summary = context["summary"]
    st.session_state.recent_changes = "\n".join(context["recent_changes"])
    st.session_state.logs = "\n".join(context["logs"])
    st.session_state.metrics_json = json.dumps(context["metrics"], indent=2)
    st.session_state.runbook_excerpt = context["runbook_excerpt"]


def run_async(coro: Any) -> Any:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@st.cache_resource(show_spinner=False)
def get_local_service() -> LLMOpsService:
    settings = load_settings(environment="streamlit-demo")
    return LLMOpsService(settings)


def split_lines(value: str) -> list[str]:
    return [line.strip() for line in value.splitlines() if line.strip()]


def parse_metrics(raw_metrics: str) -> dict[str, float]:
    if not raw_metrics.strip():
        return {}

    try:
        parsed = json.loads(raw_metrics)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Metrics must be valid JSON: {exc.msg}.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("Metrics JSON must be an object with numeric values.")

    metrics: dict[str, float] = {}
    for key, value in parsed.items():
        if not isinstance(key, str):
            raise ValueError("Metrics keys must be strings.")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Metric '{key}' must be numeric.")
        metrics[key] = float(value)
    return metrics


def build_payload(preferred_release: str) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "question": st.session_state.question.strip(),
        "context": {
            "service": st.session_state.service_name.strip(),
            "severity": st.session_state.severity,
            "summary": st.session_state.summary.strip(),
            "recent_changes": split_lines(st.session_state.recent_changes),
            "logs": split_lines(st.session_state.logs),
            "metrics": parse_metrics(st.session_state.metrics_json),
            "runbook_excerpt": st.session_state.runbook_excerpt.strip() or None,
        },
    }
    if preferred_release != "auto":
        payload["preferred_release"] = preferred_release
    return payload


def request_json(method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url=url, method=method, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach {url}: {exc.reason}") from exc

    return json.loads(body) if body else {}


def invoke_local(payload: dict[str, Any]) -> dict[str, Any]:
    response = run_async(get_local_service().respond(payload))
    return response.model_dump()


def invoke_remote(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request_json("POST", f"{base_url}/v1/respond", payload)


def get_releases_local() -> dict[str, Any]:
    return get_local_service().list_releases()


def get_releases_remote(base_url: str) -> dict[str, Any]:
    return request_json("GET", f"{base_url}/v1/releases")


def submit_feedback_local(payload: dict[str, Any]) -> dict[str, Any]:
    feedback = get_local_service().record_feedback(payload)
    return feedback.model_dump()


def submit_feedback_remote(base_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    return request_json("POST", f"{base_url}/v1/feedback", payload)


def render_release_cards(releases: dict[str, Any]) -> None:
    if not releases:
        return

    columns = st.columns(len(releases))
    for column, (alias, config) in zip(columns, releases.items(), strict=False):
        evaluation = config.get("evaluation", {})
        with column:
            st.markdown(f"### {alias.title()}")
            st.metric("Version", config.get("version", "n/a"))
            st.metric("Canary Weight", f"{config.get('canary_weight', 0)}%")
            st.caption(
                f"{config.get('provider', 'unknown')} / {config.get('model', 'unknown')}"
            )
            st.caption(
                "Gate thresholds: "
                f"recall >= {evaluation.get('min_keyword_recall', 'n/a')}, "
                f"groundedness >= {evaluation.get('min_groundedness_proxy', 'n/a')}"
            )
            with st.expander("Prompt and thresholds", expanded=False):
                st.json(config)


def main() -> None:
    st.set_page_config(
        page_title="LLMOps Canary Demo",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_page_styles()
    ensure_default_state()

    st.markdown(
        """
        <div class="demo-hero">
            <h1 style="margin:0 0 0.35rem 0;">LLMOps Canary Platform Demo</h1>
            <p style="margin:0;">
                Demo the incident-response workload locally or against the deployed ALB, inspect
                stable vs candidate release metadata, and capture operator feedback from one UI.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Runtime")
        backend_mode = st.radio(
            "Execution path",
            options=("Remote API", "Local service"),
            help="Remote mode hits the deployed FastAPI service. Local mode runs the same service in-process.",
        )
        remote_base_url = st.text_input(
            "Remote base URL",
            value=st.session_state.get("remote_base_url", DEFAULT_REMOTE_BASE_URL),
            disabled=backend_mode != "Remote API",
            help="Use your ALB DNS name here for deployed demos.",
        ).rstrip("/")
        st.session_state.remote_base_url = remote_base_url

        preferred_release = st.selectbox(
            "Preferred release",
            options=("auto", "stable", "candidate"),
            help="Force a release for demos, or leave on auto to use the canary router.",
        )

        st.divider()
        st.header("Release View")
        if st.button("Refresh release configs", use_container_width=True):
            try:
                releases = (
                    get_releases_remote(remote_base_url)
                    if backend_mode == "Remote API"
                    else get_releases_local()
                )
            except Exception as exc:  # pragma: no cover - UI path
                st.session_state.release_error = str(exc)
            else:
                st.session_state.release_error = ""
                st.session_state.release_data = releases

    sample_name = st.selectbox("Sample incident", options=tuple(SAMPLE_INCIDENTS))
    if st.button("Load sample scenario"):
        load_sample_into_state(sample_name)
        st.rerun()

    st.markdown(
        """
        <div class="demo-note">
            Use the sample scenarios to show incident investigation behavior, then switch to
            remote mode to prove the same UX against the Terraform-deployed service.
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns((1.25, 1), gap="large")

    with left:
        st.subheader("Incident Input")
        with st.form("incident_form", clear_on_submit=False):
            st.text_input("Question", key="question")
            st.text_input("Service", key="service_name")
            st.selectbox(
                "Severity",
                options=("low", "medium", "high", "critical"),
                key="severity",
            )
            st.text_area("Summary", key="summary", height=100)
            st.text_area(
                "Recent changes",
                key="recent_changes",
                height=100,
                help="One item per line.",
            )
            st.text_area(
                "Relevant logs",
                key="logs",
                height=120,
                help="One item per line.",
            )
            st.text_area(
                "Metrics JSON",
                key="metrics_json",
                height=140,
                help='Example: {"cpu_utilization": 94, "p95_latency_ms": 2200}',
            )
            st.text_area(
                "Runbook excerpt",
                key="runbook_excerpt",
                height=110,
            )
            submitted = st.form_submit_button("Run investigation", use_container_width=True)

        if submitted:
            try:
                payload = build_payload(preferred_release=preferred_release)
                if not payload["question"]:
                    raise ValueError("Question is required.")
                if not payload["context"]["service"]:
                    raise ValueError("Service is required.")
                if not payload["context"]["summary"]:
                    raise ValueError("Summary is required.")
                with st.spinner("Investigating incident..."):
                    response = (
                        invoke_remote(remote_base_url, payload)
                        if backend_mode == "Remote API"
                        else invoke_local(payload)
                    )
            except Exception as exc:  # pragma: no cover - UI path
                st.error(str(exc))
            else:
                st.session_state.last_payload = payload
                st.session_state.last_response = response
                st.success("Investigation completed.")

    active_release_source = "remote" if backend_mode == "Remote API" else "local"
    if st.session_state.get("release_source") != active_release_source:
        try:
            st.session_state.release_data = (
                get_releases_remote(remote_base_url)
                if active_release_source == "remote"
                else get_releases_local()
            )
            st.session_state.release_error = ""
            st.session_state.release_source = active_release_source
        except Exception as exc:  # pragma: no cover - UI path
            st.session_state.release_error = str(exc)

    with right:
        st.subheader("Release Metadata")
        if st.session_state.get("release_error"):
            with st.sidebar:
                st.error(st.session_state.release_error)
        render_release_cards(st.session_state.get("release_data", {}))

    if st.session_state.get("last_response"):
        response = st.session_state.last_response
        st.divider()
        st.subheader("Investigation Output")

        metric_columns = st.columns(4)
        metric_columns[0].metric("Release", response["release_name"])
        metric_columns[1].metric("Version", response["release_version"])
        metric_columns[2].metric("Latency", f'{response["latency_ms"]} ms')
        metric_columns[3].metric("Estimated Cost", f'${response["estimated_cost_usd"]:.4f}')

        answer_col, details_col = st.columns((1.3, 1), gap="large")
        with answer_col:
            st.markdown("### Recommendation")
            st.write(response["answer"])
        with details_col:
            st.markdown("### Supporting Signals")
            st.markdown("**Evidence**")
            for item in response.get("evidence", []):
                st.markdown(f"- {item}")
            st.markdown("**Risk flags**")
            risk_flags = response.get("risk_flags", [])
            if risk_flags:
                for flag in risk_flags:
                    st.markdown(f"- {flag}")
            else:
                st.markdown("- none")

        with st.expander("Raw payload and response", expanded=False):
            st.json(
                {
                    "request": st.session_state.get("last_payload", {}),
                    "response": response,
                }
            )

        st.subheader("Capture Operator Feedback")
        feedback_rating = st.slider("Rating", min_value=1, max_value=5, value=4)
        feedback_comment = st.text_area(
            "Comment",
            value="",
            help="Optional operator note for evaluation and release analysis.",
        )
        if st.button("Submit feedback"):
            feedback_payload = {
                "request_id": response["request_id"],
                "rating": feedback_rating,
                "comment": feedback_comment or None,
            }
            try:
                saved_feedback = (
                    submit_feedback_remote(remote_base_url, feedback_payload)
                    if backend_mode == "Remote API"
                    else submit_feedback_local(feedback_payload)
                )
            except Exception as exc:  # pragma: no cover - UI path
                st.error(str(exc))
            else:
                st.success(
                    f'Feedback recorded for request {saved_feedback["request_id"]}.'
                )


if __name__ == "__main__":
    main()
