# Diabetes Care Support Assistant

**Course:** AIMLCZG549 - API-Driven Cloud-Native Solutions
**Assignment:** Assignment II
**Group:** 49
**Institution:** BITS Pilani, Work Integrated Learning Programmes

## Project Overview

This project is an interactive, staff-facing prototype for a diabetes clinic support desk. It uses three natural language processing tasks to help staff route incoming messages, prepare handoff summaries, and answer general diabetes questions from a selected source. The application has a React and TypeScript interface with a FastAPI backend.

The three tasks share one workflow objective: help support staff understand and respond to routine enquiries. Classification and summarisation operate on synthetic support messages. The knowledge assistant answers general questions from a curated World Health Organization (WHO) diabetes FAQ and returns the passages used. Clinic-specific procedures and personal treatment decisions are referred to staff because they are outside the indexed source.

| Task | Input and output | Model used by the application |
|---|---|---|
| Request classification | A support message is assigned one primary clinic-support category | Fine-tuned `google/flan-t5-base` checkpoint, `clinic-support` |
| Message summarisation | A support message is condensed into a staff handoff summary | Pinned `google/flan-t5-base` |
| Retrieval-augmented question answering | A question is answered from retrieved WHO passages, with the passages returned as sources | `google/flan-t5-base` answer model and `sentence-transformers/all-MiniLM-L6-v2` retriever |

The base FLAN-T5 model revision is `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`. The application uses separate model settings for the classifier and summariser. Its API exposes `/health`, `/metadata`, `/analyze`, `/retrieve`, and `/chat`.

## I. API-Based AI Application

### Domain and workflow

The selected category is natural language processing in the healthcare-support domain. The workplace is a fictional diabetes clinic support desk, used as an industry analogue. In the proposed workflow, staff read incoming messages, route requests, prepare handoffs, and consult education material when responding to general questions. Staff review the assistant's outputs before using them.

For example, one message may request an appointment change and help finding an education leaflet. The classifier selects the primary queue; the summary preserves the relevant requests for a staff handoff. A separate question about general diabetes information can be submitted to the knowledge assistant, which displays its answer and source passages.

### Application and API

The React interface collects support messages and knowledge questions. FastAPI validates the requests and calls the configured model and retrieval components. `POST /analyze` returns the support-message classification and summary. `POST /retrieve` returns ranked source passages so retrieval can be inspected. `POST /chat` returns a source-grounded answer or a staff-referral response. `/metadata` reports component readiness and model or index versions.

The classifier uses the Hugging Face Transformers sequence-to-sequence interface. The application loads the tokenizer and model from the configured Hub model or local checkpoint. Classification uses a fixed task instruction and returns the generated label only when it matches one of the five supported categories: appointment support, education resource request, portal technical support, records/insurance administration, or clinical staff referral.

### Observed application examples

The application screenshots in Section IV show a support request classified and summarised, a WHO-sourced general-information answer, and a medication question referred to clinic staff. The screenshots use synthetic inputs and illustrate the application path.

### API demonstration

The Swagger UI request below demonstrates `POST /analyze`. Its response confirms the category and summary and makes the omitted pending-booking detail visible for review.

**Figure 1. Swagger request and response for `POST /analyze`.**

![Swagger request and successful response for support message analysis](evidence/swagger-analyze.png)

## II. Fine-Tuning

### Dataset and method

The classifier uses five support categories. The dataset contains 280 synthetic training messages, 60 validation messages, and 60 held-out test messages, with 56 training and 12 validation/test examples per category. The messages are AI-drafted and reviewed by Sanjay for the classification task. Scenario-family identifiers were used when preparing the partitions, and the exact-duplicate review found no repeated messages across the partitions.

The classifier received full fine-tuning from the pinned `google/flan-t5-base` checkpoint. AdamW updated the model parameters for one epoch, using batch size 1, gradient accumulation of 8, learning rate `5e-5`, and seed 42. The run completed 35 optimizer steps. The selected checkpoint and its data hashes, settings, and model-file checksum are recorded in the [classifier run record](evidence/classifier-run-record.json). The model weights are stored outside Git.

### Validation and held-out results

The fine-tuned checkpoint achieved 98.33% accuracy and 98.33% macro-F1 on the 60-example validation set, with no invalid category outputs. The original model scored 71.67% accuracy and 71.81% macro-F1 on the same validation set. The validation set was used during model development, so these figures are validation results.

The base and fine-tuned models were then evaluated on the same 60-example held-out test set, with the same application prompt and greedy decoding. The test set was not used for training or model selection.

| Measure | Base model | Fine-tuned classifier |
|---|---:|---:|
| Accuracy | 86.67% (52/60) | 95.00% (57/60) |
| Macro precision | 95.00% | 95.39% |
| Macro recall | 86.67% | 95.00% |
| Macro-F1 | 88.74% | 94.74% |
| Invalid category outputs | 4/60 | 0/60 |

The fine-tuned model's three errors involved authorised-contact paperwork, preferred language for clinic letters, and insurance coverage for an appointment fee. The examples are synthetic and the test set contains 60 messages; the results describe this dataset and are not a measure of real clinic performance.

### Summary quality check

The configured base summariser was evaluated on 20 reviewed synthetic message/summary cases, each with an essential-fact checklist. Its mean ROUGE-L F1 was 0.3912. Human review found all 20 summaries supported by the input and no added unsupported facts; 10 of 20 retained every essential fact. The result record contains case-level scores and review outcomes in [summariser evaluation evidence](evidence/summarizer-evaluation-record.json). This evaluation shows that summaries can omit details, so the staff handoff should be checked against the original message.

## III. Retrieval-Augmented Generation

### Source and retrieval

The indexed corpus is prepared from one public source: the WHO page [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes), dated 1 September 2026 in the local source manifest. The corpus contains eight curated passages covering diabetes basics, common symptoms, prevention, and high-level education and self-management support. Each passage carries its source title, section, URL, and chunk ID.

The retriever uses `sentence-transformers/all-MiniLM-L6-v2`, pinned to revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, and returns the three highest-ranked passages. The answer model receives the question and retrieved passages. `/chat` includes the source passages with its answer; requests identified as personal clinical advice, urgent symptoms, or clinic-specific processes are routed to staff.

### API demonstration

Swagger UI confirms that `/retrieve` returns ranked WHO passages and that `/chat` returns a staff referral for an individual medication question.

**Figure 2. Swagger response from `POST /retrieve` with ranked WHO passages.**

![Swagger request and retrieved WHO passages](evidence/swagger-retrieve.png)

**Figure 3. Swagger response from `POST /chat` for a medication question.**

![Swagger request and staff referral response](evidence/swagger-chat.png)

### Evaluation results

The first held-out evaluation used 30 reviewed cases: 20 answerable from the indexed source and 10 expected to be referred to staff. The question set was not used for tuning. It measured the application before the referral rules were expanded.

| Measure | Result |
|---|---:|
| Retrieval hit@3 on answerable cases | 20/20 (100%) |
| Expected answer/referral decisions matched | 23/30 (76.7%) |
| Expected staff referrals detected | 4/10 (40%) |
| Answerable questions incorrectly abstained | 1/20 (5%) |
| Answers judged supported by the cited text | 18/20 (90%) |
| Citations judged correct | 18/20 (90%) |
| Answers judged correct and complete | 16/20 (80%) |

The baseline missed referrals for missed-dose advice, an individual glucose reading, clinic appointment and education-session logistics, medication interaction advice, and a severe low-blood-sugar question. Two answerable-case responses were unsupported by their cited passages, and four were incomplete or incorrect. The case counts, dataset hash, model versions, and failure IDs are recorded in the [RAG evaluation record](evidence/rag-evaluation-record.json).

The table is a pre-change baseline. The current implementation includes deterministic routing for personal-care, clinic-process, and urgent-symptom questions. Regression tests cover the added phrasings; the backend suite passes 43 tests. Development diagnostic cases were used while refining the rules and are excluded from performance claims. An independent end-to-end evaluation is still needed to measure answer support and referral quality for the current version.

## IV. Situated Learning - Workplace Application

### Anchor - Identify a workplace problem

The workplace analogue is a diabetes clinic support desk. Staff receive messages about appointments, education resources, the patient portal, records, and clinical questions. The current workflow requires staff to read each message, determine where it should go, prepare a handoff, and search education material when answering general questions. The prototype is expected to reduce the effort needed to understand routine requests and locate supporting passages; no time saving has been measured. This evaluation uses synthetic messages and public education material.

### Apply - Adapt the AI solution

The support-message interface accepts a message and displays its primary category and handoff summary. The knowledge assistant accepts a question, displays an answer, and lists the retrieved WHO passages. In the representative appointment case, the system classified the request as `appointment_support`. Its summary kept the work conflict, requested Friday time, and availability check, but omitted the statement that a new booking was still unconfirmed. This observed omission matches the summary evaluation, where only 10 of 20 outputs retained every essential fact. Staff need to compare a handoff summary with the original message. The prototype does not make or confirm appointments.

For a general symptoms question, `/chat` returned an answer based on WHO01-003, “Common symptoms.” Figure 5 shows the answer and the opened source passage. For “Should I change my diabetes medication?”, the interface displayed the fixed staff-referral response and no sources. These examples demonstrate the classifier, summary, retrieval, answer, and referral components using inputs and outputs from the prototype.

**Figure 4. Appointment request, category, and handoff summary in the web interface.**

![Support request classified and summarized in the staff workspace](evidence/02-request-analysis.png)

**Figure 5. General-information answer with its retrieved WHO passage open.**

![Knowledge assistant answer with WHO source passages](evidence/03-source-grounded-answer.png)

**Figure 6. Medication question referred to clinic staff in the web interface.**

![Knowledge assistant staff referral for a medication-change question](evidence/04-staff-referral.png)

### Analyse - Evaluate workplace relevance

The classifier's held-out test result was 95.00% accuracy and 94.74% macro-F1 on synthetic messages. For summarisation, 10/20 outputs retained all required facts. In the pre-fix RAG evaluation, a relevant passage was retrieved in all 20 answerable cases, while 4/10 referral cases were correctly referred. Together, these results show that classification performed best on the evaluated examples; summarisation and answer/referral quality still require staff review. The retrieval score alone did not ensure that a generated answer was supported.

The evaluation did not measure staff handling time or throughput. It therefore does not establish a reduction in work or an efficiency gain. The prototype demonstrates the message-routing and source-inspection workflow; it does not perform clinic transactions or access a clinic's internal procedures.

### Reflect - Deployment constraints and improvement

The prototype uses synthetic support messages and public education material. Before any use with real health information, the clinic would need to determine permitted data use, access and retention controls, and applicable privacy and security requirements. The regulatory requirements depend on the organisation and jurisdiction. The model and retrieval components run as a locally configured application. Deployment costs would depend on the selected hosting, model storage, inference capacity, monitoring, and maintenance; no operating-cost estimate has been measured. Clinic-specific appointment, portal, and leaflet instructions would need to come from approved clinic sources before the assistant could answer those questions.

The priority improvement before any patient-facing use is an independent, clinician-reviewed evaluation of the full workflow on approved representative cases, focused on summary fact preservation, answer support, and correct staff referral. This is justified by the observed incomplete summaries and missed referrals in the held-out evaluations. The prototype does not connect to clinic scheduling, portal, or records systems; any integration would require approved interfaces and workflow validation.

## Team Contributions

The group confirmed an equal overall contribution share of 25% per member. The table records each member’s primary contribution area and the agreed quantitative share.

| Team member | BITS ID | Primary contribution area | Share |
|---|---|---|---:|
| Pushadapu Sanjay Kumar | 2025ae05898 | Workplace scenario, synthetic dataset and label review, evaluation review, and report | 25% |
| Sathish Krishnan V | 2025ae05425 | Diabetes knowledge source, retrieval pipeline, and source-grounded answers | 25% |
| Chezrla Raga Suma | 2025ae05828 | FLAN-T5 classifier fine-tuning and evaluation; summarisation result review | 25% |
| Bhuvnesh Mishra | 2025ae05391 | FastAPI and React application; model and retrieval integration | 25% |

## Project Links

**Source repository:** [Assignment-2 GitHub repository](https://github.com/sanjaykumarpushadapu/Assignment-APIDrivenCloudNativeSolutions-AIMLCZG549)

**Demonstration video:** Google Drive link to be added after the required project demonstration is uploaded.

## References

1. Course brief, *AIMLZG 549: API-driven Cloud Native Solutions, Assignment II* (`Assignment 2.pdf`).
2. Google / Hugging Face. [FLAN-T5 Base model card](https://huggingface.co/google/flan-t5-base).
3. Hugging Face. [Transformers T5 documentation](https://huggingface.co/docs/transformers/en/model_doc/t5).
4. World Health Organization. [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes).
5. Sentence Transformers. [all-MiniLM-L6-v2 model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).
