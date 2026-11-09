# ReproCheck — AI Research Methodology Reviewer

## 1. Project Overview

ReproCheck is an AI-powered research methodology reviewer for computer science research papers.
It helps engineers and researchers examine how clearly a paper describes its research and experiments.
It identifies missing information, incomplete descriptions, and inconsistencies between paper sections.
It also provides evidence from the submitted paper for each finding.
The long-term product has two goals:
- Check whether a paper reports the information needed to understand its methodology.
- Assess potential weaknesses in the research methodology, with evidence and clear limits.
Methodology completeness is the foundation. More advanced methodological assessment is a later capability.
ReproCheck does not prove that a study is valid, invalid, or reproducible.

## 2. Target Users

The initial users are:
- Computer science researchers.
- AI and machine learning engineers.
- Engineers who read, evaluate, or conduct technical research.
The first version focuses on modern AI systems.
Support for other computer science research areas may be added later.

## 3. Initial Research Domain

The first version focuses on research about modern AI systems, including:
- Retrieval-Augmented Generation (RAG) systems.
- Large Language Model (LLM) applications.
- AI agents.
- LLM fine-tuning.
- Model inference.
- AI model and system evaluation.
Traditional machine learning and deep learning research are possible future areas.
A single fixed checklist must not apply to every research type.
Criteria must match the paper's research focus.

## 4. Supported Inputs

### 4.1 Complete Paper

Users can upload a research paper in PDF format.
The system extracts the paper text and identifies its relevant sections.
It uses the methodology and experiment sections as primary review material.
Other sections can provide context when needed.
The system can compare information across sections to find possible inconsistencies.
### 4.2 Pasted Methodology

Users can paste a methodology section.
The system reviews the supplied text without requiring the complete paper.
The report must state when limited input prevents a check or conclusion.

## 5. Review Workflow

### 5.1 Submit the Paper

The user uploads a PDF or pastes methodology text.
The system validates and processes the input.
### 5.2 Identify the Research Type

The user may select a research type before the review.
This selection is optional.
If the user skips it, the system detects the research type from the paper.
The system displays its classification for the user to confirm or correct.
A paper can have one primary research type and relevant secondary types.
### 5.3 Generate the Checklist

The system examines the paper's research objective, contribution, methodology, and evaluation.
It then generates a checklist for that paper.
Each criterion must include a short reason for its inclusion.
The checklist must match the paper's research focus.
It must not include arbitrary, irrelevant, or duplicate criteria.
The user can add, remove, or edit checklist criteria.
The user must approve the checklist before the review starts.
### 5.4 Review the Paper

The system checks the paper against the approved checklist.
It identifies missing information and incomplete descriptions.
It also checks for relevant inconsistencies between paper sections when the full paper is available.
Every finding must have supporting evidence from the submitted paper.
### 5.5 Ask Questions

After the review, the user can ask questions about the paper and its review.
The system answers questions about the methodology, checklist, findings, evidence, and assessment.
This feature is limited to the submitted paper and its review.
It is not a general-purpose research chatbot.

## 6. Review Report

The first version produces a structured report with these components:
### 6.1 Missing Information

List relevant methodological or experimental details that the paper does not report.
### 6.2 Incomplete Descriptions

Identify details that the paper mentions but does not explain clearly enough.
### 6.3 Supporting Evidence

Show relevant excerpts or references to the submitted paper for each finding.
### 6.4 Cross-Section Inconsistencies

Report possible differences between the methodology, experiment, and results sections.
Only report an inconsistency when the paper provides evidence for it.
### 6.5 Overall Assessment

Use a qualitative label, with a short explanation based on the findings.
The initial labels are:
- Well documented.
- Partially documented.
- Insufficiently documented.
Do not use a numerical score in the initial version.
Do not present the label as a measure of scientific validity.

## 7. Evidence and Uncertainty

The submitted paper is the only evidence source for the initial version.
Do not use external guidelines or literature as review evidence.
Do not invent experimental details or fill gaps with assumptions.
Do not treat missing information as proof that an experiment was not performed.
Distinguish between information that is missing, unclear, or cannot be verified from the input.
State when the available evidence is insufficient.
Do not make unsupported claims about scientific validity or reproducibility.
The system reviews what the paper reports; it does not independently verify that experiments occurred.

## 8. Initial Version Scope

The initial version includes:
- PDF upload and pasted methodology input.
- Research type selection or automatic classification.
- Primary and relevant secondary research type identification.
- Paper-specific checklist generation and user approval.
- Review against the approved checklist.
- Missing information and incomplete description findings.
- Evidence for each finding.
- Cross-section inconsistency checks when the full paper is available.
- Qualitative overall assessment.
- Evidence-grounded question answering.
The initial version does not include:
- External research guideline integration.
- Independent verification or execution of experiments.
- General-purpose research chat.
- Numerical reproducibility or scientific validity scores.
- Comprehensive support for all computer science research areas.
- Full analysis or execution of research code.

## 9. Long-Term Direction

Future versions may add more research domains and external reporting guidelines.
They may provide deeper assessment of experimental design and evaluation methods.
They may also add research-code analysis, richer consistency checks, and user feedback features.
These are future possibilities, not commitments for the initial version.
