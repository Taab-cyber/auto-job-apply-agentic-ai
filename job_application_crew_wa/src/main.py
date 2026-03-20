"""
main.py
-------
Entry point for the Job Application Crew.
Run this file to start the job hunting process.

Usage:
    python src/main.py              # Full run: search, apply, check email
    python src/main.py --monitor    # Only check email for responses
    python src/main.py --stats      # Show application stats only
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.logger import get_logger
from utils.notifier import notify_summary, notify

logger = get_logger("Main")

LOG_PATH = os.path.join(os.path.dirname(__file__), "../data/applications_log.json")


def print_banner():
    """Print a welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════╗
║           🤖 AI Job Application Crew                     ║
║           Powered by CrewAI + GPT-4o                     ║
╠══════════════════════════════════════════════════════════╣
║  Agents: Job Scout • Resume Tailor • Cover Letter        ║
║          Application Agent • Response Monitor            ║
╚══════════════════════════════════════════════════════════╝
""")


def check_setup() -> bool:
    """
    Verify that the necessary configuration is in place before running.
    Returns True if OK, False if setup is incomplete.
    """
    issues = []

    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        issues.append("❌ OPENAI_API_KEY not set in .env")

    # Check Serper API key
    if not os.getenv("SERPER_API_KEY"):
        issues.append("⚠️  SERPER_API_KEY not set — job search will use mock data")

    # Check resume exists
    resume_path = os.path.join(os.path.dirname(__file__), "../data/resumes/base_resume.txt")
    if not os.path.exists(resume_path) or os.path.getsize(resume_path) < 100:
        issues.append("❌ Resume not found or too short — add content to data/resumes/base_resume.txt")

    # Check preferences are customized
    prefs_path = os.path.join(os.path.dirname(__file__), "../config/preferences.yaml")
    with open(prefs_path) as f:
        content = f.read()
    if "Your Full Name" in content:
        issues.append("⚠️  Please update your name in config/preferences.yaml")

    if issues:
        print("\n🔧 SETUP CHECKLIST:")
        for issue in issues:
            print(f"   {issue}")

        # Fatal issues block the run
        fatal = [i for i in issues if i.startswith("❌")]
        if fatal:
            print("\n⛔ Fix the ❌ issues above before running.\n")
            return False
        else:
            print("\n✅ No fatal issues — proceeding with warnings.\n")

    return True


def show_stats():
    """Display current application statistics."""
    if not os.path.exists(LOG_PATH):
        print("No applications logged yet.")
        return

    with open(LOG_PATH, "r") as f:
        log = json.load(f)

    if not log:
        print("No applications logged yet.")
        return

    total = len(log)
    statuses = {}
    responses = []
    
    for entry in log:
        s = entry.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
        if entry.get("response_received"):
            responses.append(entry)

    print(f"\n📊 APPLICATION STATISTICS")
    print(f"{'─'*40}")
    print(f"Total applications logged: {total}")
    for status, count in statuses.items():
        print(f"  {status}: {count}")
    print(f"\nResponses received: {len(responses)}")

    if responses:
        print("\nResponse details:")
        for r in responses:
            icon = "🎉" if r["response_type"] == "interview_request" else "😔"
            print(f"  {icon} {r['company_name']} — {r['response_type']} on {r.get('response_date', 'N/A')[:10]}")

    print(f"\n📋 Recent applications:")
    for entry in log[-10:]:
        date = entry.get("applied_at", "")[:10]
        print(f"  • [{date}] {entry['job_title']} @ {entry['company_name']} — {entry['status']}")


def run_full_crew():
    """Run the complete job application crew."""
    from crew import build_job_application_crew

    logger.info("Starting full job application crew run")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    crew = build_job_application_crew()
    
    print("\n🚀 Starting crew run...\n")
    print("The crew will now:")
    print("  1. 🔍 Search for matching jobs")
    print("  2. 📄 Tailor your resume for each job")
    print("  3. ✉️  Write custom cover letters")
    print("  4. 📬 Apply (or flag for manual application)")
    print("  5. 📧 Check email for any previous responses")
    print("\nThis may take 5-15 minutes depending on the number of jobs.\n")

    result = crew.kickoff()

    print("\n" + "="*60)
    print("✅ CREW RUN COMPLETE")
    print("="*60)
    print(result)

    # Show final stats
    show_stats()

    # Send completion notification
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH) as f:
                log = json.load(f)
            applied = sum(1 for e in log if e.get("status") == "applied")
            manual = sum(1 for e in log if e.get("status") == "manual_required")
            notify_summary(total=len(log), applied=applied, manual_needed=manual)
    except Exception:
        pass

    return result


def run_monitor_only():
    """Only check email for responses."""
    from crew import build_monitor_only_crew

    logger.info("Running email monitor check")
    crew = build_monitor_only_crew()
    
    print("\n📧 Checking email for job application responses...\n")
    result = crew.kickoff()
    
    print("\n" + "="*60)
    print("✅ MONITOR CHECK COMPLETE")
    print("="*60)
    print(result)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="AI Job Application Crew — Automates your job search"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Only check email for responses (no new applications)"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show application statistics and exit"
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run on a schedule: full run daily, email check every hour"
    )

    args = parser.parse_args()
    print_banner()

    if args.stats:
        show_stats()
        return

    if not check_setup():
        return

    if args.monitor:
        run_monitor_only()

    elif args.schedule:
        import schedule
        import time

        print("⏰ Running in scheduled mode:")
        print("   Full job search: daily at 9:00 AM")
        print("   Email check: every 60 minutes")
        print("   Press Ctrl+C to stop\n")

        schedule.every().day.at("09:00").do(run_full_crew)
        schedule.every(int(os.getenv("EMAIL_CHECK_INTERVAL", "60"))).minutes.do(run_monitor_only)

        # Run immediately on start
        run_full_crew()

        while True:
            schedule.run_pending()
            time.sleep(60)

    else:
        # Default: full run
        run_full_crew()


if __name__ == "__main__":
    main()
