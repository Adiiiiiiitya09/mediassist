import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

SYSTEM = 'You are a medical scribe. Return ONLY raw JSON. No preamble, no fences.'

PROMPT = '''Extract structured data from this transcript. Return only this JSON:
{
  "chief_complaint": "string",
  "symptoms": [{
    "name": "string",
    "type": "sharp/dull/throbbing/burning/pressure",
    "severity": 1-10,
    "duration": "string",
    "triggers": [],
    "relieving_factors": []
  }],
  "associated_symptoms": ["string"],
  "medical_history": ["string"],
  "current_medications": ["string"],
  "allergies": ["string"],
  "vital_flags": ["string – urgent details"],
  "interview_quality": "high or medium or low"
}

TRANSCRIPT:
{transcript}'''

def extract_structured_data(conversation_history):
    transcript = '\n'.join(
        f"{'Patient' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in conversation_history
    )
    
    resp = client.messages.create(
        model='claude-sonnet-4-20250514',
        max_tokens=1500,
        system=SYSTEM,
        messages=[{'role': 'user', 'content': PROMPT.format(transcript=transcript)}]
    )
    
    raw = resp.content[0].text.strip().replace('```json', '').replace('```', '').strip()
    
    try:
        return json.loads(raw)
    except:
        return {
            'chief_complaint': 'Parse error',
            'symptoms': [],
            'interview_quality': 'low',
            'vital_flags': [],
            'associated_symptoms': [],
            'medical_history': [],
            'current_medications': [],
            'allergies': []
        }
