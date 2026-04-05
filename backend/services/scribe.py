import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

SYSTEM = 'You are a medical scribe. Return ONLY raw JSON. No preamble, no markdown fences.'

PROMPT = """Extract structured data from this transcript. Return only this JSON:
{{
  "chief_complaint": "string",
  "symptoms": [
    {{
      "name": "string",
      "type": "sharp/dull/throbbing/burning/pressure",
      "severity": 1,
      "duration": "string",
      "triggers": [],
      "relieving_factors": []
    }}
  ],
  "associated_symptoms": ["string"],
  "medical_history": ["string"],
  "current_medications": ["string"],
  "allergies": ["string"],
  "vital_flags": ["string - urgent details"],
  "interview_quality": "high or medium or low"
}}

TRANSCRIPT:
{transcript}"""

def extract_structured_data(conversation_history):
    transcript = '\n'.join(
        f"{'Patient' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in conversation_history
    )

    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=[
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': PROMPT.format(transcript=transcript)}
        ],
        max_tokens=1500
    )

    raw = response.choices[0].message.content
    raw = raw.strip().replace('```json', '').replace('```', '').strip()

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