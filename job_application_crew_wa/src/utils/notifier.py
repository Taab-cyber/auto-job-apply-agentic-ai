"""
notifier.py
-----------
Sends WhatsApp notifications using Meta's official WhatsApp Cloud API.
Uses only the 'requests' library — no third-party WhatsApp packages needed.

HOW TO SET UP (follow the guide in README or the step-by-step below):
  WHATSAPP_TOKEN       — your temporary or permanent access token from Meta
  WHATSAPP_PHONE_ID    — your WhatsApp Business phone number ID from Meta
  WHATSAPP_TO          — the recipient number in international format e.g. 919876543210
"""

import os
import requests


def notify(message: str, urgent: bool = False):
    """
    Send a WhatsApp notification via Meta Cloud API.
    Falls back to console print if credentials are not configured.
    """
    prefix = "🚨 *URGENT*: " if urgent else "📢 "
    full_message = f"{prefix}{message}"

    if _send_whatsapp(full_message):
        return

    # Fallback: print to console
    print(f"\n{'='*50}")
    print("📬 NOTIFICATION (WhatsApp not configured — printing here):")
    print(full_message)
    print(f"{'='*50}\n")


def _send_whatsapp(message: str) -> bool:
    """
    Calls Meta's WhatsApp Cloud API directly using requests.
    Docs: https://developers.facebook.com/docs/whatsapp/cloud-api/messages
    """
    token    = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")
    to       = os.getenv("WHATSAPP_TO")

    if not all([token, phone_id, to]):
        return False

    url = f"https://graph.facebook.com/v19.0/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)

        if response.status_code == 200:
            print("[Notifier] ✅ WhatsApp message sent successfully")
            return True
        else:
            err = response.json()
            print(f"[Notifier] ⚠️  Meta API error {response.status_code}: {err}")
            return False

    except Exception as e:
        print(f"[Notifier] ⚠️  Failed to send WhatsApp: {e}")
        return False


# ── Helpers used throughout the crew ────────────────────────────────────────

def notify_interview(company: str, job_title: str, details: str = ""):
    msg = (
        f"🎉 *INTERVIEW REQUEST!*\n\n"
        f"Company: {company}\n"
        f"Role: {job_title}\n"
        f"{details}\n\n"
        f"Check your email and reply ASAP! ⚡"
    )
    notify(msg, urgent=True)


def notify_rejection(company: str, job_title: str):
    notify(f"Job update: {company} ({job_title}) — Not moving forward. Keep going! 💪")


def notify_application_sent(company: str, job_title: str, method: str):
    notify(f"✅ Applied: *{job_title}* at *{company}* (via {method})")


def notify_summary(total: int, applied: int, manual_needed: int):
    msg = (
        f"📊 *Application Session Complete*\n\n"
        f"Jobs found: {total}\n"
        f"Applied automatically: {applied}\n"
        f"Need your manual application: {manual_needed}\n\n"
        f"Check your applications log for details."
    )
    notify(msg)
