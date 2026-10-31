# RAG knowledge-source inventory

**Corpus choice:** two CDC public sources; source pages checked 31 October 2026.

This inventory records the two public sources selected for the initial RAG
corpus. No full webpage text is copied into this repository.

## Intended scope

The assistant may answer general diabetes-background and diabetes-education
support questions when the selected sources contain supporting information. It
must not diagnose or recommend an individual's treatment or medication changes.
It should cite the source and route unsupported clinic-specific questions to
staff. Do not generalize US insurance/Medicare details from the DSMES page to an
individual's coverage; route coverage questions to the insurer or staff.

## Selected source

| ID | Source | Page date | Intended use |
|---|---|---|---|
| K01 | [CDC: Diabetes Basics](https://www.cdc.gov/diabetes/about/) | 2 January 2026 | General diabetes background and types; curated notes in `k01_diabetes_basics.md` |
| K02 | [CDC: About Diabetes Self-Management Education and Support](https://www.cdc.gov/diabetes/education-support-programs/index.html) | 15 May 2024 | Education/support services and general enrollment information; curated notes in `k02_diabetes_education_support.md` |

## Ingestion notes

- Preserve the source ID, title, publisher, URL, and page date with every
  indexed passage.
- Keep retrieved passages traceable to their source so the assistant can show
  its evidence.
- Do not use the classification JSONL datasets as knowledge documents.
- Clinic appointment, portal, and leaflet procedures are outside the initial
  RAG corpus; the chatbot must not invent answers to those questions.
- The DSMES page includes US insurance/Medicare information. Preserve that
  context and direct individual coverage questions to the insurer or staff.
