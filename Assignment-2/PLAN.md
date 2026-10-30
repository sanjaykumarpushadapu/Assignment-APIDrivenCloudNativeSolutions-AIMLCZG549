# Assessment 2: project plan and roadmap

Planning date: 30 October 2026. Official submission date supplied by the team: **12 November 2026**. Revised internal completion target: **end of 10 November 2026**, with **11 November reserved for contingency and submission checks**. All planning dates use India time; confirm the portal's exact cutoff and timezone. Team size: **4**. This document is a plan only; no application, model, dataset, or deployment has been implemented for Assessment 2.

**Quality-first revision, 30 October:** all four assessed components are represented. The internal completion target moves from 8 to 10 November to separate dataset review, training, integration, evaluation and post-fix verification. Quality checks, planned data coverage and assessed deliverables must not be reduced to meet an internal date. Execution remains conditional on available training compute, member availability and passing the quality gates; this is not a guarantee of completion or marks. The team-supplied official deadline remains 12 November; no extension is assumed.

**Start here:** agree the fictional clinic workflow and five labels; assign the four owners; confirm training access; prepare a small pilot dataset and document sample. Complete the first-day checklist in Section 11.7 before expanding the dataset. Finish and verify the complete submission package by the end of 10 November.

## 1. Recommended project

**Diabetes Care Support Assistant: request routing, staff summaries, and document-grounded Q&A.**

Continue Assignment 1's diabetes domain with a new NLP application for a diabetes clinic's support desk. A staff member enters a patient support message. The assistant identifies the request type, produces a factual handoff summary, and helps staff answer general education or administrative questions using approved documents and visible sources. Staff review the output before communicating it to a patient.

Use a clearly labelled fictional clinic as an industry analogue unless suitable workplace material is available. The assessment explicitly permits anonymised or synthetic workplace data. Do not describe a simulated workflow as an actual clinic deployment.

**Unified objective:** reduce the effort needed to understand, route, and respond to routine diabetes support enquiries, while directing clinical decisions to qualified staff.

An illustrative demonstration input is: “I need to move my diabetes education appointment, and I cannot find the preparation leaflet in the portal.” The app should provide an appointment-support category, a summary preserving both requests, and a source-backed answer about the fictional clinic's appointment process and leaflet location. This is an expected demonstration, not an observed model result.

## 2. What the brief actually requires

Source: [Assignment 2.pdf](./Assignment%202.pdf), reviewed across all three pages.

| Assessed component | Marks | Planned response | Evidence to collect |
|---|---:|---|---|
| I. API-based AI application | 4 | One domain, one category (NLP), three connected tasks, identified language models, interactive UI and API | Workflow, model choices, UI screenshots, API requests and actual responses |
| II. Fine-tuning | 2 | Fine-tune a pretrained language model on labelled diabetes-support requests and use the saved model in the app | Dataset provenance/splits, training configuration and logs, checkpoint, before/after evaluation, app integration |
| III. RAG model | 4 | Retrieve domain documents and answer questions through a chatbot | Document inventory, retrieved passages, grounded responses, source references, failure examples |
| IV. Anchor | 1 | Explain the clinic support workflow, current limitations, and intended benefit | Before/after workflow and clearly identified industry analogue |
| IV. Apply | 2 | Demonstrate all three NLP tasks, the tuned model, and RAG in that workflow | Representative inputs and outputs with evidence IDs |
| IV. Analyse | 1 | Measure output quality and staff-workflow usefulness; describe prototype gaps | Evaluation tables, timing study, errors and limitations |
| IV. Reflect | 1 | Discuss privacy, security, regulation, infrastructure, cost, integration, and one priority improvement | Individual reflection material, justified deployment priority |
| Submission requirements | Included above | Word/PDF report, screenshots, member contributions, entire-project video on Google Drive | Final report, working video link, contribution table, individual upload confirmations |

### Interpretation and open questions

- The brief says choose **one category**, then refers to sub-tasks “across the chosen categories.” Use three tasks within NLP to satisfy the stricter interpretation.
- The brief says each student uploads the same file “except the Situated Learning – Part 4.” This could refer to all of Section IV or only its fourth subsection. Seek instructor clarification immediately. Prepare a shared technical report and a separate complete workplace section for each member so either interpretation is manageable.
- The supplied brief contains no actual due date or time. Use the team's corrected 12 November submission date, and verify the portal cutoff on 30 October. Finish internally by 10 November and retain 11 November as contingency. The brief states a one-mark-per-day late penalty and no extension/makeup.
- These two submission details cannot be settled from the brief or this plan alone. Until the instructor/portal confirms them, treat the upload wording and exact cutoff as open decisions; do not represent either as verified.
- The brief does not specify a minimum training-set size, a target accuracy, cloud hosting, number of endpoints, report length, or video duration. Any such numbers in this plan are internal targets, not assessment rules.
- Group 49 and the four names in the roadmap are carried over from the existing Assignment 1 report. Confirm the same membership before preparing final contribution declarations.

## 3. Connection to Assignment 1

Assignment 1 provides the healthcare context, experience with FastAPI and Swagger, cloud/container patterns, and report/video conventions. Its existing Random Forest and Logistic Regression models operate on tabular survey features. They do not satisfy this assessment's language-model fine-tuning, three NLP tasks, or RAG chatbot requirements.

Reuse the project narrative and engineering patterns after review. Build the Assessment 2 application separately under `Assignment-2`; retain Assignment 1 as historical work. No numerical risk-prediction integration is needed for the minimum submission, and the prior survey data must not be presented as patient conversations or a clinical knowledge base.

Repository finding: the current root deployment workflow triggers on pushes and targets Assignment 1. Before future implementation is pushed, plan path/branch scoping and separate Assessment 2 service names so documentation or application changes do not unexpectedly redeploy the earlier project. No workflow changes have been made in this planning task.

## 4. Three NLP tasks and the model strategy

| Task | Input | Output | Why it belongs in this workflow |
|---|---|---|---|
| Request classification | Original support message | One primary support category, or staff review | Routes the request to the appropriate staff queue |
| Summarisation | Original message or short conversation | Brief factual handoff summary | Reduces reading effort while retaining the user's requests |
| Question answering with RAG | Staff question plus retrieved passages | Answer with source references, or an explicit inability to answer | Helps staff find supported information without searching multiple documents |

**Proposed starting stack:** a simple Streamlit interface calling FastAPI; Hugging Face Transformers for the language model; Sentence Transformers for embeddings; a small local similarity index for retrieval. This is a design recommendation, not a tested environment or a commitment to paid infrastructure.

**Language model candidate:** `google/flan-t5-base`. Use a fine-tuned copy for request classification and retain the original checkpoint for summarisation and context-based Q&A. Its instruction-oriented text-to-text design makes these candidate uses plausible, but it must pass a small quality and hardware pilot on 31 October. The model card does not establish healthcare reliability. See the [FLAN-T5 model card](https://huggingface.co/google/flan-t5-base).

**Retrieval model candidate:** `sentence-transformers/all-MiniLM-L6-v2`, intended for sentence/paragraph embeddings and semantic search. The model card notes truncation beyond 256 word pieces by default; keep document chunks within the actual tokenizer limit. See the [embedding model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

Freeze model revisions, package versions, input limits, and the runtime after the pilot. Keep the two generator checkpoints' roles explicit in the app and report. Do not assume that classification tuning also improves summarisation or Q&A.

If the initial generator fails the pilot, choose one better-fitting instruction model or a hosted generator on 31 October after checking access, cost and handling of synthetic inputs. Preserve the actual fine-tuned classifier in the workflow. If training memory is the blocker, evaluate a smaller FLAN-T5 checkpoint or parameter-efficient tuning and document the change. Do not substitute prompt changes for fine-tuning.

Budget is unconfirmed: plan for local inference and an available training environment first; verify compute access on day one. No free GPU availability, training duration, or hosting cost is assumed.

The 31 October feasibility pilot should use development examples only: ten short summary inputs, ten supported questions with known source passages, and a small training subset. Verify that training runs, the saved model reloads, summaries preserve the requests, and answers are supported by the supplied context. Measure end-to-end latency and peak memory on the intended demonstration machine with the classifier, generator and embeddings available together. If the pilot is unusable, resolve model/runtime selection that day before committing to the full run.

## 5. Data preparation and actual fine-tuning

Maintain three separate assets:

1. **Classification dataset:** proposed 400 short, synthetic diabetes-clinic support messages in total, including its training, validation and test partitions; approximately 80 per category: appointment support, education-resource request, portal/technical support, records/administrative request, and clinical-staff referral. These are operational routing categories, not diagnoses or urgency levels.
2. **Knowledge collection:** approximately 8–12 short, reviewed documents or selected sections, combining public diabetes-education material with clearly marked synthetic clinic procedures.
3. **Development and evaluation collections:** use the classifier's validation partition for model selection. Separately prepare ten development Q&A cases and ten development summary inputs for prompt/retrieval tuning. Reserve 30 additional Q&A scenarios and 20 additional messages with human-written summaries for final evaluation. Keep benchmark question/answer pairs and reference summaries out of training data and the retrieval index. The source documents needed to answer the questions belong in the index; the benchmark answers themselves do not.

Dataset fields should include example ID, message, category, scenario-family ID, synthetic/anonymised provenance, and reviewer status. Write label definitions and examples before creating the dataset. Include paraphrases, spelling errors, mixed requests, and ambiguous messages. Use a documented primary-category rule and flag additional needs in the summary.

Split training data approximately 70/15/15 into training/validation/test while preserving class coverage. Keep paraphrases and messages from the same underlying scenario together; split by scenario family before producing variants. Have another member review each example and resolve label disagreements before the dataset handoff; independently check final test labels without exposing them to the model-development work. Do not remove difficult examples or reduce class/scenario coverage to meet a date.

For 400 messages, target roughly 280 training, 60 validation and 60 test messages; scenario-family separation takes priority over exact counts. All four members draft approximately 100 messages each across the five categories. Sanjay coordinates label review, deduplication and split assignment; Raga receives the reviewed data for training. Record whether text was human-authored or model-assisted and how it was reviewed. Sanjay keeps final benchmark labels/answers separate from the model-development work until evaluation. Retain the approximately 400-example plan and allow dedicated review time on 1 November. Dataset size is not a substitute for quality: replace duplicates or invalid examples with reviewed examples, report actual split sizes, and require an explicit team decision for any substantive redesign rather than automatically shrinking the dataset to recover time.

Define overlap handling before annotation: clinical advice requests take the clinical-staff-referral category; otherwise use the main explicit request, preserve secondary requests in the summary, and send genuinely unresolved cases for staff review. Out-of-domain requests and invalid model labels must not be silently forced into a clinic category. Staff-review status is an application outcome, not an untrained sixth class or an invented confidence percentage.

### Fine-tuning sequence

1. Define the classification input instruction and the allowed output labels.
2. Record the original model's development baseline using a fixed prompt, decoding settings, and the validation partition. Keep final test labels/results sealed during model selection.
3. Train the model on the training split; use validation results to select the checkpoint. Record model revision, seed, split IDs, hyperparameters, hardware, runtime, and loss history.
4. Freeze the selected checkpoint, prompts and decoding settings by 3 November before final evaluation on 4 November. Evaluate the baseline and tuned checkpoint on exactly the same untouched test set. Report macro-F1, accuracy, per-class precision/recall, confusion matrix, and invalid-label outputs. Do not present unmeasured improvement as a result.
5. Save the checkpoint and tokenizer, reload them in a fresh session, and verify that the API uses that checkpoint for classification.
6. Capture a small set of successes and failures. If tuning does not improve performance, report it honestly and investigate using validation data rather than repeatedly tuning against the test set.

The training artifact, training record and working integration together demonstrate fine-tuning. Calling an existing fine-tuned model or creating embeddings alone does not demonstrate that the team fine-tuned a model. Hugging Face's [sequence-to-sequence training guide](https://huggingface.co/docs/transformers/en/tasks/summarization) provides a relevant training/save/inference workflow; classification targets would be category names rather than summaries.

## 6. Knowledge documents and RAG design

Candidate public sources include [NIDDK's diabetes overview](https://www.niddk.nih.gov/health-information/diabetes/overview) and [CDC's diabetes education and support overview](https://www.cdc.gov/diabetes/education-support-programs/index.html). These are candidate education sources, not an endorsement of an automated clinical application. Review exact sections before ingestion and retain publisher, URL, title, date accessed, document version and reuse conditions. Their US context must not be presented as local clinic policy.

Prepare synthetic clinic documents for appointment changes, education-session registration, portal troubleshooting, record requests, and staff referral procedures. Clearly mark their fictional origin in both the app and report. Exclude individual treatment instructions and dosing from the supported Q&A scope.

### Retrieval and answering sequence

1. Extract text and verify it against the original document. Remove navigation noise and repeated headers; keep useful section boundaries.
2. Split into short passages with modest overlap. Start around 150–200 embedding-token chunks, then measure truncation and retrieval quality.
3. Store passage IDs with document title, source, section/page, version, and content. Embed passages and create the retrieval index once; rebuild only when documents change.
4. Retrieve the top few passages for the question; start with three, then tune on development examples. Pack only what fits the generator's verified input budget, reserving room for the instruction, question and short conversation context. Never silently truncate the evidence.
5. Ask the model to answer using the supplied context. Return source IDs that the application resolves to real passages; reject invented source IDs. Check manually that cited text actually supports the answer.
6. When evidence is weak, absent, conflicting, or outside scope, show an inability to answer and route to staff. Similarity scores alone are not probabilities of correctness.
7. Show the answer, source references and expandable retrieved passages in the chat UI. Resolve follow-up questions from bounded conversation context and retrieve again.

Clinical questions about diagnosis, personal laboratory interpretation, or medication changes should be passed to qualified staff. Scope controls must be checked independently of the learned category; a classifier error must not automatically enable a clinical answer. Do not claim the prototype reliably detects every clinical or urgent situation.

## 7. Interface and API plan

Use one screen with a support-message field, category result, handoff summary, chatbot and evidence panel. A short curated document list is sufficient; arbitrary public file upload adds unnecessary scope.

| Proposed API operation | Responsibility | Result/evidence |
|---|---|---|
| Analyse support message | Run the tuned classifier and summary model | Category/review status, summary, model identifiers |
| Chat with knowledge base | Retrieve passages and generate a grounded response | Answer or abstention, source IDs, retrieved passages, timing |
| Health and model metadata | Confirm service and artifact readiness | Availability, checkpoint version, index version |

Exact endpoint names and schemas can be fixed during implementation. Test actual requests through Swagger and ensure the UI calls the API. Keep patient-like sample data synthetic; exclude secrets and raw sensitive message content from logs. The API must surface missing models, missing index, invalid input and inference failures clearly.

Agree the component contracts on 30 October: Raga supplies the classifier checkpoint/tokenizer, label mapping, input format and summary-generation settings; Sathish supplies the index, embedding revision, passage metadata and grounded-chat result; Bhuvnesh connects these through the API. Every result identifies the model/index version and distinguishes success, staff review, insufficient evidence and runtime failure. Sanjay owns representative acceptance inputs and expected outcomes. These contracts are planning deliverables, not code required today.

A working local interactive demonstration meets the brief's stated interface requirement. Cloud hosting is a useful enhancement if time, memory and budget permit; assess a separate service after the core integration works. Do not add Composer scheduling, Kubernetes, a live hospital connector or a patient database to the minimum project.

## 8. Evaluation and workplace evidence

These are proposed internal acceptance targets, not claimed results or grade guarantees. Freeze them before the final evaluation and report any misses. Do not lower thresholds, shrink final test sets, skip reviews or remove failed cases to meet an internal date. A missed target keeps the corresponding quality gate open until corrected and verified; reporting a limitation does not turn a failed gate into a pass.

| Area | Evaluation method | Proposed gate |
|---|---|---|
| Classification | Independent held-out messages; base and tuned comparison | Target macro-F1 at least 0.80; show per-class weaknesses and invalid outputs |
| Summaries | 20 held-out messages; reviewers check retained facts and invented facts | At least 18/20 retain all essential requests; zero invented clinical facts in this set |
| Retrieval | 20 answerable Q&A cases with human-labelled relevant passages | Relevant evidence among the top three for at least 18/20 |
| Answers | Same 20 cases; reviewers check correctness, completeness and source support | At least 18/20 supported and useful; zero fabricated citations |
| Unsupported requests | 5 outside-corpus and 5 clinical/out-of-scope cases | All 10 abstain or refer appropriately in this test set |
| Workplace usefulness | 10 representative tasks completed manually and with assistance | Record completion time, correctness and staff corrections; claim efficiency only if measured |
| Integration | Fresh start; UI/API; all three tasks; model reload; source display; error paths | All core flows work using the final saved artifacts |

Counterbalance manual-first and assistant-first tasks, or use equivalent paired scenarios, to reduce timing-study practice effects. Explain that team-member simulations and small synthetic test sets do not establish clinical readiness, organisational adoption, or production-scale performance. Include a follow-up question, ambiguous request, missing document, and conflicting-document case in functional review.

The proposed test sets are small prototype checks, not clinical-safety evidence. Report exact denominators, per-class results and failures; treat the numeric gates as internal targets and do not claim a target passing establishes safe or clinically reliable performance.

For Q&A, report retrieval success among the top three candidates **and** whether supporting evidence survives context packing into the actual generation input. A relevant passage that is retrieved but omitted cannot support the resulting answer. Freeze prompts, chunking, retrieval settings and checkpoints using development examples by 3 November; run final tests on 4 November. Fix defects on 5 November and verify the corrected system on 6 November. If final-test failures lead to changes, retain the original results and label reruns as regression checks. Before claiming independent post-fix performance, use fresh, independently prepared cases with the original evaluation coverage and sample counts; for classifier comparisons, evaluate both baseline and tuned models on the same fresh cases.

Use three named end-to-end evidence cases: **A**, appointment change plus a missing education leaflet; **B**, a general diabetes-education question with a source-backed answer and follow-up; **C**, a request for an individual treatment change that is summarised and referred to staff. These cases demonstrate workflow behaviour; the separate held-out sets measure quality. Do not turn three curated demonstrations into an accuracy claim.

### Required “Situated Learning – Workplace Application” section

- **Anchor:** explain the fictional diabetes clinic, support staff, incoming messages, current document search/routing process, and intended benefit.
- **Apply:** show at least three end-to-end workplace cases, mapping the classifier, summary, fine-tuned checkpoint and RAG answer to staff actions. Include one appropriate referral/abstention.
- **Analyse:** present measured quality and timing, errors, data limitations, anticipated integration needs and the gap between the prototype and operational use.
- **Reflect:** address privacy, security, applicable regulation, infrastructure, cost and system integration. Propose **clinician-led validation of answer correctness and referral behaviour before any patient-facing use** as the single priority improvement. Justify it using prototype limitations and measured failures; do not imply clinician feedback was obtained unless it was. Other improvements remain secondary, and legal claims require jurisdiction-specific verification.

## 9. Plan review and scope controls

Review conclusion: the proposed design covers every assessed component, but feasibility depends on early compute access, actual member availability and acceptable generator quality. The schedule is a conditional target for a small four-person prototype. Reassess it after the 31 October pilot; training and retrieval must start before interface polish.

| Review finding | Risk | Resolution in this plan |
|---|---|---|
| Prior work is tabular ML | Reuse could be mistaken for meeting NLP/fine-tuning requirements | New language-model task, dataset, training and chatbot |
| Earlier internal target compressed review and integration | Rushed data or skipped validation could undermine quality | Move internal completion to 10 November; keep 11 November as contingency and preserve quality gates |
| Fine-tuning is easy to postpone | Missing mandatory two-mark component | Hardware pilot on 31 October; reviewed data on 1 November; baseline/training by 2 November |
| Small generator may give weak answers | RAG could retrieve correct text yet answer incorrectly | Pilot early; preserve context limits; evaluate retrieval and generation separately |
| Synthetic data can make tests artificially easy | Inflated evaluation | Scenario-level split, independent labels, separately authored test examples |
| Pilot and final tests can become mixed | Model and prompt choices could overfit the reported benchmark | Separate development sets; freeze on 3 November; final tests on 4 November; independent post-fix checks on 6 November |
| Dataset preparation originally rested on the model owner | Training could be delayed by annotation work | Four members author data; Sanjay coordinates review/splits; Raga focuses on models |
| Retrieved evidence can be lost when inputs are shortened | Retrieval scores can look good while answers lack support | Check both retrieved candidates and the context actually supplied to the generator |
| Healthcare context raises output-quality stakes | Personalised clinical advice could be mistaken for supported information | Staff-facing education/admin scope and tested referral behaviour |
| Workplace section carries five marks | Generic reflection could lose the largest component | Named cases, measured workflow evaluation and individual workplace material |
| Submission wording is ambiguous | Members may submit the wrong version | Instructor clarification plus separate per-member Section IV drafts |
| Existing CI targets Assignment 1 | CI runs on every push; production deployment is restricted to `main` | Keep the distinction clear and review path/workflow scoping before implementation is merged |

If time is lost, defer optional cloud hosting, cosmetic UI work and unplanned features first. Preserve the planned dataset/scenario coverage, document coverage, all three NLP tasks, real fine-tuning, document retrieval with chat, independent evaluation, workplace evidence, report and video. Reassign work and use the 11 November contingency rather than weakening checks. If mandatory work or a quality gate still cannot be completed, escalate immediately, record the failed gate honestly and seek instructor guidance; do not claim readiness or assume the official deadline can move.

## 10. Report and demonstration plan

Report order: cover and contributions; workplace problem/objective; three-task design and models; data and fine-tuning; RAG documents and workflow; interface/API evidence; evaluation; a separate **“Situated Learning – Workplace Application”** section; limitations; references; video link and reproduction notes.

Use evidence IDs for dataset/split review, training run, checkpoint reload, base-versus-tuned results, each NLP task, API responses, retrieved sources, unsupported query handling, and workplace timings. Screenshots must reflect the final working version; annotate what each proves. Each owner supplies their explanation and evidence as they finish.

Proposed video length: 6–8 minutes, as a team planning choice. Show the problem, one integrated support case, three task outputs, fine-tuning evidence and comparison, chatbot sources and follow-up, a refusal/referral case, API use, workplace results and limitations. Save a backup recording; verify the Google Drive viewer link from a separate viewer session.

Name the report `49.pdf` or `49.docx` if Group 49 continues. Capture actual contributions rather than asserting equal completed work in advance. All four members must complete their own portal submission according to the clarified Section IV requirement.

## 11. Roadmap: quality-checked completion by 10 November; submit by 12 November 2026

Finish and verify the complete submission package by **the end of 10 November**, including the working app, evaluated models, report(s), contribution statements and accessible demonstration video. Submit early if the portal permits. **11 November is contingency time only**, not planned development; **12 November is the official submission date supplied by the team**, subject to confirming the portal cutoff. This replaces the earlier 8 November internal target; it does not extend the official deadline. The allocation below uses the four-member roster from Assignment 1 and records planned work, not completed contributions.

### 11.1. Ownership and handoffs

| Owner | Primary work | Supporting work | Deliverable/handoff |
|---|---|---|---|
| Pushadapu Sanjay Kumar | Scope, workplace analogue, source selection, dataset coordination/review/splits, report coordination | Independent benchmark preparation, manual workflow baseline and final submission audit | Reviewed dataset and label guide to Raga; acceptance cases to Bhuvnesh; consolidated report and workplace evidence |
| Sathish Krishnan V | Document extraction, chunking, embeddings, retrieval, grounded answer generation and citations | Knowledge-source review, RAG evaluation and failure handling | Versioned index, chat/retriever interface and evaluated source-backed results to app owner |
| Chezrla Raga Suma | Model/runtime pilot, classification baseline, fine-tuning, summarisation and model evaluation | Training/evaluation report and model handoff support | Reloadable tuned classifier, baseline summary model, input/output conventions and metrics to app owner |
| Bhuvnesh Mishra | FastAPI, UI, integration, runtime packaging and optional deployment | API evidence, integration tests and video assembly | Working integrated demo, API screenshots and final recording |

All members draft approximately 100 classification messages, review another member's examples, draft their own workplace application/reflection material, cross-review technical outputs, and submit individually. A 25% share each is a planning target only; final qualitative and quantitative contributions must reflect the actual work. Confirm available time on 30 October and rebalance if one owner cannot meet a dependency date.

### 11.2. Daily execution plan

| Date | Work to complete | Owners | Required result before moving on |
|---|---|---|---|
| **30 Oct: scope and access** | Confirm team, Group 49, portal time and individual-section wording. Freeze the healthcare support scope, five routing labels and three tasks. Select public sources and synthetic clinic procedures. Confirm training hardware and budget. Agree API/model/retrieval handoff formats. | All; Sanjay coordinates | One agreed scope, source list, label guide, usable compute route and clear ownership. Open instructor questions recorded. |
| **31 Oct: feasibility and data start** | Pilot the generator on development summaries and source-backed answers. Run a small training/reload check and measure combined runtime memory/latency. Draft and review an initial data batch; curate the pilot documents and separate development from final-evaluation examples. Begin basic API/UI structure. Do not scale data generation until the pilot passes. | All: draft data; Sanjay: data review/splits; Raga: models; Sathish: documents/chat; Bhuvnesh: app | Go/no-go model and hardware decision; initial label/data quality checked; interface contracts agreed; remaining data work and owners explicit. |
| **1 Nov: data and document quality** | Complete approximately 400 messages, peer review, deduplication, label disagreements and scenario-grouped splits. Curate the planned 8–12 documents/sections and finalise the independent evaluation cases. Keep test labels sealed from model development. Continue API/UI wiring against agreed contracts and draft report sections. | All author/review; Sanjay owns splits; Sathish owns documents; Raga prepares training; Bhuvnesh owns app structure | Reviewed dataset with all five labels and split/provenance records; approved corpus; development/final sets separated. Unreviewed data does not advance to training. |
| **2 Nov: training and RAG components** | Record the classification baseline, fine-tune using training/validation data, save/reload the selected checkpoint and measure runtime. In parallel, build the retrieval index, grounded answering path and source metadata. Hand real component outputs to the app owner. | Raga: models; Sathish: RAG; Bhuvnesh: component wiring; Sanjay: quality review | Reloadable tuned artifact and validation results; real retrieved evidence and grounded answers; versioned component handoffs. |
| **3 Nov: full integration and evaluation freeze** | Connect all three tasks, source panel and chat follow-ups. Add staff-referral/abstention paths and visible errors. Verify fresh-start operation and artifact metadata. Freeze model, prompts, chunking and retrieval settings using development cases only. | Bhuvnesh leads; Raga/Sathish resolve component issues; Sanjay runs development cases | At least three complete workplace cases work end to end; correct checkpoint is loaded; no core dependency remains mocked; evaluation configuration recorded. |
| **4 Nov: independent evaluation** | Run the full held-out classifier, summary and RAG evaluation. Complete manual-versus-assisted workflow timing. Record failures and prioritise corrections. Draft all members' Section IV material. | Sanjay coordinates independent review; all supply results | Complete metrics, sample counts, workplace timings and a prioritised defect list. No failed cases omitted and no targets weakened. |
| **5 Nov: corrections** | Fix material defects without new feature work. Preserve original benchmark results and run regression checks. Independently prepare fresh post-fix evaluation cases where model/prompt/retrieval changes require new quality claims. | Component owners fix; Sanjay coordinates fresh cases without exposing answers to developers | Fixes ready for independent verification; original results retained; fresh cases match the planned evaluation coverage and sample counts where required. |
| **6 Nov: independent verification and final freeze** | Another member verifies fixes, runs relevant regression and fresh-case evaluation, and repeats all core integration/error paths from a fresh start. Freeze final app, model and index versions only after the relevant gates pass. | Sanjay coordinates; another member verifies each owner's changes | Quality gates verified against unchanged targets; unsupported claims removed; final artifact versions recorded. Any failed gate remains open and triggers recovery planning. |
| **7 Nov: evidence and reproduction** | Rehearse from a fresh start, verify checkpoint/index loading, capture final UI/API/source screenshots and complete workplace cases. Check all evidence matches the final version. | Bhuvnesh: rehearsal/API; Sathish: RAG; Raga: model evidence; Sanjay: audit | Complete evidence inventory, reproducible demo and measured workplace findings ready for the report. |
| **8 Nov: report and individual sections** | Complete the shared report, references and actual contributions. Finalise each member's workplace material using clarified submission instructions. Review the exported Word/PDF layout and evidence coverage. | Sanjay compiles; all author and cross-review | Complete report draft(s), accurate contribution table and no missing rubric sections. |
| **9 Nov: video and submission rehearsal** | Record the full demonstration, upload to Google Drive and verify viewer access. Cross-check video, report and final app. Each member checks their submission file and naming. | Bhuvnesh: recording; all: presentation/review | Accessible final video, consistent report(s), correct member packages and backup assets. |
| **10 Nov: internal completion** | Complete independent final review and only blocking corrections. Verify report rendering, video access and fresh-start demo. Back up the final package. Submit individually now if the portal permits. | All four members | App, models/index, evaluation, report(s), contributions and video finished with recorded quality-gate results. Early-submission receipts retained where available. |
| **11 Nov: contingency only** | Keep the completed package ready; recover from unexpected blocking defects, access or portal issues if any. Reverify affected gates and refresh evidence after any app/artifact change. No scope expansion. | Relevant owner; all monitor their own submission | Any missed 10 November target is recorded honestly; no gate is waived, and any exceptional correction is documented and verified before readiness is claimed. |
| **12 Nov: official submission deadline** | Every member verifies their individual upload and video link before the exact portal cutoff, including members who submitted early. | Every member | Four individual submission confirmations and final files safely retained. |

### 11.3. Dependencies that control the schedule

1. **Scope and labels → dataset split → baseline → fine-tuning → saved model → API integration.** Fine-tuning is a required path; do not leave it until video day.
2. **Approved documents → extraction/chunks → retrieval → grounded chat → evaluated sources.** A chat screen without document retrieval is not completed RAG.
3. **Shared interface contracts → component delivery → end-to-end app → final evidence.** UI work can start alongside model and retrieval work once contracts are agreed.
4. **Workplace scenario → evaluation design → measured outputs → individual workplace sections.** Begin this on day one because it accounts for 5/15 marks.
5. **Final working app + evaluation → corrections → independent verification → evidence → report/video → member checks → individual submissions.** Freeze evaluation configuration on 3 November, verify corrections and freeze final artifacts on 6 November, and complete evidence and delivery work by 10 November; 11 November is contingency only. A failed gate takes priority over a planned handoff date and must not be bypassed.

### 11.4. Milestone review gates

| Gate | Check | If it fails |
|---|---|---|
| **G0 — 30 Oct** | Hardware access, four owners, supported domain, source availability | Resolve access and data feasibility immediately; use the permitted synthetic industry analogue |
| **G1 — 31 Oct** | Candidate model can train and produce usable short summaries/Q&A on the available runtime | Resolve model/compute suitability before scaling up; preserve task quality and real tuning |
| **G2 — 1 Nov** | Reviewed dataset, defensible splits, approved documents and separated evaluation sets ready | Reassign review work and replace invalid examples; do not shrink coverage or use unchecked data |
| **G3 — 2 Nov** | Saved trained model reloads; retrieval returns real supporting passages | Prioritise training/index repair; defer hosting and visual polish |
| **G4 — 3 Nov** | All three tasks work together through UI/API; evaluation configuration frozen | Fix integration before final tests; keep test labels sealed |
| **G5 — 4 Nov** | Full evaluation complete against the unchanged targets | Fix failures; preserve original results and prepare independent post-fix checks |
| **G6 — 6 Nov** | Corrections independently verified; relevant quality gates passed; final artifacts frozen | Keep failed gates open, reassign work and use contingency; do not waive checks or claim readiness |
| **G7 — 7 Nov** | Final-version evidence and fresh-start demonstration verified | Repair evidence/reproduction gaps before recording the video |
| **G8 — 9 Nov** | Report(s), contributions, individual workplace material and video ready | Resolve content/access gaps before final review; do not omit assessed evidence |
| **G9 — 10 Nov** | All deliverables complete, quality gates recorded and package independently checked | Record any missed internal target honestly; use 11 November for verified recovery |
| **G10 — 12 Nov** | All four individual submission confirmations checked | Resolve portal/file issues before the exact official cutoff; no extension assumed |

### 11.5. Evidence ownership checklist

- [ ] **Sanjay:** approved scope, workplace before/after process, source/provenance inventory, reviewed data/splits, independent benchmark records and final rubric audit.
- [ ] **Raga:** dataset/split summary, base-model comparison, training logs/configuration, checkpoint reload, summary examples and model metrics.
- [ ] **Sathish:** document/chunk inventory, retrieval cases, cited answers, follow-up question and unsupported-question results.
- [ ] **Bhuvnesh:** UI screenshots for all tasks, successful and failed API calls, final runtime/version record, end-to-end video.
- [ ] **All:** measured workplace cases, individual Section IV draft, real contribution statement and peer review.
- [ ] **All:** verified video access, final report(s), exact portal instructions and individual upload acknowledgement.

### 11.6. Reviewed scope: retain and defer

**Retain:** one healthcare NLP workflow; three tasks; an actually fine-tuned model used by the app; document retrieval with chat and source evidence; measurable workplace application; screenshots; report; video; four individual submissions.

**Defer unless the core is complete:** live hospital integration, patient database, multilingual support, voice/image features, automatic appointments or messaging, diabetes-risk prediction integration, complex cloud architecture and scheduled retraining.

The project is ready to begin with scope/data preparation. The next unresolved decisions are the training runtime/budget, the portal cutoff and the instructor's meaning of the individual Situated Learning requirement. These do not prevent preparing the agreed healthcare scenario, labels and source inventory.

### 11.7. First-day checklist: 30 October

- [ ] Confirm the four members' availability and the owners in Section 11.1.
- [ ] Verify the 12 November portal cutoff, record the revised internal 10 November completion target and 11 November contingency, and request clarification of the individual Section IV requirement.
- [ ] Agree the fictional clinic description, five category definitions, overlap rules and three demonstration cases.
- [ ] Confirm a usable training environment, the intended demo machine and any spending limit.
- [ ] Select two public education sources and draft one short synthetic clinic procedure for the pilot.
- [ ] Prepare a small reviewed training sample plus separate development questions and summary examples; assign the remaining data preparation across all four members.
- [ ] Agree model/API/retrieval input-output contracts; record reviewed-data handoff on 1 November, model/RAG handoff on 2 November and integrated evaluation freeze on 3 November.
- [ ] Begin shared technical-report notes and each member's workplace notes alongside the practical work.
