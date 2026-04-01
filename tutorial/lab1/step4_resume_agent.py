"""
Step 4: Complete Resume Parsing Agent
======================================

This combines everything from Steps 1-3 into a complete resume
parsing agent. This is the foundation we'll build on in Lab 2.

What this agent can do:
- Accept resume text and parse it into structured JSON
- Validate input length
- Extract: name, email, phone, summary, skills, experience, education
- Handle follow-up questions about the parsed resume

What we'll add in Lab 2:
- PDF support (AWS Textract)
- Job description parsing

Run: uv run python step4_resume_agent.py
"""

import os
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

model = BedrockModel(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
)


@tool
def parse_resume(resume_text: str) -> dict:
    """Validate resume text for structured parsing.

    Call this when the user provides resume text. Validates the text
    length and returns confirmation to proceed with extraction.

    Args:
        resume_text: Plain text content of a resume (100-50000 chars).

    Returns:
        Validation result with character count.
    """
    text_length = len(resume_text.strip())

    if text_length < 100:
        raise ValueError(
            f"Resume too short ({text_length} chars). "
            "Please provide a complete resume with at least 100 characters."
        )
    if text_length > 50_000:
        raise ValueError(
            f"Resume too long ({text_length} chars). Maximum is 50,000."
        )

    return {
        "status": "validated",
        "char_count": text_length,
        "instructions": (
            "Text validated. Now extract structured JSON with: "
            "name, email, phone, summary, skills, experience "
            "(company, title, dates, bullets), education "
            "(institution, degree, field, date), certifications, projects."
        ),
    }


SYSTEM_PROMPT = """You are a professional resume parsing agent.

When given resume text:
1. Call parse_resume to validate the text
2. Extract a structured JSON object with these exact fields:
   - name (string, required)
   - email (string)
   - phone (string)
   - summary (string)
   - skills (list of strings, at least one)
   - experience (list of objects with: company, title, start_date, end_date, bullets)
   - education (list of objects with: institution, degree, field_of_study, graduation_date)
   - certifications (list of strings)
   - projects (list of objects with: name, description, technologies)

Rules:
- Order experience by date descending (most recent first)
- Only extract information present in the text — NEVER fabricate
- If a field is not found, use an empty string or empty list

For follow-up questions, reference the previously parsed resume data."""

agent = Agent(
    model=model,
    tools=[parse_resume],
    system_prompt=SYSTEM_PROMPT,
)


def main():
    """Interactive resume parsing session."""
    print("=" * 60)
    print("  Resume Parsing Agent — Lab 1")
    print("  Type 'quit' to exit")
    print("=" * 60)
    print()

    # Pre-load with a sample resume for demo
    sample = """
Sarah Chen
Email: sarah.chen@email.com | Phone: (415) 555-0198
LinkedIn: linkedin.com/in/sarahchen

PROFESSIONAL SUMMARY
Senior data engineer with 7 years of experience designing and
maintaining large-scale data pipelines. Expert in Python, Spark,
and cloud-native architectures on AWS and GCP.

SKILLS
Python, Scala, SQL, Spark, Airflow, Kafka, AWS (Glue, Redshift,
S3, Lambda, EMR), GCP (BigQuery, Dataflow), Docker, Kubernetes,
Terraform, dbt, Snowflake, PostgreSQL, MongoDB

EXPERIENCE

Lead Data Engineer | DataFlow Inc | Apr 2022 - Present
- Designed real-time streaming pipeline processing 50M events/day
  using Kafka and Spark Structured Streaming
- Reduced data warehouse costs by 45% migrating from Redshift to
  Snowflake with dbt transformations
- Led team of 6 engineers; established code review and testing standards
- Built ML feature store serving 200+ features to 15 ML models

Senior Data Engineer | CloudScale | Jan 2020 - Mar 2022
- Architected ETL framework on AWS Glue processing 10TB daily
- Implemented data quality monitoring with Great Expectations,
  catching 95% of data issues before production
- Migrated legacy Oracle data warehouse to BigQuery, reducing
  query times by 80%

Data Engineer | TechStart | Jun 2017 - Dec 2019
- Built batch processing pipelines using Airflow and Spark
- Developed Python data validation framework used across 3 teams
- Created Tableau dashboards for executive reporting

EDUCATION
M.S. Data Science | UC Berkeley | 2017
B.S. Statistics | UCLA | 2015

CERTIFICATIONS
AWS Certified Data Analytics - Specialty
Google Professional Data Engineer
Databricks Certified Associate Developer for Apache Spark
"""

    print("Demo: Parsing a sample resume...\n")
    response = agent(f"Parse this resume into structured JSON:\n\n{sample}")
    print(response)

    # Interactive loop
    print("\n" + "=" * 60)
    print("Now you can ask follow-up questions about the resume,")
    print("or paste a new resume to parse.")
    print("=" * 60 + "\n")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        response = agent(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    main()
