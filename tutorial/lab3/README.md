# Lab 3: Skill Matching, HTML Generation & Version Management

## Overview
Add the remaining tools to complete the agent pipeline.

| Step | File | What You Learn |
|------|------|----------------|
| 1 | `step1_skill_matching.py` | match_skills tool, alignment analysis |
| 2 | `step2_html_generation.py` | generate_resume_html tool, ATS HTML output |
| 3 | `step3_version_management.py` | S3-backed version storage and retrieval |

## Prerequisites
- Completed Lab 2
- S3 bucket and `RESUME_S3_BUCKET` env var set

## Quick Start

```bash
cd tutorial/lab3
uv run python step1_skill_matching.py
uv run python step2_html_generation.py
uv run python step3_version_management.py
```

## Step-by-Step Guide

### Step 1: Skill Matching (`step1_skill_matching.py`)

The `match_skills` tool validates that the agent has both a parsed resume profile and job requirements before performing analysis. The LLM then produces:
- `matched_skills`: skills you have that the job wants
- `missing_skills`: required skills you lack
- `transferable_skills`: your skills that map to requirements
- `keyword_coverage`: 0.0 to 1.0 score
- `recommendations`: suggestions for resume optimization

Key invariant: `matched_skills + missing_skills = all required_skills` (no overlap).

### Step 2: HTML Generation (`step2_html_generation.py`)

The `generate_resume_html` tool validates inputs, then the LLM generates a complete HTML resume following ATS rules:
- Semantic tags (`section`, `h1`-`h3`, `ul`, `li`)
- No JavaScript or external resources
- All matched keywords included
- Inline CSS only

The output HTML is saved to `output_resume.html` — open it in your browser.

### Step 3: Version Management (`step3_version_management.py`)

Demonstrates S3-backed version storage without the agent (plain functions) so you can see the S3 operations clearly:
- `save_version`: stores HTML + metadata as JSON in S3
- `list_versions`: lists all versions for a session (newest first)
- `get_latest`: retrieves the most recent version

S3 key structure: `versions/<session_id>/<version_id>.json`

## Design Pattern: Tool Validates, LLM Reasons

Notice that our tools are mostly validators — they check inputs and return confirmation. The actual intelligence (parsing, matching, generating) comes from the LLM. This is intentional:

- Tools handle I/O (S3, Textract) and validation (length checks, type checks)
- The LLM handles reasoning (extraction, analysis, generation)
- This keeps tools simple and testable while leveraging the model's intelligence

## Next: Lab 4
In Lab 4, you'll deploy to AgentCore and build a web frontend.
