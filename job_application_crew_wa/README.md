# 🤖 AI Job Application Crew

An agentic AI system built with [CrewAI](https://crewai.com) that automatically:
- 🔍 Searches for jobs matching your preferences across LinkedIn, Indeed, and more
- 📄 Tailors your resume for each job posting
- ✉️ Writes custom cover letters
- 📬 Applies to jobs on your behalf
- 🔔 Monitors your email for responses and notifies you

---

## 🏗️ Project Structure

```
job_application_crew/
├── README.md
├── requirements.txt
├── .env.example                    # Copy to .env and fill in your keys
├── config/
│   ├── preferences.yaml            # YOUR job search preferences go here
│   └── agents.yaml                 # Agent configurations
├── src/
│   ├── main.py                     # Entry point — run this!
│   ├── crew.py                     # Crew assembly and orchestration
│   ├── agents/
│   │   └── job_agents.py           # All agent definitions
│   ├── tools/
│   │   ├── job_search_tool.py      # Searches job boards
│   │   ├── resume_tool.py          # Reads & tailors resume
│   │   ├── cover_letter_tool.py    # Generates cover letters
│   │   ├── application_tool.py     # Submits applications
│   │   └── email_monitor_tool.py   # Monitors inbox for replies
│   └── utils/
│       ├── logger.py               # Logs all applications
│       └── notifier.py             # Sends you notifications
├── data/
│   ├── resumes/
│   │   └── base_resume.txt         # Paste your resume content here
│   └── applications_log.json       # Auto-created; tracks all applications
└── logs/
    └── crew.log                    # Runtime logs
```

---

## 🚀 Setup (Step by Step for Beginners)

### 1. Prerequisites
- Python 3.10 or higher
- A terminal / command prompt

### 2. Clone / Download this project
```bash
# Navigate to where you want the project
cd ~/Desktop
# If using git:
git clone <your-repo-url>
cd job_application_crew
```

### 3. Create a virtual environment (recommended)
```bash
python -m venv venv

# Activate it:
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Set up your API keys
```bash
cp .env.example .env
```
Now open `.env` in a text editor and fill in:
- `OPENAI_API_KEY` — from https://platform.openai.com
- `SERPER_API_KEY` — from https://serper.dev (free tier available, for Google job search)
- `GMAIL_USER` and `GMAIL_APP_PASSWORD` — your Gmail address + an App Password (not your regular password). See: https://support.google.com/accounts/answer/185833

### 6. Add your resume
Open `data/resumes/base_resume.txt` and paste your full resume as plain text.

### 7. Set your job preferences
Open `config/preferences.yaml` and customize:
- Job titles you want
- Location / remote preference
- Salary range
- Skills to highlight
- Companies to avoid

### 8. Run the crew!
```bash
python src/main.py
```

---

## 🤖 The Agents

| Agent | Role |
|-------|------|
| **Job Scout** | Searches job boards for openings matching your preferences |
| **Resume Tailor** | Adapts your base resume to match each job's keywords and requirements |
| **Cover Letter Writer** | Writes a personalized cover letter for each application |
| **Application Agent** | Submits the application (where automation is possible) |
| **Response Monitor** | Checks your email for replies and sends you notifications |

---

## ⚠️ Important Notes

- **Not all job boards allow automation.** LinkedIn and Indeed have anti-bot measures. This tool works best with job boards that have public application URLs or email-based applications.
- **Always review** tailored resumes before they go out. Set `REQUIRE_APPROVAL=true` in `.env` to approve each application manually.
- **This is a starting point.** You'll likely need to customize the application tool per job board.

---

## 📋 Configuration Reference

See `config/preferences.yaml` for all options with inline comments.
