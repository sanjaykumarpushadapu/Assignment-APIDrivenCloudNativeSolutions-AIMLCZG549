"""Scene list for the Group 49 Assignment II demonstration video.

Each scene is one shot: what the viewer sees (``kind`` + its options) and what
the narrator says (``say``). The recorder turns every scene into one clip whose
length follows the narration, then joins them in order.

Narration placeholders such as ``{macro_f1_tuned}`` are filled from facts
collected during preflight: live test results, ``/metadata`` versions, and the
tracked run records in ``docs/report/evidence``. RAG figures are explicitly
labelled as a pre-fix baseline; no current post-fix RAG score or workplace time
study is claimed.

Scene kinds: card, image, code, terminal, json, links, url, app, swagger.
``app`` scenes type into the live React app using its visible labels.
"""

# ---------------------------------------------------------------- local URLs
APP_URL = "http://127.0.0.1:5173"
API_URL = "http://127.0.0.1:8001"
APP_HEADING = "Diabetes support"
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

# Tracked result records and report figures are the shared evidence source.
RESULT_RECORDS = {
    "classifier": "docs/report/evidence/classifier-run-record.json",
    "summarizer": "docs/report/evidence/summarizer-evaluation-record.json",
    "rag": "docs/report/evidence/rag-evaluation-record.json",
}
IMAGES_DIR = "docs/report/evidence"

ANALYZE_BODY = (
    '{\n  "message": "I need to move my diabetes education appointment, and I cannot find '
    'the preparation leaflet in the portal."\n}'
)
CHAT_BODY = (
    '{\n  "question": "What symptoms might someone with diabetes experience?"\n}'
)


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
        "eyebrow": "AIMLCZG549 · API-Driven Cloud-Native Solutions · Assignment II · Group 49",
        "title": "Diabetes Care Support Assistant",
        "subtitle": "Request routing · staff handoffs · source-grounded Q&A",
        "lines": MEMBERS,
        "footnote": "Automated screen recording · synthesized narration",
        "say": (
            "Group 49 presents the Diabetes Care Support Assistant for A.I.M.L. C.Z.G. five four nine, Assignment Two. "
            "The team members are Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra."
        ),
    },
    {
        "id": "architecture",
        "kind": "card",
        "eyebrow": "Application architecture",
        "title": "React + TypeScript · FastAPI · three connected NLP tasks",
        "lines": [
            "Support message → fine-tuned FLAN-T5 classifier → category",
            "Support message → FLAN-T5 summariser → staff handoff summary",
            "Question → referral rules → WHO passage retrieval → grounded answer and sources",
            "Staff review before information is shared",
        ],
        "say": (
            "The architecture: a React and TypeScript interface calls a FastAPI backend. The backend runs a "
            "fine-tuned request classifier, the base FLAN-T5 summariser, and a retrieval-augmented question-"
            "answering service over curated World Health Organization material. Staff review every output."
        ),
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "API-Based AI Application",
        MEMBERS[3],
        "Part one outlines the workplace scenario: a fictional diabetes clinic "
        "support desk handles requests about appointments, education, portal access, records and clinical questions. "
        "The application demonstrates message classification, handoff summaries and source-based answers for staff.",
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
        "Requests are routed into five categories: appointment support, education resource request, portal "
            "technical support, records and insurance administration, and clinical staff referral. Any personal clinical question overrides the other "
            "labels and is referred to staff, without advice or an urgency assessment."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning",
        MEMBERS[2],
        "Part two covers full fine-tuning of the request classifier and the summary-quality evaluation.",
    ),
    {
        "id": "fine_tuning",
        "kind": "image",
        "images": ["03-classifier-fine-tuning.png"],
        "caption": "Classifier full fine-tuning method and held-out test results",
        "say": (
            "The classifier, {classifier_model}, was fine-tuned on reviewed synthetic support messages. On "
            "{test_messages} held-out test messages, macro F1 moved from {macro_f1_base} for the base model to "
            "{macro_f1_tuned} after fine-tuning."
        ),
    },
    {
        "id": "summaries",
        "kind": "image",
        "images": ["02-request-analysis.png"],
        "caption": "Example support-message analysis and handoff summary",
        "say": (
            "Handoff summaries kept every essential request in {summary_ok} of {summary_total} held-out messages, "
            "as checked by a reviewer."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3,
        "RAG Model",
        MEMBERS[1],
        "Part three: retrieval-augmented Q&A grounded in curated World Health Organization diabetes information.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["03-source-grounded-answer.png"],
        "caption": "Grounded answer with retrieved WHO source sections",
        "say": (
            "The index contains curated passages from the WHO diabetes questions-and-answers page. In the "
            "pre-fix baseline, a relevant passage appeared in the top three for {retrieval_hits} of "
            "{retrieval_total} answerable questions; {answers_supported} generated answers were judged source-"
            "supported. That baseline also identified referral cases for improvement."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Situated Learning – Workplace Application",
        MEMBERS[0],
        "Part four: the interactive application, documented API, and workplace workflow demonstration.",
    ),
    {
        "id": "tests_terminal",
        "kind": "terminal",
        "commands": ["pytest", "build"],
        "caption": "Backend tests and frontend build, run on this machine moments ago",
        "say": "The backend tests and frontend build were run just before recording: {pytest_summary}.",
    },
    {
        "id": "app_analysis",
        "kind": "app",
        "steps": [
            {
                "fill": "Incoming message",
                "text": (
                    "I need to move my diabetes education appointment, and I cannot find the preparation "
                    "leaflet in the portal."
                ),
            },
            {"click": "Analyze request"},
            {"expect": "appointment support"},
        ],
        "say": (
            "In the live app, a staff member pastes a support message. The fine-tuned classifier returns the "
            "primary category, and the configured base summariser prepares a handoff note for staff review."
        ),
    },
    {
        "id": "app_chat",
        "kind": "app",
        "steps": [
            {
                "fill": "Ask a question",
                "text": "What symptoms might someone with diabetes experience?",
            },
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
                "fill": "Incoming message",
                "text": (
                    "I started a new medicine and now feel sick. Should I stop taking it?"
                ),
            },
            {"click": "Analyze request"},
            {"expect": "clinical staff referral"},
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
        "images": ["04-staff-referral.png"],
        "caption": "Workplace example: a personal medication question is referred to clinic staff",
        "say": "In this workplace scenario, a personal medication question is referred to clinic staff.",
    },
    {
        "id": "closing",
        "kind": "card",
        "eyebrow": "Group 49 · AIMLCZG549 Assignment II",
        "title": "Three connected NLP tasks for clinic support",
        "lines": MEMBERS,
        "say": (
            "To summarise: the application combines a fine-tuned support classifier, handoff summarisation, "
            "and source-grounded question answering for a diabetes clinic support desk. Staff can inspect "
            "categories, summaries, answers, and source passages in the application. Thank you for watching."
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
        "fine-tuned classifier, the base FLAN-T5 summariser, and a retrieval-augmented question-answering "
        "service over curated WHO material. Staff review every output."
    ),
    "part1_card": (
        "Part one outlines the workplace scenario: a fictional diabetes clinic support desk handles requests "
        "about appointments, education, portal access, records, and clinical questions. The application "
        "demonstrates message classification, handoff summaries, and source-based answers for staff."
    ),
    "label_guide": (
        "We route requests into five categories: appointment support, education resource request, portal "
        "technical support, records and insurance administration, and clinical-staff referral. Any personal clinical question overrides the rest and goes "
        "to staff."
    ),
    "part2_card": "Part two covers full fine-tuning of the classifier and summary-quality evaluation.",
    "fine_tuning": (
        "We fully fine-tuned our classifier on synthetic support messages. The held-out results compare the "
        "base model with the fine-tuned checkpoint."
    ),
    "summaries": (
        "We evaluated the configured base summariser on held-out messages for essential-fact retention and unsupported additions."
    ),
    "part3_card": "Part three is the RAG model, grounded in curated WHO diabetes information.",
    "rag_pipeline": (
        "Our index contains curated passages from the WHO diabetes questions-and-answers page. The results shown "
        "are the pre-fix baseline, retained to document the failures that prompted referral-rule changes."
    ),
    "part4_card": "Part four applies the AI solution in a diabetes-clinic workplace scenario.",
    "tests_terminal": "We ran our backend tests and frontend build just before recording.",
    "app_analysis": (
        "In our live app, a staff member pastes a support message. The fine-tuned classifier gives the primary "
        "category, and the base summariser prepares a handoff note for staff review."
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
    "workplace": "In this workplace scenario, a personal medication question is referred to clinic staff.",
    "closing": (
        "To summarise: our application combines a fine-tuned support classifier, handoff summarisation, "
        "and source-grounded question answering for a diabetes clinic support desk. Staff can inspect "
        "categories, summaries, answers, and source passages in the application. Thank you!"
    ),
}
