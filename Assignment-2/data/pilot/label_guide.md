# Classification Pilot Label Guide

**Status:** Draft pilot only. The 25 examples are synthetic, AI-drafted, and pending team review. They are not patient records and are not ready for training until reviewed.

## Labels

| Label | Use when the main request is about | Boundary |
|---|---|---|
| `appointment_support` | Booking, confirming, cancelling, or changing an appointment | If the appointment is the main request in a mixed message, use this label and preserve the other request in the handoff summary. |
| `education_resource_request` | General diabetes education materials, class information, or registration for an education session | Class enrollment belongs here. Do not answer personal diagnosis, treatment, or medication questions as education requests. |
| `portal_technical_support` | Login, account access, website errors, or a failure to upload or view information online | Use this when the main problem is a technical failure, even if the uploaded item is a billing or insurance form. If the person asks for medical interpretation, use `clinical_staff_referral`. |
| `records_insurance_admin` | Medical-record copies/status, insurance coverage, billing, general clinic forms, or routine paperwork | General administrative forms belong here; education-session registration belongs in `education_resource_request`. Administrative status is in scope; medical interpretation is not. |
| `clinical_staff_referral` | Personal medical advice, new symptoms, medication changes or side effects, test-result interpretation, or prescription requests needing clinical review | Route to qualified staff. Do not provide advice, assess urgency, or suggest a medication change. |

## Primary-label rule

1. If any part asks for personal clinical advice or interpretation, use `clinical_staff_referral` and route it to staff.
2. Otherwise, label the main explicit request. A failed online upload is `portal_technical_support`; asking where to submit a paper form is `records_insurance_admin`.
3. Keep secondary requests in the handoff summary. For example, a request to reschedule an appointment and obtain a class handout is `appointment_support` when rescheduling is the main request.
4. If two nonclinical requests are equally important and neither is clearly primary, send the message for human review. Do not force it into a training label or create a sixth class.
5. Out-of-scope messages are also sent for human review and excluded from the five-class training set; do not force them into the closest category.

## Pilot data fields

Each JSONL record has `example_id`, `message`, `category`, `scenario_family_id`, `provenance`, `authoring_method`, and `review_status`. The IDs and other metadata are for tracking only: use `message` as model input and `category` as its target, never the ID or scenario-family field. All pilot records are marked `synthetic`, `AI-drafted`, and `pending_team_review`. Review labels and realism before training; keep paraphrases of the same underlying scenario in one family when expanding the dataset.