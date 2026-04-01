# Implementation Plan: Resume Modifier Agent

## Overview

Build a Strands SDK agent that accepts a PDF resume and job description, extracts text via AWS Textract, analyzes skill alignment, and generates a tailored ATS-friendly HTML resume. Deployed on Amazon Bedrock AgentCore with a static HTML/CSS/JS frontend. Implementation starts with project setup and core parsing tools, then layers on remaining tools, deployment, and frontend.

## Tasks

- [x] 1. Project setup and dependencies
  - [x] 1.1 Initialize Python project with uv and install dependencies
    - Run `uv init resume-modifier-agent` and `cd resume-modifier-agent`
    - Run `uv add strands-agents strands-agents-builder bedrock-agentcore boto3 amazon-textract-textractor`
    - Run `uv add --dev bedrock-agentcore-starter-toolkit moto hypothesis pytest`
    - Create directory structure: `src/tools/`, `src/models/`, `tests/`
    - _Requirements: Design Dependencies table_

- [x] 2. Define data models
  - [x] 2.1 Create data model dataclasses in `src/models/schemas.py`
    - Implement `ResumeProfile`, `ExperienceEntry`, `EducationEntry`, `ProjectEntry`
    - Implement `JobRequirements`, `SkillMatchResult`, `VersionRecord`
    - Add validation helpers: `session_id` UUID check, `keyword_coverage` bounds check, non-empty `html_content` check
    - _Requirements: 3.1, 4.1, 5.1, 7.1_

  - [ ]* 2.2 Write property tests for data model validation
    - **Property 6: Keyword Coverage Bounds** — verify `keyword_coverage` constrained to [0.0, 1.0]
    - **Validates: Requirement 5.4**

- [x] 3. Implement `parse_resume` tool
  - [x] 3.1 Create `src/tools/parse_resume.py` with the `@tool` decorated function
    - Accept `resume_text: str`, validate length (100–50,000 chars)
    - Use the agent's LLM to extract structured fields into a `ResumeProfile` dict
    - Ensure `name` is non-empty, `skills` has at least one entry, `experience` ordered by date descending
    - Return dict conforming to `ResumeProfile` schema
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 3.2 Write property test for `parse_resume`
    - **Property 3: Resume Parsing Produces Valid ResumeProfile** — for any valid resume text (100–50,000 chars), output conforms to schema with non-empty name, at least one skill, experience ordered descending
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [-] 4. Implement `extract_text_from_pdf` tool
  - [x] 4.1 Create `src/tools/extract_text_from_pdf.py` with the `@tool` decorated function
    - Accept `resume_pdf_base64: str` and `session_id: str`
    - Decode base64, validate PDF magic bytes (`%PDF`), validate size ≤ 10 MB
    - Upload PDF to S3 at `s3://<bucket>/<session_id>/resume.pdf`
    - Invoke AWS Textract `DetectDocumentText` on the S3 object
    - Concatenate text blocks in reading order (top-to-bottom, left-to-right) joined by newlines
    - Raise `ValueError` for invalid base64, non-PDF content, or oversized files
    - Raise `RuntimeError` for Textract failures, empty text, or S3 errors
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 4.2 Write property test for PDF validation
    - **Property 1: PDF Input Validation Rejects Invalid Content** — for any base64 input whose decoded bytes don't start with `%PDF` or whose base64 is invalid, `extract_text_from_pdf` raises `ValueError` before S3/Textract calls
    - **Validates: Requirements 1.2, 2.1, 2.3**

  - [ ]* 4.3 Write unit tests for `extract_text_from_pdf` with mocked S3 and Textract
    - Test valid PDF upload and text extraction with moto mocks
    - Test error cases: invalid base64, non-PDF content, oversized PDF, Textract failure, empty text, S3 failure
    - **Property 2: Textract Text Block Assembly** — verify blocks concatenated in reading order with newlines
    - **Validates: Requirements 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 5. Basic agent setup and local testing
  - [x] 5.1 Create `src/agent.py` with Strands agent wired to `parse_resume` and `extract_text_from_pdf`
    - Configure `BedrockModel` with Claude 3.7 Sonnet
    - Define `SYSTEM_PROMPT` for resume optimization workflow
    - Register `extract_text_from_pdf` and `parse_resume` as tools
    - _Requirements: 11.1_

  - [x] 5.2 Create `main.py` for local testing of the agent
    - Instantiate the agent and invoke with sample resume text and job description
    - Verify the agent calls tools in correct sequence and returns structured output
    - _Requirements: 11.1, 11.2_

- [ ] 6. Checkpoint — Validate core parsing pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement `parse_job_description` tool
  - [ ] 7.1 Create `src/tools/parse_job_description.py` with the `@tool` decorated function
    - Accept `job_description: str`, validate length (50–30,000 chars)
    - Use the agent's LLM to extract structured fields into a `JobRequirements` dict
    - Ensure `required_skills` has at least one entry, `keywords` is non-empty
    - Only extract requirements present in input text — no fabrication
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 7.2 Write property test for `parse_job_description`
    - **Property 4: Job Parsing Produces Valid JobRequirements** — for any valid job description (50–30,000 chars), output has at least one required skill and non-empty keywords
    - **Validates: Requirements 4.1, 4.2, 4.3**

- [ ] 8. Implement `match_skills` tool
  - [ ] 8.1 Create `src/tools/match_skills.py` with the `@tool` decorated function
    - Accept `profile: dict` and `requirements: dict`
    - Classify every required skill as matched or missing (complete partition, no overlap)
    - Identify transferable skills from user profile
    - Compute `keyword_coverage` as float in [0.0, 1.0]
    - Produce at least one recommendation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 8.2 Write property test for `match_skills`
    - **Property 5: Skill Match Partitioning** — `matched_skills ∪ missing_skills = required_skills` and `matched_skills ∩ missing_skills = ∅`
    - **Property 6: Keyword Coverage Bounds** — `keyword_coverage` in [0.0, 1.0]
    - **Validates: Requirements 5.2, 5.3, 5.4**

- [ ] 9. Implement `generate_resume_html` tool
  - [ ] 9.1 Create `src/tools/generate_resume_html.py` with the `@tool` decorated function
    - Accept `profile`, `match_result`, `job_requirements`, optional `feedback` and `current_html`
    - Generate ATS-friendly HTML using semantic tags (`section`, `h1`–`h3`, `ul`, `li`)
    - Include all `matched_skills` in output HTML
    - No `<script>` tags or external resource references
    - When `feedback` and `current_html` provided, refine existing resume preserving factual info
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [ ]* 9.2 Write property tests for `generate_resume_html`
    - **Property 7: Valid ATS HTML Output** — output is non-empty HTML with semantic tags, no `<script>` or external refs
    - **Property 8: ATS Keyword Inclusion** — all `matched_skills` appear in output HTML
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [ ] 10. Implement `manage_versions` tool
  - [ ] 10.1 Create `src/tools/manage_versions.py` with the `@tool` decorated function
    - Support actions: `save`, `get_latest`, `get`, `list`
    - Store/retrieve versions in S3 under `<session_id>/versions/` prefix
    - `save`: generate UUID `version_id`, ISO 8601 timestamp, store HTML in S3, return `VersionRecord`
    - `get_latest`: return most recent version or empty dict
    - `get`: return specific version by `version_id`
    - `list`: return all versions ordered by timestamp descending
    - Only modify S3 state on `save` actions
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2_

  - [ ]* 10.2 Write property tests for `manage_versions` with mocked S3
    - **Property 10: Version Round-Trip Integrity** — save then get returns exact same `html_content`
    - **Property 11: Version Ordering Monotonicity** — successive saves produce strictly increasing version_id/timestamp
    - **Property 12: Read Operations Are Side-Effect Free** — get/get_latest/list don't modify S3 state
    - **Property 13: Session Isolation** — operations for session A never touch session B's S3 prefix
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.1, 8.2, 8.3**

- [ ] 11. Wire all tools into the agent and test full pipeline
  - [ ] 11.1 Update `src/agent.py` to register all six tools
    - Add `parse_job_description`, `match_skills`, `generate_resume_html`, `manage_versions`
    - Update system prompt to cover full workflow and refinement flow
    - _Requirements: 11.1, 11.2_

  - [ ] 11.2 Update `main.py` to test full end-to-end flow locally
    - Test generate flow: extract PDF → parse resume → parse job → match skills → generate HTML → save version
    - Test refinement flow: get latest version → apply feedback → save new version
    - _Requirements: 9.1, 9.2, 9.3, 11.1, 11.2_

- [ ] 12. Checkpoint — Validate full agent pipeline
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. AgentCore deployment entrypoint
  - [ ] 13.1 Create `src/entrypoint.py` with `BedrockAgentCoreApp` wrapper
    - Implement `@app.entrypoint` `invoke` function
    - Parse payload for `session_id`, `message`, `resume_pdf_base64`
    - Route to Strands agent and return structured JSON response
    - Handle missing `message` with error response
    - Handle S3 failure during version save by returning HTML in response
    - Handle model timeout with error message
    - _Requirements: 11.2, 11.3, 11.4_

  - [ ]* 13.2 Write unit tests for the AgentCore entrypoint
    - Test payload parsing and routing
    - Test error handling for missing message, S3 failure, timeout
    - **Property 14: Error Recovery Preserves No Side Effects** — validation/extraction errors return error message with no VersionRecord created
    - **Validates: Requirements 2.7, 11.3, 11.4**

- [ ] 14. Implement frontend SPA
  - [ ] 14.1 Create `frontend/index.html` with PDF upload, job description input, and resume preview
    - File upload input accepting `.pdf` only
    - Text area for job description
    - Preview area for rendered HTML resume
    - Feedback text input for iterative refinement
    - Version history sidebar
    - _Requirements: 10.1, 10.2, 10.5, 10.6, 10.7_

  - [ ] 14.2 Create `frontend/app.js` with agent endpoint integration
    - Encode uploaded PDF as base64 and send to agent endpoint
    - Reject non-PDF files with error message
    - Display upload progress and extraction status
    - Render generated HTML in preview area
    - Handle refinement submissions
    - Handle version history navigation
    - _Requirements: 1.1, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [ ] 14.3 Create `frontend/styles.css` with layout and styling
    - Responsive layout for upload form, preview, and version sidebar
    - _Requirements: 10.1_

- [ ] 15. Final checkpoint — Full system validation
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation language is Python, matching the design document
