"""
cover_letter_tool.py
--------------------
Provides context and instructions for writing personalized cover letters.
The AI agent does the actual writing using this tool's output as a guide.
"""

import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import yaml
import requests


def load_preferences() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../config/preferences.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class CoverLetterInput(BaseModel):
    job_title: str = Field(description="The job title being applied for")
    company_name: str = Field(description="Name of the company")
    job_description: str = Field(description="Full job description text")
    tailored_resume_summary: str = Field(
        description="A brief summary of the tailored resume highlights to reference"
    )


class CoverLetterTool(BaseTool):
    """
    Provides writing guidelines and company research context for
    generating a personalized cover letter.
    """
    name: str = "Cover Letter Writer Tool"
    description: str = (
        "Provides guidelines and context for writing a compelling cover letter "
        "for a specific job. Returns instructions for the Cover Letter Writer agent "
        "including tone, structure, and key points to include."
    )
    args_schema: type[BaseModel] = CoverLetterInput

    def _run(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        tailored_resume_summary: str
    ) -> str:
        prefs = load_preferences()
        candidate = prefs.get("candidate", {})
        cl_prefs = prefs.get("cover_letter", {})

        tone = cl_prefs.get("tone", "professional")
        max_words = cl_prefs.get("max_words", 350)
        include_why = cl_prefs.get("include_why_company", True)

        # Identify key requirements from JD
        key_requirements = self._extract_requirements(job_description)

        # Try to get a little company info (basic search)
        company_context = self._get_company_context(company_name)

        output = f"""
=== COVER LETTER WRITING TASK ===

Candidate: {candidate.get('name', 'Candidate')}
Applying for: {job_title} at {company_name}
Tone: {tone}
Max words: {max_words}

--- KEY JOB REQUIREMENTS (match these) ---
{chr(10).join(f"• {req}" for req in key_requirements[:8])}

--- RESUME HIGHLIGHTS TO REFERENCE ---
{tailored_resume_summary}

--- COMPANY CONTEXT (research this further if needed) ---
{company_context}

--- COVER LETTER STRUCTURE TO FOLLOW ---
Paragraph 1 (Hook — 2-3 sentences):
  - Open with something specific about {company_name} that excites the candidate
  - Immediately state the role and why you're an ideal fit
  - DO NOT start with "I am writing to apply for..."

Paragraph 2 (Most Relevant Achievement — 3-4 sentences):
  - Pick ONE achievement from the resume that maps directly to the top requirement
  - Be specific with numbers/impact where possible
  - Connect it explicitly to what {company_name} needs

Paragraph 3 (Why This Company — 2-3 sentences):
  {'- Research and mention something specific about the company: their mission, recent product, or culture' if include_why else '- Brief additional relevant experience or skill'}
  - Show genuine interest, not generic admiration

Closing (2 sentences):
  - Confident call to action
  - Contact info: {candidate.get('email', '')} | {candidate.get('phone', '')}

--- FORMATTING RULES ---
• Use plain text, no markdown
• Keep it under {max_words} words
• Sound human and enthusiastic, not corporate
• Never: "I am a passionate...", "I have always dreamed...", "Rockstar"
• Do: Be specific, use numbers, show you understand their problems
"""
        return output

    def _extract_requirements(self, job_description: str) -> list[str]:
        """Extract bullet-point requirements from the job description."""
        lines = job_description.split("\n")
        requirements = []
        for line in lines:
            line = line.strip()
            if line.startswith(("•", "-", "*", "·")) and len(line) > 10:
                requirements.append(line.lstrip("•-*· "))
            elif any(kw in line.lower() for kw in ["required", "must have", "you will", "you'll"]):
                requirements.append(line[:120])
        return requirements[:10]

    def _get_company_context(self, company_name: str) -> str:
        """
        Attempts a quick company lookup. In production, you'd use a proper
        company data API like Clearbit or LinkedIn. Here we use Serper.
        """
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return f"Research {company_name} online to find their mission, recent news, or notable products to reference."

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": f"{company_name} company mission values culture 2024", "num": 3},
                timeout=10
            )
            results = response.json().get("organic", [])
            if results:
                snippets = [r.get("snippet", "") for r in results[:2] if r.get("snippet")]
                return " ".join(snippets)[:400]
        except Exception:
            pass

        return f"Research {company_name} to find specific details to mention in the cover letter."
