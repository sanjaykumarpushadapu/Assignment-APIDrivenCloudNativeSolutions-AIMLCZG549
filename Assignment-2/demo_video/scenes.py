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
            "Hello, we are Group 49. Our project is the Diabetes Care Support Assistant. It brings three tasks together "
            "for a diabetes-clinic support desk: sorting requests, preparing handoff summaries, and answering general "
            "questions from trusted sources. This is our A.I.M.L. C.Z.G. five four nine, Assignment Two project. "
            "Our team members are Pushadapu Sanjay Kumar, Sathish Krishnan V, Chezrla Raga Suma, and Bhuvnesh Mishra. "
            "We contributed equally, with 25 percent each."
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
            "We shared the work across all four assessment parts, and each of us contributed 25 percent. "
            "Bhuvnesh worked on the React interface, FastAPI routes, and integration. Raga prepared classification examples, "
            "fine-tuned the classifier, and evaluated it. Sathish reviewed the WHO source, prepared local passages, and worked "
            "on embedding retrieval. Sanjay developed the clinic workflow, prepared synthetic cases, and analysed the workplace fit. "
            "These are our main contributions; the tasks overlap across the project."
        ),
    },
    {
        "id": "architecture",
        "kind": "mermaid",
        "title": "Architecture Overview",
        "caption": "Architecture Overview",
        "say": (
            "Here is how the pieces work together. Our React interface sends a JSON request to FastAPI and displays the response. "
            "The analyze route returns a category from the fine-tuned classifier and a handoff summary from FLAN-T5. "
            "Retrieve shows the highest-ranked WHO passages. Chat sends selected urgent phrases to a fixed urgent-care response "
            "and personal-care questions to clinic staff. For general questions, it uses retrieved passages to prepare an answer "
            "and show its sources."
        ),
    },
    {
        "id": "chat_checks",
        "kind": "mermaid",
        "diagram_index": 1,
        "title": "Chat Routing and Answer Checks",
        "caption": "Chat Routing and Answer Checks",
        "say": "When someone uses chat, we check urgent phrases first, then check whether the question is personal or clinic-specific. Those cases get a fixed response or a staff referral. For a general question, we retrieve WHO passages. If none meets our score check, we refer the question. Otherwise, FLAN-T5 drafts an answer from the question and passages. We return it with the passages so staff can review both.",
    },
    # ------------------------------------------------------------- Part 1
    part_card(
        1,
        "API-Based AI Application",
        "Part One is our API-Based AI Application. We chose a diabetes-clinic support desk as our workplace example. Staff may need to route "
        "appointment, education, portal, records, or clinical questions. The React interface sends requests to FastAPI, which connects "
        "classification, handoff summarisation, and question answering from WHO passages.",
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
            "We use five request categories: appointments, education resources, portal support, records and insurance, and "
            "clinical staff referral. When a message asks for personal clinical advice, our label guide prioritises referral. "
            "The classifier was trained with that rule in mind. We check selected urgent phrases separately and return a fixed urgent-care response."
        ),
    },
    # ------------------------------------------------------------- Part 2
    part_card(
        2,
        "Fine-Tuning",
        "Part Two is our fine-tuning work. We prepared and reviewed classification examples, then compared the tuned classifier with the original model.",
    ),
    {
        "id": "fine_tuning",
        "kind": "image",
        "images": ["03-classifier-fine-tuning.png"],
        "caption": "Classifier full fine-tuning method and held-out test results",
        "say": (
            "For training, we gave the model an instruction and a support message, then asked it to produce the reviewed category name. "
            "We fully fine-tuned {classifier_model} for our five clinic-support labels. On {test_messages} held-out messages, "
            "macro F1 went from {macro_f1_base} with the prompted base model to {macro_f1_tuned} with our tuned model."
        ),
    },
    {
        "id": "summaries",
        "kind": "image",
        "images": ["02-request-analysis.png"],
        "caption": "Example support-message analysis and handoff summary",
        "say": (
            "We kept summarisation separate from classifier fine-tuning. The app uses base FLAN-T5 to prepare a handoff summary. "
            "We reviewed {summary_total} messages: every summary stayed within its original message, and {summary_ok} kept every fact marked as essential."
        ),
    },
    # ------------------------------------------------------------- Part 3
    part_card(
        3,
        "Retrieval-Augmented Generation (RAG)",
        "Part Three covers retrieval-augmented generation. We prepared WHO passages and use them to answer general diabetes questions with sources staff can inspect.",
    ),
    {
        "id": "rag_pipeline",
        "kind": "image",
        "images": ["03-source-grounded-answer.png"],
        "caption": "Grounded answer with retrieved WHO source sections",
        "say": (
            "When a staff member asks a general question, we rank the WHO passages by similarity and send the top three, along with the question, to FLAN-T5. "
            "The API returns the answer with those sources. In our {rag_cases}-case baseline, retrieval found a relevant passage for {retrieval_hits} of {retrieval_total} "
            "answerable questions. Reviewers found {answers_supported} answers supported and {answers_complete} both correct and complete. "
            "We also checked {regression_total} existing development cases; the answer or referral decision matched in {regression_matches}. "
            "Those familiar cases make this a regression check, not a fresh evaluation."
        ),
    },
    # ------------------------------------------------------------- Part 4
    part_card(
        4,
        "Situated Learning – Workplace Application",
        "For Part Four, we apply the project to a diabetes-clinic support desk. Staff sort incoming requests, prepare handoffs, and look up public education information for general questions. Our app brings the category, summary, and source passages into one workflow, with staff reviewing the results.",
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
            "Let’s try a support message. The tuned classifier suggests a category, and the summariser prepares a short handoff. "
            "A staff member can compare both with the original message before routing it."
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
            "For a general question, the app first retrieves relevant WHO passages. FLAN-T5 uses them to draft an answer, "
            "and the app displays the passages so staff can check where the information came from."
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
            "Here the question is about changing diabetes medication, so the assistant sends it to clinic staff. "
            "It does not try to recommend a treatment change."
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
            "We also checked an urgent example about someone who is unconscious. The chat returns a fixed urgent-care "
            "message straight away, without trying to generate an answer from the documents."
        ),
    },
    {
        "id": "swagger_intro",
        "kind": "url",
        "url": API_URL + "/docs",
        "wait_for": ".opblock",
        "caption": "Swagger / OpenAPI — FastAPI backend",
        "say": "We can use the same features through FastAPI's Swagger page. I’ll show the request and response for each route.",
    },
    {
        "id": "api_metadata",
        "kind": "swagger",
        "path": "/metadata",
        "say": (
            "First, `/metadata` shows which classifier, summariser, and knowledge index are loaded. This request returned HTTP {status_/metadata}."
        ),
    },
    {
        "id": "api_analyze",
        "kind": "swagger",
        "path": "/analyze",
        "body": ANALYZE_BODY,
        "say": "Here I send a support message to `/analyze`. The response includes the predicted category and the handoff summary.",
    },
    {
        "id": "api_retrieve",
        "kind": "swagger",
        "path": "/retrieve",
        "body": RETRIEVE_BODY,
        "say": (
            "Next, `/retrieve` lets us inspect the passages before an answer is generated. They are ranked by similarity to the question."
        ),
    },
    {
        "id": "api_chat",
        "kind": "swagger",
        "path": "/chat",
        "body": CHAT_BODY,
        "say": "Finally, `/chat` returns an answer with the passages used to prepare it. Staff can read the answer and check its sources together.",
    },
    # ------------------------------------------------------- workplace + end
    {
        "id": "workplace",
        "kind": "image",
        "images": ["04-staff-referral.png"],
        "caption": "Staff referral for a personal medication question",
        "say": (
            "This medication question is referred to clinic staff rather than answered with treatment advice. "
            "Across the workflow, staff can see a request category, a handoff summary, and source passages in one place. "
            "We used synthetic examples for the evaluation."
        ),
    },
    {
        "id": "workplace_analysis",
        "kind": "card",
        "eyebrow": "Situated Learning · Part IV",
        "title": "Analyse and Reflect",
        "subtitle": "Workplace Evidence and Priority Improvement",
        "say": (
            "We checked category accuracy, summary fact retention, retrieval relevance, and whether answers were supported. "
            "We did not measure staff time or test the system in a live clinic. For this demo, we used synthetic messages and public WHO text. "
            "Before workplace use, the clinic would need to approve privacy and security controls, review health-data rules, plan computing and "
            "storage costs, and decide how the system should connect to existing services. Our first step would be a clinic-approved pilot "
            "with deidentified cases and staff review."
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
            "For Part Four, we prepared four individual workplace perspectives on the same diabetes-clinic example. "
            "Bhuvnesh focuses on bringing analysis, handoffs, and answers into one staff workflow. Raga focuses on using the "
            "fine-tuned labels to support request routing. Sathish focuses on retrieving WHO passages for general questions and "
            "referring personal-care questions to staff. Sanjay focuses on preserving details in compound requests and their "
            "handoff summaries. In the report, each perspective follows Anchor, Apply, Analyse, and Reflect."
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
            "To wrap up, we built one staff workflow that combines request classification, handoff summaries, and question answering from WHO passages. "
            "We fully fine-tuned the classifier, and we show the sources beside general answers so staff can review them. "
            "Thanks for watching our project demonstration."
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
