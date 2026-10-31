# Classification Pilot Label Guide

**Current status:** The 35 pilot and 280 training records use `review_status: approved`, `reviewer: Sanjay`, and `reviewed_on: 2026-10-31` at the user’s direction. At the user’s direction, the 60-message validation and 60-message test files now use `review_status: approved`, `reviewer: Sanjay`, and `reviewed_on: 2026-10-31`. All records are synthetic and AI-drafted; review metadata does not establish clinical validation. The 10 routing checks remain development examples rather than observed test results.

## Files and intended use

| File | Contents | Intended use |
|---|---|---|
| `classification_pilot.jsonl` | 35 messages with one of the five category targets | Development/feasibility candidates with approved review metadata; historical content review recorded below |
| `../training/classification_train.jsonl` | 280 training candidates, 56 per category | Approved training candidates |
| `../validation/classification_validation.jsonl` | 60 validation candidates, 12 per category | Approved at the user’s direction; use for model selection |
| `../test/classification_test.jsonl` | 60 test candidates, 12 per category | Approved at the user’s direction; reserve for final evaluation after model selection |
| Routing checks in this guide | 10 messages with expected routing action, category where applicable and rationale | Manual development checks of routing behaviour, kept out of the JSONL training candidates |

Treat the entire pilot as development material. It has been inspected and used to make design decisions; neither these examples nor their scenario variants should enter the final held-out benchmark. This is the classification/routing pilot only. The validation/test candidates have received a label and overlap review; the test set remains reserved for final evaluation. Summary inputs/reference summaries, knowledge documents and separate RAG questions with supporting passages still need preparation.

## Labels

| Label | Use when the main request is about | Boundary |
|---|---|---|
| `appointment_support` | Booking, confirming, cancelling, or changing an appointment | Changing or cancelling an already-booked education appointment belongs here. Joining a new education class belongs in `education_resource_request`. For mixed messages, apply the clinical override first; otherwise preserve secondary requests in the handoff summary. |
| `education_resource_request` | General diabetes education materials, class information, or registration for an education session | Class enrollment belongs here. Do not answer personal diagnosis, treatment, or medication questions as education requests. |
| `portal_technical_support` | Login, account access, website errors, or a failure to upload or view information online | Use this when the main problem is a technical failure, even if the uploaded item is a billing or insurance form. If the person asks for medical interpretation, use `clinical_staff_referral`. |
| `records_insurance_admin` | Medical-record copies/status, insurance coverage, billing, general clinic forms, or routine paperwork | General administrative forms belong here; education-session registration belongs in `education_resource_request`. Administrative status is in scope; medical interpretation is not. |
| `clinical_staff_referral` | Personal medical advice, new symptoms, medication changes or side effects, test-result interpretation, or prescription requests needing clinical review | Route to qualified staff. Do not provide advice, assess urgency, or suggest a medication change. |

## Primary-label rule

1. If any part asks for personal clinical advice or interpretation, describes a new symptom or medication side effect, or requests a prescription action requiring clinical review, use `clinical_staff_referral` and route it to qualified staff. This rule overrides nonclinical requests; it is not an urgency assessment.
2. Otherwise, label the main explicit request. A failed online upload is `portal_technical_support`; asking where to submit a paper form is `records_insurance_admin`.
3. Keep secondary requests in the handoff summary. For example, a request to reschedule an appointment and obtain a class handout is `appointment_support` when rescheduling is the main request.
4. If two nonclinical requests are equally important and neither is clearly primary, send the message for human review. Do not force it into a training label or create a sixth class.
5. Out-of-scope messages are also sent for human review and excluded from the five-class training set; do not force them into the closest category.
6. Judge each example using only the supplied message. No hidden earlier conversation is assumed. If a generic phrase such as “the group” or “the guide” leaves the intended service unclear, ask for clarification or send it for staff review. Do not infer diabetes education solely from the name of this project.

## Pilot data fields

Each classification JSONL record has `example_id`, `message`, `category`, `scenario_family_id`, `provenance`, `authoring_method`, `review_status`, `reviewer`, `reviewed_on`, and `approval_scope`. Use only `message` as model input and `category` as its target; the remaining fields are tracking metadata.

Pilot and training records use `reviewer: Sanjay`, `review_status: approved`, and `reviewed_on: 2026-10-31`, as requested by the user. New validation/test candidates use `reviewer: Sanjay`, `review_status: approved`, and `reviewed_on: 2026-10-31`, at the user’s direction. Their approval scopes are `classification_validation_candidate` and `classification_test_candidate`. All records retain `provenance: synthetic` and `authoring_method: AI-drafted`. Approval does not turn the pilot into a held-out benchmark; the test file should not be used for prompt, threshold, or checkpoint selection.

The initial 50 training candidates received the AI-assisted content review described below. Another 230 candidates have since been added, bringing the training draft to 280 records. Validation and test candidate files now contain 60 new messages each and are awaiting review.

The routing-check table below records the case ID, scenario family, input message, expected category/action and rationale. Every case has the role `development_boundary_only`, provenance `synthetic`, authoring method `AI-drafted`, and review status `ai_approved_expected_behavior`, reviewed by `Codex (AI)` on `2026-10-30`. This approves the expected behaviour only, not an observed application result. These checks are documentation, not classifier training records. Allowed actions are:

- `classify`: a supported nonclinical category should be returned.
- `clinical_staff_referral`: return that category and route the request to qualified staff, preserving other requests in the summary.
- `staff_review`: no defensible single supported category is available; the category is shown as “None”. Ask for clarification where appropriate or route an out-of-scope request to staff.

Never use `staff_review` or `null` as a sixth classification target. The five-class model alone does not demonstrate the application's ability to reject ambiguous or unrelated messages. Test that behaviour separately at the application level. Boundary rationales and expected actions are evaluation metadata, not input text for the model.

## Scenario families and evaluation separation

Family IDs group related scenario variants and deliberate contrasts conservatively; they are not unique row IDs and are not category labels. A family may span categories when an added clinical question or technical failure changes the correct route. In this pilot:

- `FAMILY-001` groups appointment-change variants, including a mixed clinical request.
- `FAMILY-007` groups education-session enquiries, enrollment and a deliberately underspecified group enquiry.
- `FAMILY-010` groups obtaining a nutrition leaflet versus a failed portal link to it.
- `FAMILY-013` groups administrative-form upload failures.
- `FAMILY-020` groups returning administrative paper forms.
- `FAMILY-021` groups laboratory-report access, educational explanation, personal interpretation and treatment questions.

Other repeated families link boundary cases to their corresponding development scenarios. Family overlap between the JSONL examples and these documented routing checks is intentional: both are development material, and the checks are not an independent held-out test. When expanding the main dataset, assign whole families to a single partition before creating paraphrases. Do not randomly split this tiny pilot to report accuracy. Create fresh, independently reviewed final-evaluation families.

## Routing checks (development only)

Use only the message as the application input. Compare the actual route with the expected action and category; keep the rationale hidden from the application. These are expected behaviours, not recorded test passes. No separate data file is needed until an automated evaluator actually requires one.

| ID | Scenario family | Message | Expected category | Expected action | Rationale |
|---|---|---|---|---|---|
| BOUNDARY-001 | FAMILY-026 | I need to cancel my appointment, and I want a clinician to tell me whether I should stop my medicine. | clinical_staff_referral | clinical_staff_referral | A personal medication question overrides the administrative cancellation request. Preserve both requests in the summary. |
| BOUNDARY-002 | FAMILY-021 | My results page is not loading. If I read the numbers to you, can you tell me whether my treatment needs changing? | clinical_staff_referral | clinical_staff_referral | Personal treatment interpretation overrides the portal issue; this is routing, not clinical advice or urgency assessment. |
| BOUNDARY-003 | FAMILY-021 | Where can I find a general diabetes education leaflet explaining what an A1C test is? I am not asking about my own result. | education_resource_request | classify | A request for general educational material is distinct from interpreting an individual result. |
| BOUNDARY-004 | FAMILY-021 | Please send me a copy of my latest laboratory report for my records. I do not need an explanation of the result. | records_insurance_admin | classify | Obtaining a document copy is administrative; the word laboratory does not make it a clinical-advice request. |
| BOUNDARY-005 | FAMILY-016 | I can sign in, but downloading my clinic visit notes always fails with an error. | portal_technical_support | classify | The explicit problem is a technical download failure, not a request to interpret or create records. |
| BOUNDARY-006 | FAMILY-001 | I am already booked into a diabetes education appointment. Please change that booking to another day. | appointment_support | classify | Changing an existing booking belongs to appointment support; joining a new education session belongs to education-resource requests. |
| BOUNDARY-007 | FAMILY-BOUNDARY-007 | Please change my appointment date and send a copy of my records. Both are equally important; neither should come first. | None | staff_review | Two equally primary nonclinical requests require clarification or staff review under the label guide. |
| BOUNDARY-008 | FAMILY-006 | Please send the getting-started guide. | None | staff_review | Without context this could refer to clinic administration, the portal, or diabetes education. Ask which guide is needed. |
| BOUNDARY-009 | FAMILY-BOUNDARY-009 | Can you book a hotel room for my holiday next month? | None | staff_review | Outside the clinic-support scope; do not force the booking keyword into appointment support. |
| BOUNDARY-010 | FAMILY-007 | How do I sign up for the group? | None | staff_review | No preceding conversation identifies the group. Ask whether this is the diabetes education session or something else. |

## Historical pilot content review and remaining validation

The revision clarifies the guide/class examples (`PILOT-006`–`008`), distinguishes an existing education booking from new enrollment (`005`), makes the clinical nature of `024` explicit, and adds two examples per category (`026`–`035`). The typo in `015` is intentional robustness coverage. Mixed clinical/nonclinical requests, paperwork versus class enrollment, technical failures versus record requests, and ambiguous/out-of-scope messages now have explicit coverage.

Reviewer: **Codex (AI)**. Date: **30 October 2026**. User-authorized scope: review and approve this pilot. Decision: **35/35 labels accepted; 10/10 expected routing behaviours accepted; no unresolved label corrections for pilot use**. This is a content review of AI-drafted examples by the same assistant, not independent validation. No training or inference was run during approval.

| Classification examples reviewed | Accepted category | Basis for acceptance |
|---|---|---|
| 001, 002, 003, 004, 005, 026, 027 | `appointment_support` | Existing appointment changes, arrival/booking confirmation, new routine booking or cancellation; 005 explicitly gives the appointment priority over the handout. |
| 006, 007, 008, 009, 010, 028, 029 | `education_resource_request` | Requests for general educational material, accessible format or new class enrollment; 029 remains education enrollment even though it mentions a paper form. |
| 011, 012, 013, 014, 015, 030, 031 | `portal_technical_support` | Reset, login, display, upload, sign-in-code or broken-link failures; the document type does not override the technical problem. The typo in 015 does not change its meaning. |
| 016, 017, 018, 019, 020, 032, 033 | `records_insurance_admin` | Record copies/status, visit charges, accepted insurance, administrative forms, invoice correction or address paperwork; no personal clinical interpretation is requested. |
| 021, 022, 023, 024, 025, 034, 035 | `clinical_staff_referral` | Personal result interpretation, medication decisions, new symptom, prescription review or mixed clinical requests; 034 and 035 correctly apply the clinical override. |

Routing review: BOUNDARY-001–002 correctly require clinical referral; 003–006 correctly distinguish educational, administrative, technical and appointment requests; 007–010 correctly require staff review because no defensible single category is available or the request is outside scope. Their individual rationales are recorded in the table above.

- [x] Read all 35 messages and validate their labels against the guide.
- [x] Read all 10 routing cases and verify expected actions and rationales.
- [x] Check family grouping, JSON structure, unique IDs, duplicate messages, class balance and synthetic provenance.
- [x] Record AI reviewer, review date and approval scope without claiming team-member approval.
- [ ] During implementation, train only on the classification messages/categories; keep routing checks out of training and all pilot families out of the final benchmark.
- [ ] Record actual training/reload and routing outcomes. Label approval does not mean the model or application has passed.
- [ ] Retain the independent review and sealed-test requirements for the larger assessment dataset; this pilot approval does not approve examples that have not yet been created or reviewed.


## Historical initial training batch review — 31 October 2026

Reviewer: **Codex (AI)**, at the user's request to act as a team reviewer. This is an additional AI review within the same project chat. A chat-model switch is not evidence of independent human review; no human team-member contribution or approval is claimed.

Decision: **50/50 labels accepted after five wording clarifications; approved for classification training/reload feasibility only.** No category was changed, and no training or inference was performed during this data review.

| Reviewed records | Category | Review basis |
|---|---|---|
| TRAIN-001–010 | `appointment_support` | Routine booking, rescheduling, cancellation, confirmation and appointment waiting lists |
| TRAIN-011–020 | `education_resource_request` | General diabetes materials, new workshop enrollment and class information; no personal treatment advice |
| TRAIN-021–030 | `portal_technical_support` | Sign-in, code, session, display, transfer and website failures; the document's subject does not override the technical problem |
| TRAIN-031–040 | `records_insurance_admin` | Copies, record-request status, insurance details, billing, receipts, forms and identity corrections |
| TRAIN-041–050 | `clinical_staff_referral` | Personal results, medication decisions/effects, symptoms and prescription actions requiring clinical staff |

Corrections made:

- TRAIN-009 now explicitly requests a clinic appointment waiting list.
- TRAIN-012, 014, 018 and 020 now explicitly identify diabetes education or the clinic, avoiding reliance on hidden context.
- Replaced the arbitrary two-record family groupings with scenario-based assignments. Related training and pilot examples now share IDs: for example, appointment changes use `FAMILY-001`, education enrollment uses `FAMILY-007`, upload failures use `FAMILY-013`, and general/personal result contrasts use `FAMILY-021`. Distinct booking-confirmation, waiting-list, site-outage and administrative scenarios have descriptive new family IDs.

Structure checks confirmed 50 records, ten per class, unique IDs, valid JSON, the expected metadata fields, and zero exact message duplicates within the training batch or against the pilot. Manual review still found related scenarios and paraphrases across the files: the batch is development/training material, not an independent benchmark. Shared family IDs document known overlap; they are not an exhaustive semantic leakage detector.

Coverage gaps identified in the initial 50-message batch: predominantly short, clean, single-request messages, with too few mixed-request clinical overrides, spelling variations, informal phrases and longer messages. The subsequent expansion adds examples in each of these areas; adequacy still needs team review. Ambiguous/out-of-domain cases stay in separate routing checks rather than becoming a sixth training label. Future validation/test scenarios must be prepared separately and checked against both the pilot and this batch; do not report accuracy from a random split of these 50 examples.


## Expanded training draft and review metadata

At the user's request, the training file now contains **280 synthetic candidates, 56 per category**. TRAIN-001–050 preserve the previously reviewed batch; TRAIN-051–280 add 230 examples. The additions include appointment-versus-class distinctions, document-request-versus-portal failures, general education versus personal-result interpretation, and clinical requests that override secondary administrative needs. All messages are authored as requests; they contain no model answer, clinical recommendation, or label text to copy as an answer.

Known related scenarios reuse pilot/training family IDs. Exact duplicates are checked separately from semantic overlap: similar training messages are not independent evaluation cases. Keep validation/test scenarios and their variants outside these training families, and review semantic overlap before finalising those collections.

At the user’s direction, the original 315 pilot/training records and the new 60-message validation and 60-message test files use `review_status: approved`, `reviewer: Sanjay`, and `reviewed_on: 2026-10-31`. All examples are AI-drafted and synthetic. Reviewing the test set led to 15 wording changes to reduce overlap with other partitions and clarified TEST-020 as an education-resource request. Exact-duplicate and string-similarity checks found no exact duplicates or high lexical matches across the four files after revision; these checks cannot prove full semantic independence. Keep the test file out of model selection and use it only for final evaluation. One CPU epoch completed on the 280 training records; its checkpoint and tokenizer were saved under `artifacts/models/clinic-support` and reload-verified. The three-epoch plan is not complete; the test set remains unused.
