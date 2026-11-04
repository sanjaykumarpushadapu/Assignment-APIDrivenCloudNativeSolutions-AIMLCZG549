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
        "subtitle": "Classification · Handoff Summaries · Source-Grounded Answers",
        "lines": MEMBERS,
        "footnote": "Equal contribution · 25% per member",
        "say": (
            "Group 49 presents the Diabetes Care Support Assistant: a clinic-support application for classification, "
            "handoff summaries, and source-grounded answers. This is our A.I.M.L. C.Z.G. five four nine, Assignment Two project. "
            "The team members are Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra. "
            "Each member contributed equally, with a 25 percent share."
        ),
    },
    {
        "id": "architecture",
        "kind": "mermaid",
        "title": "Architecture Overview",
        "caption": "Architecture Overview",
        "say": (
            "The React interface sends JSON HTTP requests to FastAPI and receives JSON responses. Inside FastAPI, analyze runs the fine-tuned "
            "classifier and shared FLAN-T5 runtime to return a category and handoff summary. Retrieve returns ranked WHO passages. Chat returns a fixed urgent-care response for matched urgent phrases and a staff referral for matched personal questions; general questions use the shared retriever and FLAN-T5 runtime to return an answer with sources."
        ),
    },
    {
        "id": "chat_checks",
        "kind": "mermaid",
        "diagram_index": 1,
        "title": "Chat Routing and Answer Checks",
        "caption": "Chat Routing and Answer Checks",
        "say": "Chat first checks urgent and personal or clinic-specific requests. For other questions, it retrieves WHO passages. Missing passages or a low retrieval score produce a staff referral. The model then generates an answer. Empty output, an abstention marker, or citation-only text also produces a referral. Accepted output is returned with the retrieved passages for staff review.",
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "API-Based AI Application",
        MEMBERS[3],
        "Part one, API-based AI application, presents the workplace scenario: a fictional diabetes clinic "
        "support desk handles requests about appointments, education, portal access, records and clinical questions. "
        "Bhuvnesh built the React and FastAPI application integrating text classification, text summarisation, "
        "and question answering grounded in retrieved WHO passages.",
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
        "Requests are routed into five categories: appointment support, education resource request, portal "
            "technical support, records and insurance administration, and clinical staff referral. The label guide gives personal clinical questions priority over the other labels; the classifier is trained to follow that rule. Selected urgent phrases receive a fixed urgent-care response."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning",
        MEMBERS[2],
        "Part two, fine-tuning, covers Chezrla's reviewed classification data, supervised training, and base-versus-tuned evaluation.",
    ),
    {
        "id": "fine_tuning",
        "kind": "image",
        "images": ["03-classifier-fine-tuning.png"],
        "caption": "Classifier full fine-tuning method and held-out test results",
        "say": (
            "Each training input combined the classification instruction with a support message; its target "
            "was the reviewed category name. This supervised full fine-tuning adapted {classifier_model} to "
            "the clinic's local taxonomy. On {test_messages} held-out messages, macro F1 increased from "
            "{macro_f1_base} for the prompted base model to {macro_f1_tuned}."
        ),
    },
    {
        "id": "summaries",
        "kind": "image",
        "images": ["02-request-analysis.png"],
        "caption": "Example support-message analysis and handoff summary",
        "say": (
            "The base FLAN-T5 summariser turns the support message into a handoff field. In a separate "
            "{summary_total}-message review, all outputs were supported by their inputs and {summary_ok} "
            "retained every essential fact."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3,
        "Retrieval-Augmented Generation (RAG)",
        MEMBERS[1],
        "Part three, retrieval-augmented generation, covers Sathish's WHO source preparation, curated passages, retrieval, and question answering.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["03-source-grounded-answer.png"],
        "caption": "Grounded answer with retrieved WHO source sections",
        "say": (
            "For each general question, the retriever ranks the WHO passages by embedding similarity and returns "
            "the top three. FLAN-T5 uses those passages as context, and the API returns the answer with its "
            "sources. In the {rag_cases}-case "
            "RAG baseline, retrieval found relevant evidence for {retrieval_hits} of {retrieval_total} "
            "answerable questions; the reviewer judged {answers_supported} answers supported and {answers_complete} "
            "both correct and complete. A current regression check matched {regression_matches} of {regression_total} answer or referral decisions on existing development cases. Those checks measure known-case behaviour."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Situated Learning – Workplace Application",
        MEMBERS[0],
        "Part four, Situated Learning – Workplace Application, presents the team's workplace case: a diabetes-clinic support desk. In this scenario, staff read incoming messages, route appointment, education, portal, and records requests, prepare handoffs, and consult public education material for general questions. The application brings a first-pass category, summary, and relevant passages into one workflow.",
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
            "A staff member enters a natural-language request. The fine-tuned classifier maps it to a primary "
            "clinic category, and the base summariser prepares a handoff field for staff review."
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
            "The question-answering task uses RAG: the system retrieves WHO passages, conditions answer generation "
            "on that context, and displays the passages so staff can verify the source."
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
            "When the question describes someone unconscious, the chat returns a fixed urgent-care response "
            "before retrieval or answer generation."
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
        "id": "api_retrieve",
        "kind": "swagger",
        "path": "/retrieve",
        "body": RETRIEVE_BODY,
        "say": (
            "The retrieve endpoint returns ranked source passages before answer generation, allowing staff "
            "to inspect which information the knowledge assistant selected."
        ),
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
        "caption": "Staff referral for a personal medication question",
        "say": (
            "In this example, the assistant refers a personal medication question to clinic staff. The wider "
            "staff workflow brings request categories, handoff summaries, and source passages into one place. "
            "The evaluation used synthetic cases."
        ),
    },
    {
        "id": "workplace_analysis",
        "kind": "card",
        "eyebrow": "Situated Learning · Part IV",
        "title": "Analyse and Reflect",
        "subtitle": "Workplace Evidence and Priority Improvement",
        "say": (
            "Under Analyse, the reviewed cases assess classification accuracy, summary fact retention, retrieval relevance, and answer support. "
            "They do not measure staff time, request throughput, or live-clinic performance. Under Reflect, the demonstration uses synthetic "
            "messages and public WHO text; its API has no authentication and it is not integrated with scheduling, the patient portal, or records. "
            "Use with identifiable health information would require privacy and security controls, health-data and clinical review, approved "
            "computing, cost planning, and system integration. The single priority before any live workflow is a clinic-approved, access-controlled "
            "pilot with deidentified representative cases and staff review."
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
            "Project summary: the Diabetes Care Support Assistant provides classification, handoff summaries, and question "
            "answering with RAG. The classifier is fully fine-tuned for clinic-support labels, and staff can "
            "inspect answers alongside their retrieved WHO sources. Thank you for watching."
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
        "Part one, API-based AI application, presents the workplace scenario: a fictional diabetes clinic support desk handles requests "
        "about appointments, education, portal access, records, and clinical questions. Bhuvnesh built the "
        "React and FastAPI application integrating classification, summarisation, and source-grounded answers."
    ),
    "label_guide": (
        "We route requests into five categories: appointment support, education resource request, portal "
        "technical support, records and insurance administration, and clinical-staff referral. The label guide gives personal clinical questions priority; the classifier is trained to follow this rule. Selected urgent phrases receive a fixed urgent-care response."
    ),
    "part2_card": (
        "Part two, fine-tuning, covers Chezrla's reviewed classification data, supervised training, and base-versus-tuned evaluation."
    ),
    "fine_tuning": (
        "We fully fine-tuned the pretrained FLAN-T5 model on reviewed synthetic support-message and category "
        "pairs. This adapts its general language understanding to the clinic's exact routing labels."
    ),
    "summaries": (
        "The base summariser was reviewed on 20 messages. All outputs were supported by their input, and 10 retained every essential fact."
    ),
    "part3_card": (
        "Part three, retrieval-augmented generation, covers Sathish's WHO source preparation, curated passages, retrieval, and question answering."
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
        "messages and public WHO text; its API has no authentication and it is not integrated with scheduling, the patient portal, or records. "
        "Use with identifiable health information would require privacy and security controls, health-data and clinical review, approved "
        "computing, cost planning, and system integration. The single priority before any live workflow is a clinic-approved, access-controlled "
        "pilot with deidentified representative cases and staff review."
    ),
    "closing": (
        "Project summary: our Diabetes Care Support Assistant provides classification, handoff summaries, and question "
        "answering with RAG. The classifier is fully fine-tuned for clinic-support labels, and staff can inspect "
        "answers with their WHO sources. Thank you!"
    ),
}
