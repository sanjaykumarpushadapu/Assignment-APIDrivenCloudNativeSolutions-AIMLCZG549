# RAG knowledge-source inventory

**Status:** source review in progress  
**Last checked:** 31 October 2026

This inventory records source provenance and intended use before any documents
are added to the retrieval index. It is not itself an indexed knowledge source.

## Intended scope

The assistant may answer general diabetes-education questions and questions
about the clearly fictional clinic's administrative procedures. It must not
diagnose, recommend an individual's treatment or medication changes, or present
fictional clinic procedures as real. Answers should cite the source used.

## Public education sources

| ID | Source | Last updated/reviewed on source | Intended use | Status |
|---|---|---|---|---|
| K01 | [CDC: Diabetes Basics](https://www.cdc.gov/diabetes/about/) | 2 January 2026 | General diabetes background and types | Preferred current candidate |
| K02 | [CDC: About Diabetes Self-Management Education and Support](https://www.cdc.gov/diabetes/education-support-programs/index.html) | 15 May 2024 | General information about diabetes education/support and enrollment | Candidate for initial corpus |
| K03 | [NIDDK: Diabetes Overview](https://www.niddk.nih.gov/health-information/diabetes/overview) | Last reviewed November 2016 | Broad overview | Hold for freshness review; prefer K01 for initial corpus |

K03 was part of the initially agreed source set. Its page says it was last
reviewed in 2016, so it is recorded here but should not be ingested into the
initial corpus without a decision to accept that review date. K01 covers the
general-background role with more recent page content.

## Fictional clinic procedure

| ID | Planned document | Intended use | Status |
|---|---|---|---|
| K04 | Fictional clinic support procedures for appointments, portal access, and education leaflets | Answer clinic-process questions that public health sources cannot answer | Not drafted; must be clearly labelled fictional and reviewed before indexing |

Do not invent real clinic contacts, insurance terms, appointment guarantees, or
clinical instructions. The procedure should say when staff confirmation is
required and route clinical questions to qualified staff.

## Ingestion notes

- Keep source title, publisher, URL, and page update/review date with each
  indexed passage.
- Keep the public education pages separate from the fictional clinic procedure
  so answers can show which source type supports each claim.
- Do not use the classification JSONL datasets as knowledge documents.
- No full webpage text has been copied into this repository. Extraction and
  index-build details will be recorded when the retrieval implementation is
  planned.
