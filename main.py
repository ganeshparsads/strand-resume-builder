"""Local testing script for the Resume Modifier Agent.

Tests the full end-to-end flow:
PDF → Textract → parse → match skills → generate HTML → save version

Run: uv run python main.py
"""

import uuid
from src.agent import create_agent

SAMPLE_JOB_DESCRIPTION = """
Senior Machine Learning Engineer - Amazon

About the role:
We are looking for a Senior ML Engineer to join our team building
next-generation recommendation systems. You will design and deploy
ML models at scale using AWS services.

Required Skills:
- Python, Java
- Machine Learning (TensorFlow, PyTorch)
- AWS (SageMaker, Lambda, S3)
- Distributed systems
- Docker, Kubernetes

Preferred Skills:
- Experience with recommendation systems
- NLP / LLM experience
- Spark, Kafka
- CI/CD pipelines

Responsibilities:
- Design and implement ML pipelines for production systems
- Collaborate with scientists on model development
- Optimize model inference latency and cost
- Mentor junior engineers

Qualifications:
- MS in Computer Science or related field
- 5+ years of ML engineering experience
- Strong coding skills in Python and Java
"""

SESSION_ID = str(uuid.uuid4())


def main():
    print("Creating Resume Modifier Agent...")
    agent = create_agent()

    print(f"\nSession ID: {SESSION_ID}")
    print("\n=== Full Pipeline Test ===")
    print("PDF → Textract → Parse → Match Skills → Generate HTML → Save\n")

    response = agent(
        f"Here is my workflow:\n"
        f"1. Extract text from the PDF at file_path 'resume.pdf'\n"
        f"2. Parse the extracted resume text into structured JSON\n"
        f"3. Parse this job description into structured JSON:\n"
        f"{SAMPLE_JOB_DESCRIPTION}\n"
        f"4. Match my skills against the job requirements\n"
        f"5. Generate a tailored ATS-friendly HTML resume\n"
        f"6. Save the version using session_id '{SESSION_ID}'\n"
        f"\nPlease execute all steps and return the final HTML resume."
    )

    print("\n--- Agent Response ---")
    print(str(response)[:2000])  # Truncate for readability
    print("\n... (truncated)")


if __name__ == "__main__":
    main()
