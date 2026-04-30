# FollowUp Boss AI Lead Analyzer

## What This Project Does
Automatically analyzes real estate leads in FollowUp Boss CRM using GPT-4o. When a new lead is created, it fetches the full lead data, sends it to GPT-4o for analysis, and writes 6 AI insights back to custom fields in FollowUp Boss — all within seconds.

## Architecture
- **script/followup_boss_ai_analyzer.py** — Main application (single file)
- **Procfile** — Railway deployment: `web: python script/followup_boss_ai_analyzer.py server`
- **runtime.txt** — Python 3.11
- **requirements.txt** (root) — Flask, OpenAI, Requests, python-dotenv
- **script/.env** — Real credentials (git ignored)
- **script/.env.example** — Credentials template

## Running the App

### Manual mode (analyze existing leads once)
```bash
cd script
python followup_boss_ai_analyzer.py
```

### Server mode (listen for Make.com webhooks)
```bash
cd script
python followup_boss_ai_analyzer.py server
```
Starts Flask on PORT env var (default 5000).

## Environment Variables (script/.env)
```
FOLLOWUP_BOSS_API_KEY=      # From FUB Admin → API
FOLLOWUP_BOSS_X_SYSTEM=     # Registered system name
FOLLOWUP_BOSS_X_SYSTEM_KEY= # Registered system key
OPENAI_API_KEY=              # No leading spaces
```

## API Endpoints
- `POST /analyze` — Receives lead from Make.com, fetches full lead from FUB, runs GPT-4o analysis, updates FUB custom fields
- `GET /health` — Returns `{"status": "running"}`

## Make.com Integration
1. Make scenario triggers on new FUB contact creation
2. HTTP module POSTs the contact bundle to `/analyze`
3. Script ignores Make's partial data — fetches full lead directly from FUB API using the lead ID
4. GPT-4o receives the complete lead JSON (all fields, notes, custom fields)
5. 6 insights written back to FUB

## 6 Custom Fields Written to FUB
| Field | API Name |
|---|---|
| AI_Score | customAIScore |
| AI_NextAction | customAINextAction |
| AI_EmailDraft | customAIEmailDraft |
| AI_RiskFactors | customAIRiskFactors |
| AI_BuyerType | customAIBuyerType |
| AI_FollowupTime | customAIFollowupTime |

## Deployment (Railway)
- Live URL: `https://followupboss-ai-analyzer-production.up.railway.app`
- Auto-deploys on every push to `master`
- PORT env var set automatically by Railway
- All 4 env vars must be set in Railway → Variables tab

## GitHub
- Repo: `https://github.com/engrwardakhan-collab/followupboss-ai-analyzer`
- Branch: master
- .env is git-ignored — never commit credentials

## Key Implementation Notes
- FUB custom fields are at the ROOT level of the lead object (e.g. `customNotes`, `customMoveInDate`) — NOT nested under `customFields`
- Make.com "Create a Contact" output only returns basic fields — script always re-fetches full lead from FUB using `GET /v1/people/{id}?fields=allFields`
- AI fields are stripped before sending to GPT-4o to avoid bias from previous scores
- GPT-4o receives the entire lead JSON — no field filtering
