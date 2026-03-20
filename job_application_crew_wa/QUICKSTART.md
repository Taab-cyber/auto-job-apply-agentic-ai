# ⚡ Quickstart Cheat Sheet

## First time? Do these 5 things:

```
1.  pip install -r requirements.txt
2.  cp .env.example .env          → open .env, add your OPENAI_API_KEY
3.  Get free Serper key at serper.dev → add to .env as SERPER_API_KEY  
4.  Paste your resume into data/resumes/base_resume.txt
5.  Edit config/preferences.yaml  → set your name, job titles, location
```

## Then run it:

```bash
# Full run (search jobs → tailor resume → write cover letters → apply → check email)
python src/main.py

# Just check email for responses
python src/main.py --monitor

# See your application stats
python src/main.py --stats

# Run on autopilot (daily search + hourly email checks)
python src/main.py --schedule
```

## Want notifications on your phone?

1. Open Telegram → search for **@BotFather** → `/newbot` → copy the token
2. Message your new bot once, then visit:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Copy your `chat_id` from the response
3. Add both to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   ```

## Safety switch (IMPORTANT):

In `.env`, keep this set to `true` until you trust the system:
```
REQUIRE_APPROVAL=true
```
With this on, the crew will prepare everything but won't send emails without your OK.

## Files to know:

| File | What it does |
|------|-------------|
| `config/preferences.yaml` | Your job search settings — edit this! |
| `data/resumes/base_resume.txt` | Your resume — paste it here |
| `data/applications_log.json` | Auto-updated tracker of all applications |
| `.env` | Your API keys — never share this file |
