# Diabetes Care Support Assistant

**Course:** AIMLCZG549 - API-Driven Cloud-Native Solutions  
**Assignment:** Assignment II  
**Group:** 49\
**Institution:** BITS Pilani, Work Integrated Learning Programmes  
**Document status:** Working draft.

This report records the design, implementation and evidence for a staff-facing diabetes-clinic support assistant. The project covers three connected NLP tasks: request classification, message summarisation and document-grounded question answering. The classifier has been fine-tuned from `google/flan-t5-base`; a separate summariser checkpoint has also been trained, while inference remains configured to use the original base model pending comparative evaluation. The revised-prompt summariser's best validation ROUGE-L F1 was 0.4563 after three epochs; this synthetic-data metric alone does not establish quality. Summary accuracy, faithfulness and completeness still require review. Retrieval and the complete workplace evaluation remain pending.

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
| Summarisation | Original pinned `google/flan-t5-base` at inference; fine-tuned candidate saved locally for evaluation |
| Evaluation data | Synthetic, balanced training, validation and held-out test partitions |
| Execution environment | Local macOS CPU inference and CPU/MPS training; no real clinic deployment |
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
| Summariser and knowledge answerer | Generate summaries and document-grounded answers | Configurable sequence-to-sequence runtime for summaries and retrieved-context answers; answer quality and refusal behavior await evaluation |

The classifier and base-model generation tasks use separate lazy runtimes; summarisation and question answering share the configured base-model runtime to avoid a duplicate model copy. Each runtime loads on first use and remains in memory for the process. `/analyze` returns a generated summary and primary category. `/chat` retrieves source passages, asks the base model to answer only from them, returns their source details alongside the answer, and refuses common personal medical requests before generation. This is an initial safeguard, not a clinical safety guarantee; runtime behavior and answer quality require evaluation. An initial summary omitted the leaflet download request. An attempted source-coverage guard appended original sentences based on word matching, but a longer-message check showed that this repeated paraphrased requests and could make the output longer than the input. The guard was removed. Summarisation now uses four-beam decoding with repeated three-word sequences blocked. A local CPU smoke check retained the requested Friday-after-2-pm change and pending confirmation without appended repetition, but shortening was modest. These selected examples do not establish summary completeness, faithfulness, or overall accuracy; staff review and broader evaluation remain necessary.

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

The **base model** is the original pretrained `google/flan-t5-base` checkpoint at revision `7bcac572ce56db69c1ea7c8af255c5d7c9672fc2`. It provides the starting weights and tokenizer for both classification and summarisation. The **fine-tuned models** are complete FLAN-T5 checkpoints adapted separately for clinic-support classification and message summarisation. Part II describes the classifier training method; the summariser training run is recorded below.

| Application task | Configured model | Role |
|---|---|---|
| Classification | `./artifacts/models/clinic-support` (`CLASSIFIER_MODEL_NAME`) | Locally saved, one-epoch fine-tuned checkpoint derived from the pinned base model |
| Summarisation | `google/flan-t5-base` (`SUMMARIZER_MODEL_NAME`) | Current inference model; the revised-prompt candidate is `artifacts/models/clinic-summary-v2` |

The app loads the two task models through separate lazy runtimes. `CLASSIFIER_MODEL_NAME` and `SUMMARIZER_MODEL_NAME` override the shared `MODEL_NAME` fallback. The base model identifier and revision remain the training/evaluation source settings. This arrangement lets each task change independently, but the two model copies can both occupy memory after both tasks have run. The local classifier checkpoint is ignored by Git and must be present on the machine running the app.

Summariser fine-tuning is implemented separately in `scripts/train_summarizer.py`. Its base checkpoint is configured with `SUMMARIZER_BASE_MODEL_NAME`, independently of `SUMMARIZER_MODEL_NAME`, which selects the inference checkpoint. It reads the 280-example training partition and 60-example validation partition, uses the same prompt builder as application inference, and selects a checkpoint using validation ROUGE-L. On the Mac, the initial MPS run completed three epochs and 105 optimizer updates (batch size 1, gradient accumulation 8, learning rate `5e-5`, seed 42). Mean training loss decreased from 2.0435 to 1.3911; validation ROUGE-L F1 reached 0.4436. After the qualitative audit, the shared prompt was revised to preserve questions, uncertainty, pending status, conditions, exclusions, and separate requests. A second MPS run with that prompt completed the same schedule; mean loss decreased from 2.0008 to 1.3800 and validation ROUGE-L F1 reached 0.4563. The selected checkpoint and tokenizer are saved under `artifacts/models/clinic-summary-v2`; its `training_summary.json` and `validation_comparison.json` contain predictions and metrics. The tracked [run evidence](evidence/summarizer-v2-run.json) records training parameters, data hashes, validation outputs and the checkpoint checksum without including the binary weights. Both runs used training and validation data only; the held-out test partition was not read.

On the earlier prompt, base and fine-tuned checkpoints scored 0.2848 and 0.4436 mean ROUGE-L F1 respectively, with output/input word ratios 0.8804 and 0.6080. On the revised prompt, the base model scored 0.2977 and 0.9201; the fine-tuned checkpoint scored 0.4563 and 0.5997. Each comparison used the same 60 validation messages on CPU, with the application decoding settings. Fine-tuning improved lexical overlap and produced shorter summaries on this synthetic validation set. However, qualitative review found recurring semantic errors even after the revised prompt: SUM-VAL-012 still changes a question about large-print availability into a claim that it is available; SUM-VAL-037 changes “any day except Thursday” into a reason involving Thursday; SUM-VAL-049 omits the request to send appointment messages by email; and SUM-VAL-057 says the person registers for a noon session instead of needing to leave at noon. The base model is often much less concise and also has errors. These results do not establish that either model is reliable. Keep `SUMMARIZER_MODEL_NAME` on the base model for now; inspect the training examples for these failure patterns before deciding on another training change. The held-out test partition remains unused until model and prompt choices are final.

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

The local retrieval step is implemented as `POST /retrieve`: it ranks curated chunks from the WHO [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes) page, updated 1 September 2026, using transformer embeddings, and returns matching passages with source metadata and similarity scores. In three manual in-scope smoke checks, the expected chunk ranked first each time. One out-of-scope check shows that retrieval still returns passages even when they do not support a safe answer:

| Question | Expected and top-ranked chunk | Cosine similarity |
|---|---|---:|
| What is diabetes? | WHO01-001 — What diabetes is | 0.7357 |
| What are common symptoms of diabetes? | WHO01-003 — Common symptoms | 0.6913 |
| What symptoms might someone with diabetes experience? | WHO01-003 — Common symptoms | 0.7393 |
| How can type 2 diabetes be prevented or delayed? | WHO01-005 — Type 2 prevention | 0.8670 |
| Should I change my diabetes medication? | No passage should advise a personal medication change; chatbot should abstain | WHO01-008 — Supporting someone (indirect), followed by WHO01-006 — General diabetes care (mentions medication generally); top score 0.4704 |
| Where can I download the clinic leaflet? | No clinic procedure is covered; chatbot should abstain | WHO01-008 — Supporting someone (indirect); top score 0.1048. The initial `/chat` response was citation-only; after adding the provisional score floor, it abstained. |

Manual `/chat` checks now include a definition question answered from WHO01-001 and a paraphrased symptoms question answered from WHO01-003. The paraphrased question, “What symptoms might someone with diabetes experience?”, returned a concise source-supported response, `abstained: false`, and WHO01-003 as its top source. The answer matched the retrieved text. A personal medication-change question returned the fixed clinic-referral response, `abstained: true`, and no sources. A clinic-leaflet question initially returned a citation-only answer despite the weak retrieval score. After adding a configurable `/chat` score floor of 0.20, repeating that query returned the fixed refusal response, `abstained: true`, and no sources. This confirms handling of these specific cases only; the floor is provisional and is not a calibrated confidence threshold. Similarity scores are not probabilities. These manual checks do not establish retrieval quality, answer quality, or broad refusal coverage. The retrieval endpoint returns top matches; the answerer has a rule for common personal medical requests and prompts the generator to abstain when passages do not answer the question. These initial safeguards remain to be evaluated. The local source snapshot was used to prepare paraphrased notes and source-attributed chunks; the snapshot is excluded from the submission, while the notes and chunks are included. The chatbot should not answer questions about clinic procedures or individual diagnosis and treatment; unsupported requests should be routed to staff. Evaluation will assess retrieval relevance, answer support, source citations, and appropriate handling of unsupported questions.

## 4. Situated Learning - Workplace Application

### 4.1 Anchor - Workplace problem

Proposed industry analogue: a fictional diabetes clinic support desk. Staff manually inspect incoming messages, identify the responsible queue, summarise requests and search approved procedures or education documents. The intended benefit is lower handling effort with outputs reviewed by staff. This is a proposed workflow, not an observed organisational deployment.

### 4.2 Apply - Adaptation and representative outputs

**Full workflow demonstration pending.** Retrieval checks and general-information and medication-referral `/chat` smoke checks are recorded in Section 3. A complete workplace case should show the summary, fine-tuned classifier, retrieved sources and chatbot answer together.

### 4.3 Analyse - Workplace relevance

**Evaluation pending.** The workplace evaluation will measure answer quality, source support, completeness, response time, corrections required and representative manual-versus-assisted handling times. It will report failures, sample sizes and the gap between this synthetic prototype and practical organisational use. No efficiency improvement, clinical readiness or scalability result is claimed at this stage.

### 4.4 Reflect - Constraints and priority improvement

**Reflection pending.** The final reflection will address privacy, security, applicable regulation, infrastructure, cost and integration using the implementation and observed failures. A priority improvement for consideration is clinician-led validation of answer correctness and referral behaviour before patient-facing use.

## 5. Demonstration, Limitations and Submission

The current prototype has a fine-tuned classifier, a sequence-to-sequence summariser using beam search and repeated-phrase blocking, and configurable task-specific model loading. RAG remains unfinished; the summaries and full workplace evaluation still require human review. The recorded examples and automated engineering checks have different purposes and must not be combined into an AI accuracy claim.

The final demonstration video will cover the complete project and be uploaded to Google Drive with verified viewer access. **Final video link: pending.** The completed submission will include screenshots, measured outcomes, confirmed member contributions and the required workplace material. The report will be exported to the format specified in the course brief.

## References

1. Course Assignment II brief, supplied locally as `Assignment-2/Assignment 2.pdf`; assessed requirements and submission instructions.
2. Google / Hugging Face. [FLAN-T5 Base model card](https://huggingface.co/google/flan-t5-base). Model identity and loading reference; the verified revision is recorded in Section 1.3.
3. Hugging Face. [Transformers T5 documentation](https://huggingface.co/docs/transformers/en/model_doc/t5). Tokenizer and sequence-to-sequence model API reference.
4. World Health Organization. [Diabetes: Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes). Updated 1 September 2026; selected public source for general diabetes information and self-management education/support.
