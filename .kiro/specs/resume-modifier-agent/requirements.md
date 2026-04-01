# Requirements Document

## Introduction

The Resume Modifier Agent is an AI-powered system that accepts a user's PDF resume and a target job description, extracts text from the PDF using AWS Textract, analyzes the resume against the job requirements, and generates a tailored, ATS-friendly HTML resume. The system supports iterative refinement through conversational feedback and maintains version history per session. It is deployed as a Strands SDK agent on Amazon Bedrock AgentCore with a static HTML/CSS/JS frontend.

## Glossary

- **Agent**: The Strands SDK AI agent deployed on AgentCore that orchestrates all resume processing tools
- **Frontend**: The static HTML/CSS/JS single-page application used by the user
- **Textract**: AWS Textract service used to extract text from PDF documents
- **PDF_Extractor**: The `extract_text_from_pdf` tool that uploads PDFs to S3 and invokes Textract
- **Resume_Parser**: The `parse_resume` tool that converts extracted text into a structured ResumeProfile
- **Job_Parser**: The `parse_job_description` tool that converts job posting text into structured JobRequirements
- **Skill_Matcher**: The `match_skills` tool that analyzes alignment between a candidate profile and job requirements
- **HTML_Generator**: The `generate_resume_html` tool that produces ATS-friendly HTML resumes
- **Version_Manager**: The `manage_versions` tool that handles resume version storage and retrieval in S3
- **ResumeProfile**: Structured data model containing parsed resume fields (name, email, skills, experience, education, etc.)
- **JobRequirements**: Structured data model containing parsed job posting fields (title, required skills, keywords, etc.)
- **SkillMatchResult**: Data model containing skill alignment analysis (matched, missing, transferable skills, keyword coverage)
- **VersionRecord**: Data model representing a stored resume version (version_id, session_id, timestamp, html_content)
- **ATS**: Applicant Tracking System — automated software used by employers to filter resumes by keyword matching
- **Session**: A user interaction session identified by a UUID, scoping all versions and data to one user flow

## Requirements

### Requirement 1: PDF Resume Upload and Text Extraction

**User Story:** As a user, I want to upload my resume as a PDF file, so that the system can extract and process the text content without requiring me to copy-paste.

#### Acceptance Criteria

1. WHEN a user uploads a PDF file, THE Frontend SHALL encode the PDF as base64 and transmit it to the Agent endpoint
2. WHEN the PDF_Extractor receives a base64-encoded PDF, THE PDF_Extractor SHALL decode it and validate that the decoded bytes start with the `%PDF` magic bytes
3. WHEN the PDF_Extractor receives a valid PDF, THE PDF_Extractor SHALL upload it to S3 at the path `s3://<bucket>/<session_id>/resume.pdf`
4. WHEN the PDF is uploaded to S3, THE PDF_Extractor SHALL invoke AWS Textract to extract all text content from the PDF
5. WHEN Textract returns extracted text blocks, THE PDF_Extractor SHALL concatenate them in reading order (top-to-bottom, left-to-right) joined by newlines and return the result as a plain text string
6. THE PDF_Extractor SHALL return a non-empty string for any valid PDF that contains visible text content

### Requirement 2: PDF Validation and Error Handling

**User Story:** As a user, I want clear error messages when my PDF upload fails, so that I can correct the issue and try again.

#### Acceptance Criteria

1. IF the uploaded file's decoded bytes do not start with `%PDF` magic bytes, THEN THE PDF_Extractor SHALL raise a ValueError before uploading to S3 or invoking Textract
2. IF the decoded PDF exceeds 10 MB, THEN THE PDF_Extractor SHALL raise a ValueError indicating the size limit
3. IF the base64 encoding is invalid, THEN THE PDF_Extractor SHALL raise a ValueError with a descriptive message
4. IF Textract fails to extract text from a corrupted or unsupported PDF, THEN THE PDF_Extractor SHALL raise a RuntimeError explaining the extraction failure
5. IF Textract returns no text content from the PDF, THEN THE PDF_Extractor SHALL raise a RuntimeError indicating no text was found
6. IF the S3 upload fails, THEN THE PDF_Extractor SHALL raise a RuntimeError with S3 error details
7. WHEN a PDF validation or extraction error occurs, THE Agent SHALL return a clear error message to the user without creating any version record

### Requirement 3: Resume Parsing

**User Story:** As a user, I want my resume text to be parsed into structured sections, so that the system can analyze and optimize each part individually.

#### Acceptance Criteria

1. WHEN the Resume_Parser receives extracted text from the PDF_Extractor, THE Resume_Parser SHALL produce a ResumeProfile containing name, email, phone, summary, skills, experience, education, certifications, and projects
2. THE Resume_Parser SHALL extract a non-empty name field from any valid resume text
3. THE Resume_Parser SHALL extract at least one skill from any valid resume text
4. WHEN experience entries are extracted, THE Resume_Parser SHALL order them by date descending (most recent first)
5. THE Resume_Parser SHALL accept text between 100 and 50,000 characters in length

### Requirement 4: Job Description Parsing

**User Story:** As a user, I want the system to analyze the job description I provide, so that it can identify the key requirements and keywords to target.

#### Acceptance Criteria

1. WHEN the Job_Parser receives job description text, THE Job_Parser SHALL produce a JobRequirements structure containing title, company, required skills, preferred skills, responsibilities, qualifications, and ATS keywords
2. THE Job_Parser SHALL extract at least one required skill from any valid job description
3. THE Job_Parser SHALL extract ATS-relevant keywords from the job posting
4. THE Job_Parser SHALL only extract requirements present in the input text without fabricating additional requirements
5. THE Job_Parser SHALL accept text between 50 and 30,000 characters in length

### Requirement 5: Skill Matching and Analysis

**User Story:** As a user, I want the system to identify how my skills align with the job requirements, so that I can understand my strengths and gaps.

#### Acceptance Criteria

1. WHEN the Skill_Matcher receives a ResumeProfile and JobRequirements, THE Skill_Matcher SHALL produce a SkillMatchResult containing matched skills, missing skills, transferable skills, keyword coverage, and recommendations
2. THE Skill_Matcher SHALL classify every required skill as either matched or missing, such that matched_skills ∪ missing_skills = required_skills
3. THE Skill_Matcher SHALL produce no overlap between matched and missing skills, such that matched_skills ∩ missing_skills = ∅
4. THE Skill_Matcher SHALL compute keyword_coverage as a float value in the range [0.0, 1.0]
5. THE Skill_Matcher SHALL identify transferable skills from the user's profile that map to required skills
6. THE Skill_Matcher SHALL produce at least one recommendation for resume optimization

### Requirement 6: HTML Resume Generation

**User Story:** As a user, I want the system to generate a professionally formatted, ATS-friendly HTML resume tailored to the job description, so that I can maximize my chances of passing automated screening.

#### Acceptance Criteria

1. WHEN the HTML_Generator receives a ResumeProfile, SkillMatchResult, and JobRequirements, THE HTML_Generator SHALL produce a non-empty string of valid HTML
2. THE HTML_Generator SHALL use semantic HTML tags (section, h1-h3, ul, li) for ATS compatibility
3. THE HTML_Generator SHALL include all skills from matched_skills in the output HTML
4. THE HTML_Generator SHALL produce HTML containing no JavaScript or external resource references
5. WHEN feedback and current_html are provided, THE HTML_Generator SHALL apply the feedback to refine the existing resume
6. WHEN refining with feedback, THE HTML_Generator SHALL preserve all factual information from the original profile (name, dates, company names) unless the feedback explicitly requests removal

### Requirement 7: Version Management

**User Story:** As a user, I want the system to save each version of my resume, so that I can review previous versions and track changes over time.

#### Acceptance Criteria

1. WHEN the Version_Manager receives a "save" action with html_content, THE Version_Manager SHALL store the version in S3 and return a VersionRecord with a new version_id and ISO 8601 timestamp
2. WHEN saving a new version, THE Version_Manager SHALL produce a version_id and timestamp strictly greater than all previous versions in the same session
3. WHEN the Version_Manager receives a "get" action with a version_id, THE Version_Manager SHALL return the exact html_content that was stored by the corresponding save operation
4. WHEN the Version_Manager receives a "get_latest" action, THE Version_Manager SHALL return the most recent VersionRecord for the session, or an empty dict if no versions exist
5. WHEN the Version_Manager receives a "list" action, THE Version_Manager SHALL return all VersionRecords for the session ordered by timestamp descending
6. THE Version_Manager SHALL only modify S3 state on "save" actions

### Requirement 8: Session Isolation

**User Story:** As a user, I want my resume data to be isolated from other users' sessions, so that my personal information remains private and secure.

#### Acceptance Criteria

1. THE Agent SHALL scope all S3 operations (PDF uploads, version storage, version retrieval) to the session_id prefix
2. THE Version_Manager SHALL only read or write data under the S3 key prefix matching the provided session_id
3. THE PDF_Extractor SHALL upload PDFs only under the S3 key prefix matching the provided session_id

### Requirement 9: Iterative Refinement

**User Story:** As a user, I want to provide feedback on the generated resume and have the system refine it, so that I can iteratively improve the output.

#### Acceptance Criteria

1. WHEN a user submits feedback text, THE Agent SHALL retrieve the latest version for the session and apply the feedback to generate a refined resume
2. WHEN a refinement is completed, THE Agent SHALL save the refined HTML as a new version with the feedback recorded in the VersionRecord
3. IF a user requests refinement but no prior version exists for the session, THEN THE Agent SHALL inform the user that no prior resume exists and ask them to generate one first

### Requirement 10: Frontend PDF Upload Interface

**User Story:** As a user, I want a clear interface to upload my PDF resume and enter a job description, so that I can easily start the resume optimization process.

#### Acceptance Criteria

1. THE Frontend SHALL provide a file upload input that accepts only `.pdf` files
2. THE Frontend SHALL provide a text input area for the job description
3. WHEN a non-PDF file is selected, THE Frontend SHALL reject the file and display an error message
4. THE Frontend SHALL display upload progress and extraction status during PDF processing
5. THE Frontend SHALL render the generated HTML resume in a preview area
6. THE Frontend SHALL provide a feedback text input for iterative refinement
7. THE Frontend SHALL provide a version history sidebar for navigating between resume versions

### Requirement 11: Agent Orchestration

**User Story:** As a user, I want the system to automatically coordinate all processing steps, so that I only need to upload my resume and job description to get a tailored result.

#### Acceptance Criteria

1. WHEN a user submits a PDF resume and job description, THE Agent SHALL orchestrate the tools in sequence: extract_text_from_pdf → parse_resume → parse_job_description → match_skills → generate_resume_html → manage_versions("save")
2. WHEN the Agent completes resume generation, THE Agent SHALL return the html_content and version_id to the Frontend
3. IF S3 storage fails during version save, THEN THE Agent SHALL return the generated HTML in the response so the user does not lose work
4. IF the Bedrock model call exceeds the timeout, THEN THE Agent SHALL return a timeout error message
