"""Scene list for the Group 49 Assignment II demonstration video.

Each scene is one shot: what the viewer sees (``kind`` + its options) and what
the narrator says (``say``). The recorder turns every scene into one clip whose
length follows the narration, then joins them in order.

Narration placeholders such as ``{macro_f1_tuned}`` are filled from facts
collected during preflight: live test results, ``/metadata`` versions, and the
tracked run records in ``docs/report/evidence``.

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
    "rag_regression": "docs/report/evidence/rag-current-regression.json",
}
IMAGES_DIR = "docs/report/evidence"

ANALYZE_BODY = (
    '{\n  "message": "I need to move my diabetes education appointment, and I cannot find '
    'the preparation leaflet in the portal."\n}'
)
CHAT_BODY = (
    '{\n  "question": "What symptoms might someone with diabetes experience?"\n}'
)
RETRIEVE_BODY = (
    '{\n  "question": "What symptoms might someone with diabetes experience?"\n}'
)


def part_card(number, title, say):
    return {
        "id": f"part{number}_card",
        "kind": "card",
        "eyebrow": f"Part {number} of 4",
        "title": title,
        "say": say,
    }


SCENES = [
    {
        "id": "title",
        "kind": "card",
        "eyebrow": "AIMLCZG549 · API-Driven Cloud-Native Solutions · Assignment II · Group 49",
        "title": "Diabetes Care Support Assistant",
        "subtitle": "Classification · Handoff Summaries · Source-Grounded Answers",
        "lines": MEMBERS,
        "footnote": "Equal contribution · 25% per member",
        "say": (
            "Hello, we are Group 49. This is our Diabetes Care Support Assistant for Assignment Two. It classifies clinic requests, "
            "prepares handoff summaries, and answers general questions using WHO sources. Our team is Pushadapu Sanjay Kumar, "
            "Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra. Each contributed 25 percent."
        ),
    },
    {
        "id": "team_contributions",
        "kind": "card",
        "eyebrow": "Group 49 · Equal contribution · 25% each",
        "title": "Team Contributions",
        "subtitle": "Shared project work across the four assessment parts",
        "lines": [
            "Bhuvnesh Mishra · React interface, FastAPI routes, and workflow integration",
            "Chezrla Raga Suma · Classification examples, fine-tuning, and model evaluation",
            "Sathish Krishnan V · WHO source review, local passages, and embedding retrieval",
            "Pushadapu Sanjay Kumar · Clinic workflow, synthetic cases, and workplace analysis",
        ],
        "footnote": "Each member contributed 25%",
        "say": (
            "Our contributions were equal across the project. Bhuvnesh built the React interface and FastAPI routes. "
            "Raga prepared classification examples and evaluated the fine-tuned model. Sathish curated WHO passages and retrieval. "
            "Sanjay developed the workflow, synthetic cases, and workplace analysis. We also reviewed the connected system together."
        ),
    },
    {
        "id": "architecture",
        "kind": "mermaid",
        "title": "Architecture Overview",
        "caption": "Architecture Overview",
        "say": (
            "React sends JSON requests to FastAPI and displays its responses. Analyze uses the fine-tuned classifier and FLAN-T5 summariser; "
            "retrieve returns ranked WHO passages. Chat checks urgent and personal-care questions before using retrieved text to answer general questions."
        ),
    },
    {
        "id": "chat_checks",
        "kind": "mermaid",
        "diagram_index": 1,
        "title": "Chat Routing and Answer Checks",
        "caption": "Chat Routing and Answer Checks",
        "say": "Chat checks urgent phrases and personal-care requests first, returning urgent guidance or a staff referral. For general questions, it retrieves WHO passages, checks their scores, and asks FLAN-T5 to draft an answer. The response includes its sources for staff review.",
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "API-Based AI Application",
        "Part One presents our React and FastAPI application. It connects request classification, handoff summarisation, and WHO-grounded question answering for a diabetes-clinic workflow.",
    ),
    {
        "id": "label_guide",
        "kind": "code",
        "file": "data/pilot/label_guide.md",
        "regex": r"^## Labels",
        "window": [0, 24],
        "highlight": r"clinical_staff_referral",
        "caption": "Five Support Categories and the Clinical Referral Rule",
        "say": (
            "Our five labels cover appointments, education, portal support, records or insurance, and clinical referral. Personal-care requests are referred; selected urgent phrases receive a fixed urgent-care response."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning",
        "Part Two compares the prompted base model with our fully fine-tuned classifier on held-out messages.",
    ),
    {
        "id": "fine_tuning",
        "kind": "image",
        "images": ["03-classifier-fine-tuning.png"],
        "caption": "Classifier full fine-tuning method and held-out test results",
        "say": (
            "We fine-tuned {classifier_model} to produce one of five reviewed labels from a support message. On {test_messages} held-out examples, "
            "macro F1 improved from {macro_f1_base} for the prompted base model to {macro_f1_tuned} for the tuned model."
        ),
    },
    {
        "id": "summaries",
        "kind": "image",
        "images": ["02-request-analysis.png"],
        "caption": "Example support-message analysis and handoff summary",
        "say": (
            "Summarisation uses base FLAN-T5. All {summary_total} reviewed summaries were supported by their messages; {summary_ok} retained every required fact."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3,
        "Retrieval-Augmented Generation (RAG)",
        "Part Three uses retrieved WHO passages to ground answers to general diabetes questions.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["03-source-grounded-answer.png"],
        "caption": "Grounded answer with retrieved WHO source sections",
        "say": (
            "We rank local WHO passages and give the top three to FLAN-T5 with the question. In the {rag_cases}-case baseline, retrieval found a relevant passage for "
            "{retrieval_hits} of {retrieval_total} answerable questions; {answers_supported} answers were supported and {answers_complete} were correct and complete. "
            "A separate {regression_total}-case development regression check matched {regression_matches} expected decisions; it is not an independent evaluation."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Situated Learning – Workplace Application",
        "Part Four applies the workflow to a diabetes-clinic support desk, with separate workplace perspectives for all four members.",
    ),
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
            "The classifier suggests a request category and the summariser prepares a handoff for staff review."
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
            "For general questions, the answer appears with the WHO passages staff can check."
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
            "A medication-change question is referred to clinic staff, not answered with treatment advice."
        ),
    },
    {
        "id": "app_urgent_care",
        "kind": "app",
        "steps": [
            {
                "fill": "Ask a question",
                "text": "My father is unconscious, what is the next step?",
            },
            {"click": "Send question"},
            {
                "expect": (
                    "This may need urgent medical attention. Contact local emergency "
                    "services or follow your clinic’s urgent-care instructions now."
                )
            },
        ],
        "say": (
            "An unconscious-person example returns the fixed urgent-care message before document retrieval or generation."
        ),
    },
    {
        "id": "swagger_intro",
        "kind": "url",
        "url": API_URL + "/docs",
        "wait_for": ".opblock",
        "caption": "Swagger / OpenAPI — FastAPI backend",
        "say": "Swagger shows the same FastAPI routes and their JSON responses.",
    },
    {
        "id": "api_metadata",
        "kind": "swagger",
        "path": "/metadata",
        "say": (
            "`/metadata` reports readiness for the classifier, summariser, and knowledge index: HTTP {status_/metadata}."
        ),
    },
    {
        "id": "api_analyze",
        "kind": "swagger",
        "path": "/analyze",
        "body": ANALYZE_BODY,
        "say": "`/analyze` returns the request category and handoff summary.",
    },
    {
        "id": "api_retrieve",
        "kind": "swagger",
        "path": "/retrieve",
        "body": RETRIEVE_BODY,
        "say": (
            "`/retrieve` returns passages ranked by similarity to the question."
        ),
    },
    {
        "id": "api_chat",
        "kind": "swagger",
        "path": "/chat",
        "body": CHAT_BODY,
        "say": "`/chat` returns the answer with its source passages for review.",
    },
    # ------------------------------------------------------- workplace + end
    {
        "id": "workplace",
        "kind": "image",
        "images": ["04-staff-referral.png"],
        "caption": "Staff referral for a personal medication question",
        "say": (
            "The workflow combines categories, summaries, and source passages. We evaluated it with synthetic cases."
        ),
    },
    {
        "id": "workplace_analysis",
        "kind": "card",
        "eyebrow": "Situated Learning · Part IV",
        "title": "Analyse and Reflect",
        "subtitle": "Workplace Evidence and Priority Improvement",
        "say": (
            "We measured classification, summary fact retention, retrieval relevance, and answer support using synthetic cases and public WHO text. "
            "We did not measure staff time or live-clinic performance. Workplace use needs approved privacy and security controls, health-data review, "
            "infrastructure and cost planning, and integration decisions. Our priority improvement is a clinic-approved pilot with deidentified cases and staff review."
        ),
    },
    {
        "id": "workplace_perspectives",
        "kind": "card",
        "eyebrow": "Situated Learning · Part IV",
        "title": "Four Workplace Perspectives",
        "subtitle": "One clinic workflow, four individual applications",
        "lines": [
            "Bhuvnesh · bring analysis, handoffs, and answers into one staff workflow",
            "Raga · use the fine-tuned labels to support request routing",
            "Sathish · retrieve WHO passages for general questions and refer personal-care questions",
            "Sanjay · preserve details when a message combines requests",
        ],
        "say": (
            "Our report has four individual Part Four applications. Bhuvnesh focuses on joining analysis, handoffs, and answers in one staff workflow; "
            "Raga on classification for request routing; Sathish on source-based answers and staff referral; and Sanjay on preserving details in compound handoffs. "
            "Each version covers the assessment’s workplace context, application, evaluation, and reflection."
        ),
    },
    {
        "id": "closing",
        "kind": "card",
        "eyebrow": "Group 49 · AIMLCZG549 Assignment II",
        "title": "Project Summary",
        "subtitle": "Classification · Handoff Summaries · Question Answering with RAG",
        "lines": MEMBERS,
        "say": (
            "Our application combines classification, handoff summaries, and WHO-grounded answers, with outputs available for staff review. Thank you for watching."
        ),
    },
]

# ---------------------------------------------------------------------------
# Student-style script for your own voice (record_voice.py, --tts files).
# One person reads every scene. No {placeholders}: the measured values are on
# screen, so these scripts can be recorded on any computer.
# ---------------------------------------------------------------------------
SELF_SCRIPTS = {
    "chat_checks": next(scene["say"] for scene in SCENES if scene["id"] == "chat_checks"),
    "team_contributions": next(scene["say"] for scene in SCENES if scene["id"] == "team_contributions"),
    "title": (
        "Hello everyone! We're Group 49, and this is our AIMLCZG549, Assignment Two project: the Diabetes "
        "Care Support Assistant for classification, handoff summaries, and source-grounded answers. Our team is Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, "
        "and Bhuvnesh Mishra. Each member contributed equally, with a 25 percent share."
    ),
    "architecture": (
        "The React interface sends JSON HTTP requests to FastAPI and receives JSON responses. Inside FastAPI, analyse runs the fine-tuned "
        "classifier and shared FLAN-T5 runtime to return a category and handoff summary. Retrieve returns ranked WHO passages. Chat returns a fixed urgent-care response for matched urgent phrases and a staff referral for matched personal questions; general questions use the shared retriever and FLAN-T5 runtime to return an answer with sources."
    ),
    "part1_card": (
        "Part one is our API-based AI Application. We use a fictional diabetes-clinic support desk where staff handle requests "
        "about appointments, education, portal access, records, and clinical questions. The React interface sends requests to FastAPI, "
        "which connects classification, handoff summaries, and source-grounded answers."
    ),
    "label_guide": (
        "We route requests into five categories: appointment support, education resource request, portal "
        "technical support, records and insurance administration, and clinical-staff referral. The label guide gives personal clinical questions priority; the classifier is trained to follow this rule. Selected urgent phrases receive a fixed urgent-care response."
    ),
    "part2_card": (
        "Part two covers our classification examples, supervised fine-tuning, and base-versus-tuned evaluation."
    ),
    "fine_tuning": (
        "We fully fine-tuned the pretrained FLAN-T5 model on reviewed synthetic support-message and category "
        "pairs. This adapts its general language understanding to the clinic's exact routing labels."
    ),
    "summaries": (
        "The base summariser was reviewed on 20 messages. All outputs were supported by their input, and 10 retained every essential fact."
    ),
    "part3_card": (
        "Part three covers our WHO source preparation, curated passages, retrieval, and question answering."
    ),
    "rag_pipeline": (
        "For each general question, the retriever ranks the WHO passages by embedding similarity and returns "
        "the top three. FLAN-T5 uses those passages as context, and the API returns the answer with its sources. "
        "In the reviewed baseline, retrieval found relevant passages for all 20 answerable questions; the reviewer "
        "judged 18 answers supported and 16 correct and complete."
    ),
    "part4_card": (
        "Part four, Situated Learning – Workplace Application, presents the team's workplace case: a diabetes-clinic support desk. In this scenario, staff read incoming messages, route appointment, education, portal, and records requests, prepare handoffs, and consult public education material for general questions. The application brings a first-pass category, summary, and relevant passages into one workflow."
    ),
    "app_analysis": (
        "In our live app, a staff member enters a support message. The fine-tuned classifier returns a clinic "
        "category, and the base summariser prepares a handoff field."
    ),
    "app_chat": (
        "Our RAG question-answering flow retrieves WHO passages, generates an answer using that context, and "
        "shows the sources for staff review."
    ),
    "app_referral": (
        "A personal medication question is routed to clinical staff. Our assistant doesn't give clinical "
        "advice."
    ),
    "app_urgent_care": (
        "When a question describes someone unconscious, the chat returns a fixed urgent-care response before retrieval or answer generation."
    ),
    "swagger_intro": "The same features are available through our documented API.",
    "api_metadata": "The metadata endpoint shows which model and index versions are loaded.",
    "api_analyze": "The analyse endpoint returns the category and the handoff summary.",
    "api_retrieve": "The retrieve endpoint returns the ranked source passages before answer generation.",
    "api_chat": "And the chat endpoint returns a grounded answer with its sources.",
    "workplace": (
        "In this example, the assistant refers a personal medication question to clinic staff. The wider staff "
        "workflow brings request categories, handoff summaries, and source passages into one place. The evaluation "
        "used synthetic cases."
    ),
    "workplace_analysis": (
        "Under Analyse, the reviewed cases assess classification accuracy, summary fact retention, retrieval relevance, and answer support. "
        "They do not measure staff time, request throughput, or live-clinic performance. Under Reflect, the demonstration uses synthetic "
        "messages and public WHO text. Workplace use would require clinic-approved privacy and security controls, review of health-data "
        "requirements, approved computing and storage, cost planning, and decisions about integration with existing systems. The single "
        "priority before applying the workflow is a clinic-approved pilot with deidentified representative cases and staff review."
    ),
    "workplace_perspectives": (
        "For Part Four, we prepared four individual workplace perspectives on the same diabetes-clinic example. Bhuvnesh focuses on bringing "
        "analysis, handoffs, and answers into one staff workflow. Raga focuses on using the fine-tuned labels to support request routing. "
        "Sathish focuses on retrieving WHO passages for general questions and referring personal-care questions to staff. Sanjay focuses on "
        "preserving details in compound requests and their handoff summaries. In the report, each perspective follows Anchor, Apply, Analyse, and Reflect."
    ),
    "closing": (
        "Project summary: our Diabetes Care Support Assistant provides classification, handoff summaries, and question "
        "answering with RAG. The classifier is fully fine-tuned for clinic-support labels, and staff can inspect "
        "answers with their WHO sources. Thank you!"
    ),
}
