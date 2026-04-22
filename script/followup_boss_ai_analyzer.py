"""
FollowUp Boss AI Lead Analyzer
Generates 6 AI insights per lead: Score, Next Action, Email Draft, Risk Factors, Buyer Type, Follow-up Time

Usage:
  python followup_boss_ai_analyzer.py          -> runs on all leads manually
  python followup_boss_ai_analyzer.py server   -> starts web server for Make.com
"""

import os
import sys
import json
import base64
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class FollowUpBossAnalyzer:
    def __init__(self):
        self.fub_api_key = os.getenv('FOLLOWUP_BOSS_API_KEY')
        self.fub_x_system = os.getenv('FOLLOWUP_BOSS_X_SYSTEM', 'arterra-1')
        self.fub_x_system_key = os.getenv('FOLLOWUP_BOSS_X_SYSTEM_KEY')
        self.fub_base_url = 'https://api.followupboss.com/v1'

        self.openai_client = OpenAI()

        self.custom_fields = {
            'AI_Score': 'customAIScore',
            'AI_NextAction': 'customAINextAction',
            'AI_EmailDraft': 'customAIEmailDraft',
            'AI_RiskFactors': 'customAIRiskFactors',
            'AI_BuyerType': 'customAIBuyerType',
            'AI_FollowupTime': 'customAIFollowupTime',
        }

        self.session = requests.Session()
        self._setup_auth_headers()

    def _setup_auth_headers(self):
        auth_string = base64.b64encode(f"{self.fub_api_key}:".encode()).decode()
        self.headers = {
            'X-System': self.fub_x_system,
            'X-System-Key': self.fub_x_system_key,
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }

    def fetch_leads(self, limit=10):
        print(f"\n[>>] Fetching leads from FollowUp Boss...")
        try:
            response = self.session.get(
                f'{self.fub_base_url}/people',
                headers=self.headers,
                params={'fields': 'allFields', 'limit': limit}
            )
            response.raise_for_status()
            data = response.json()
            leads = data.get('people', [])
            print(f"[OK] Found {len(leads)} leads")
            return leads
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Error fetching leads: {e}")
            return []

    def analyze_lead_with_gpt(self, lead):
        lead_name = f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip()
        lead_email = lead.get('emails', [{}])[0].get('value', 'N/A') if lead.get('emails') else 'N/A'
        lead_phone = lead.get('phones', [{}])[0].get('value', 'N/A') if lead.get('phones') else 'N/A'

        # Strip existing AI fields so GPT doesn't get confused by old values
        lead_clean = {k: v for k, v in lead.items() if not k.startswith('customAI')}

        prompt = f"""
You are a real estate CRM analyst. Below is the complete data for a lead. Analyze ALL fields —
especially notes, custom fields, move-in date, urgency signals — and return 6 AI insights.

FULL LEAD DATA:
{json.dumps(lead_clean, indent=2)}

Based on everything above, return ONLY a JSON object (no other text):

{{
  "ai_score": <number 1-10>,
  "ai_score_reasoning": "<why this score, referencing specific data from the lead>",
  "next_action": "<specific actionable next step based on their needs>",
  "email_draft": "<2-3 sentence personalized email using their name, unit type, move-in date, and notes>",
  "risk_factors": "<any red flags or 'None identified'>",
  "buyer_type": "<one of: Serious Buyer, Window Shopper, Just Curious, Investor, First-time Buyer>",
  "followup_time": "<one of: ASAP (Follow up today!), This week, In 2 weeks, Re-engage in 30 days>"
}}

SCORING RULES:
- Notes/custom fields saying urgent, ASAP, moving soon, specific move-in date → score 8-10, Serious Buyer, ASAP
- Some engagement, moderate interest → score 6-7, This week
- No urgency, vague interest → score 1-5
"""

        print(f"  [AI] Analyzing {lead_name} with GPT-4o...")

        try:
            message = self.openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.choices[0].message.content.strip()

            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            else:
                json_str = response_text

            insights = json.loads(json_str)
            print(f"  [OK] Analysis complete for {lead_name}")
            return insights

        except json.JSONDecodeError as e:
            print(f"  [ERROR] Failed to parse AI response: {e}")
            return None
        except Exception as e:
            print(f"  [ERROR] Error analyzing lead: {e}")
            return None

    def update_lead_with_insights(self, lead_id, insights):
        if not insights:
            return False

        update_data = {
            self.custom_fields['AI_Score']: f"{insights.get('ai_score', 'N/A')}/10",
            self.custom_fields['AI_NextAction']: insights.get('next_action', ''),
            self.custom_fields['AI_EmailDraft']: insights.get('email_draft', ''),
            self.custom_fields['AI_RiskFactors']: insights.get('risk_factors', ''),
            self.custom_fields['AI_BuyerType']: insights.get('buyer_type', ''),
            self.custom_fields['AI_FollowupTime']: insights.get('followup_time', ''),
        }

        print(f"  [>>] Updating lead {lead_id} with AI insights...")

        try:
            response = self.session.put(
                f'{self.fub_base_url}/people/{lead_id}',
                headers=self.headers,
                json=update_data
            )
            response.raise_for_status()
            print(f"  [OK] Lead updated successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"  [WARN] Error updating lead: {e}")
            return False

    def fetch_full_lead(self, lead_id):
        """Fetch complete lead data from FUB including notes and all custom fields"""
        try:
            response = self.session.get(
                f'{self.fub_base_url}/people/{lead_id}',
                headers=self.headers,
                params={'fields': 'allFields'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] Failed to fetch full lead: {e}")
            return None

    def process_single_lead(self, lead):
        """Process one lead received from Make.com — always fetches full data from FUB"""
        lead_id = lead.get('id')
        lead_name = f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip()
        print(f"\n[>>] Processing lead from Make: {lead_name} (ID: {lead_id})")

        # Fetch full lead data from FUB (Make only sends basic fields)
        full_lead = self.fetch_full_lead(lead_id)
        if not full_lead:
            print(f"  [WARN] Could not fetch full lead, using Make data instead")
            full_lead = lead

        # Log exactly what we received from FUB
        print(f"  [DEBUG] Full lead data from FUB: {json.dumps(full_lead, indent=2)}")

        insights = self.analyze_lead_with_gpt(full_lead)
        if insights:
            self.update_lead_with_insights(lead_id, insights)
            return insights
        return None

    def run_analysis_on_all_leads(self, limit=5):
        print("\n" + "="*60)
        print("FOLLOWUP BOSS AI LEAD ANALYZER")
        print("Analyzing: Lead Score, Next Action, Email Draft,")
        print("           Risk Factors, Buyer Type, Follow-up Time")
        print("="*60)

        leads = self.fetch_leads(limit=limit)
        if not leads:
            print("No leads found. Check your API key and account.")
            return

        results = []
        for i, lead in enumerate(leads, 1):
            lead_id = lead.get('id')
            lead_name = f"{lead.get('firstName', '')} {lead.get('lastName', '')}".strip()
            print(f"\n[{i}/{len(leads)}] Processing: {lead_name}")
            insights = self.analyze_lead_with_gpt(lead)
            if insights:
                self.update_lead_with_insights(lead_id, insights)
                results.append({'name': lead_name, 'id': lead_id, 'insights': insights})

        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)

        for result in results:
            print(f"\n>> {result['name']}")
            insights = result['insights']
            print(f"  Score: {insights.get('ai_score')}/10 - {insights.get('ai_score_reasoning')}")
            print(f"  Buyer Type: {insights.get('buyer_type')}")
            print(f"  Risk Factors: {insights.get('risk_factors')}")
            print(f"  Follow-up: {insights.get('followup_time')}")
            print(f"  Next Action: {insights.get('next_action')}")
            print(f"  Email: \"{insights.get('email_draft')}\"")

        return results


# ── Web server for Make.com ──────────────────────────────────────────────────

def start_server():
    from flask import Flask, request, jsonify

    app = Flask(__name__)
    analyzer = FollowUpBossAnalyzer()

    @app.route('/analyze', methods=['POST'])
    def analyze():
        data = request.get_json(force=True)

        # Make sends the FUB contact object directly
        # It may be wrapped in a list (Make sometimes sends arrays)
        if isinstance(data, list):
            lead = data[0]
        else:
            lead = data

        if not lead or not lead.get('id'):
            return jsonify({'error': 'No lead data or missing id'}), 400

        insights = analyzer.process_single_lead(lead)

        if insights:
            return jsonify({'status': 'success', 'lead_id': lead.get('id'), 'insights': insights}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Analysis failed'}), 500

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({'status': 'running'}), 200

    print("\n" + "="*60)
    print("FOLLOWUP BOSS AI ANALYZER - SERVER MODE")
    print("Listening for leads from Make.com...")
    print("Endpoint: POST http://localhost:5000/analyze")
    print("="*60)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        start_server()
    else:
        analyzer = FollowUpBossAnalyzer()
        analyzer.run_analysis_on_all_leads(limit=1)

if __name__ == "__main__":
    main()
