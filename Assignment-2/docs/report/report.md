# Diabetes Care Support Assistant

**Course:** AIMLCZG549 - API-Driven Cloud-Native Solutions  
**Assignment:** Assignment II  
**Group:** 49\
**Institution:** BITS Pilani, Work Integrated Learning Programmes  
**Document status:** Working draft.

This report records the design, implementation and evidence for a staff-facing diabetes-clinic support assistant. The project covers three connected NLP tasks: request classification, message summarisation and document-grounded question answering. The classifier has been fine-tuned from `google/flan-t5-base`; the summariser continues to use the original base model. A source-coverage guard retains original sentences omitted by generated summaries. Retrieval and the complete workplace evaluation remain pending; summary accuracy still requires staff review.

## Team Contributions

Assignment II contributions and percentages must be confirmed from actual completed work before submission.

| Team member | BITS ID | Assignment II contribution | Confirmed share |
|---|---|---|---|
| Pushadapu Sanjay Kumar | 2025ae05898 | Pending final member confirmation | Pending |
| Sathish Krishnan V | 2025ae05425 | Pending final member confirmation | Pending |
| Chezrla Raga Suma | 2025ae05828 | Pending final member confirmation | Pending |
| Bhuvnesh Mishra | 2025ae05391 | Pending final member confirmation | Pending |

## Project and Platform Details

| Detail | Description |
|---|---|
| Domain | Staff-facing support for a fictional diabetes clinic |
| Application | React + TypeScript interface and FastAPI endpoints documented with Swagger/OpenAPI |
| Classification | Fine-tuned `google/flan-t5-base` checkpoint with five clinic-support categories |
| Summarisation | Original pinned `google/flan-t5-base` checkpoint with source-coverage safeguard |
| Evaluation data | Synthetic, balanced training, validation and held-out test partitions |
| Execution environment | Local macOS CPU inference and training; no real clinic deployment |
| Scope | Education and administrative support; not diagnosis or individual treatment advice |

## Architecture Overview

The existing application separates the interface, HTTP routes, workflow logic and model adapters. This allows the model implementation to change while the workflow continues to call the same `classify(message)` operation.

| Component | Responsibility | Current implementation |
|---|---|---|
| React + TypeScript frontend | Collect support messages and questions; show API results | React client for the support workflow |
| FastAPI presentation layer | Validate HTTP requests and expose `/health`, `/metadata`, `/analyze` and `/chat` | Implemented routes |
| Application layer | Coordinate classification, summarisation and knowledge answering | Use cases coordinate the three task interfaces |
| Classifier interface | Define `classify(message)` and readiness status | Protocol implemented by the sequence-to-sequence classifier |
| Model infrastructure | Load tokenizer/weights and generate predictions/summaries | Separate lazy `Seq2SeqRuntime` instances for `Seq2SeqClassifier` and `Seq2SeqSummarizer` |
| Configuration | Select model, revision, device, paths and generation limits | `ModelSettings` reads shared defaults and task-specific `.env`/environment overrides |
| Summariser and knowledge answerer | Generate summaries and document-grounded answers | Configurable sequence-to-sequence summariser with a source-coverage guard; knowledge answerer remains unconfigured |

The classifier and summariser each have a separate lazy runtime and can load different model checkpoints. Each model is loaded on its first request and remains in memory for that application process; if both tasks are used, both model copies may occupy memory. `/analyze` returns a generated summary and a primary category; `/chat` returns HTTP 503 until the knowledge component is configured. An initial summary omitted the leaflet download request. A source-coverage guard now appends an original sentence when its meaningful words are absent from the generated summary. This can create repetition for paraphrases, and it does not detect unsupported additions; staff review remains necessary.

## 1. API-Based AI Application

### 1.1 Domain, problem and users

The selected domain is healthcare support for a fictional diabetes clinic. The application addresses routine support messages that clinic staff must read, route and answer using education resources and administrative procedures. The clinic is an industry analogue; no real clinic deployment or access to patient records is claimed.

The intended user is a clinic support worker. Staff review outputs before communicating with patients. The assistant supports education and administrative workflows; personal clinical decisions are referred to qualified staff.

### 1.2 Three cohesive NLP tasks

| Task | Intended input and output | Role in the workflow |
|---|---|---|
| Request classification | Support message to a primary support category | Route the request to a support queue or staff review |
| Summarisation | Message/conversation to a factual staff handoff summary | Preserve the requests for staff handoff |
| Question answering | Staff question and retrieved passages to an answer with citations | Answer general questions using the selected WHO source |

All three tasks support one objective: reduce staff effort in understanding and responding to diabetes support enquiries. A representative case is an appointment-change request combined with a missing education leaflet. Classification identifies the main request and the summary retains both needs. The RAG component is scoped to general diabetes information and education support from the selected WHO source; clinic-specific appointment and portal procedures are routed to staff because they are outside the source corpus.

### 1.3 Model choice and baseline inference

The initial language model is `google/flan-t5-base`, loaded with Hugging Face Transformers using `AutoTokenizer` and `AutoModelForSeq2SeqLM`. The verified baseline uses revision `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` for both tokenizer and weights.

#### Base model and fine-tuned model roles

The **base model** is the original pretrained `google/flan-t5-base` checkpoint at revision `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`. It provides the starting weights and tokenizer for classification and remains the model used for message summarisation. The **fine-tuned model** is a complete FLAN-T5 checkpoint adapted for clinic-support classification. Part II describes the training method and saved checkpoint.

| Application task | Configured model | Role |
|---|---|---|
| Classification | `./artifacts/models/clinic-support` (`CLASSIFIER_MODEL_NAME`) | Locally saved, one-epoch fine-tuned checkpoint derived from the pinned base model |
| Summarisation | `google/flan-t5-base` (`SUMMARIZER_MODEL_NAME`) | Original pinned base checkpoint; it is not fine-tuned for summarisation |

The app loads the two task models through separate lazy runtimes. `CLASSIFIER_MODEL_NAME` and `SUMMARIZER_MODEL_NAME` override the shared `MODEL_NAME` fallback. The base model identifier and revision remain the training/evaluation source settings. This arrangement lets each task change independently, but the two model copies can both occupy memory after both tasks have run. The local classifier checkpoint is ignored by Git and must be present on the machine running the app.

The classification instruction lists five categories and their meanings:

1. `appointment_support`: appointment booking, confirmation, cancellation or changes.
2. `education_resource_request`: general education materials and new class enrollment.
3. `portal_technical_support`: login, display, upload or other portal failures.
4. `records_insurance_admin`: records, insurance, billing and administrative paperwork.
5. `clinical_staff_referral`: personal medical questions or requests needing clinical review.

The prompt directs mixed requests containing personal clinical advice to the clinical-referral category. This instruction is not evidence of reliable referral performance; that behaviour still requires evaluation.

The tokenizer converts the complete instruction and message into numerical tensors. The model runs in evaluation mode under `torch.inference_mode()`, generates at most 32 new tokens by default with random sampling disabled, and the tokenizer decodes the answer. The code preserves unexpected output and returns a null category if the answer does not exactly match an allowed label. Category validity alone does not establish correctness.

No optimizer, training loop or weight update is used in these baseline runs. The current output records `weights_updated_during_inference: false`.

#### Full validation baseline

The original `google/flan-t5-base` checkpoint was run on all 60 validation messages before fine-tuning. The evaluation uses the application classifier's fixed prompt and greedy decoding (`do_sample=false`, 32 maximum new tokens) on CPU. The script loads only `data/validation/classification_validation.jsonl`; it does not open the test partition. The test set has not been used for model selection.

| Measure | Baseline result |
|---|---:|
| Accuracy | 71.67% (43/60) |
| Macro precision | 86.02% |
| Macro recall | 71.67% |
| Macro F1 | 71.81% |
| Invalid category outputs | 6/60 (10.00%) |

| Category | Precision | Recall | F1 |
|---|---:|---:|---:|
| Appointment support | 57.89% | 91.67% | 70.97% |
| Education resource request | 91.67% | 91.67% | 91.67% |
| Portal technical support | 91.67% | 91.67% | 91.67% |
| Records, insurance and administration | 100.00% | 16.67% | 28.57% |
| Clinical staff referral | 88.89% | 66.67% | 76.19% |

The validation set contains 12 examples per category. Records/insurance/administration was the weakest baseline category: 2 of 12 examples were correct, and five outputs were invalid category names. The results are a synthetic-data baseline and do not establish clinical performance.

The run metadata and per-example predictions were saved locally to the ignored file `artifacts/evaluation/classification_baseline_validation.json`. It records the model revision, dataset SHA-256, predictions, invalid outputs and confusion matrix. The checked-in script can regenerate it with `.venv/bin/python scripts/evaluate_classifier.py` from the Assignment-2 directory.



### 1.4 Configurable model and runtime

`ModelSettings.from_env()` reads the project `.env` file and applies environment-variable overrides. Training and evaluation use `MODEL_NAME` and `MODEL_REVISION` for the base model; the application uses task-specific model names and revisions when supplied. The local `.env` file is excluded from version control.

The local configuration points `CLASSIFIER_MODEL_NAME` to `./artifacts/models/clinic-support` and `SUMMARIZER_MODEL_NAME` to `google/flan-t5-base`. The classifier checkpoint directory exists on the development Mac and was reload-verified there. A Swagger `POST /analyze` request returned HTTP 200, `model: clinic-support`, category `appointment_support`, and the expected one-sentence summary. `model_revision: null` is expected because this is a local checkpoint without a Hub revision. A subsequent `GET /metadata` confirmed both model runtimes ready: classifier `clinic-support@local`, summarizer `google/flan-t5-base@7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`. The knowledge index remained not ready because RAG is not configured yet.

| Setting | Verified/default value | Purpose |
|---|---|---|
| `MODEL_NAME` | `google/flan-t5-base` | Shared fallback and base model used by training/evaluation |
| `MODEL_REVISION` | Blank resolves to `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2` for the base | Select a reproducible Hub revision |
| `CLASSIFIER_MODEL_NAME` | `./artifacts/models/clinic-support` | Fine-tuned classifier checkpoint; overrides `MODEL_NAME` in the app |
| `SUMMARIZER_MODEL_NAME` | `google/flan-t5-base` | Original model for summaries; overrides `MODEL_NAME` in the app |
| `CLASSIFIER_MODEL_REVISION` / `SUMMARIZER_MODEL_REVISION` | Blank; inherit `MODEL_REVISION` | Optional task-specific Hub revisions |
| `MODEL_DEVICE` | `cpu` | Choose CPU, CUDA, MPS or automatic device selection |
| `MODEL_CACHE_DIR` | `artifacts/huggingface` | Keep model downloads outside source control |
| `MODEL_MAX_INPUT_TOKENS` | `512` | Reject oversized full prompts rather than silently truncating them |
| `CLASSIFICATION_MAX_NEW_TOKENS` | `32` | Bound category output length |
| `SUMMARY_MAX_NEW_TOKENS` | `128` | Bound summary output length |
| `MODEL_LOCAL_FILES_ONLY` | `false` | Optionally require cached/local weights without downloads |

Changing a Hub model without specifying a revision does not inherit the baseline's commit SHA. Relative checkpoint/cache paths resolve from Assignment-2. The current loader supports compatible Hugging Face sequence-to-sequence models with safetensors weights and a matching tokenizer. Chat-model architectures, hosted providers and adapter-only LoRA checkpoints need an appropriate implementation behind the classifier interface. The fine-tuned classifier checkpoint has been loaded and reload-verified on CPU; alternative model quality and GPU inference have not been demonstrated.

### 1.5 Selected baseline examples

The pinned base model returned the expected categories for these selected development examples. They are sanity checks, not an accuracy estimate.

| Input | Expected category | Observed output | Outcome |
|---|---|---|---|
| Please move my appointment to Friday. | `appointment_support` | `appointment_support` | Matches |
| The clinic portal will not let me sign in. | `portal_technical_support` | `portal_technical_support` | Matches |

These selected checks do not establish performance across all five categories or reliable clinical referral. On macOS with Python 3.11.5, PyTorch 2.15.0 and Transformers 5.22.1, the backend suite passed **17 tests** after the model-configuration and display-name changes. The test suite includes configuration and mocked-loader checks; it does not establish alternative-model or GPU performance. Swagger confirmed that `/analyze` returns both outputs and that the classifier and summariser report their separate model identities.

Reproduction command from Assignment-2, after installing the inference dependencies:

```bash
.venv/bin/python -m diabetes_support.infrastructure.seq2seq_classifier --message "The clinic portal will not let me sign in."
```

## 2. Fine-Tuning

### 2.1 Dataset development and review

The classification pilot contains 35 synthetic, AI-drafted messages, seven per category. Each record tracks its example ID, message, category, scenario family, provenance, authoring method and review metadata. The pilot records have `review_status: approved` and reviewer `Sanjay`, scoped to classification feasibility. Historical AI-assisted content review is recorded in the label guide; it is not independent clinical validation.

Ten additional routing checks are documented in the existing label guide. They cover mixed clinical/administrative messages, educational versus personal-result questions, technical failures, ambiguous requests and unrelated requests. These are expected behaviours, not observed test passes, and remain outside classifier training.

The pilot has valid JSON, balanced class counts, unique IDs and no exact duplicate messages. Related scenarios are grouped to support leakage-aware dataset preparation. The pilot is development material and must not be presented as a final held-out benchmark. The validation and test candidates have received label and overlap review; 15 test messages were revised and one ambiguous category was clarified. The training run and evaluation results are reported in Sections 2.2–2.4.

The training draft is in `data/training/classification_train.jsonl`: **280 synthetic messages, 56 per category**, with tracking metadata and scenario-family IDs. The initial 50 examples received an AI-assisted content review, during which five messages were clarified and scenario groupings corrected. A further 230 examples add spelling variation, informal requests, longer inputs and mixed requests with clinical overrides. All records retain AI-drafted provenance.

Pilot and training records use `review_status: approved`, `reviewer: Sanjay`, and a recorded `reviewed_on` date. The examples remain synthetic and AI-drafted; approval covers the recorded review scope and is not clinical validation. Historical AI-assisted review details are in the label guide. Exact duplicate checks found no repeated training messages or exact overlap with the pilot; known related scenarios share family IDs. Separate validation and test candidate files contain 60 synthetic messages each (12 per category), with the same review metadata. Review of the test set revised 15 messages that were too close to examples in other partitions and clarified TEST-020. Final checks found no exact duplicates or high lexical matches across the four files; text-similarity checks do not prove complete semantic independence. The one-epoch validation and final test results are reported in Sections 2.3 and 2.4; the synthetic test set remains too small to support a clinical-performance claim.

### 2.2 Training procedure and checkpoint

This was full fine-tuning: AdamW updated the FLAN-T5 model parameters rather than training an adapter. The one-epoch run used all 280 training examples, batch size 1, gradient accumulation of 8, learning rate `5e-5`, and seed 42. It completed 35 optimizer updates with mean training loss 0.1699, evaluated the 60-message validation set, and saved the best checkpoint. On the development Mac, automatic device selection chose CPU. Training and validation were the only data partitions loaded; the test set was not used.

### 2.3 Validation result

After one epoch, validation accuracy was **98.33% (59/60)** and macro-F1 was **98.33%**, with **0 invalid outputs**. Per-class F1 was 95.65% for appointment support, 100% for education resources, portal technical support and records/insurance/admin, and 96.00% for clinical referral. The sole error was an appointment request predicted as clinical referral. The original checkpoint scored 71.67% accuracy and 71.81% macro-F1 on the same validation set. Because the validation set selected the checkpoint, this difference is a development result, not a final unbiased estimate. The test set was reserved for final scoring and has not been used for training or model selection.

The checkpoint and tokenizer were saved to `artifacts/models/clinic-support`. A fresh process loaded that directory through the application classifier and correctly classified “Please move my appointment to Friday.” as `appointment_support`. These results use small synthetic datasets and do not establish clinical performance.

### 2.4 Final held-out test evaluation

The base and fine-tuned models were evaluated on the same 60-message test file with the same application prompt and greedy decoding. The result files record the same test-file SHA-256. No training, prompt selection or checkpoint choice used these test results.

| Measure | Base FLAN-T5 | Fine-tuned checkpoint |
|---|---:|---:|
| Accuracy | 86.67% (52/60) | 95.00% (57/60) |
| Macro precision | 95.00% | 95.39% |
| Macro recall | 86.67% | 95.00% |
| Macro F1 | 88.74% | 94.74% |
| Invalid category outputs | 4/60 (6.67%) | 0/60 (0%) |

| Actual category | Base predictions | Fine-tuned predictions |
|---|---|---|
| Appointment support | 12 appointment | 12 appointment |
| Education resource request | 11 education, 1 appointment | 12 education |
| Portal technical support | 12 portal | 12 portal |
| Records, insurance and administration | 6 records, 2 appointment, 4 invalid | 9 records, 1 appointment, 1 education, 1 portal |
| Clinical staff referral | 11 clinical, 1 appointment | 12 clinical |

The tuned model’s three remaining errors were TEST-041 (authorised-contact paperwork), TEST-045 (preferred language for clinic letters), and TEST-047 (insurance coverage for an appointment fee); all were predicted as another supported category rather than invalid text. The higher result is evidence only for this small synthetic test set. It is not clinical-performance evidence. The test set remains held out and must not be used to choose further tuning changes.


## 3. Retrieval-Augmented Generation

The local retrieval step is implemented as `POST /retrieve`: it ranks curated chunks from the WHO [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes) page, updated 1 September 2026, using transformer embeddings, and returns matching passages with source metadata and similarity scores. Retrieval quality has not yet been evaluated with the configured embedding model. The local source snapshot was used to prepare paraphrased notes and source-attributed chunks; the snapshot is excluded from the submission, while the notes and chunks are included. Answer generation is not yet connected, so `/chat` remains unavailable. The completed chatbot should not answer questions about clinic procedures or individual diagnosis and treatment; unsupported requests should be routed to staff. Evaluation will assess retrieval relevance, answer support, source citations, and appropriate handling of unsupported questions.

## 4. Situated Learning - Workplace Application

### 4.1 Anchor - Workplace problem

Proposed industry analogue: a fictional diabetes clinic support desk. Staff manually inspect incoming messages, identify the responsible queue, summarise requests and search approved procedures or education documents. The intended benefit is lower handling effort with outputs reviewed by staff. This is a proposed workflow, not an observed organisational deployment.

### 4.2 Apply - Adaptation and representative outputs

**Demonstration evidence pending.** The selected baseline classifications in Section 1.5 provide limited technical evidence. A complete workplace case should show the summary, fine-tuned classifier, retrieved sources and chatbot answer together, with an appropriate referral or abstention case.

### 4.3 Analyse - Workplace relevance

**Evaluation pending.** The workplace evaluation will measure answer quality, source support, completeness, response time, corrections required and representative manual-versus-assisted handling times. It will report failures, sample sizes and the gap between this synthetic prototype and practical organisational use. No efficiency improvement, clinical readiness or scalability result is claimed at this stage.

### 4.4 Reflect - Constraints and priority improvement

**Reflection pending.** The final reflection will address privacy, security, applicable regulation, infrastructure, cost and integration using the implementation and observed failures. A priority improvement for consideration is clinician-led validation of answer correctness and referral behaviour before patient-facing use.

## 5. Demonstration, Limitations and Submission

The current prototype has a fine-tuned classifier, a sequence-to-sequence summariser with an omission guard, and configurable task-specific model loading. RAG remains unfinished; the summaries and full workplace evaluation still require human review. The recorded examples and automated engineering checks have different purposes and must not be combined into an AI accuracy claim.

The final demonstration video will cover the complete project and be uploaded to Google Drive with verified viewer access. **Final video link: pending.** The completed submission will include screenshots, measured outcomes, confirmed member contributions and the required workplace material. The report will be exported to the format specified in the course brief.

## References

1. Course Assignment II brief, supplied locally as `Assignment-2/Assignment 2.pdf`; assessed requirements and submission instructions.
2. Google / Hugging Face. [FLAN-T5 Base model card](https://huggingface.co/google/flan-t5-base). Model identity and loading reference; the verified revision is recorded in Section 1.3.
3. Hugging Face. [Transformers T5 documentation](https://huggingface.co/docs/transformers/en/model_doc/t5). Tokenizer and sequence-to-sequence model API reference.
4. World Health Organization. [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes). Updated 1 September 2026; selected public source for general diabetes information and self-management education/support.
