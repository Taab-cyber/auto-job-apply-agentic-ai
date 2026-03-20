"""
job_agents.py
-------------
Defines all five AI agents in the job application crew.
Each agent has a specific role, goal, and set of tools.
"""

import os
import yaml
from crewai import Agent
from langchain_openai import ChatOpenAI

# Import all tools
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.job_search_tool import JobSearchTool
from tools.resume_tool import ReadResumeTool, ResumeTailorTool
from tools.cover_letter_tool import CoverLetterTool
from tools.application_tool import (
    LogApplicationTool,
    SendEmailApplicationTool,
    GetApplicationStatsTool
)
from tools.email_monitor_tool import EmailMonitorTool


def load_agent_config() -> dict:
    config_path = os.path.join(os.path.dirname(__file__), "../../config/agents.yaml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def create_llm():
    """Create the LLM instance used by all agents."""
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        temperature=0.3,   # Low temperature = more consistent, focused output
        api_key=os.getenv("OPENAI_API_KEY")
    )


def create_all_agents() -> dict:
    """
    Creates and returns all five agents.
    Returns a dict so they can be referenced by name.
    """
    config = load_agent_config()
    llm = create_llm()

    # ── Agent 1: Job Scout ──────────────────────────────────────────────────
    job_scout = Agent(
        role=config["job_scout"]["role"],
        goal=config["job_scout"]["goal"],
        backstory=config["job_scout"]["backstory"],
        tools=[JobSearchTool()],
        llm=llm,
        verbose=True,
        memory=True,
        max_iter=5,           # Max iterations before giving up
        allow_delegation=False,
    )

    # ── Agent 2: Resume Tailor ──────────────────────────────────────────────
    resume_tailor = Agent(
        role=config["resume_tailor"]["role"],
        goal=config["resume_tailor"]["goal"],
        backstory=config["resume_tailor"]["backstory"],
        tools=[ReadResumeTool(), ResumeTailorTool()],
        llm=llm,
        verbose=True,
        memory=True,
        max_iter=3,
        allow_delegation=False,
    )

    # ── Agent 3: Cover Letter Writer ────────────────────────────────────────
    cover_letter_writer = Agent(
        role=config["cover_letter_writer"]["role"],
        goal=config["cover_letter_writer"]["goal"],
        backstory=config["cover_letter_writer"]["backstory"],
        tools=[CoverLetterTool()],
        llm=llm,
        verbose=True,
        memory=True,
        max_iter=3,
        allow_delegation=False,
    )

    # ── Agent 4: Application Agent ──────────────────────────────────────────
    application_agent = Agent(
        role=config["application_agent"]["role"],
        goal=config["application_agent"]["goal"],
        backstory=config["application_agent"]["backstory"],
        tools=[
            LogApplicationTool(),
            SendEmailApplicationTool(),
            GetApplicationStatsTool(),
        ],
        llm=llm,
        verbose=True,
        memory=True,
        max_iter=5,
        allow_delegation=False,
    )

    # ── Agent 5: Response Monitor ───────────────────────────────────────────
    response_monitor = Agent(
        role=config["response_monitor"]["role"],
        goal=config["response_monitor"]["goal"],
        backstory=config["response_monitor"]["backstory"],
        tools=[EmailMonitorTool(), GetApplicationStatsTool()],
        llm=llm,
        verbose=True,
        memory=True,
        max_iter=3,
        allow_delegation=False,
    )

    return {
        "job_scout": job_scout,
        "resume_tailor": resume_tailor,
        "cover_letter_writer": cover_letter_writer,
        "application_agent": application_agent,
        "response_monitor": response_monitor,
    }
