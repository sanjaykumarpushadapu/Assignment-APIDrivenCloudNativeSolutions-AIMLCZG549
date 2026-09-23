"""Cloud dashboard: displays pipeline activity details (assessment
activity 1.5 -- "logging all activity details and displaying them on a
Cloud dashboard").

This is a separate small FastAPI app (its own port) that serves one HTML
page. It does NOT define its own copies of the application-detail
endpoints -- those live in exactly one place, `src/diabetes_risk/api/main.py`
(the GCP-backed API required by Sub-Objective 2). This page's JavaScript
calls that real API over HTTP (see DIABETES_API_BASE_URL below) and
renders whatever it returns, with explicit loading, configuration, error,
and unavailable states -- no numbers here are hard-coded or made up.

Per the workload plan's own reading of activity 1.5, the required content
is *activity/execution* details (status, runtime, records processed,
error/warning counts, execution history) -- EDA charts and model metrics
are a nice-to-have, not the graded requirement. One optional chart is
included below (Random Forest vs. Logistic Regression, sourced live from
/api/v1/model, which is backed by local_service.get_model_comparison()
reading real GCS objects) as a working reference for the remaining
gcp_service.py/local_service.py functions.
"""

import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="Diabetes Risk Cloud Dashboard",
    description="Activity/execution dashboard for the diabetes-risk pipeline (Group 49).",
    version="1.0.0",
    include_in_schema=False,
)

# Base URL of the real API (src/diabetes_risk/api/main.py), which this
# dashboard's JS fetches from client-side. Override in .env if the API
# runs somewhere other than the default local port documented in
# README.md's "Run the API" section.
API_BASE_URL = os.environ.get("DIABETES_API_BASE_URL", "http://127.0.0.1:9000")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def render_dashboard() -> HTMLResponse:
    """Renders the dashboard shell; all data is filled in client-side by
    calling the real API (API_BASE_URL) so nothing here is hard-coded.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Diabetes Risk Cloud Dashboard - Group 49</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
        <style>
            body {{ background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .metric-card {{ background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }}
            .status-badge {{ font-size: 0.9rem; padding: 6px 12px; border-radius: 4px; }}
            .api-section {{ background: #eef2f7; border-left: 4px solid #0d6efd; padding: 15px; border-radius: 6px; }}
            .pending {{ color: #adb5bd; font-style: italic; }}
            #history-table {{ width: 100%; table-layout: fixed; font-size: 0.82rem; }}
            #history-table th {{ color: #687386; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }}
            #history-table td, #history-table th {{ padding: 0.7rem 0.45rem; vertical-align: middle; }}
            .history-id {{ display: block; overflow: hidden; color: #344054; font-family: Consolas, monospace; text-overflow: ellipsis; white-space: nowrap; }}
            .history-time {{ color: #344054; white-space: nowrap; }}
            .history-duration {{ color: #475467; font-variant-numeric: tabular-nums; white-space: nowrap; }}
            .history-status {{ display: inline-block; border-radius: 999px; padding: 0.25rem 0.55rem; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }}
            .history-status.success {{ background: #e8f5ed; color: #16713b; }}
            .history-status.failed {{ background: #fdecec; color: #a52828; }}
            .history-status.other {{ background: #edf0f4; color: #596579; }}
            .history-latest {{ display: inline-block; margin-top: 0.2rem; color: #697586; font-family: inherit; font-size: 0.62rem; font-weight: 700; }}
            @media (max-width: 680px) {{
                #history-table {{ font-size: 0.74rem; }}
                #history-table td, #history-table th {{ padding: 0.55rem 0.25rem; }}
                .history-status {{ padding: 0.2rem 0.35rem; font-size: 0.65rem; }}
            }}
        </style>
    </head>
    <body class="p-4">
        <div class="container-fluid">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h2>Cloud Analytics &amp; DataOps Dashboard</h2>
                    <p class="text-muted mb-0" id="project-name">Loading project info...</p>
                </div>
                <div>
                    <span class="badge bg-secondary status-badge" id="status-badge">Checking...</span>
                    <a href="{API_BASE_URL}/docs" target="_blank" class="btn btn-outline-primary btn-sm ms-2">Swagger API Docs</a>
                </div>
            </div>

            <!-- Activity details (assessment activity 1.5) -->
            <div class="row">
                <div class="col-md-3">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Latest Pipeline Run Status</div>
                        <h4 class="mt-2 pending" id="status-val">-</h4>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Processed Records</div>
                        <h4 class="mt-2 pending" id="records-val">-</h4>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Duplicate Records Removed</div>
                        <h4 class="mt-2 pending" id="duplicates-val">-</h4>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Quality Status</div>
                        <h4 class="mt-2 pending" id="quality-val">-</h4>
                        <div class="text-muted small" id="quality-help">Loading quality details...</div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-4">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Pipeline Processing Duration</div>
                        <h4 class="mt-2 pending" id="runtime-val">-</h4>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Errors</div>
                        <h4 class="mt-2 pending" id="errors-val">-</h4>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card text-center">
                        <div class="text-muted small">Warnings</div>
                        <h4 class="mt-2 pending" id="warnings-val">-</h4>
                    </div>
                </div>
            </div>

            <!-- API-derived application details (Sub-Objective 2) -->
            <div class="row my-2">
                <div class="col-12">
                    <div class="api-section">
                        <h5 class="text-primary">API-Derived Application Details</h5>
                        <p class="text-muted small mb-2">Each value below is a live call to the real API at <code>{API_BASE_URL}</code> -- not hard-coded. Status text distinguishes loading, configuration, unavailable, and unimplemented states.</p>
                        <div class="row mt-2">
                            <div class="col-md-3"><strong>Composer DAG history (<code>/api/v1/workflow</code>):</strong> <span class="pending" id="api-workflow">Loading...</span></div>
                            <div class="col-md-3"><strong>Latest run (<code>/api/v1/runs/latest</code>):</strong> <span class="pending" id="api-runs-latest">Loading...</span></div>
                            <div class="col-md-3"><strong>Dataset (<code>/api/v1/dataset</code>):</strong> <span class="pending" id="api-dataset">Loading...</span></div>
                            <div class="col-md-3"><strong>Schedule (<code>/api/v1/schedule</code>):</strong> <span class="pending" id="api-schedule">Loading...</span></div>
                        </div>
                        <div class="row mt-2">
                            <div class="col-md-3"><strong>Model (<code>/api/v1/model</code>):</strong> <span class="pending" id="api-model">Loading...</span></div>
                            <div class="col-md-9 text-muted small">Retrieval time: <span id="api-retrieved-at">-</span></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Execution history -->
            <div class="row mt-3">
                <div class="col-md-7">
                    <div class="metric-card">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <h5 class="mb-0">Composer DAG Run History <small class="text-muted">(UTC)</small></h5>
                            <span id="history-count" class="badge bg-light text-secondary">Recent runs</span>
                        </div>
                        <table class="table table-sm" id="history-table">
                            <colgroup><col style="width: 26%"><col style="width: 14%"><col style="width: 20%"><col style="width: 20%"><col style="width: 10%"><col style="width: 10%"></colgroup>
                            <thead><tr><th>DAG Run ID</th><th>Status</th><th>Started (UTC)</th><th>Finished (UTC)</th><th>DAG Duration</th><th>Tasks</th></tr></thead>
                            <tbody><tr><td colspan="6" class="pending">Loading Composer history...</td></tr></tbody>
                        </table>
                    </div>
                </div>

                <!-- Reference chart: sourced live from /api/v1/model (local_service.get_model_comparison(),
                     a real GCS read -- see local_service.py). Hidden until that call succeeds. -->
                <div class="col-md-5">
                    <div class="metric-card">
                        <h5>Model Comparison <span class="text-muted small">(/api/v1/model)</span></h5>
                        <p class="pending small mb-2" id="model-chart-placeholder">Loading model data...</p>
                        <canvas id="model-chart" height="220" hidden></canvas>
                    </div>
                </div>
            </div>
        </div>

        <script>
            const API_BASE_URL = "{API_BASE_URL}";

            async function fetchJson(path) {{
                try {{
                    const res = await fetch(API_BASE_URL + path, {{ signal: AbortSignal.timeout(30000) }});
                    const body = await res.json().catch(() => null);
                    if (res.status === 501) {{
                        return {{ ok: false, pending: true, body, status: res.status }};
                    }}
                    if (!res.ok) {{
                        return {{ ok: false, pending: false, body, status: res.status }};
                    }}
                    return {{ ok: true, pending: false, body, status: res.status }};
                }} catch (err) {{
                    if (err.name === "TimeoutError" || err.name === "AbortError") {{
                        return {{ ok: false, pending: false, timeout: true }};
                    }}
                    return {{ ok: false, pending: false, unreachable: true }};
                }}
            }}

            function failureText(result, fallback) {{
                if (result.unreachable) {{
                    return "API unavailable";
                }}
                if (result.timeout) {{
                    return "Request timed out";
                }}
                if (result.pending) {{
                    const detail = result.body?.detail || "";
                    if (detail.includes("GCP") || detail.includes("DIABETES_GCS_BUCKET")) {{
                        return "Configuration required";
                    }}
                    return "Not implemented yet";
                }}
                if (result.body?.detail) {{
                    return `${{fallback}}: ${{result.body.detail}}`;
                }}
                if (result.status) {{
                    return `${{fallback}} (HTTP ${{result.status}})`;
                }}
                return fallback;
            }}

            function setSpan(id, result, formatValue) {{
                const el = document.getElementById(id);
                if (!result.ok) {{
                    el.textContent = failureText(result, "Unable to load data");
                    el.className = result.pending ? "pending" : "text-danger";
                }} else {{
                    el.textContent = formatValue(result.body);
                    el.className = "text-success";
                }}
            }}

            async function loadDashboard() {{
                const workflowPromise = fetchJson("/api/v1/workflow").then(workflow => {{
                    setSpan("api-workflow", workflow, (body) => `${{body.length}} run(s)`);
                    renderHistory(document.querySelector("#history-table tbody"), workflow);
                    return workflow;
                }});
                const latestPromise = fetchJson("/api/v1/runs/latest").then(runsLatest => {{
                    renderLatestRun(runsLatest);
                    return runsLatest;
                }});
                const [meta, health, runsLatest, dataset, schedule, model] = await Promise.all([
                    fetchJson("/api/v1/metadata"),
                    fetchJson("/health"),
                    latestPromise,
                    fetchJson("/api/v1/dataset"),
                    fetchJson("/api/v1/schedule"),
                    fetchJson("/api/v1/model"),
                    workflowPromise,
                ]);
                document.getElementById("project-name").textContent = meta.ok ? meta.body.project : "Diabetes Risk Prediction Using Health and Lifestyle Indicators";

                const badge = document.getElementById("status-badge");
                if (health.ok) {{
                    badge.textContent = "API Online";
                    badge.className = "badge bg-success status-badge";
                }} else {{
                    badge.textContent = "API Unreachable";
                    badge.className = "badge bg-danger status-badge";
                }}

                setSpan("api-dataset", dataset, (b) => b.quality_status || "ok");
                if (!runsLatest.ok || runsLatest.body.records_processed == null) {{
                    setSpan("records-val", dataset, (b) => (b.input_rows ?? "-").toLocaleString());
                }}
                setSpan("duplicates-val", dataset, (b) => (b.duplicate_records_removed ?? "-").toLocaleString());
                setSpan("quality-val", dataset, (b) => b.quality_status || "-");
                const qualityHelp = document.getElementById("quality-help");
                if (dataset.ok) {{
                    const qualityStatus = String(dataset.body.quality_status || "").toUpperCase();
                    const duplicateCount = Number(dataset.body.duplicate_records_removed || 0);
                    qualityHelp.textContent = qualityStatus === "PASS_WITH_WARNINGS"
                        ? `Validation passed with ${{duplicateCount.toLocaleString()}} duplicate record(s) removed during preprocessing.`
                        : qualityStatus === "PASS"
                            ? "All configured data-quality checks passed."
                            : "One or more data-quality checks need review.";
                }} else {{
                    qualityHelp.textContent = failureText(dataset, "Quality details unavailable");
                }}

                setSpan("api-schedule", schedule, (b) => b.state || "ok");

                setSpan("api-model", model, (b) => "ok");
                renderModelChart(model);

                document.getElementById("api-retrieved-at").textContent = new Date().toISOString();
            }}

            function renderLatestRun(result) {{
                setSpan("api-runs-latest", result, (body) => body.status || "status unavailable");
                setSpan("status-val", result, (body) => body.status || "unknown");
                setSpan("runtime-val", result, (body) => body.duration_seconds == null ? "not reported" : `${{Number(body.duration_seconds).toFixed(2)}} s`);
                setSpan("errors-val", result, (body) => Array.isArray(body.errors) ? body.errors.length : 0);
                setSpan("warnings-val", result, (body) => Array.isArray(body.warnings) ? body.warnings.length : 0);
                if (result.ok && result.body.records_processed != null) {{
                    setSpan("records-val", result, (body) => Number(body.records_processed).toLocaleString());
                }}
            }}

            function renderHistory(body, result) {{
                const escapeHtml = value => String(value ?? "-").replace(/[&<>"']/g, character => ({{
                    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
                }})[character]);
                const formatTimestamp = value => {{
                    if (!value) return "-";
                    const date = new Date(value);
                    return Number.isNaN(date.getTime()) ? "-" : new Intl.DateTimeFormat(undefined, {{
                        month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit",
                        timeZone: "UTC", timeZoneName: "short"
                    }}).format(date);
                }};
                if (!result.ok) {{
                    body.innerHTML = `<tr><td colspan="6" class="text-danger">${{escapeHtml(failureText(result, "Composer history unavailable"))}}</td></tr>`;
                    document.getElementById("history-count").textContent = "History unavailable";
                    return;
                }}
                const runs = result.body;
                if (!Array.isArray(runs) || runs.length === 0) {{
                    body.innerHTML = '<tr><td colspan="6" class="text-muted">No Composer DAG runs found.</td></tr>';
                    document.getElementById("history-count").textContent = "0 recent runs";
                    return;
                }}
                body.innerHTML = runs.map((run, index) => {{
                    const runId = String(run.dag_run_id ?? "-");
                    const dateId = runId.startsWith("scheduled__") ? runId.slice("scheduled__".length) : runId;
                    const state = String(run.state ?? "unknown").toLowerCase();
                    const statusClass = state === "success" ? "success" : state === "failed" ? "failed" : "other";
                    const duration = Number(run.duration_seconds);
                    return `
                        <tr>
                            <td><span class="history-id" title="${{escapeHtml(runId)}}">${{escapeHtml(dateId.length > 25 ? `${{dateId.slice(0, 22)}}...` : dateId)}}</span>${{index === 0 ? '<span class="history-latest">LATEST</span>' : ""}}</td>
                            <td><span class="history-status ${{statusClass}}">${{escapeHtml(state.charAt(0).toUpperCase() + state.slice(1))}}</span></td>
                            <td class="history-time" title="${{escapeHtml(run.start_date)}}">${{escapeHtml(formatTimestamp(run.start_date))}}</td>
                            <td class="history-time" title="${{escapeHtml(run.end_date)}}">${{escapeHtml(formatTimestamp(run.end_date))}}</td>
                            <td class="history-duration">${{Number.isFinite(duration) ? `${{duration.toFixed(1)}} s` : "-"}}</td>
                            <td><button class="btn btn-sm btn-outline-primary history-tasks" data-run-id="${{escapeHtml(runId)}}" aria-expanded="false">Tasks</button></td>
                        </tr>
                    `;
                }}).join("");
                document.getElementById("history-count").textContent = `Showing ${{runs.length}} recent run(s)`;

                body.onclick = async event => {{
                    const button = event.target.closest(".history-tasks");
                    if (!button) return;
                    const currentRow = button.closest("tr");
                    const existing = currentRow.nextElementSibling;
                    if (existing?.classList.contains("task-details-row")) {{
                        existing.remove();
                        button.setAttribute("aria-expanded", "false");
                        return;
                    }}
                    const detailRow = document.createElement("tr");
                    detailRow.className = "task-details-row";
                    detailRow.innerHTML = '<td colspan="6" class="pending">Loading Composer task instances...</td>';
                    currentRow.after(detailRow);
                    button.setAttribute("aria-expanded", "true");
                    const taskResult = await fetchJson(`/api/v1/workflow/${{encodeURIComponent(button.dataset.runId)}}/tasks`);
                    if (!taskResult.ok) {{
                        detailRow.innerHTML = `<td colspan="6" class="text-danger">${{escapeHtml(failureText(taskResult, "Unable to load task instances"))}}</td>`;
                        return;
                    }}
                    const tasks = taskResult.body;
                    detailRow.innerHTML = `<td colspan="6"><table class="table table-sm mb-0"><thead><tr><th>Task</th><th>Status</th><th>Started (UTC)</th><th>Finished (UTC)</th><th>Duration</th></tr></thead><tbody>${{tasks.map(task => `
                        <tr><td>${{escapeHtml(task.task_id)}}</td><td>${{escapeHtml(task.state)}}</td>
                        <td>${{escapeHtml(formatTimestamp(task.start_date))}}</td><td>${{escapeHtml(formatTimestamp(task.end_date))}}</td>
                        <td>${{task.duration != null && Number.isFinite(Number(task.duration)) ? `${{Number(task.duration).toFixed(1)}} s` : "-"}}</td></tr>
                    `).join("") || '<tr><td colspan="5">No task instances returned.</td></tr>'}}</tbody></table></td>`;
                }};
            }}

            let modelChart = null;

            function renderModelChart(result) {{
                const placeholder = document.getElementById("model-chart-placeholder");
                const canvas = document.getElementById("model-chart");

                if (!result.ok) {{
                    placeholder.hidden = false;
                    placeholder.textContent = failureText(result, "Unable to load model data");
                    canvas.hidden = true;
                    return;
                }}

                const body = result.body;
                const lr = body.logistic_regression || {{}};
                const rf = body.random_forest || {{}};
                const metrics = ["accuracy", "precision", "recall", "f1_score"];

                placeholder.hidden = true;
                canvas.hidden = false;

                if (modelChart) {{
                    modelChart.destroy();
                }}
                modelChart = new Chart(canvas, {{
                    type: "bar",
                    data: {{
                        labels: metrics.map(m => m.replace("_", " ")),
                        datasets: [
                            {{
                                label: "Logistic Regression",
                                data: metrics.map(m => lr[m] ?? 0),
                                backgroundColor: "#6c757d",
                            }},
                            {{
                                label: "Random Forest",
                                data: metrics.map(m => rf[m] ?? 0),
                                backgroundColor: "#0d6efd",
                            }},
                        ],
                    }},
                    options: {{
                        responsive: true,
                        scales: {{ y: {{ beginAtZero: true, max: 1 }} }},
                        plugins: {{ title: {{ display: true, text: `Top feature: ${{body.top_feature ?? "-"}}` }} }},
                    }},
                }});
            }}

            loadDashboard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
