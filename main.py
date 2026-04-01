"""Local testing script for the Resume Modifier Agent.

Tests the full PDF → Textract → parse_resume flow.
Run: uv run python main.py
"""

from src.agent import create_agent


def main():
    print("Creating Resume Modifier Agent...")
    agent = create_agent()

    print("\nSending resume.pdf for extraction and parsing...\n")
    response = agent(
        "Extract text from the PDF at file_path 'resume.pdf' "
        "and then parse it into structured JSON."
    )

    print("\n--- Agent Response ---")
    print(response)


if __name__ == "__main__":
    main()
