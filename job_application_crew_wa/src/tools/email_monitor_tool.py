"""
email_monitor_tool.py
---------------------
Monitors the candidate's Gmail inbox for job application responses.
Categorizes responses as: interview_request, rejection, follow_up, or unknown.
Updates the applications log and sends notifications.
"""

import os
import imaplib
import email
import json
from datetime import datetime, timedelta
from email.header import decode_header
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


LOG_PATH = os.path.join(os.path.dirname(__file__), "../../data/applications_log.json")

# Keywords that suggest different response types
INTERVIEW_KEYWORDS = [
    "interview", "schedule a call", "phone screen", "video call",
    "we'd like to speak", "move forward", "next steps", "opportunity to chat",
    "impressed with your", "excited to learn more"
]

REJECTION_KEYWORDS = [
    "not moving forward", "will not be moving", "decided to move",
    "other candidates", "position has been filled", "not a match",
    "unfortunately", "we regret", "not selected", "keep your resume on file"
]

FOLLOWUP_KEYWORDS = [
    "received your application", "application is under review",
    "we will be in touch", "thank you for applying", "reviewing candidates"
]


class CheckEmailInput(BaseModel):
    days_back: int = Field(
        default=7,
        description="How many days back to check for emails"
    )


class EmailMonitorTool(BaseTool):
    """
    Checks Gmail for job application-related responses.
    Returns a summary of any new emails found and updates the application log.
    """
    name: str = "Check Email for Job Responses"
    description: str = (
        "Monitors Gmail inbox for responses to job applications. "
        "Categorizes them as interview requests, rejections, or follow-ups. "
        "Updates the application log and returns a summary."
    )
    args_schema: type[BaseModel] = CheckEmailInput

    def _run(self, days_back: int = 7) -> str:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_pass:
            return (
                "Email monitoring not configured. "
                "Add GMAIL_USER and GMAIL_APP_PASSWORD to your .env file."
            )

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(gmail_user, gmail_pass)
            mail.select("inbox")

            # Search for emails from the past N days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
            _, message_ids = mail.search(None, f'SINCE "{since_date}"')

            emails = []
            for msg_id in message_ids[0].split():
                _, msg_data = mail.fetch(msg_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = self._decode_header(msg["Subject"] or "")
                sender = msg.get("From", "")
                body = self._get_body(msg)

                if self._is_job_related(subject, body):
                    response_type = self._classify_response(subject, body)
                    emails.append({
                        "subject": subject,
                        "sender": sender,
                        "response_type": response_type,
                        "body_preview": body[:300]
                    })

            mail.logout()

            if not emails:
                return f"No new job-related emails found in the last {days_back} days."

            # Update application log
            self._update_log(emails)

            # Format response
            output = f"📬 Found {len(emails)} job-related email(s):\n\n"
            for e in emails:
                icon = {"interview_request": "🎉", "rejection": "😔", "follow_up": "📋"}.get(
                    e["response_type"], "📧"
                )
                output += f"{icon} [{e['response_type'].upper()}]\n"
                output += f"   From: {e['sender']}\n"
                output += f"   Subject: {e['subject']}\n"
                output += f"   Preview: {e['body_preview'][:150]}...\n\n"

            return output

        except Exception as e:
            return f"Error checking email: {str(e)}\nMake sure you're using an App Password, not your regular Gmail password."

    def _decode_header(self, header: str) -> str:
        decoded = decode_header(header)
        parts = []
        for part, encoding in decoded:
            if isinstance(part, bytes):
                parts.append(part.decode(encoding or "utf-8", errors="replace"))
            else:
                parts.append(part)
        return " ".join(parts)

    def _get_body(self, msg) -> str:
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
                    except Exception:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
            except Exception:
                pass
        return body.lower()

    def _is_job_related(self, subject: str, body: str) -> bool:
        """Check if an email is related to a job application."""
        job_signals = [
            "application", "position", "role", "job", "interview",
            "recruiter", "hiring", "opportunity", "candidate"
        ]
        text = (subject + " " + body).lower()
        return any(signal in text for signal in job_signals)

    def _classify_response(self, subject: str, body: str) -> str:
        """Classify the type of response."""
        text = (subject + " " + body).lower()

        if any(kw in text for kw in INTERVIEW_KEYWORDS):
            return "interview_request"
        elif any(kw in text for kw in REJECTION_KEYWORDS):
            return "rejection"
        elif any(kw in text for kw in FOLLOWUP_KEYWORDS):
            return "follow_up"
        else:
            return "unknown"

    def _update_log(self, emails: list):
        """Update the applications log with response information."""
        if not os.path.exists(LOG_PATH):
            return

        with open(LOG_PATH, "r") as f:
            log = json.load(f)

        for entry in log:
            company = entry.get("company_name", "").lower()
            for email_data in emails:
                if company and company in email_data["sender"].lower():
                    entry["response_received"] = True
                    entry["response_type"] = email_data["response_type"]
                    entry["response_date"] = datetime.now().isoformat()

        with open(LOG_PATH, "w") as f:
            json.dump(log, f, indent=2)
