"""
resume_tool.py
--------------
Reads the candidate's base resume and uses AI to tailor it for a specific
job posting by highlighting relevant skills and optimizing for ATS.
"""

import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import yaml


BASE_RESUME_PATH = os.path.join(
    os.path.dirname(__file__), "../../data/resumes/base_resume.txt"
)


def load_base_resume() -> str:
    """Load the candidate's base resume from disk."""
    if not os.path.exists(BASE_RESUME_PATH):
        return (
            "ERROR: No resume found. Please add your resume to "
            "data/resumes/base_resume.txt"
        )
    with open(BASE_RESUME_PATH, "r") as f:
        return f.read()


def load_preferences() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../config/preferences.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class ResumeTailorInput(BaseModel):
    job_title: str = Field(description="The job title being applied for")
    company_name: str = Field(description="Name of the company")
    job_description: str = Field(description="Full text of the job description")


class ReadResumeInput(BaseModel):
    pass


class ReadResumeTool(BaseTool):
    """Reads the candidate's base resume."""
    name: str = "Read Base Resume"
    description: str = (
        "Reads and returns the candidate's current base resume. "
        "Use this before tailoring to understand what's in the resume."
    )
    args_schema: type[BaseModel] = ReadResumeInput

    def _run(self) -> str:
        resume = load_base_resume()
        return f"=== CANDIDATE'S BASE RESUME ===\n\n{resume}"


class ResumeTailorTool(BaseTool):
    """
    Tailors the resume for a specific job posting.
    Returns a tailored version of the resume as a string.
    The actual AI rewriting is done by the agent using this tool as context.
    """
    name: str = "Tailor Resume for Job"
    description: str = (
        "Provides the base resume and tailoring instructions for a specific job. "
        "Returns the resume content plus a tailoring guide based on the job description. "
        "The Resume Tailor agent will produce the final tailored version."
    )
    args_schema: type[BaseModel] = ResumeTailorInput

    def _run(self, job_title: str, company_name: str, job_description: str) -> str:
        prefs = load_preferences()
        base_resume = load_base_resume()
        tailoring_level = prefs["resume_tailoring"].get("tailoring_level", "moderate")
        core_skills = prefs["resume_tailoring"].get("core_skills", [])

        # Extract key requirements from job description (keyword analysis)
        keywords = self._extract_keywords(job_description)

        output = f"""
=== RESUME TAILORING TASK ===

Target Job: {job_title} at {company_name}
Tailoring Level: {tailoring_level}

--- BASE RESUME ---
{base_resume}

--- JOB DESCRIPTION ---
{job_description[:2000]}

--- TAILORING INSTRUCTIONS ---
1. Identify keywords from the job description: {', '.join(keywords[:15])}
2. Core skills to always include: {', '.join(core_skills)}
3. Reorder bullet points in experience to lead with most relevant items
4. Adjust the summary/objective to match this specific role
5. Do NOT invent experience or skills the candidate doesn't have
6. Tailoring level is '{tailoring_level}':
   - conservative: Only add missing keywords to existing bullet points
   - moderate: Reorder and rewrite bullet points to emphasize relevance  
   - aggressive: Rewrite whole sections while keeping facts accurate

Please produce a complete, ATS-optimized resume tailored for this role.
Save the output as text — it will be used for the application.
"""
        return output

    def _extract_keywords(self, job_description: str) -> list[str]:
        """Simple keyword extraction — the AI will do a better job contextually."""
        # Common technical keywords to look for
        tech_terms = [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "SQL", "NoSQL",
            "MongoDB", "PostgreSQL", "REST", "GraphQL", "microservices",
            "CI/CD", "agile", "scrum", "machine learning", "AI", "data",
            "leadership", "management", "communication", "collaboration"
        ]

        found = []
        jd_lower = job_description.lower()
        for term in tech_terms:
            if term.lower() in jd_lower:
                found.append(term)

        return found
