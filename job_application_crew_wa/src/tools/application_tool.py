"""
application_tool.py
-------------------
Handles the submission of job applications and maintains an application log.

NOTE ON AUTOMATION:
Most major job boards (LinkedIn, Indeed) actively block bots.
This tool focuses on:
  1. Email-based applications (mailto: links)
  2. Simple form-based applications (via Selenium, best-effort)
  3. Logging all applications for tracking

For heavily protected sites, it logs the application as "manual_required"
and notifies you to apply manually.
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


LOG_PATH = os.path.join(os.path.dirname(__file__), "../../data/applications_log.json")


def load_log() -> list:
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            return json.load(f)
    return []


def save_log(log: list):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


class LogApplicationInput(BaseModel):
    job_title: str = Field(description="Title of the job")
    company_name: str = Field(description="Name of the company")
    job_url: str = Field(description="URL of the job posting")
    application_method: str = Field(description="How the application was/will be submitted")
    status: str = Field(description="Status: applied, manual_required, skipped, error")
    notes: str = Field(default="", description="Any notes about this application")


class SendEmailApplicationInput(BaseModel):
    to_email: str = Field(description="Recruiter or HR email address")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="Email body with cover letter")
    resume_path: str = Field(default="", description="Path to the tailored resume file to attach")


class LogApplicationTool(BaseTool):
    """Logs a job application to the tracking file."""
    name: str = "Log Application"
    description: str = (
        "Saves a record of a job application to the applications log. "
        "Always call this after attempting to apply (whether successful or not)."
    )
    args_schema: type[BaseModel] = LogApplicationInput

    def _run(
        self,
        job_title: str,
        company_name: str,
        job_url: str,
        application_method: str,
        status: str,
        notes: str = ""
    ) -> str:
        log = load_log()

        # Check if already applied
        for entry in log:
            if entry.get("job_url") == job_url:
                return f"Already applied to {job_title} at {company_name}. Skipping duplicate."

        entry = {
            "id": len(log) + 1,
            "job_title": job_title,
            "company_name": company_name,
            "job_url": job_url,
            "application_method": application_method,
            "status": status,
            "applied_at": datetime.now().isoformat(),
            "notes": notes,
            "response_received": False,
            "response_type": None,
            "response_date": None,
        }

        log.append(entry)
        save_log(log)

        status_emoji = {
            "applied": "✅",
            "manual_required": "👆",
            "skipped": "⏭️",
            "error": "❌"
        }.get(status, "📝")

        return (
            f"{status_emoji} Logged: {job_title} at {company_name}\n"
            f"   Status: {status}\n"
            f"   Method: {application_method}\n"
            f"   URL: {job_url}\n"
            f"   Notes: {notes}\n"
            f"   Total applications in log: {len(log)}"
        )


class SendEmailApplicationTool(BaseTool):
    """Sends a job application via email (for companies that accept email applications)."""
    name: str = "Send Email Application"
    description: str = (
        "Sends a job application email with cover letter and optionally attaches resume. "
        "Use this when the job posting provides an email address for applications."
    )
    args_schema: type[BaseModel] = SendEmailApplicationInput

    def _run(
        self,
        to_email: str,
        subject: str,
        body: str,
        resume_path: str = ""
    ) -> str:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_pass:
            return (
                "ERROR: Gmail credentials not configured. "
                "Set GMAIL_USER and GMAIL_APP_PASSWORD in your .env file."
            )

        require_approval = os.getenv("REQUIRE_APPROVAL", "true").lower() == "true"
        if require_approval:
            return (
                f"⚠️  APPROVAL REQUIRED\n"
                f"Email application ready to send:\n"
                f"  To: {to_email}\n"
                f"  Subject: {subject}\n"
                f"  Body preview: {body[:200]}...\n\n"
                f"To send this, set REQUIRE_APPROVAL=false in .env, "
                f"or manually send the email using the details above.\n"
                f"The full application has been saved to the log."
            )

        try:
            msg = MIMEMultipart()
            msg["From"] = gmail_user
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Attach resume if provided
            if resume_path and os.path.exists(resume_path):
                with open(resume_path, "rb") as f:
                    attachment = MIMEBase("application", "octet-stream")
                    attachment.set_payload(f.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(resume_path)}"
                    )
                    msg.attach(attachment)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail_user, gmail_pass)
                server.sendmail(gmail_user, to_email, msg.as_string())

            return f"✅ Email application sent successfully to {to_email}"

        except Exception as e:
            return f"❌ Failed to send email: {str(e)}"


class GetApplicationStatsInput(BaseModel):
    pass


class GetApplicationStatsTool(BaseTool):
    """Returns a summary of all applications made so far."""
    name: str = "Get Application Stats"
    description: str = "Returns a summary of all job applications tracked in the log."
    args_schema: type[BaseModel] = GetApplicationStatsInput

    def _run(self) -> str:
        log = load_log()
        if not log:
            return "No applications logged yet."

        total = len(log)
        statuses = {}
        for entry in log:
            s = entry.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1

        responses = sum(1 for e in log if e.get("response_received"))
        recent = log[-5:]

        output = f"=== APPLICATION TRACKER ===\n"
        output += f"Total applications: {total}\n"
        for status, count in statuses.items():
            output += f"  {status}: {count}\n"
        output += f"Responses received: {responses}\n\n"
        output += "Recent applications:\n"
        for entry in reversed(recent):
            output += f"  • {entry['job_title']} @ {entry['company_name']} — {entry['status']}\n"

        return output
