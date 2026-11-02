# Assignment 2 Gap Review

**Review date:** 2 November 2026  
**Scope:** Assignment-2 workspace source, data, tests, report, and plan.  
**Rubric basis:** The rubric summary in `PLAN.md`. The local assignment PDF was not text-extractable with the available review tools; confirm the part names and mark allocation against the official brief before submission.  
**Verification:** Read-only review. Tests were not run.

## Overall Assessment

The project has a substantial technical prototype: a React UI, FastAPI endpoints, a full-fine-tuned classifier, a summarizer, and a RAG flow that returns source passages. It is **not submission-ready**. The principal gaps are incomplete Part IV evidence, limited RAG evaluation, missing portable classifier artifacts/evidence, test expectations that no longer match current code, and unfinished final submission materials.

| Part | Marks in `PLAN.md` | Current status | Main gap |
|---|---:|---|---|
| I. API-based AI application | 4 | Mostly implemented | E2E/API tests are stale or narrow; integrated evidence is missing |
| II. Fine-tuning | 2 | Implemented, evidence incomplete | Classifier run record and checkpoint are not in the workspace |
| III. RAG model | 4 | Prototype implemented | Planned held-out retrieval, answer, and abstention evaluation is missing |
| IV. Situated Learning | 5 | Incomplete | Anchor is drafted; Apply, Analyse, and Reflect are pending |
| Submission package | Not separately scored in the plan | Incomplete | Contributions, screenshots, video, and final export are pending |

## Part I: API-Based AI Application

| # | Requirement / check | Status | Evidence and gap | Action |
|---|---|---|---|---|
| 1.1 | Domain and NLP category | Present | The report describes a fictional diabetes-clinic support desk. | Keep the fictional setting explicit; do not imply real-clinic deployment. |
| 1.2 | Three connected NLP tasks | Implemented | Classification, summarisation, and document-grounded Q&A are wired through the application. | Demonstrate them together in one complete workflow case. |
| 1.3 | AI models identified | Present | The report names `google/flan-t5-base` and `sentence-transformers/all-MiniLM-L6-v2`. | Pin and record the retrieval-model revision; its current default revision is unset. |
| 1.4 | API and UI | Implemented | The API exposes `/analyze`, `/retrieve`, and `/chat`; the React UI calls analysis and chat and displays source passages. | Add final screenshots and request/response evidence. The report's architecture table should also list `/retrieve`. |
| 1.5 | API analysis test | Test expectation is stale | In `backend/tests/test_api.py`, the fake generator looks for `Create a concise staff handoff summary`. The current prompt in `backend/src/diabetes_support/infrastructure/seq2seq_summarizer.py` says `Create a concise, factual staff handoff summary`. The fake therefore returns `appointment_support` instead of its expected summary. | Update the fake prompt check to match the current prompt, then run the test suite. This is a code-based finding; the test was not run in this review. |
| 1.6 | Browser workflow test | Test selectors are stale | `tests/e2e/test_react_app.py` expects heading `Diabetes support desk` and textbox `Incoming support message`. `frontend/src/App.tsx` currently renders `Diabetes support` and labels the field `Incoming message`. | Align selectors with the current UI, then exercise analysis and chat rather than checking only initial controls. The test was not run in this review. |
| 1.7 | API test coverage | Limited | The API tests cover health, metadata, one mocked analysis, and personal-medication abstention. They do not establish end-to-end retrieval quality or source-supported generation. | Add focused tests for retrieved sources, low-score abstention, answerer output, and invalid/missing components. |

## Part II: Fine-Tuning

| # | Requirement / check | Status | Evidence and gap | Action |
|---|---|---|---|---|
| 2.1 | Domain-relevant labelled data | Present | The report describes synthetic classification partitions: 280 training, 60 validation, and 60 test examples across five labels. | Retain provenance and review limits; these AI-drafted synthetic examples are not clinical validation. |
| 2.2 | Training method | Implemented | `scripts/train_classifier.py` uses AdamW with `model.parameters()` and saves a full model checkpoint. This is full fine-tuning, not LoRA or QLoRA. | Describe it accurately. Full fine-tuning changes existing weight values; parameter count need not increase. |
| 2.3 | Baseline-versus-tuned evaluation | Reported, not independently verifiable here | `docs/report/report.md` reports classifier validation and held-out test results. The classifier's raw run/evaluation artifacts and checkpoint are not present in the workspace; the report says they are local/ignored. | Add a compact tracked run record with base revision, data hashes, training settings, metrics, and checkpoint checksum. Keep large weights in approved storage if they should not be committed. |
| 2.4 | Tuned checkpoint used by app | Reported | The report says the classifier checkpoint was reload-verified locally and configured through `CLASSIFIER_MODEL_NAME`. | Confirm the complete checkpoint and tokenizer are available in the final demo environment, with the correct local `.env` setting. |
| 2.5 | Summarizer fine-tuning | Candidate evidence present | `docs/report/evidence/summarizer-v2-run.json` records a full fine-tuning run and validation comparison. It explicitly says the checkpoint is not configured for inference. | Keep it labelled as an experiment until quality review and held-out evaluation support changing the app configuration. |
| 2.6 | Summary test evaluation | Missing from workspace | Training and validation summary files exist, but no separate summarization test partition was found. The run record says the test set was not loaded. | Create/use the planned independent human-written summary test set before claiming test performance. |

## Part III: RAG Model

| # | Requirement / check | Status | Evidence and gap | Action |
|---|---|---|---|---|
| 3.1 | Domain source and corpus | Implemented, narrow scope | WHO Diabetes Q&A is documented in `data/knowledge/manifest.json`; curated notes and chunks support general diabetes information. It does not cover fictional clinic procedures. | State the scope limit in the UI/report and refer clinic-specific questions to staff. |
| 3.2 | Retrieval and source display | Implemented | The retriever returns top passages, source metadata, and similarity scores; the UI exposes passages and original-source links. | Keep recording exact retrieved passages in evaluation evidence. |
| 3.3 | Grounded answer generation | Implemented as a prototype | `/chat` supplies retrieved passages to FLAN-T5 and returns the retrieved records as sources. The prompt asks the model to answer only from context, but generated claims are not independently checked against the passage. | Review answer correctness and citation support; do not treat prompt instructions or returned sources as proof of grounding. |
| 3.4 | Abstention and referral | Partial | There is a provisional retrieval-score floor and a small set of regex rules for common personal-care questions. The score is not a calibrated probability, and regex coverage is limited. | Test varied clinical, urgent, ambiguous, and out-of-corpus wording; report failures and retain staff-review language. |
| 3.5 | RAG evaluation | Missing | The report describes a few manual smoke checks. No held-out RAG question/evidence set was found in the workspace. | Build and report the planned answerable, outside-corpus, and clinical test cases; include retrieval relevance, answer support, citation correctness, and abstention results. |
| 3.6 | Follow-up context | Not implemented | The UI stores previous exchanges locally, but `askKnowledgeQuestion` sends only the current question and the API schema accepts only one question. | Either implement bounded conversation context and test it, or remove follow-up support claims from the report/demo. |

## Part IV: Situated Learning - Workplace Application

| # | Sub-part | Marks in `PLAN.md` | Status | Required completion |
|---|---|---:|---|---|
| 4.1 | Anchor | 1 | Drafted | Describe the fictional workplace, current manual process, pain points, and intended benefit. Keep this as a proposed analogue, not an observed deployment. |
| 4.2 | Apply | 2 | Pending | Demonstrate three complete cases: appointment change plus missing leaflet; a general WHO-backed education question; and a personal treatment-change request referred to staff. Show classifier, summary, retrieved evidence, answer/referral, and staff action. |
| 4.3 | Analyse | 1 | Pending | Measure representative manual-versus-assisted tasks. Report sample sizes, completion times, quality, staff corrections, failures, and limitations; do not claim efficiency without measured results. |
| 4.4 | Reflect | 1 | Pending | Address privacy, security, applicable regulation, infrastructure, cost, integration, and one justified priority improvement. Clinician-led validation is a proposed improvement, not feedback already obtained. |

The report also says the individual-submission wording is ambiguous. Confirm whether each member needs a separate Part IV section and record the instructor's answer.

## Report and Submission Readiness

| # | Item | Status | Action |
|---|---|---|---|
| 5.1 | Team contribution table | Pending | Confirm actual contributions and shares with all members. |
| 5.2 | Screenshots and evidence IDs | Missing from the workspace review | Capture final-version UI/API/model/RAG evidence and identify exactly what each image proves. |
| 5.3 | Demonstration video | Pending | Record the complete workflow, upload it, and verify viewer access. |
| 5.4 | Final report export | Pending | Complete and review the report, then export to the format and filename required by the official brief. |
| 5.5 | Status consistency | Needs update | `PLAN.md` still says no application/model/data has been implemented. `README.md` and `docs/report/report.md` also contain stale base-model/RAG status descriptions. Update them to distinguish implemented prototype from pending evaluation. |

## Priority Actions

1. Fix the stale backend test prompt expectation and E2E selectors; run and record the focused tests.
2. Complete the three integrated Part IV cases, workplace timing study, and reflection.
3. Add portable classifier run evidence and ensure the tuned checkpoint is available in the demo environment.
4. Create and run held-out RAG evaluations for retrieval, answer support/citations, and abstention; keep the narrow source scope explicit.
5. Reconcile stale report/README/plan statements, confirm contribution and individual-submission requirements, and finish screenshots, video, and final export.

## Limitations of This Review

The assessment PDF was not text-extractable with the available review tools, so rubric labels and marks above follow `PLAN.md` and must be checked against the official brief. Tests were not run, and ignored local checkpoints/evaluation artifacts were not available for inspection. Reported model metrics are therefore recorded as report claims, not independently reproduced results.