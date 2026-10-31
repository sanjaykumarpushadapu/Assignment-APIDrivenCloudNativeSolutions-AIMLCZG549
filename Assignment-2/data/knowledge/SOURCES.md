# RAG knowledge-source inventory

**Current indexed corpus:** one World Health Organization (WHO) public source.
The page was reviewed on 31 October 2026.

This inventory records the source used to prepare the local paraphrased notes
and retrieval chunks. The full WHO snapshot is kept locally for processing;
the machine-readable source metadata, curated notes, and generated chunks are
committed. The full snapshot is excluded from Git.

## Intended scope

The assistant may answer general diabetes-background and diabetes-education
support questions when the source contains supporting information. It must not
diagnose or recommend an individual's treatment, diet plan, medication, or
monitoring schedule. It should cite the source and route unsupported or
clinic-specific questions to staff.

## Selected source

| ID | Source | Page date | Intended use |
|---|---|---|---|
| WHO01 | [WHO: Diabetes — Questions and Answers](https://www.who.int/news-room/questions-and-answers/item/diabetes) | 1 September 2026 | General background, common symptoms, type 2 prevention, and high-level self-management education/support; curated notes in `k01_diabetes_basics.md` and `k02_diabetes_education_support.md` |

The canonical local source path, retrieval date, and SHA-256 of normalized FAQ
text are in `manifest.json`. The checksum ignores changes to unrelated HTML
wrappers and scripts while detecting changes to the visible FAQ content.

## Ingestion notes

- The paraphrased notes are reviewed content derived from the local WHO01
  snapshot. `scripts/prepare_knowledge.py` checks the normalized FAQ content
  hash, page date, and key sections, then regenerates one retrieval chunk per
  note section.
- Each generated chunk carries source identity, publisher, URL, page date,
  content hash, section, and curated note filename. It does not require the
  ignored raw snapshot path at runtime.
- Index only factual notes derived from WHO01. The assistant's scope, refusal,
  and staff-routing rules are application instructions, not source content, and
  must stay outside the document index.
- Do not turn diagnostic thresholds or individualized treatment instructions
  into chunks. Route personal diagnosis and care questions to qualified staff.
- The full WHO webpage snapshot is ignored by Git and retained only in the
  local working copy. The WHO website permits extracts for research or private
  study and requires authorization for reproducing substantial portions; do
  not add the full page to submission materials. See the [WHO website terms of
  use](https://www.who.int/about/policies/terms-of-use).
- Clinic appointment, portal, and leaflet procedures are outside the RAG
  corpus; the assistant must not invent answers to those questions.
- Do not use the classification JSONL datasets as knowledge documents.

## Other source reviewed

Sources are selected for authority, accuracy, fit with the assistant's scope,
and usefulness; country of origin is not a requirement. The following official
National Centre for Disease Control (NCDC), Ministry of Health and Family
Welfare FAQ was reviewed. Its local PDF copy was removed after it was excluded:

| Status | Source | Local review copy | Notes |
|---|---|---|---|
| Reviewed; excluded from retrieval | [NCDC: Diabetes Mellitus English FAQs](https://ncdc.mohfw.gov.in/uploads/pdf/Diabetes%20Mellitus%20English%20FAQs.pdf) | No local copy retained | The official directory lists the PDF on 22 January 2026. The PDF has no visible version date in its metadata. It contains prescriptive diet, monitoring, and treatment statements that are unsuitable for this assistant's general education scope. Do not create chunks from it. |

## Retrieval behaviour

Keep retrieved passages traceable to WHO01 so the assistant can show its
evidence. The answer-generation component must abstain or route to staff when
the retrieved passages do not support an answer.
