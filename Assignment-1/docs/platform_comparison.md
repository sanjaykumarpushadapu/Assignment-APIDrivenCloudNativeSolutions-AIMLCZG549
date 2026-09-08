# Cloud Platform Comparison — Group 49

BITS does not provide institutional credits for self-service platforms
(Azure/GCP/AWS/Databricks/Prefect), but does offer an optional AWS
Virtual Lab for this course (see below). This compares Azure, GCP,
Prefect Cloud, AWS, and Databricks (ordered by fit for the core
scheduling/API/dashboard requirements) against what the assignment's PDF
explicitly requires (`Assignment-1_API Driven_Assignment1.pdf`, Activity
1.5): a workflow that **runs every 2 minutes**, logs activity, displays it
on a **cloud dashboard**, and exposes **≥4 application details through
built-in APIs**, testable via Swagger/OpenAPI.

| Criteria | Azure | GCP | Prefect Cloud | AWS | Databricks |
|---|---|---|---|---|---|
| Matching compute model | Azure Functions (serverless) — good fit | Cloud Functions (serverless) — good fit | Purpose-built workflow orchestrator; includes 500 min/month of managed serverless execution on the free tier | Lambda (serverless) — good fit | Spark clusters — **poor fit**: even light job clusters take real minutes to start, incompatible with a 2-minute cadence |
| 2-minute schedule | Timer Trigger cron (`0 */2 * * * *`) — **self-contained in the function itself**, 1 resource | Cloud Scheduler (HTTP target) + Cloud Function — 2 resources to wire together | Native interval scheduling, set directly to 2 minutes — purpose-built for exactly this | EventBridge Scheduler + Lambda — 2 resources to wire together | Not really available on a lightweight setup — no true sub-hour scheduler without an always-on cluster |
| Cloud dashboard | Application Insights — built-in | Cloud Monitoring/Logging — built-in | Flow-run dashboard is the product's core feature — arguably the most direct fit of any option here | CloudWatch Dashboards — built-in | No usable dashboard without a paid workspace |
| Built-in APIs + Swagger/OpenAPI | HTTP-triggered Functions **auto-export OpenAPI**; Resource Manager REST APIs map cleanly to "≥4 application details" (status, deployment, schedule, last run) | REST + Discovery Docs — solid, but Discovery format needs an extra conversion step to load into Swagger UI | **Strongest match of all options**: API vocabulary is literally `/flows`, `/deployments`, `/flow_runs`, `/task_runs` — mirrors the assignment PDF's own wording ("flow, deployment etc."); FastAPI backend auto-generates real Swagger UI | Rich management APIs, but testing needs **AWS SigV4 request signing** — notably more complex to set up/screenshot in Postman than a bearer token | REST API exists (jobs, clusters) but needs a personal access token per call — harder to screenshot without exposing a credential |
| Setup complexity | Low–medium | Medium | Low for orchestration, but still needs a place to store/run the raw data (not a full platform) | High — IAM roles/policies are the classic beginner blocker | High, for what this assignment specifically needs |
| Free credit / tier | $100, valid 1 year, renewable while a student | $300, valid 90 days | Free "Hobby" tier: 5 deployments, 500 min/month serverless execution, 7-day run retention | $100–200, 6 months | None — Community Edition is free but very limited |
| Credit card required | **No** | Yes (identity check only, not charged) | Not stated on pricing page — unconfirmed | Yes | No |
| Eligibility | Verify via **institution email** (test your BITS WILP email works before committing) | Any Google account | Any email | Any new account | Any email |
| Team access model | Each member gets an independent $100 subscription — simplest for a 4-person team | Each member needs own trial + card, or share one billing project | **Only 2 users per workspace** on the free tier — a real constraint for your 4-person team; the other two would need to work via screenshots/screen-share rather than their own login | Each member needs own account + card | Single-user per account — no real shared team workspace on the free tier |
| India region | Central India, South India | Mumbai, Delhi | Not region-specific (managed SaaS) | Mumbai, Hyderabad | Depends on underlying cloud host |
| **Overall fit for this assignment** | **Best all-round fit** | Strong alternative | Best-in-class fit for the *scheduling/dashboard/API* half specifically, but the 2-user cap and being outside the workload plan's named candidate list are real risks for a 4-person team | Workable, most moving parts | Mismatch regardless of cost — built for big distributed data, not this job |

## BITS-provided AWS Virtual Lab (discovered during comparison)

BITS makes an optional "Virtual Lab Session" available for this course
(`AIMLZG549`), pre-loaded with API Gateway, AWS Billing and Cost Services,
Bedrock, CloudWatch, EC2, Glue, IAM, IAM Access Key Creation, Lambda, and
SageMaker. **It is not mandatory to use.** The lab enforces a 15-minute
idle limit and a 60-minute stop limit before the instance auto-terminates,
and only the `~/workspace` directory survives a stop — everything else is
destroyed. This strongly suggests a short-session training sandbox rather
than a persistent production account, so it's a good fit for hands-on
exploration (trying Lambda/Glue/SageMaker), testing, and recording parts
of the demo video, but risky to rely on as the host for a pipeline that
must run every 2 minutes continuously for 3 weeks, unless persistence
across sessions is confirmed with the professor or lab FAQ.

**Proposed approach (pending team discussion):** use Azure for the actual
always-on scheduled pipeline (known persistent for the full year-long
student subscription); use the free BITS AWS lab opportunistically for
testing/demo footage only. Not yet confirmed with the full team.

## Recommendation

**Azure** remains the safest overall pick — it's already named as a candidate in the workload plan (same standing as AWS or GCP, not formally approved by anyone yet), has no credit-card barrier, and covers every requirement (scheduler, dashboard, API/Swagger) natively with one account per teammate. **Prefect Cloud** is worth a mention to your professor specifically because its API and dashboard are almost purpose-built for this rubric's exact wording, but the 2-user free-tier cap and the fact that it isn't one of the named candidates make it riskier as the primary choice for a 4-person team on a fixed deadline. **GCP** is the solid fallback to Azure. **AWS** works but has the most setup friction. **Databricks is a mismatch regardless of cost.**

## Decision

_Pending team confirmation — record the final choice in
`Assignment_1_Workload_Plan.md` → "Platform decision record" once agreed._
