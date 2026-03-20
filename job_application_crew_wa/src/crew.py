"""
crew.py
-------
Assembles the CrewAI crew with all agents and tasks.
This is where the workflow is defined — tasks run sequentially,
with each agent's output passed to the next.
"""

import os
import yaml
from crewai import Crew, Task, Process
from agents.job_agents import create_all_agents


def load_preferences() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../config/preferences.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def build_job_application_crew() -> Crew:
    """
    Builds the complete job application crew with all tasks defined.
    Returns a ready-to-run Crew object.
    """
    prefs = load_preferences()
    agents = create_all_agents()

    # Extract key preferences for task descriptions
    job_titles = prefs["job_search"]["titles"]
    location = prefs["job_search"]["location"]
    remote_ok = prefs["job_search"]["remote_ok"]
    max_apps = int(os.getenv("MAX_APPLICATIONS_PER_RUN", "5"))
    candidate_name = prefs["candidate"]["name"]
    tailoring_level = prefs["resume_tailoring"]["tailoring_level"]
    cover_letter_tone = prefs["cover_letter"]["tone"]

    # ──────────────────────────────────────────────────────────────────────
    # TASK 1: Search for matching jobs
    # ──────────────────────────────────────────────────────────────────────
    task_search = Task(
        description=f"""
        Search for job openings that match the following criteria:
        
        Job titles to search: {', '.join(job_titles)}
        Location: {location}
        Remote OK: {remote_ok}
        Max applications this run: {max_apps}
        
        For each job title, search for current openings. Return a list of the TOP {max_apps}
        most relevant and promising opportunities. For each job include:
        - Job title
        - Company name  
        - Location
        - Job URL
        - Salary (if listed)
        - A brief description of why this is a good match
        
        Filter out any blacklisted companies and jobs with red-flag keywords.
        Prioritize jobs posted within the last 7 days.
        """,
        expected_output=f"""
        A structured list of exactly {max_apps} (or fewer if not enough are found) 
        job opportunities, each with: title, company, location, URL, salary, and 
        a brief match explanation.
        """,
        agent=agents["job_scout"],
    )

    # ──────────────────────────────────────────────────────────────────────
    # TASK 2: Tailor resume for each job
    # ──────────────────────────────────────────────────────────────────────
    task_tailor_resume = Task(
        description=f"""
        For each job found in the previous task, tailor {candidate_name}'s resume.
        
        Tailoring level: {tailoring_level}
        
        Steps for each job:
        1. Read the base resume using the Read Base Resume tool
        2. Use the Tailor Resume tool with the job title, company, and job description
        3. Produce a tailored version that:
           - Highlights skills and experience most relevant to THIS job
           - Includes keywords from the job description naturally
           - Is ATS-optimized (no tables, graphics, or unusual formatting)
           - Does NOT invent or exaggerate experience
        
        For each job, output:
        - Company and job title
        - The complete tailored resume text
        - A 2-sentence summary of what was changed and why
        """,
        expected_output="""
        For each job: the company name, job title, and complete tailored resume text,
        plus a brief explanation of the key tailoring choices made.
        """,
        agent=agents["resume_tailor"],
        context=[task_search],   # Uses output from job search task
    )

    # ──────────────────────────────────────────────────────────────────────
    # TASK 3: Write cover letters
    # ──────────────────────────────────────────────────────────────────────
    task_cover_letters = Task(
        description=f"""
        Write a personalized cover letter for each job opportunity.
        
        Cover letter style: {cover_letter_tone}
        Candidate: {candidate_name}
        
        For each job:
        1. Use the Cover Letter Writer Tool to get guidelines and company context
        2. Write a compelling, human-sounding cover letter that:
           - Opens with something specific about the company (NOT "I am writing to apply")
           - Highlights the single most relevant achievement from the tailored resume
           - Shows genuine interest in this specific company
           - Closes confidently with contact information
           - Is under 350 words
        
        Output each cover letter clearly labeled with the company and job title.
        """,
        expected_output="""
        For each job: a complete, personalized cover letter (under 350 words) 
        labeled with company name and job title.
        """,
        agent=agents["cover_letter_writer"],
        context=[task_search, task_tailor_resume],
    )

    # ──────────────────────────────────────────────────────────────────────
    # TASK 4: Submit applications and log everything
    # ──────────────────────────────────────────────────────────────────────
    task_apply = Task(
        description=f"""
        For each job, submit the application and log it in the tracking system.
        
        For each job:
        1. Determine the best application method from the job URL:
           - If the job URL contains "mailto:", send an email application
           - If it's a direct application form URL, log as "manual_required" with the URL
           - If it's a job board (LinkedIn, Indeed, Glassdoor), log as "manual_required"
        
        2. For email applications: send the cover letter as the email body with 
           the candidate's contact information
        
        3. For ALL jobs (regardless of method): use the Log Application tool to 
           record: job title, company, URL, method used, and status
        
        4. After all applications, get and display the application statistics.
        
        Important: Never apply to the same URL twice (the tool will catch duplicates).
        """,
        expected_output="""
        A log of all applications attempted, showing:
        - Each job title and company
        - Application method used  
        - Status (applied/manual_required)
        - Final application statistics summary
        """,
        agent=agents["application_agent"],
        context=[task_search, task_tailor_resume, task_cover_letters],
    )

    # ──────────────────────────────────────────────────────────────────────
    # TASK 5: Check email for responses
    # ──────────────────────────────────────────────────────────────────────
    task_monitor = Task(
        description="""
        Check the candidate's email inbox for any responses to previous job applications.
        
        1. Use the Check Email tool to scan the last 14 days of emails
        2. Identify and categorize any job-related emails:
           - Interview requests (URGENT — note these first)
           - Rejections
           - Follow-up/acknowledgment emails
        3. Get current application stats to show the full picture
        4. Create an actionable summary for the candidate
        
        Format the final report as:
        
        🎉 INTERVIEW REQUESTS (if any):
        [list with company, role, what to do next]
        
        📬 OTHER RESPONSES:
        [rejections and follow-ups]
        
        📊 OVERALL STATS:
        [application totals]
        
        ✅ RECOMMENDED NEXT ACTIONS:
        [specific, actionable steps]
        """,
        expected_output="""
        A clear summary report covering: interview requests, rejections, follow-ups,
        overall application stats, and specific recommended next actions for the candidate.
        """,
        agent=agents["response_monitor"],
        context=[task_apply],
    )

    # ──────────────────────────────────────────────────────────────────────
    # Assemble the Crew
    # ──────────────────────────────────────────────────────────────────────
    crew = Crew(
        agents=list(agents.values()),
        tasks=[
            task_search,
            task_tailor_resume,
            task_cover_letters,
            task_apply,
            task_monitor,
        ],
        process=Process.sequential,   # Tasks run in order, each feeding the next
        verbose=True,
        memory=True,                  # Agents remember context across tasks
        embedder={
            "provider": "openai",
            "config": {"model": "text-embedding-3-small"}
        }
    )

    return crew


def build_monitor_only_crew() -> Crew:
    """
    A lightweight crew that ONLY checks email for responses.
    Use this for the periodic monitoring mode (scheduled runs).
    """
    agents = create_all_agents()

    task_monitor_only = Task(
        description="""
        Check the candidate's email for any new job application responses in the last 3 days.
        Categorize them and provide a clear summary with recommended actions.
        Update the applications log with any responses found.
        """,
        expected_output="Summary of new job-related emails and recommended next actions.",
        agent=agents["response_monitor"],
    )

    return Crew(
        agents=[agents["response_monitor"]],
        tasks=[task_monitor_only],
        process=Process.sequential,
        verbose=False,
    )
