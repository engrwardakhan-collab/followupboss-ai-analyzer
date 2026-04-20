# FollowUp Boss AI Lead Analyzer

Automatically analyzes real estate leads in FollowUp Boss using GPT-4o and writes 6 AI insights back to each lead's custom fields.

## What It Does

For every lead it processes, it generates:

| Field | Example |
|---|---|
| AI_Score | `8/10` |
| AI_BuyerType | `Serious Buyer` |
| AI_NextAction | `Call within 24 hours` |
| AI_EmailDraft | Ready-to-send personalized email |
| AI_RiskFactors | `No property views yet` |
| AI_FollowupTime | `ASAP (Follow up today!)` |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/your-username/followupboss-ai-analyzer.git
cd followupboss-ai-analyzer
```

### 2. Install dependencies

```bash
pip install requests openai python-dotenv flask pyngrok
```

### 3. Configure environment variables

```bash
cp script/.env.example script/.env
```

Fill in your credentials in `script/.env`:

```
FOLLOWUP_BOSS_API_KEY=fka_your_api_key_here
FOLLOWUP_BOSS_X_SYSTEM=your_system_name
FOLLOWUP_BOSS_X_SYSTEM_KEY=your_system_key_here
OPENAI_API_KEY=sk-your_openai_key_here
```

**Where to get these:**
- **FUB API Key** → FollowUp Boss → Admin → API
- **X-System / X-System-Key** → Register at https://docs.followupboss.com/reference/registration
- **OpenAI API Key** → https://platform.openai.com/api-keys

### 4. Create custom fields in FollowUp Boss

Create these 6 fields (type: Text) under Admin → Custom Fields:

- `AI_Score`
- `AI_NextAction`
- `AI_EmailDraft`
- `AI_RiskFactors`
- `AI_BuyerType`
- `AI_FollowupTime`

---

## Usage

### Manual mode — analyze leads once

```bash
cd script
python followup_boss_ai_analyzer.py
```

### Server mode — auto-analyze via Make.com

```bash
cd script
python followup_boss_ai_analyzer.py server
```

This starts a web server on port 5000 that Make.com calls whenever a new lead is created in FollowUp Boss.

---

## Make.com Integration (Auto Mode)

To automatically analyze every new lead the moment it's created:

### Step 1 — Start the server

```bash
python followup_boss_ai_analyzer.py server
```

### Step 2 — Expose it with ngrok

```bash
ngrok http 5000
```

Copy the public URL shown (e.g. `https://abc123.ngrok.io`).

### Step 3 — Add HTTP module in Make.com

In your existing Make scenario, click **+** after the **Follow Up Boss → Create a Contact** module and add:

**HTTP → Make a request**

| Field | Value |
|---|---|
| URL | `https://abc123.ngrok.io/analyze` |
| Method | `POST` |
| Body type | `Raw` |
| Content type | `application/json` |
| Body | Map the full FUB contact output from the previous module |

Every new lead will now be automatically scored and enriched within seconds.

---

## Project Structure

```
├── README.md
├── .gitignore
├── SETUP_INSTRUCTIONS.md
├── script/
│   ├── followup_boss_ai_analyzer.py   # Main script
│   ├── .env.example                   # Template — copy to .env and fill in
│   └── .env                           # Your real credentials (git ignored)
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `Authentication failed` | Check FUB API key and X-System registration |
| `Custom field not found` | Verify field names match in FUB Admin → Custom Fields |
| `No leads found` | Check API key has access to leads |
| Make.com can't reach server | Make sure ngrok is running and URL is up to date |
