# Generic Document Evaluation Tool

🔍 **Evaluate PDFs against custom business criteria**

A simple, adaptable solution for analyzing and categorizing transactional documents using predefined evaluation criteria. Perfect for analysts, auditors, or developers seeking to automate document review in enterprise, finance, education, or public sector scenarios and more.

Reviewed: 22.09.2025

## Overview

**Document Evaluation Tool** lets you upload one or more documents (PDF), define your evaluation criteria in a CSV format or manual entry, and receive a professional markdown report categorizing each document as appropriate, with a rationale for each decision. With the option to add additional input to the prompt, making sure it's easy to customize for all sorts of scenarios where documents and criteria is involved.

**What's Included:**

 **Frontend**: Modern React interface
- **Backend**: Oracle GenAI Service integration 

---

 
# When to use this asset?
 
Analysts, compliance teams, auditors, or operational staff would use this asset whenever they need to systematically evaluate, validate, or categorize documents—such as visa applications, insurance claims, or student financial aid requests—based on well-defined criteria.

Developers and solution architects may also use this asset to rapidly prototype or demo document analysis workflows, including LLM-driven or human-in-the-loop review scenarios.
 
# How to use this asset?
 
Collect the Documents: Gather one or more PDFs containing the applications or claims to be evaluated.

Define Evaluation Criteria: Prepare a CSV file listing the evaluation criteria and descriptions tailored for the specific use case (e.g., insurance claim completeness, income eligibility for student aid). Optionally, you can give the criteria in a free-format in the front-end including additional requirements that may not be criteria.

Run the Tool: Upload the documents and relevant criterion.

Automated Evaluation: The tool analyzes the content of each document, evaluating and categorizing them according to your criteria.

Review the Results: Receive a professional, human-readable markdown report showing the outcome for each document (Ready to Admit, Conditional, Rejected), along with explanations and a summary table.

Take Action: Use the evaluation output to make operational decisions (e.g., approve/reject applications, flag items for manual review, generate audit trails).


---

## Architecture

The solution consists of two complementary components:

### Frontend (React/Next.js)

- Multi-tenant chat interface
- Multiple input option allows flexibility for use-case

### Backend (Node.js/Express)

- Oracle GenAI Services
- Embedding documents in local qdrant vector store 


---

## Quick Start

### Full Stack 

Complete setup with Oracle GenAI Service:
#TO-DO
```bash
# Start backend
cd backend/
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your Configure Oracle Credentials

# Start main.py
python main.py

# Start frontend (in new terminal)
cd files/frontend/
npm install
cp .env.example .env.local
# Configure Oracle Digital Assistant + Speech Service URL
npm run dev
```

--- 
## Example  Use Cases

- Visa application processing
- Insurance claim validation
- Student financial aid and scholarship assessment
- RFP evaluation
- Resume evaluation
- ESG Document review
- Any transactional document requiring multi-criteria analysis



---
## Example Criteria



### Insurance Claim (CSV)

| Criteria               | Description                                                                              |
|------------------------|------------------------------------------------------------------------------------------|
| Completeness           | All required fields are filled out and information is provided for each section.         |
| Incident Clarity       | Incident details are clearly described, dates and type of incident are consistent.       |
| Cost Breakdown Accuracy| All claimed expenses are itemized, reasonable, and total matches the sum of items.       |
| Supporting Evidence    | Incident verification is provided (e.g., police report, doctor’s note).                  |
| Policy Coverage Check  | Total claimed amount is within the policy coverage limit.                                |
| Contact Validity       | Contact information for the claimant is complete and plausible.                          |

### Visa Application (CSV)

| Criteria                    | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| Completeness                | All required fields are filled and accurate.                                |
| Financial Sufficiency       | Applicant has sufficient bank balance (e.g., minimum €3,000).               |
| Passport Validity           | Passport expiration is at least 6 months after intended departure.          |
| Employment/Sponsorship Info | Clear and valid employment or sponsorship details provided.                 |

### Student Financial Aid (CSV)

| Criteria           | Description                                                        |
|--------------------|--------------------------------------------------------------------|
| Completeness       | All fields filled and supporting docs present.                     |
| Income Eligibility | Household income and size match program limits.                    |
| Academic Merit     | If required: grades, honors, awards, or other evidence provided.   |
| Loan Co-signer     | If loan: co-signer details are complete and income is sufficient.  |

---

## Example Outcome Categories

- **Ready to Admit**: Document is fully verified, consistent, and meet all criteria
- **Conditional**: Document is mostly satisfactory but missing minor details or require further clarification
- **Rejected**: Documents are clearly incomplete, falsified, or contain highly inconsistent information

---

## Quick Start

1. Upload your document(s) as PDF.
2. Provide a CSV listing your evaluation criteria (see templates above).
3. Add any additional requirements you have such as asking for a scoring over hundred for each criteria.

---


# Components

- **Frontend**: [`files/frontend/`](files/frontend/) - Complete React interface
- **Backend**: [`files/backend/`](files/backend/) - Oracle Generative AI Service integration

## Technology Stack

**Frontend**: Next.js 15, React 19, Material-UI, Framer Motion, Oracle WebSDK  
**Backend**: Node.js, Express, WebSocket, Oracle GenAI, FFmpeg #TO-DO update this

# Browser Requirements

- Modern browser with WebSocket support
- LocalStorage for project persistence

---
# License

Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.