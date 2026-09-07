# Assignment 1 — Workload and Project Plan

## Open Questions

These questions must be answered by the team or instructor before the platform and final implementation are locked.

1. Which cloud platform can all four team members access: Azure, AWS, Google Cloud, Databricks, Dataiku, KNIME, or another approved platform? Does the university provide accounts, licenses, or student credits?
2. Is the required two-minute schedule supported by the selected platform and account plan?
3. Should the dashboard display EDA charts, or are activity metrics, logs, and summary results sufficient?
4. Is the prediction model compulsory, or is it an optional value-added component?
5. If a model is built, must it be deployed as an endpoint?
6. Are there university restrictions on cloud regions, services, or student credits?
7. Is there a required demonstration-video length or format?
8. Does the API requirement mean the cloud platform's built-in APIs, a team-created API, or either one?

Do not remove an open question until the team or instructor has answered it. Resolved decisions should be moved to the section below.

---

## Confirmed Project Details

- **Group ID:** 49
- **Project topic:** Diabetes Risk Prediction Using Health and Lifestyle Indicators
- **Approved dataset:** Kaggle Diabetes Health Indicators Dataset
- **Dataset source:** https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset
- **API documentation/testing tool:** Swagger/OpenAPI where available; otherwise an API client or the selected platform's API explorer
- **Submission deadline:** Friday, 18 September 2026

---

# 1. Project Scope

## 1.1 Business problem

Healthcare organizations collect large volumes of patient health and lifestyle data, but identifying people at risk of diabetes can be challenging when the data is analyzed manually. Early risk screening can help healthcare providers take preventive measures, prioritize support, and improve patient outcomes.

### Current state

- Patient health and lifestyle data is available but not fully utilized.
- Identifying people at higher risk can be time-consuming.
- Delayed risk identification may contribute to health complications and increased treatment costs.

## 1.2 Proposed solution

Create a cloud-based data pipeline that:

1. Ingests the approved Kaggle dataset.
2. Checks and preprocesses the data.
3. Performs exploratory data analysis.
4. Identifies important diabetes-risk indicators.
5. Builds and evaluates a diabetes-risk prediction model as a value-added component.
6. Automates preprocessing and EDA activities.
7. Runs the workflow every two minutes.
8. Records execution details.
9. Displays activity information on a cloud dashboard.
10. Provides at least four application details through accepted built-in APIs.

This enables earlier intervention and better decision-making. The result must be described as a **risk-screening or risk-prediction system**, not as a medical diagnosis system.

## 1.3 Required assignment scope

The assignment explicitly requires:

- Business understanding
- Public dataset ingestion
- Summary statistics
- Missing-value checks
- Numeric-value imputation where required
- Data-type display
- Normalization or standardization
- Correlation analysis
- Numeric and categorical analysis
- Binning and encoding where appropriate
- Feature-importance analysis
- Univariate and bivariate visualizations
- Automation of preprocessing and EDA activities
- A workflow schedule of every two minutes
- Activity logging
- Activity details displayed on a cloud dashboard
- At least four application details retrieved through APIs
- API testing, status-code verification, documentation, and screenshots
- Final Word/PDF report
- Demonstration video uploaded to Google Drive

## 1.4 Optional value-added scope

The prediction model is a strong addition because it matches the project topic, but it is not listed as a separate scored activity in the assignment brief.

If the team includes the model, document:

- Model selection
- Training and testing
- Target-class distribution
- Class-imbalance handling
- Evaluation metrics
- Feature importance
- Deployment decision
- Monitoring decision

Do not allow the optional model to reduce the quality of the required data pipeline, EDA, DataOps, dashboard, or API work.

---

# 2. Platform Selection Requirements

The final platform must support:

- Public dataset ingestion
- Raw and processed data storage
- Data preprocessing
- EDA output generation
- Workflow automation
- A two-minute schedule
- Execution logging
- Cloud dashboarding
- At least four acceptable application APIs
- API-client, API-explorer, or Swagger/OpenAPI testing support
- Student or university access
- Approved cost or student credits
- Secure authentication without exposing credentials
- Failure reporting and execution history

## Platform decision record

After the team chooses a platform, record:

- Selected platform
- Account, license, or student-credit source
- Selected region or workspace
- Required services
- Two-minute scheduling method
- Exact four APIs
- Dashboard method
- Authentication method
- Cost limit
- Data-storage locations
- Failure-handling method
- Overlapping-run policy
- Person responsible for platform administration
- Platform decision date and fallback platform

## Platform-neutral architecture

Replace the boxes with the selected platform's actual services after the platform decision.

```text
Approved Kaggle Dataset
          ↓
Raw Data Storage
          ↓
Data Ingestion
          ↓
Data-Quality Checks
          ↓
Preprocessing
          ↓
Automated EDA Outputs
          ↓
Optional Prediction Model
          ↓
Dashboard and Execution Logs
          ↓
Built-in Application APIs
```

---

# 4. Equal Workload Allocation

Each person owns one complete work package. Each package includes application work, report writing, evidence collection, handoff, and verification.

| Person | Work package | Main outputs |
|---|---|---|
| Person 1 | Business understanding, dataset, and ingestion | Business section, data dictionary, raw-data ingestion |
| Person 2 | Data quality, preprocessing, and pipeline automation | Cleaned dataset, preprocessing, schedule, logs |
| Person 3 | EDA, optional model, and dashboard analysis | Charts, correlations, model results, dashboard metrics |
| Person 4 | Dashboard implementation, APIs, and demonstration | Dashboard, four APIs, API evidence, video |

The workload is balanced by assigning each person one major project package. No person is responsible for recreating another person's work.

## Shared contribution rule

Every person must provide:

- Their assigned application work
- Their report section
- Their screenshots and evidence
- Their explanation for the demonstration
- Their verification result
- Their contribution statement

All members participate in final review, but each person retains ownership of their assigned package.

---

# 5. Person 1 — Business Understanding, Dataset, and Ingestion

## Objective

Define the project and provide a verified raw dataset for the other team members.

## Steps

### Step 1: Confirm the project topic

Use the title:

**Diabetes Risk Prediction Using Health and Lifestyle Indicators**

### Step 2: Write the business problem

Explain:

- Why healthcare organizations need early diabetes-risk screening
- Why manual identification is difficult
- How delayed identification affects decisions and costs
- Who will use the project results

### Step 3: Describe the current and proposed states

Current state:

- Health data is available but not fully utilized.
- Risk identification may be time-consuming.
- Analysis is not sufficiently automated.

Proposed state:

- Data is processed through an automated cloud workflow.
- Diabetes-risk indicators are analyzed.
- Results are presented through a dashboard and APIs.

### Step 4: Select one exact dataset file

Use the approved Kaggle source:

https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset

Select one exact file and record:

- Filename
- Source URL
- Row count
- Column count
- Target column
- Feature columns
- Numeric columns
- Categorical or binary columns
- Target-value distribution

Also explain why the confirmed row count is sufficient for the planned EDA and, if included, model experiment.

Do not assume these values from memory. Confirm them after import.

### Step 5: Prepare the data dictionary

For every column, record:

- Column name
- Business meaning
- Data type
- Example values
- Feature or target role

### Step 6: Document suitability and limitations

Explain why the dataset is suitable for preprocessing, EDA, classification, feature-importance analysis, and pipeline automation.

Document:

- Dataset source and license information, if available
- Possible survey or self-report limitations
- Generalization limitations
- Bias and fairness considerations
- No use as a clinical diagnosis

### Step 7: Ingest and version the raw data

Import the selected file into the chosen platform.

Verify:

- File opens successfully.
- Expected columns are present.
- Expected records are present.
- Target column is available.
- Raw data is preserved before preprocessing.
- Raw-data location and import date are recorded.
- Processed-data location is separate from raw data.

## Report sections

- Introduction
- Business problem
- Current state
- Proposed solution
- Objectives and benefits
- Dataset source and profile
- Data dictionary
- Dataset limitations
- Data ingestion

## Evidence

- Dataset source link
- Exact dataset filename
- Dataset profile
- Data dictionary
- Raw dataset screenshot
- Data-ingestion screenshot
- Raw-data verification result

## Handoff to Person 2

Provide:

- Confirmed dataset file
- Confirmed target column
- Data dictionary
- Raw-data location
- Dataset profile
- Ingestion evidence

## Completion condition

Person 1 is complete when the business problem is approved, the exact dataset file and target column are recorded, and the raw dataset is successfully imported and verified.

---

# 6. Person 2 — Data Quality, Preprocessing, and Pipeline Automation

## Objective

Create the clean dataset and automate preprocessing, EDA generation, scheduling, and execution logging.

## Steps

### Step 1: Validate Person 1's dataset

Confirm the expected filename, columns, target, and record count.

### Step 2: Produce data-quality results

Check and document:

- Summary statistics
- Data types
- Missing values and percentages
- Duplicate records
- Invalid target values
- Invalid or unusual numeric values
- Unexpected category values

### Step 3: Preprocess the data

Perform and document:

- Numeric-value imputation where required
- Categorical or binary encoding
- Normalization or standardization where appropriate
- Feature/target separation
- Cleaned-data output

### Step 4: Verify the cleaned dataset

Confirm:

- Required columns remain available.
- Target values remain correct.
- No critical unresolved errors remain.
- The cleaned data can be used by Person 3.

### Step 5: Add preprocessing and EDA to the workflow

After receiving the EDA output specification from Person 3, include:

- Data-quality checks
- Missing-value handling
- Encoding
- Normalization or standardization
- Cleaned-data output
- Summary-statistics generation
- Target-distribution generation
- Feature-distribution generation
- Correlation-matrix generation
- Selected bivariate-analysis generation
- Missing-value summary generation

### Step 6: Configure the required schedule

Configure the workflow to run automatically every two minutes.

The schedule must trigger preprocessing and EDA activities, not only data ingestion.

### Step 7: Configure execution logging

Record:

- Start time
- End time
- Execution status
- Number of processed records
- Errors
- Warnings
- Runtime duration

### Step 8: Verify the scheduled workflow

Confirm that the workflow:

- Runs successfully.
- Produces the cleaned dataset.
- Refreshes the EDA outputs.
- Records execution details.
- Shows errors and warnings.
- Has a defined overlapping-run policy as a reliability safeguard.

Capture evidence of at least two consecutive scheduled runs approximately two minutes apart. For each run, show its trigger time, completion status, distinct log entry, and refreshed EDA-output timestamp.

## Report sections

- Data-quality checks
- Summary statistics and data types
- Missing and duplicate values
- Invalid-value handling
- Preprocessing
- Encoding and normalization
- Cleaned dataset
- DataOps workflow
- Two-minute schedule
- Execution logging

## Evidence

- Summary-statistics screenshot
- Data-types screenshot
- Missing-value results
- Duplicate-value results
- Preprocessing screenshot
- Cleaned-data output
- Workflow screenshot
- Two-minute schedule screenshot
- Execution-log screenshot
- Refreshed-EDA execution evidence

## Handoff to Person 3

Provide:

- Cleaned dataset
- Preprocessing steps
- Data-quality results
- Transformation explanation
- Workflow output locations
- EDA refresh outputs

## Completion condition

Person 2 is complete when the cleaned dataset is available, preprocessing and EDA are included in the automated workflow, the workflow is scheduled every two minutes, and logs are working.

---

# 7. Person 3 — EDA, Optional Model, and Dashboard Analysis

## Objective

Analyze the cleaned data, produce the required EDA outputs, and prepare the analytical content for the dashboard.

## Steps

### Step 1: Validate the cleaned dataset

Confirm that the target and feature columns are available and that preprocessing is understood.

### Step 2: Analyze the target distribution

Record:

- Count for each target class
- Percentage for each target class
- Whether the classes are balanced or imbalanced

### Step 3: Perform univariate analysis

Analyze suitable indicators such as:

- BMI
- Age
- Blood pressure
- Cholesterol
- General health
- Physical activity

### Step 4: Perform bivariate analysis

Analyze relationships such as:

- BMI versus diabetes risk
- Age versus diabetes risk
- Blood pressure versus diabetes risk
- Cholesterol versus diabetes risk
- Physical activity versus diabetes risk
- General health versus diabetes risk

### Step 5: Calculate and interpret correlations

Calculate correlation coefficients for relevant numeric or encoded features. Explain important relationships and their limitations.

### Step 6: Analyze categorical and binary features

Analyze indicators such as:

- Smoking status
- Physical activity
- High blood pressure
- High cholesterol
- Heart disease
- Stroke history

### Step 7: Perform binning where useful

Create and explain meaningful groups such as:

- Age groups
- BMI groups
- Health-condition groups

### Step 8: Prepare automated EDA output specifications

Tell Person 2 exactly which outputs must refresh on every workflow run:

- Summary statistics
- Target distribution
- Feature distributions
- Correlation matrix
- Selected bivariate results
- Missing-value summary
- Chart or table output locations

### Step 9: Decide whether to include the optional model

If the team does not include the model, clearly state that the project focuses on the required data pipeline, EDA, DataOps, dashboard, and APIs.

If the team includes the model, document:

- Model selection and reason
- Input features and target
- Train/test split
- Target-class balance
- Class-imbalance handling
- Leakage prevention
- Random seed or reproducibility setting
- Training and testing approach
- Deployment or non-deployment decision
- Monitoring approach

If included, cover model development, training, deployment decision, and monitoring.

### Step 10: Evaluate the optional model

Use suitable metrics such as:

- Accuracy
- Precision
- Recall
- F1-score
- Confusion matrix
- ROC-AUC, if available

Do not rely on accuracy alone when the target classes are imbalanced.

### Step 11: Prepare feature importance

Produce and explain a feature-importance result whether or not the optional prediction model is included. If a model is included, use a suitable model-based method such as permutation or tree-based importance. If no model is included, use a documented model-independent ranking method appropriate to the selected platform, such as mutual information or feature-target association. Do not present feature importance as proof of causation.

### Step 12: Prepare dashboard content

Provide Person 4 with:

- Target distribution
- Main EDA charts
- Correlation results
- Important indicators
- Refreshed EDA metrics
- Model metrics, if the model is included
- Latest analysis summary
- Explanation of each result

## Report sections

- Exploratory data analysis
- Target distribution
- Univariate analysis
- Bivariate analysis
- Correlation analysis
- Categorical-feature analysis
- Binning
- Feature importance
- Optional prediction model
- Model evaluation
- Dashboard analysis results

## Evidence

- Target-distribution chart
- Univariate charts
- Bivariate charts
- Correlation result
- Binning result
- Feature-importance chart
- Model-evaluation screenshot, if applicable
- EDA refresh evidence
- Dashboard content evidence

## Handoff to Person 4

Provide:

- Final EDA charts
- Analytical findings
- Correlation results
- Dashboard metrics
- Model results, if applicable
- Output locations
- Explanation of each result

## Completion condition

Person 3 is complete when required EDA activities are finished, outputs are defined for automatic refresh, findings are explained, and optional model results are complete or formally excluded.

---

# 8. Person 4 — Dashboard, APIs, and Demonstration

## Objective

Present the completed application, document four accepted APIs, and produce the final demonstration.

## Steps

### Step 1: Collect completed work

Collect and verify:

- Business and dataset material from Person 1
- Preprocessing and workflow material from Person 2
- EDA and optional model material from Person 3
- Schedule and log evidence from Person 2

### Step 2: Verify the complete workflow

Run the application flow and confirm:

1. Input data is available.
2. Data-quality checks run.
3. Preprocessing runs.
4. EDA runs.
5. EDA outputs refresh.
6. Optional prediction results are produced if included.
7. Logs are generated.
8. The workflow completes successfully.

Also verify the failure path for missing input data, invalid data, failed preprocessing, failed EDA, and failed API requests.

### Step 3: Build the cloud dashboard

Display the agreed activity information, including where supported:

- Latest workflow status
- Last successful execution
- Runtime duration
- Number of records processed
- Missing-value count or percentage
- Duplicate-record count
- Error count
- Warning count
- Execution history
- EDA refresh time
- Main EDA findings
- Model metrics, if applicable

Define the source of each dashboard item. For example, activity metrics may come from the platform monitoring service, while EDA charts may come from platform storage or a visualization service.

Add an **API-derived application details** section that visibly presents at least four labelled values retrieved from the selected built-in APIs. For every displayed value, record the API name or endpoint, retrieval time, and the dashboard/report location where it appears.

### Step 4: Confirm four APIs before implementation is complete

After the platform is selected, confirm that the following types of application details are available through accepted built-in APIs:

1. Workflow or pipeline information
2. Latest execution status
3. Processing, dataset, or flow information
4. Schedule, deployment, model, dashboard, or execution-history information

Do not list a deployment API unless a deployment actually exists.

### Step 5: Test the APIs using Swagger/OpenAPI or an equivalent API client

For each API, record:

- API name
- Purpose
- Endpoint
- HTTP method
- Parameters
- Authentication method
- Sample request
- Sample response
- HTTP status code
- Screenshot from Swagger/OpenAPI, an API client, or the selected platform's API explorer

Do not expose passwords, tokens, or private credentials.

### Step 6: Prepare the API documentation table

| API | Purpose | Method | Returned detail | Status code | Screenshot |
|---|---|---|---|---|---|
| API 1 | Workflow/pipeline detail | Confirm after platform selection | Confirm after testing | Confirm after testing | Required |
| API 2 | Execution detail | Confirm after platform selection | Confirm after testing | Confirm after testing | Required |
| API 3 | Processing/data/flow detail | Confirm after platform selection | Confirm after testing | Confirm after testing | Required |
| API 4 | Schedule/deployment/model/dashboard detail | Confirm after platform selection | Confirm after testing | Confirm after testing | Required |

### Step 7: Record the demonstration video

The video should show:

1. Project title and business problem
2. Dataset source and ingestion
3. Data-quality checks
4. Preprocessing
5. EDA charts and refreshed outputs
6. Optional prediction model and evaluation, if included
7. Automated workflow
8. Two-minute schedule
9. Execution logs
10. Cloud dashboard
11. Four Swagger/API requests and responses
12. Final project outcome

Person 4 records and organizes the video. Each member explains their own assigned section.

### Step 8: Upload and verify the video

- Upload the video to Google Drive.
- Set the correct sharing permission.
- Test the link using a separate account or private browser window where possible.
- Confirm that the video can be viewed.
- Add the working link to the final submission document.

## Report sections

- Cloud dashboard
- API access
- API testing
- Swagger/OpenAPI documentation
- HTTP status-code verification
- Demonstration process
- Final application overview

## Evidence

- Cloud-dashboard screenshot
- Screenshot showing four labelled API-derived application details
- Four API request screenshots
- Four API response screenshots
- HTTP status-code evidence
- API documentation table
- Demonstration video
- Working Google Drive link

## Completion condition

Person 4 is complete when the dashboard presents the required activity information, four APIs are tested and documented, the complete workflow is verified, and the video is uploaded and accessible.

---

# 9. Final Review by All Members

Every member must review the complete project and confirm:

- The exact dataset file is used consistently.
- The target column is the same throughout the project.
- Preprocessing is included in the workflow.
- EDA is included in the workflow.
- EDA outputs refresh during scheduled runs.
- The workflow runs every two minutes.
- Activity logs are available.
- Dashboard details match the actual application.
- Four accepted APIs are tested.
- Swagger/OpenAPI evidence is complete.
- HTTP status codes are recorded.
- No credentials appear in screenshots.
- The report matches the actual application.
- Each member's contribution is listed.
- The video demonstrates the complete project.
- The Google Drive link works.

---

# 10. Final Acceptance Checklist

## Assignment requirements

- [ ] Business problem is clearly explained.
- [ ] Approved Kaggle source is cited.
- [ ] Exact dataset filename is recorded.
- [ ] Target column is recorded.
- [ ] Row and column counts are recorded.
- [ ] Raw dataset is imported.
- [ ] Summary statistics are displayed.
- [ ] Missing values are checked.
- [ ] Numeric missing values are handled where required.
- [ ] Data types are displayed.
- [ ] Data is normalized or standardized where appropriate.
- [ ] Correlation coefficients are calculated.
- [ ] Numeric and categorical relationships are analyzed.
- [ ] Binning is demonstrated where appropriate.
- [ ] Encoding is demonstrated.
- [ ] Feature importance is shown where applicable.
- [ ] Univariate charts are included.
- [ ] Bivariate charts are included.
- [ ] Preprocessing is automated.
- [ ] EDA is automated.
- [ ] Workflow runs every two minutes.
- [ ] Activity logs are generated.
- [ ] Activity details are displayed on a cloud dashboard.
- [ ] At least four accepted application details are retrieved through APIs.
- [ ] API requests are tested through Swagger/OpenAPI or the approved equivalent.
- [ ] API responses and HTTP status codes are documented.
- [ ] Screenshots are included.

## Submission

- [ ] Final report is prepared as Word or PDF.
- [ ] Final report is named `49.docx` or `49.pdf`.
- [ ] A designated group member uploads the final report to the portal.
- [ ] Portal upload is verified before the deadline.
- [ ] Individual contributions are clearly listed.
- [ ] Screenshots are readable.
- [ ] Every screenshot has a short explanatory caption in the final report.
- [ ] Architecture diagram is included.
- [ ] Demonstration video is complete.
- [ ] Video is uploaded to Google Drive.
- [ ] Google Drive permissions are verified.
- [ ] Submission deadline is Friday, 18 September 2026.
- [ ] All members complete the final review.
