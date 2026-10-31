# Diabetes Care Support Assistant

**Course:** AIMLCZG549 - API-Driven Cloud-Native Solutions  
**Assignment:** Assignment II  
**Group:** 49 (carried over from Assignment I; confirm before submission)  
**Institution:** BITS Pilani, Work Integrated Learning Programmes  
**Last updated:** 31 October 2026  
**Document status:** Working draft; updated as implementation and verification progress.

This report records the design, implementation and evidence for a staff-facing diabetes-clinic support assistant. The project covers three connected NLP tasks: request classification, message summarisation and document-grounded question answering. The current verified implementation covers baseline classification and its configuration. Fine-tuning, summarisation, retrieval and the complete workplace evaluation remain pending.

The Markdown report is the editable source. Screenshots, completed results, references and confirmed contributions will be added here before final PDF export. This is not the final submission.

## Team Contributions

The roster below follows Assignment I. Assignment II contributions and percentages must be confirmed from actual completed work before submission; the previous assignment's contributions are not reused as evidence.

| Team member | BITS ID | Assignment II contribution | Confirmed share |
|---|---|---|---|
| Pushadapu Sanjay Kumar | 2025ae05898 | Pending final member confirmation | Pending |
| Sathish Krishnan V | 2025ae05425 | Pending final member confirmation | Pending |
| Chezrla Raga Suma | 2025ae05828 | Pending final member confirmation | Pending |
| Bhuvnesh Mishra | 2025ae05391 | Pending final member confirmation | Pending |

## Project and Implementation Status

| Assessment component | Marks | Current status | Evidence still required |
|---|---:|---|---|
| I. API-based AI application | 4 | React/FastAPI skeleton exists; baseline classifier implemented and wired through its interface | Working summariser and chatbot; integrated application screenshots and final API demonstrations |
| II. Fine-tuning | 2 | Pilot labels reviewed; no model training performed | Reviewed training/validation/test data, training records, saved checkpoint, reload and base-versus-tuned results |
| III. RAG model | 4 | Knowledge-answering interface exists; implementation pending | Document inventory, retrieval, grounded chatbot answers, sources and evaluation |
| IV. Situated Learning - Workplace Application | 5 | Industry-analogue workflow proposed | Anchor, Apply, Analyse and Reflect supported by actual workflow evidence |
| Report and video | Included above | This report is in progress; recording utilities exist | Final screenshots, complete-project video, accessible Google Drive link and member submissions |

## Architecture Overview

The existing application separates the interface, HTTP routes, workflow logic and model adapters. This allows the model implementation to change while the workflow continues to call the same `classify(message)` operation.

| Component | Responsibility | Current implementation |
|---|---|---|
| React + TypeScript frontend | Collect support messages and questions; show API results | Application skeleton |
| FastAPI presentation layer | Validate HTTP requests and expose `/health`, `/metadata`, `/analyze` and `/chat` | Implemented routes |
| Application layer | Coordinate classification, summarisation and knowledge answering | Existing use cases |
| Classifier interface | Define `classify(message)` and readiness status | Existing protocol |
| Model infrastructure | Load tokenizer/weights and generate predictions | Configurable `FlanT5Classifier` |
| Configuration | Select model, revision, device, paths and generation limits | `ClassifierSettings` reads `.env` and environment variables |
| Summariser and knowledge answerer | Generate summaries and document-grounded answers | Unconfigured placeholders |

The classifier loads on first prediction and reuses its weights for subsequent calls in the same process. Each new process loads its own model copy. A new API process initially reports the classifier as not ready until loading occurs. `/analyze` requires both classification and summarisation; while the summariser is missing it returns HTTP 503 before running classification. `/chat` also returns HTTP 503 until the knowledge component is configured.

## 1. API-Based AI Application

### 1.1 Domain, problem and users

The selected domain is healthcare support, continuing Assignment I's diabetes theme. The application addresses routine support messages that clinic staff must read, route and answer using education resources and administrative procedures. The proposed organisation is a fictional diabetes clinic used as an industry analogue; no real clinic deployment or access to patient records is claimed.

The intended user is a clinic support worker. Staff review outputs before communicating with patients. The assistant supports education and administrative workflows; personal clinical decisions are referred to qualified staff.

### 1.2 Three cohesive NLP tasks

| Task | Intended input and output | Progress |
|---|---|---|
| Request classification | Support message to a primary support category | Baseline prediction verified |
| Summarisation | Message/conversation to a factual staff handoff summary | Pending |
| Question answering | Staff question and retrieved documents to an answer with sources | Pending; covered by the RAG implementation |

All three tasks support one objective: reduce staff effort in understanding and responding to diabetes support enquiries. A representative case is an appointment-change request combined with a missing education leaflet. Classification identifies the main request, the summary retains both needs, and document-grounded Q&A supplies the relevant procedure once implemented.

### 1.3 Model choice and baseline inference

The initial language model is `google/flan-t5-base`, loaded with Hugging Face Transformers using `AutoTokenizer` and `AutoModelForSeq2SeqLM`. The verified baseline uses revision `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` for both tokenizer and weights.

The classification instruction lists five categories and their meanings:

1. `appointment_support`: appointment booking, confirmation, cancellation or changes.
2. `education_resource_request`: general education materials and new class enrollment.
3. `portal_technical_support`: login, display, upload or other portal failures.
4. `records_insurance_admin`: records, insurance, billing and administrative paperwork.
5. `clinical_staff_referral`: personal medical questions or requests needing clinical review.

The prompt directs mixed requests containing personal clinical advice to the clinical-referral category. This instruction is not evidence of reliable referral performance; that behaviour still requires evaluation.

The tokenizer converts the complete instruction and message into numerical tensors. The model runs in evaluation mode under `torch.inference_mode()`, generates at most 32 new tokens by default with random sampling disabled, and the tokenizer decodes the answer. The code preserves unexpected output and returns a null category if the answer does not exactly match an allowed label. Category validity alone does not establish correctness.

No optimizer, training loop or weight update is used in these baseline runs. The current output records `weights_updated_during_inference: false`.

### 1.4 Pilot data and review

The classification pilot contains 35 synthetic, AI-drafted messages, seven per category. Each record tracks its example ID, message, category, scenario family, provenance, authoring method and review metadata. Codex reviewed the labels on 30 October 2026 at the user's request and marked the examples `ai_approved_for_pilot`, scoped to classification feasibility. This is AI review by the same assistant that drafted the examples; it is not independent team-member or clinical review.

Ten additional routing checks are documented in the existing label guide. They cover mixed clinical/administrative messages, educational versus personal-result questions, technical failures, ambiguous requests and unrelated requests. These are expected behaviours, not observed test passes, and remain outside classifier training.

The pilot has valid JSON, balanced class counts, unique IDs and no exact duplicate messages. Related scenarios are grouped to support leakage-aware dataset preparation. The pilot is development material and must not be presented as a final held-out benchmark. The larger reviewed dataset and separate evaluation collections remain pending.

### 1.5 Configurable model and runtime

The active `.env` file was created from `.env.example` on 31 October 2026. `ClassifierSettings.from_env()` reads the file from Assignment-2 regardless of the terminal's working directory. Environment variables take precedence. Both the terminal command and application classifier read the same configuration. Changes apply after restarting the process. The active `.env` is excluded from Git.

| Setting | Verified/default value | Purpose |
|---|---|---|
| `CLASSIFIER_MODEL` | `google/flan-t5-base` | Hub model ID or complete compatible checkpoint directory |
| `CLASSIFIER_REVISION` | Blank resolves to the pinned baseline revision | Select a reproducible Hub revision |
| `CLASSIFIER_DEVICE` | `cpu` | Choose CPU, CUDA, MPS or automatic device selection |
| `CLASSIFIER_CACHE_DIR` | `artifacts/huggingface` | Keep model downloads outside source control |
| `CLASSIFIER_MAX_INPUT_TOKENS` | `512` | Reject oversized full prompts rather than silently truncating them |
| `CLASSIFIER_MAX_NEW_TOKENS` | `32` | Bound generated answer length |
| `CLASSIFIER_LOCAL_FILES_ONLY` | `false` | Optionally require cached/local weights without downloads |

Changing the Hub model without specifying a revision does not inherit the baseline's commit SHA. Relative checkpoint/cache paths resolve from Assignment-2. The current loader supports compatible Hugging Face sequence-to-sequence models with safetensors weights and a matching tokenizer. Chat-model architectures, hosted providers and adapter-only LoRA checkpoints need an appropriate implementation behind the classifier interface. Alternative model quality, GPU inference and fine-tuned checkpoint loading have not yet been demonstrated.

### 1.6 Verified baseline results

The following two messages were run by the user from the terminal on 31 October 2026 and returned the expected categories. The same messages also passed after moving the implementation into the application skeleton. The configurable adapter subsequently returned the portal category using the cached baseline model.

| Input | Expected category | Observed output | Outcome |
|---|---|---|---|
| Please move my appointment to Friday. | `appointment_support` | `appointment_support` | Matches |
| The clinic portal will not let me sign in. | `portal_technical_support` | `portal_technical_support` | Matches |

These are selected development examples. They are not a held-out accuracy estimate and do not establish performance across all five categories or reliable clinical referral.

Observed environment: Python 3.11.5, PyTorch 2.15.0, Transformers 5.22.1, macOS and CPU inference. Dependency ranges do not lock future installations to these exact versions. Model loading logged a macOS redirection note and a tied-weights warning; prediction completed successfully, and the configuration was not changed merely to suppress those messages.

Verified engineering checks include two successive predictions reusing one model object, rejection of blank and oversized inputs, and reporting the missing summariser through the API. On 31 October, the automated backend/configuration suite completed with **15 tests passed and one browser test deselected**. The configuration tests include file/environment precedence, revision selection, local paths, invalid settings and passing configured loader options. Mocked loader tests establish configuration behaviour, not actual alternative-model or GPU performance. Formatting and lint checks passed.

Reproduction command from Assignment-2, after installing the inference dependencies:

```bash
.venv/bin/python -m diabetes_support.infrastructure.flan_t5_classifier --message "The clinic portal will not let me sign in."
```

Evidence still to add: readable terminal screenshots of both selected examples, active settings verification and the final integrated UI/API. No screenshot is claimed to exist merely because a terminal result is recorded here.

## 2. Fine-Tuning

**Status: pending.** No model has been fine-tuned in the work documented above. The intended experiment trains a compatible language model on labelled support messages, retains an untouched test partition, and compares original and tuned models using identical test cases. Record actual dataset provenance, review, scenario-grouped splits, hyperparameters, hardware, loss history, saved checkpoint/tokenizer, reload verification, macro-F1, accuracy, per-class results and failures when completed.

The 35-message pilot can verify the mechanics of a small training/save/reload run. It does not replace the planned reviewed dataset or justify an overall quality claim.

## 3. Retrieval-Augmented Generation

**Status: pending.** The intended chatbot retrieves relevant passages from reviewed domain documents and uses them as context for source-backed answers. Add the actual document inventory and permissions, extraction/chunking details, embedding model and index versions, retrieved passages, generation settings, source display, follow-up behaviour, unsupported-query handling and retrieval/answer evaluation after implementation. Public diabetes-education sources and fictional clinic procedures must be distinguished.

## 4. Situated Learning - Workplace Application

### 4.1 Anchor - Workplace problem

Proposed industry analogue: a fictional diabetes clinic support desk. Staff manually inspect incoming messages, identify the responsible queue, summarise requests and search approved procedures or education documents. The intended benefit is lower handling effort with outputs reviewed by staff. This is a proposed workflow, not an observed organisational deployment.

### 4.2 Apply - Adaptation and representative outputs

**Pending full demonstration.** The two baseline classifications in Section 1.6 provide limited technical evidence. Complete workplace cases must additionally show the summary, the fine-tuned classifier, retrieved sources and chatbot answers together. Include an appropriate referral or abstention case and retain representative inputs and actual outputs.

### 4.3 Analyse - Workplace relevance

**Pending measurement.** Evaluate quality, source support, completeness, response time, corrections required and representative manual-versus-assisted handling times. Report failures, sample sizes and the gap between this synthetic prototype and practical organisational use. No efficiency improvement, clinical readiness or scalability result is claimed at this stage.

### 4.4 Reflect - Constraints and priority improvement

**Pending final reflection.** Address privacy, security, applicable regulation, infrastructure, cost and integration, using the final implementation and observed failures. Justify one most important improvement before workplace deployment. The current candidate is clinician-led validation of answer correctness and referral behaviour before patient-facing use; confirm that priority against the final evidence.

The brief's exception for individual Situated Learning submissions needs instructor clarification. Keep this section ready for member-specific adaptation before final submission.

## 5. Demonstration, Limitations and Submission

The current prototype has a functioning baseline classifier and configurable model loading. Summarisation, full application analysis, fine-tuning and RAG remain unfinished. The recorded examples and automated engineering checks have different purposes and must not be combined into an AI accuracy claim.

The final demonstration video must cover the complete project and be uploaded to Google Drive with verified viewer access. **Final video link: pending.** Screenshots, measured outcomes, member-approved contributions and the complete separate workplace section are also pending. After final review, export this report as `49.pdf` or `49.docx` if Group 49 continues, and verify every member's required portal submission. The team has supplied 12 November 2026 as the official date; the portal's exact cutoff still needs verification.

## References

1. Course Assignment II brief, supplied locally as `Assignment-2/Assignment 2.pdf`; assessed requirements and submission instructions.
2. Google / Hugging Face. [FLAN-T5 Base model card](https://huggingface.co/google/flan-t5-base). Model identity and loading reference; the verified revision is recorded in Section 1.3.
3. Hugging Face. [Transformers T5 documentation](https://huggingface.co/docs/transformers/en/model_doc/t5). Tokenizer and sequence-to-sequence model API reference.
4. Group 49. Assignment I report, `Assignment-1/docs/report/REPORT.md`. Structure and team roster reference; Assignment I results are not Assignment II evidence.
