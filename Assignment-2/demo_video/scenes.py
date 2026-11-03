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
        "kind": "mermaid",
        "caption": "NLP workflow: classification, summarisation, RAG-based QA, and staff review",
        "say": (
            "This is an NLP application because it takes unstructured messages and questions and transforms "
            "them into a category, a handoff summary, or a source-backed answer. The React and TypeScript "
            "interface calls FastAPI. Classification and summarisation support incoming messages; question "
            "answering uses RAG to retrieve WHO passages before FLAN-T5 generates an answer."
        ),
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "API-Based AI Application",
        MEMBERS[3],
        "Part one outlines the workplace scenario: a fictional diabetes clinic "
        "support desk handles requests about appointments, education, portal access, records and clinical questions. "
        "Bhuvnesh built the React and FastAPI application connecting text classification, text summarisation, "
        "and question answering grounded with retrieved WHO passages.",
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
            "labels and is referred to staff. Separate chat rules handle selected urgent phrases; neither "
            "component replaces clinical triage."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning",
        MEMBERS[2],
        "Part two covers Chezrla's reviewed classification data, supervised fine-tuning, and base-versus-tuned evaluation.",
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
        "RAG Model",
        MEMBERS[1],
        "Part three covers Sathish's WHO source preparation, curated passages, retrieval, and RAG question answering.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["03-source-grounded-answer.png"],
        "caption": "Grounded answer with retrieved WHO source sections",
        "say": (
            "A pretrained language model can produce fluent text without showing which approved source supports "
            "it. Our RAG pipeline embeds the question, ranks WHO passages by similarity, and gives the top three "
            "to FLAN-T5 as context. The answer is returned with its source passages. In the {rag_cases}-case "
            "RAG baseline, retrieval found relevant evidence for {retrieval_hits} of {retrieval_total} "
            "answerable questions; the reviewer judged {answers_supported} answers supported and {answers_complete} "
            "both correct and complete."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Situated Learning – Workplace Application",
        MEMBERS[0],
        "Part four covers Sanjay's workplace scenario, representative cases, and analysis of the staff workflow.",
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
            "For this selected urgent phrase, the chat returns a predefined urgent-care "
            "response before retrieval or answer generation."
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
        "caption": "Workplace example: a personal medication question is referred to clinic staff",
        "say": (
            "In this clinic analogue, staff manually identify requests, prepare handoffs, and consult education "
            "material. The application brings categories, summaries, and retrieved sources into one review flow. "
            "Evaluation used synthetic cases; the priority next step is expert review of representative outputs."
        ),
    },
    {
        "id": "closing",
        "kind": "card",
        "eyebrow": "Group 49 · AIMLCZG549 Assignment II",
        "title": "NLP for diabetes-clinic support",
        "lines": MEMBERS,
        "say": (
            "To summarise: this API-driven NLP application combines text classification, text summarisation, "
            "and question answering implemented with RAG. The classifier is fully fine-tuned for clinic-support "
            "labels, and staff can inspect answers alongside their retrieved WHO sources. Thank you for watching."
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
        "Our NLP application processes unstructured support messages and questions. A React and TypeScript "
        "interface calls FastAPI for text classification, handoff summarisation, and question answering with "
        "retrieval-augmented generation over curated WHO material."
    ),
    "part1_card": (
        "Part one outlines the workplace scenario: a fictional diabetes clinic support desk handles requests "
        "about appointments, education, portal access, records, and clinical questions. Bhuvnesh built the "
        "React and FastAPI application connecting classification, summarisation, and source-grounded answers."
    ),
    "label_guide": (
        "We route requests into five categories: appointment support, education resource request, portal "
        "technical support, records and insurance administration, and clinical-staff referral. Any personal clinical question overrides the rest and goes "
        "to staff."
    ),
    "part2_card": (
        "Part two covers Chezrla's reviewed classification data, supervised fine-tuning, and base-versus-tuned evaluation."
    ),
    "fine_tuning": (
        "We fully fine-tuned the pretrained FLAN-T5 model on reviewed synthetic support-message and category "
        "pairs. This adapts its general language understanding to the clinic's exact routing labels."
    ),
    "summaries": (
        "The base summariser was reviewed on 20 messages. All outputs were supported by their input, and 10 retained every essential fact."
    ),
    "part3_card": (
        "Part three covers Sathish's WHO source preparation, curated passages, retrieval, and RAG question answering."
    ),
    "rag_pipeline": (
        "A pretrained model alone may generate an answer without showing its evidence. Our retriever ranks the "
        "WHO passages for each question, passes the top three into FLAN-T5, and returns those sources with the "
        "answer. In the reviewed baseline, retrieval found relevant passages for all 20 answerable questions; "
        "the reviewer judged 18 answers supported and 16 correct and complete."
    ),
    "part4_card": (
        "Part four covers Sanjay's workplace scenario, representative cases, and analysis of the staff workflow."
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
        "For this selected urgent phrase, the chat returns a predefined urgent-care response before retrieval or answer generation."
    ),
    "swagger_intro": "The same features are available through our documented API.",
    "api_metadata": "The metadata endpoint shows which model and index versions are loaded.",
    "api_analyze": "The analyse endpoint returns the category and the handoff summary.",
    "api_retrieve": "The retrieve endpoint returns the ranked source passages before answer generation.",
    "api_chat": "And the chat endpoint returns a grounded answer with its sources.",
    "workplace": (
        "In this clinic analogue, staff manually identify requests, prepare handoffs, and consult education "
        "material. The application brings categories, summaries, and retrieved sources into one review flow. "
        "Evaluation used synthetic cases; the priority next step is expert review of representative outputs."
    ),
    "closing": (
        "To summarise: our API-driven NLP application combines text classification, text summarisation, and "
        "question answering implemented with RAG. It applies supervised fine-tuning to clinic-support labels "
        "and returns WHO passages alongside answers. Thank you!"
    ),
}
