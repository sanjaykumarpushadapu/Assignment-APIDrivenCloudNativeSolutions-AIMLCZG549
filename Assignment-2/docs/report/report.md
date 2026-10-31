# Diabetes Care Support Assistant

**Course:** AIMLCZG549 - API-Driven Cloud-Native Solutions  
**Assignment:** Assignment II  
**Group:** 49 (carried over from Assignment I; confirm before submission)  
**Institution:** BITS Pilani, Work Integrated Learning Programmes  
**Last updated:** 31 October 2026  
**Document status:** Working draft; updated as implementation and verification progress.

This report records the design, implementation and evidence for a staff-facing diabetes-clinic support assistant. The project covers three connected NLP tasks: request classification, message summarisation and document-grounded question answering. The current implementation covers baseline classification and a configurable sequence-to-sequence summariser. A source-coverage guard retains original sentences omitted by generated summaries. Fine-tuning, retrieval and the complete workplace evaluation remain pending; summary accuracy still requires staff review.

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
| I. API-based AI application | 4 | React/FastAPI skeleton; classifier and first summariser wired through existing interfaces | Summary quality review; chatbot; integrated screenshots and final API demonstrations |
| II. Fine-tuning | 2 | 280 synthetic training candidates (56/class); one CPU epoch completed; checkpoint saved and reload verified | Reviewed full dataset and scenario-grouped splits, training records, saved checkpoint, reload and base-versus-tuned results |
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
| Model infrastructure | Load tokenizer/weights and generate predictions/summaries | `Seq2SeqRuntime` shared by configurable `Seq2SeqClassifier` and `Seq2SeqSummarizer` |
| Configuration | Select model, revision, device, paths and generation limits | `ModelSettings` reads `.env` and environment variables |
| Summariser and knowledge answerer | Generate summaries and document-grounded answers | Configurable sequence-to-sequence summariser with a source-coverage guard; knowledge answerer remains unconfigured |

The classifier and summariser use one lazy runtime and reuse its model weights in the same process. Each new process loads its own model copy. Both components report ready after the first model load. `/analyze` returns a generated summary and a primary category; `/chat` returns HTTP 503 until the knowledge component is configured. The user confirmed through Swagger that the first model summary omitted the leaflet download issue. A conservative source-coverage guard now appends an original sentence when its meaningful words are absent from the generated summary. This can create repetition for paraphrases, and it does not detect unsupported additions; staff review remains necessary.

## 1. API-Based AI Application

### 1.1 Domain, problem and users

The selected domain is healthcare support, continuing Assignment I's diabetes theme. The application addresses routine support messages that clinic staff must read, route and answer using education resources and administrative procedures. The proposed organisation is a fictional diabetes clinic used as an industry analogue; no real clinic deployment or access to patient records is claimed.

The intended user is a clinic support worker. Staff review outputs before communicating with patients. The assistant supports education and administrative workflows; personal clinical decisions are referred to qualified staff.

### 1.2 Three cohesive NLP tasks

| Task | Intended input and output | Progress |
|---|---|---|
| Request classification | Support message to a primary support category | Baseline prediction verified |
| Summarisation | Message/conversation to a factual staff handoff summary | Adapter and source-coverage guard implemented; human quality review pending |
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

#### Full validation baseline — 31 October 2026

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

The validation set contains 12 examples per category. The records/insurance/admin category had the largest gap: only 2 of 12 examples were classified correctly, and five outputs were not valid category names. This makes it a clear area to investigate using training and validation data. Do not edit the held-out test set or tune against it. These results are a small synthetic-data baseline, not evidence of clinical performance.

The run metadata and per-example predictions were saved locally to the ignored file `artifacts/evaluation/classification_baseline_validation.json`. It records the model revision, dataset SHA-256, predictions, invalid outputs and confusion matrix. The checked-in script can regenerate it with `.venv/bin/python scripts/evaluate_classifier.py` from the Assignment-2 directory.

The one-step smoke run completed on the Mac CPU using one training example (loss 1.2364); it loaded neither validation nor test data and saved no checkpoint. A separate one-epoch run then trained on all 280 training examples with batch size 1, gradient accumulation 8, learning rate 5e-5, and seed 42. It completed 35 optimizer updates with mean training loss 0.1699, evaluated the 60-message validation set, and saved the best checkpoint. `scripts/train_classifier.py` supports `auto`, `cpu`, `mps` and `cuda`; on this Mac, `auto` selected CPU. Training and validation were the only data partitions loaded; the test set was not used.

#### One-epoch fine-tuning result

After one epoch, validation accuracy was **98.33% (59/60)** and macro-F1 was **98.33%**, with **0 invalid outputs**. Per-class F1 was 95.65% for appointment support, 100% for education resources, portal technical support and records/insurance/admin, and 96.00% for clinical referral. The sole error was an appointment request predicted as clinical referral. The original checkpoint scored 71.67% accuracy and 71.81% macro-F1 on the same validation set. Because the validation set selected the checkpoint, this difference is a development result, not a final unbiased estimate. The test set remains untouched.

The checkpoint and tokenizer were saved to the ignored local directory `artifacts/models/clinic-support`. A fresh process loaded that directory through the application classifier and correctly classified “Please move my appointment to Friday.” as `appointment_support`. The selected checkpoint was trained for one epoch; the planned three-epoch run has not been completed. These results use small synthetic datasets and do not establish clinical performance.

### 1.4 Pilot data and review

The classification pilot contains 35 synthetic, AI-drafted messages, seven per category. Each record tracks its example ID, message, category, scenario family, provenance, authoring method and review metadata. At the user's direction, the records have `review_status: approved`, reviewer `Sanjay`, and review date 31 October 2026, scoped to classification feasibility. Historical AI-assisted content review is recorded in the label guide; it is not independent clinical validation.

Ten additional routing checks are documented in the existing label guide. They cover mixed clinical/administrative messages, educational versus personal-result questions, technical failures, ambiguous requests and unrelated requests. These are expected behaviours, not observed test passes, and remain outside classifier training.

The pilot has valid JSON, balanced class counts, unique IDs and no exact duplicate messages. Related scenarios are grouped to support leakage-aware dataset preparation. The pilot is development material and must not be presented as a final held-out benchmark. The validation and test candidates have received label and overlap review; 15 test messages were revised and one ambiguous category was clarified. Model training remains pending.

The training draft is in `data/training/classification_train.jsonl`: **280 synthetic messages, 56 per category**, with tracking metadata and scenario-family IDs. The initial 50 examples received an AI-assisted content review, during which five messages were clarified and scenario groupings corrected. A further 230 examples add spelling variation, informal requests, longer inputs and mixed requests with clinical overrides. All records retain AI-drafted provenance.

At the user’s direction, all pilot and training records use `review_status: approved`, `reviewer: Sanjay`, and `reviewed_on: 2026-10-31`. The examples remain synthetic and AI-drafted, and their approval scope is unchanged. Historical AI-assisted review details are in the label guide. Exact duplicate checks found no repeated training messages or exact overlap with the pilot; known related scenarios share family IDs. Separate validation and test candidate files now contain 60 synthetic messages each (12 per category), with approved review metadata at the user’s direction. Review of the test set revised 15 messages that were too close to examples in other partitions and clarified TEST-020. Final checks found no exact duplicates or high lexical matches across the four files; text-similarity checks do not prove complete semantic independence. No full training run or measured model improvement is claimed.

### 1.5 Configurable model and runtime

The active `.env` file was created from `.env.example` on 31 October 2026. `ModelSettings.from_env()` reads the file from Assignment-2 regardless of the terminal's working directory. Environment variables take precedence. Both terminal adapters and the application read the same configuration; `MODEL_NAME` selects the model shared by classification and summarisation. Changes apply after restarting the process. The active `.env` is excluded from Git.

| Setting | Verified/default value | Purpose |
|---|---|---|
| `MODEL_NAME` | `google/flan-t5-base` | Hub model ID or complete compatible checkpoint directory |
| `MODEL_REVISION` | Blank resolves to the pinned baseline revision | Select a reproducible Hub revision |
| `MODEL_DEVICE` | `cpu` | Choose CPU, CUDA, MPS or automatic device selection |
| `MODEL_CACHE_DIR` | `artifacts/huggingface` | Keep model downloads outside source control |
| `MODEL_MAX_INPUT_TOKENS` | `512` | Reject oversized full prompts rather than silently truncating them |
| `CLASSIFICATION_MAX_NEW_TOKENS` | `32` | Bound category output length |
| `SUMMARY_MAX_NEW_TOKENS` | `128` | Bound summary output length |
| `MODEL_LOCAL_FILES_ONLY` | `false` | Optionally require cached/local weights without downloads |

Changing the Hub model without specifying a revision does not inherit the baseline's commit SHA. Relative checkpoint/cache paths resolve from Assignment-2. The current loader supports compatible Hugging Face sequence-to-sequence models with safetensors weights and a matching tokenizer. Chat-model architectures, hosted providers and adapter-only LoRA checkpoints need an appropriate implementation behind the classifier interface. Alternative model quality, GPU inference and fine-tuned checkpoint loading have not yet been demonstrated.

### 1.6 Verified baseline results

The following two messages were run by the user from the terminal on 31 October 2026 and returned the expected categories. The same messages also passed after moving the implementation into the application skeleton. The configurable adapter subsequently returned the portal category using the cached baseline model.

| Input | Expected category | Observed output | Outcome |
|---|---|---|---|
| Please move my appointment to Friday. | `appointment_support` | `appointment_support` | Matches |
| The clinic portal will not let me sign in. | `portal_technical_support` | `portal_technical_support` | Matches |

These are selected development examples. They are not a held-out accuracy estimate and do not establish performance across all five categories or reliable clinical referral.

Observed environment: Python 3.11.5, PyTorch 2.15.0, Transformers 5.22.1, macOS and CPU inference. Dependency ranges do not lock future installations to these exact versions. Model loading logged a macOS redirection note and a tied-weights warning; prediction completed successfully, and the configuration was not changed merely to suppress those messages.

Verified engineering checks include two successive predictions reusing one model object, rejection of blank and oversized inputs, and a mocked API check that `/analyze` returns both fields, and unit checks for the summary coverage guard. The automated backend/configuration suite completed with **17 tests passed**. A real offline inference run loaded the cached baseline model and produced `appointment_support`; after the guard was added, the returned summary retained both original sentences. The user also exercised `/analyze` through Swagger before this guard was added and observed the omission. The configuration tests include file/environment precedence, revision selection, local paths, invalid settings and passing configured loader options. Mocked loader tests establish configuration behaviour, not actual alternative-model or GPU performance. Formatting and lint checks passed.

Reproduction command from Assignment-2, after installing the inference dependencies:

```bash
.venv/bin/python -m diabetes_support.infrastructure.seq2seq_classifier --message "The clinic portal will not let me sign in."
```

Evidence still to add: readable terminal screenshots of both selected examples, active settings verification and the final integrated UI/API. No screenshot is claimed to exist merely because a terminal result is recorded here.

## 2. Fine-Tuning

**Status: partially complete.** One CPU epoch was trained and its checkpoint/tokenizer were saved and reload-verified. Validation metrics are recorded above; the test set has not been evaluated. The remaining work is to decide whether to train more epochs using validation only, freeze the checkpoint and settings, then compare base and tuned models on the untouched test set. Record the final test metrics and failures without tuning against test results.

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

The current prototype has a functioning baseline classifier, a sequence-to-sequence summariser with an omission guard, and configurable model loading. Fine-tuning and RAG remain unfinished; the summaries and full workplace evaluation still require human review. The recorded examples and automated engineering checks have different purposes and must not be combined into an AI accuracy claim.

The final demonstration video must cover the complete project and be uploaded to Google Drive with verified viewer access. **Final video link: pending.** Screenshots, measured outcomes, member-approved contributions and the complete separate workplace section are also pending. After final review, export this report as `49.pdf` or `49.docx` if Group 49 continues, and verify every member's required portal submission. The team has supplied 12 November 2026 as the official date; the portal's exact cutoff still needs verification.

## References

1. Course Assignment II brief, supplied locally as `Assignment-2/Assignment 2.pdf`; assessed requirements and submission instructions.
2. Google / Hugging Face. [FLAN-T5 Base model card](https://huggingface.co/google/flan-t5-base). Model identity and loading reference; the verified revision is recorded in Section 1.3.
3. Hugging Face. [Transformers T5 documentation](https://huggingface.co/docs/transformers/en/model_doc/t5). Tokenizer and sequence-to-sequence model API reference.
4. Group 49. Assignment I report, `Assignment-1/docs/report/REPORT.md`. Structure and team roster reference; Assignment I results are not Assignment II evidence.
