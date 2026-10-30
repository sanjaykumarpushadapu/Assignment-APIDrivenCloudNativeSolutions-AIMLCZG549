"""Scene list for the Group 49 Assignment II demonstration video.

Each scene is one shot: what the viewer sees (``kind`` + its options) and what
the narrator says (``say``). The recorder turns every scene into one clip whose
length follows the narration, then joins them in order.

Narration placeholders such as ``{macro_f1_tuned}`` are filled from facts
collected during preflight: live test results, ``/metadata`` versions, and the
measured results in ``evaluation/results.json``. A scene whose evidence does
not exist yet cannot be recorded, so the video never states unmeasured results.

Scene kinds: card, image, code, terminal, json, links, url, app, swagger.
``app`` scenes type into the live React app using its visible labels.
"""

# ---------------------------------------------------------------- local URLs
APP_URL = "http://127.0.0.1:5173"
API_URL = "http://127.0.0.1:8001"
APP_HEADING = "Diabetes support desk"
REQUIRED_ENDPOINTS = ["/health", "/metadata"]

# ------------------------------------------------------------------- team
MEMBERS = [
    "Pushadapu Sanjay Kumar",
    "Sathish Krishnan V",
    "Chezrla Raga Suma",
    "Bhuvnesh Mishra",
]

# Commands run on this machine during preflight; their real output is shown in
# the terminal scene. "{py}" is the project's virtual-env Python, "{npm}" is npm.
TERMINAL_COMMANDS = {
    "pytest": {
        "argv": [
            "{py}",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:warnings",
        ],
        "shown_as": "pytest -q",
    },
    "build": {
        "argv": ["{npm}", "--prefix", "frontend", "run", "build"],
        "shown_as": "npm --prefix frontend run build",
    },
}

# Measured results written by the evaluation step (see README.md for the keys).
RESULTS_FILE = "evaluation/results.json"
IMAGES_DIR = "docs/report/imgs"

ANALYZE_BODY = (
    '{\n  "message": "I need to move my diabetes education appointment, and I cannot find '
    'the preparation leaflet in the portal."\n}'
)
CHAT_BODY = '{\n  "question": "How do I change a clinic appointment?"\n}'


def part_card(number, title, member, say):
    return {
        "id": f"part{number}_card",
        "kind": "card",
        "eyebrow": f"Part {number} of 4",
        "title": title,
        "subtitle": member,
        "say": say,
    }


SCENES = [
    {
        "id": "title",
        "kind": "card",
        "eyebrow": "AIMLCZG549 · API-Driven Cloud-Native Solutions · Assignment II",
        "title": "Diabetes Care Support Assistant",
        "subtitle": "Request routing, handoff summaries and document-grounded Q&A · Group 49",
        "lines": MEMBERS,
        "footnote": "Automated screen recording · synthesized narration",
        "say": (
            "Group 49 presents the Diabetes Care Support Assistant, for A.I.M.L. C.Z.G. 5 4 9, Assignment Two. "
            "The team: Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra."
        ),
    },
    {
        "id": "architecture",
        "kind": "image",
        "images": ["architecture.png"],
        "caption": "React + TypeScript UI → FastAPI → fine-tuned classifier, summariser and RAG retrieval",
        "say": (
            "The architecture: a React and TypeScript interface calls a FastAPI backend. The backend runs a "
            "fine-tuned request classifier, a summariser, and a retrieval-augmented question-answering service "
            "over approved documents. Staff review every output before it reaches a patient."
        ),
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "Workplace Problem, Labels & Data",
        MEMBERS[0],
        "Part one, by Pushadapu Sanjay Kumar: the workplace problem. A fictional diabetes clinic's support "
        "desk reads, routes and answers routine messages by hand. The assistant reduces that effort and sends "
        "clinical decisions to qualified staff.",
    ),
    {
        "id": "label_guide",
        "kind": "code",
        "file": "data/pilot/label_guide.md",
        "regex": r"^## Labels",
        "window": [0, 24],
        "highlight": r"clinical_staff_referral",
        "caption": "Five routing labels and the clinical-referral override",
        "say": (
            "Requests are routed into five categories: appointment support, education resources, portal support, "
            "records and billing, and clinical-staff referral. Any personal clinical question overrides the other "
            "labels and is referred to staff, without advice or an urgency assessment."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning & Summarisation",
        MEMBERS[2],
        "Part two, by Chezrla Raga Suma: fine-tuning the request classifier and the summariser.",
    ),
    {
        "id": "fine_tuning",
        "kind": "image",
        "images": ["training_loss.png", "confusion_matrix.png"],
        "caption": "Fine-tuning: training loss and held-out confusion matrix",
        "say": (
            "The classifier, {classifier_model}, was fine-tuned on reviewed synthetic support messages. On "
            "{test_messages} held-out test messages, macro F1 moved from {macro_f1_base} for the base model to "
            "{macro_f1_tuned} after fine-tuning."
        ),
    },
    {
        "id": "summaries",
        "kind": "image",
        "images": ["summary_examples.png"],
        "caption": "Handoff summaries — reviewer check of retained and invented facts",
        "say": (
            "Handoff summaries kept every essential request in {summary_ok} of {summary_total} held-out messages, "
            "as checked by a reviewer."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3,
        "Retrieval-Augmented Q&A",
        MEMBERS[1],
        "Part three, by Sathish Krishnan V: the retrieval-augmented chatbot over approved documents.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["rag_pipeline.png"],
        "caption": "Documents → passages → embeddings → top-k retrieval → grounded answer with sources",
        "say": (
            "Approved public education material and clearly fictional clinic procedures are split into passages "
            "and embedded. Relevant evidence was in the top three for {retrieval_hits} of {retrieval_total} test "
            "questions, and {answers_supported} of {answers_total} answers were supported by their cited sources."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Application, API & Tests",
        MEMBERS[3],
        "Part four, by Bhuvnesh Mishra: the application, the API, and the tests.",
    ),
    {
        "id": "tests_terminal",
        "kind": "terminal",
        "commands": ["pytest", "build"],
        "caption": "Tests and the production frontend build, run on this machine moments ago",
        "say": "The backend tests and the production frontend build were run just before recording: {pytest_summary}.",
    },
    {
        "id": "app_analysis",
        "kind": "app",
        "steps": [
            {
                "fill": "Incoming support message",
                "text": (
                    "I need to move my diabetes education appointment, and I cannot find the preparation "
                    "leaflet in the portal."
                ),
            },
            {"click": "Analyze request"},
            {"expect": "Primary category"},
        ],
        "say": (
            "In the live app, a staff member pastes a support message. The fine-tuned classifier returns the "
            "primary category, and the summariser keeps both requests in the handoff note."
        ),
    },
    {
        "id": "app_chat",
        "kind": "app",
        "steps": [
            {"fill": "Question", "text": "How do I change a clinic appointment?"},
            {"click": "Send question"},
            {"expect": "Sources"},
        ],
        "say": (
            "The knowledge assistant answers from retrieved passages and lists its sources, so staff can check "
            "the evidence."
        ),
    },
    {
        "id": "app_referral",
        "kind": "app",
        "steps": [
            {
                "fill": "Incoming support message",
                "text": (
                    "I started a new medicine and now feel sick. Should I stop taking it?"
                ),
            },
            {"click": "Analyze request"},
            {"expect": "clinical_staff_referral"},
        ],
        "say": (
            "A personal medication question is routed to clinical staff. The assistant does not give clinical "
            "advice."
        ),
    },
    {
        "id": "swagger_intro",
        "kind": "url",
        "url": API_URL + "/docs",
        "wait_for": ".opblock",
        "caption": "Swagger / OpenAPI — FastAPI backend",
        "say": "The same capabilities are available through the documented API.",
    },
    {
        "id": "api_metadata",
        "kind": "swagger",
        "path": "/metadata",
        "say": (
            "The metadata endpoint reports which classifier, summariser and index versions are loaded. "
            "HTTP {status_/metadata}."
        ),
    },
    {
        "id": "api_analyze",
        "kind": "swagger",
        "path": "/analyze",
        "body": ANALYZE_BODY,
        "say": "The analyse endpoint returns the category and the handoff summary.",
    },
    {
        "id": "api_chat",
        "kind": "swagger",
        "path": "/chat",
        "body": CHAT_BODY,
        "say": "The chat endpoint returns a grounded answer with its source passages.",
    },
    # ------------------------------------------------------- workplace + end
    {
        "id": "workplace",
        "kind": "image",
        "images": ["workplace_results.png"],
        "caption": "Situated learning: manual versus assisted handling of representative support tasks",
        "say": (
            "In the workplace study, {workflow_tasks} representative tasks took {time_manual_min} minutes by hand "
            "and {time_assisted_min} minutes with the assistant, including staff review. Unsupported or clinical "
            "questions were declined or referred in {refusals_ok} of {refusals_total} test cases."
        ),
    },
    {
        "id": "closing",
        "kind": "card",
        "eyebrow": "Group 49 · AIMLCZG549 Assignment II",
        "title": "A staff-facing prototype, not a clinical decision system",
        "lines": MEMBERS,
        "say": (
            "To summarise: three connected N.L.P. tasks, a fine-tuned classifier, and a retrieval-augmented chatbot "
            "support a clinic's routine requests. Before any patient-facing use, clinicians must validate answer "
            "correctness and referral behaviour. Thank you for watching."
        ),
    },
]

# ---------------------------------------------------------------------------
# Student-style script for your own voice (record_voice.py, --tts files).
# One person reads every scene. No {placeholders}: the measured values are on
# screen, so these scripts can be recorded on any computer.
# ---------------------------------------------------------------------------
SELF_SCRIPTS = {
    "title": (
        "Hello everyone! We're Group 49, and this is our project for AIMLCZG549, Assignment Two: the Diabetes "
        "Care Support Assistant. Our team is Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, "
        "and Bhuvnesh Mishra."
    ),
    "architecture": (
        "Here's our architecture. A React and TypeScript interface calls our FastAPI backend, which runs a "
        "fine-tuned classifier, a summariser, and a retrieval-augmented question-answering service. Staff "
        "review every output before it reaches a patient."
    ),
    "part1_card": (
        "Part one, by Sanjay, is the workplace problem. Our fictional diabetes clinic's support desk reads, "
        "routes and answers routine messages by hand. Our assistant reduces that effort and sends clinical "
        "decisions to qualified staff."
    ),
    "label_guide": (
        "We route requests into five categories: appointments, education resources, portal support, records "
        "and billing, and clinical-staff referral. Any personal clinical question overrides the rest and goes "
        "to staff."
    ),
    "part2_card": "Part two, by Raga Suma, covers fine-tuning the classifier and the summariser.",
    "fine_tuning": (
        "We fine-tuned our classifier on reviewed synthetic support messages. Here are the training loss and "
        "the held-out confusion matrix, comparing the base model with the fine-tuned one."
    ),
    "summaries": (
        "Here are our handoff summaries, checked by a reviewer for retained and invented facts on held-out "
        "messages."
    ),
    "part3_card": "Part three, by Sathish, is our retrieval-augmented chatbot over approved documents.",
    "rag_pipeline": (
        "We split approved education material and fictional clinic procedures into passages and embed them. "
        "On screen are our retrieval and answer-support results on held-out questions."
    ),
    "part4_card": "Part four, by Bhuvnesh, covers the application, the API, and the tests.",
    "tests_terminal": "We ran our backend tests and the production frontend build just before recording.",
    "app_analysis": (
        "In our live app, a staff member pastes a support message. The fine-tuned classifier gives the primary "
        "category, and the summary keeps both requests."
    ),
    "app_chat": (
        "Our knowledge assistant answers from retrieved passages and shows its sources, so staff can check "
        "the evidence."
    ),
    "app_referral": (
        "A personal medication question is routed to clinical staff. Our assistant doesn't give clinical "
        "advice."
    ),
    "swagger_intro": "The same features are available through our documented API.",
    "api_metadata": "The metadata endpoint shows which model and index versions are loaded.",
    "api_analyze": "The analyse endpoint returns the category and the handoff summary.",
    "api_chat": "And the chat endpoint returns a grounded answer with its sources.",
    "workplace": (
        "For the workplace study, we compared handling representative tasks by hand and with the assistant. "
        "Our measured times and referral results are on screen."
    ),
    "closing": (
        "To wrap up: three connected NLP tasks, a fine-tuned classifier, and a retrieval-augmented chatbot "
        "support a clinic's routine requests. Before any patient-facing use, clinicians must validate the "
        "answers and referrals. Thank you!"
    ),
}
