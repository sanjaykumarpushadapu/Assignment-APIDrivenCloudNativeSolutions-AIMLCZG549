# Classification Pilot Label Guide

**Status:** AI-reviewed and approved for pilot use on 30 October 2026, following the user's request for Codex to review and approve. All 35 classification examples (seven per class) passed review against the label rules and may be used for a small training/reload feasibility run. The 10 documented routing checks are approved as expected development behaviours; they have not been executed against a model. All content remains synthetic and AI-drafted. This approval is by Codex (AI), not an independent team-member or clinical review, and does not establish model accuracy or readiness for workplace deployment.

## Files and intended use

| File | Contents | Intended use |
|---|---|---|
| `classification_pilot.jsonl` | 35 messages with one of the five category targets | Approved for a small classifier training/reload feasibility check; not a final accuracy benchmark |
| Routing checks in this guide | 10 messages with expected routing action, category where applicable and rationale | Manual development checks of routing behaviour, kept out of the JSONL training candidates |

Treat the entire pilot as development material. It has been inspected and used to make design decisions; neither these examples nor their scenario variants should enter the final held-out benchmark. This is the classification/routing pilot only. The assessment still needs the larger reviewed classification dataset, summary inputs/reference summaries, knowledge documents and separate RAG questions with supporting passages.

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

Each classification JSONL record has `example_id`, `message`, `category`, `scenario_family_id`, `provenance`, `authoring_method`, `review_status`, `reviewer`, `reviewed_on`, and `approval_scope`. Use only `message` as model input and `category` as its target; all other fields are tracking metadata. Every record retains provenance `synthetic` and authoring method `AI-drafted`, with status `ai_approved_for_pilot`, reviewer `Codex (AI)`, review date `2026-10-30`, and approval scope `classification_feasibility_only`.

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

## Review record and remaining validation

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
