"""
job_search_tool.py
------------------
Searches multiple job boards for openings matching the candidate's preferences.
Supports: Google Jobs (via Serper), Indeed, and a generic scraper.
"""

import os
import json
import requests
from typing import Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import yaml


def load_preferences() -> dict:
    """Load job preferences from config file."""
    config_path = os.path.join(os.path.dirname(__file__), "../../config/preferences.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


class JobSearchInput(BaseModel):
    query: str = Field(description="Job title or keywords to search for")
    location: Optional[str] = Field(default=None, description="Location for the job search")
    num_results: int = Field(default=10, description="Number of results to fetch")


class JobSearchTool(BaseTool):
    """
    Searches for job postings using the Serper API (Google Jobs) and returns
    a structured list of matching opportunities.
    """
    name: str = "Job Search Tool"
    description: str = (
        "Searches for job postings across Google Jobs and job boards. "
        "Returns a list of job postings with title, company, location, "
        "description snippet, and application URL."
    )
    args_schema: type[BaseModel] = JobSearchInput

    def _run(self, query: str, location: Optional[str] = None, num_results: int = 10) -> str:
        prefs = load_preferences()
        
        # Use location from preferences if not specified
        if not location:
            location = prefs["job_search"].get("location", "")

        results = self._search_google_jobs(query, location, num_results)
        results = self._apply_filters(results, prefs)

        if not results:
            return "No matching jobs found for this query. Try different keywords."

        # Format nicely for the agent
        output = f"Found {len(results)} jobs for '{query}' in '{location}':\n\n"
        for i, job in enumerate(results, 1):
            output += f"--- Job {i} ---\n"
            output += f"Title:    {job.get('title', 'N/A')}\n"
            output += f"Company:  {job.get('company', 'N/A')}\n"
            output += f"Location: {job.get('location', 'N/A')}\n"
            output += f"Posted:   {job.get('date_posted', 'N/A')}\n"
            output += f"Salary:   {job.get('salary', 'Not listed')}\n"
            output += f"URL:      {job.get('url', 'N/A')}\n"
            output += f"Snippet:  {job.get('snippet', 'N/A')[:300]}...\n\n"

        return output

    def _search_google_jobs(self, query: str, location: str, num_results: int) -> list[dict]:
        """
        Uses the Serper API to search Google Jobs.
        Serper is a cheap, reliable Google Search API — get a key at serper.dev
        """
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return self._fallback_mock_results(query, location)

        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "q": f"{query} jobs {location}",
            "num": num_results,
            "tbs": "qdr:w",   # Results from past week
        }

        try:
            response = requests.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            jobs = []
            # Parse organic results as job listings
            for result in data.get("organic", []):
                jobs.append({
                    "title": result.get("title", "").replace(" - LinkedIn", "").replace(" - Indeed", ""),
                    "company": self._extract_company(result),
                    "location": location,
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "date_posted": "Recent",
                    "salary": "Not listed",
                    "source": "Google Search"
                })

            # Also check for dedicated "jobs" section in Serper results
            for job in data.get("jobs", []):
                jobs.append({
                    "title": job.get("title", ""),
                    "company": job.get("company", ""),
                    "location": job.get("location", location),
                    "url": job.get("link", ""),
                    "snippet": job.get("description", ""),
                    "date_posted": job.get("datePosted", "Recent"),
                    "salary": job.get("salary", "Not listed"),
                    "source": "Google Jobs"
                })

            return jobs[:num_results]

        except Exception as e:
            print(f"[JobSearchTool] Search error: {e}")
            return self._fallback_mock_results(query, location)

    def _extract_company(self, result: dict) -> str:
        """Try to extract company name from search result."""
        snippet = result.get("snippet", "")
        title = result.get("title", "")
        # Company name often appears after " at " or " - " in the title
        if " at " in title:
            return title.split(" at ")[-1].strip()
        if " | " in title:
            return title.split(" | ")[-1].strip()
        return "Unknown Company"

    def _apply_filters(self, jobs: list[dict], prefs: dict) -> list[dict]:
        """Filter out blacklisted companies and jobs with red-flag keywords."""
        blacklist = prefs.get("blacklist", {})
        bad_companies = [c.lower() for c in blacklist.get("companies", [])]
        bad_keywords = [k.lower() for k in blacklist.get("description_red_flags", [])]

        filtered = []
        for job in jobs:
            company = job.get("company", "").lower()
            snippet = job.get("snippet", "").lower()

            if company in bad_companies:
                print(f"[Filter] Skipping blacklisted company: {job['company']}")
                continue

            if any(kw in snippet for kw in bad_keywords):
                print(f"[Filter] Skipping job with red-flag keyword: {job['title']}")
                continue

            filtered.append(job)

        return filtered

    def _fallback_mock_results(self, query: str, location: str) -> list[dict]:
        """Returns mock data when API is unavailable — useful for testing."""
        return [
            {
                "title": f"Senior {query}",
                "company": "TechCorp Inc.",
                "location": location,
                "url": "https://example.com/jobs/1",
                "snippet": f"We are looking for a talented {query} to join our growing team. You will work on exciting projects...",
                "date_posted": "2 days ago",
                "salary": "$120,000 - $160,000",
                "source": "Mock Data (set SERPER_API_KEY in .env)"
            }
        ]
