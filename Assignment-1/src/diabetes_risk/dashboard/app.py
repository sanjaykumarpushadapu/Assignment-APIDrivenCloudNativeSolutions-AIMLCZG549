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
                        <div class="text-muted small">Latest Workflow Status</div>
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
                            <div class="col-md-3"><strong>Workflow (<code>/api/v1/workflow</code>):</strong> <span class="pending" id="api-workflow">Loading...</span></div>
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
                        <h5>Execution History</h5>
                        <table class="table table-sm" id="history-table">
                            <thead><tr><th>Run</th><th>Status</th><th>Start</th><th>End</th></tr></thead>
                            <tbody><tr><td colspan="4" class="pending">Loading...</td></tr></tbody>
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
                    const res = await fetch(API_BASE_URL + path);
                    const body = await res.json().catch(() => null);
                    if (res.status === 501) {{
                        return {{ ok: false, pending: true, body, status: res.status }};
                    }}
                    if (!res.ok) {{
                        return {{ ok: false, pending: false, body, status: res.status }};
                    }}
                    return {{ ok: true, pending: false, body, status: res.status }};
                }} catch (err) {{
                    return {{ ok: false, pending: false, unreachable: true }};
                }}
            }}

            function failureText(result, fallback) {{
                if (result.unreachable) {{
                    return "API unavailable";
                }}
                if (result.pending) {{
                    const detail = result.body?.detail || "";
                    if (detail.includes("GCP") || detail.includes("DIABETES_GCS_BUCKET")) {{
                        return "Configuration required";
                    }}
                    return "Not implemented yet";
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
                document.getElementById("api-retrieved-at").textContent = new Date().toISOString();

                const meta = await fetchJson("/api/v1/metadata");
                document.getElementById("project-name").textContent = meta.ok ? meta.body.project : "Diabetes Risk Prediction Using Health and Lifestyle Indicators";

                const health = await fetchJson("/health");
                const badge = document.getElementById("status-badge");
                if (health.ok) {{
                    badge.textContent = "API Online";
                    badge.className = "badge bg-success status-badge";
                }} else {{
                    badge.textContent = "API Unreachable";
                    badge.className = "badge bg-danger status-badge";
                }}

                const workflow = await fetchJson("/api/v1/workflow");
                setSpan("api-workflow", workflow, (b) => `${{b.length}} run(s)`);

                const runsLatest = await fetchJson("/api/v1/runs/latest");
                setSpan("api-runs-latest", runsLatest, (b) => `${{b.length}} task(s)`);
                setSpan("status-val", runsLatest, (b) => (b.length ? b[0].state : "unknown"));

                const dataset = await fetchJson("/api/v1/dataset");
                setSpan("api-dataset", dataset, (b) => b.quality_status || "ok");
                setSpan("records-val", dataset, (b) => (b.input_rows ?? "-").toLocaleString());
                setSpan("duplicates-val", dataset, (b) => (b.duplicate_records_removed ?? "-").toLocaleString());
                setSpan("quality-val", dataset, (b) => b.quality_status || "-");

                const schedule = await fetchJson("/api/v1/schedule");
                setSpan("api-schedule", schedule, (b) => b.state || "ok");

                const model = await fetchJson("/api/v1/model");
                setSpan("api-model", model, (b) => "ok");
                renderModelChart(model);

                const historyBody = document.querySelector("#history-table tbody");
                if (workflow.ok && workflow.body.length) {{
                    historyBody.innerHTML = workflow.body.map(r => `
                        <tr>
                            <td>${{r.dag_run_id ?? "-"}}</td>
                            <td>${{r.state ?? "-"}}</td>
                            <td>${{r.start_date ?? "-"}}</td>
                            <td>${{r.end_date ?? "-"}}</td>
                        </tr>
                    `).join("");
                }} else {{
                    historyBody.innerHTML = `<tr><td colspan="4" class="pending">${{failureText(workflow, "No execution history available")}}</td></tr>`;
                }}
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
