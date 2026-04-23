import os
import re
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

_SYMPTOM_LIST_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ml', 'symptom_list.json'
)

def _load_symptom_vocab():
    try:
        with open(_SYMPTOM_LIST_PATH) as f:
            return json.load(f)
    except Exception:
        return []

SYSTEM = (
    'You are a medical scribe. Output ONLY a single valid JSON object. '
    'No markdown, no code fences, no explanation before or after.'
)

PROMPT = """Extract symptoms from the transcript below.

Rules:
- "symptoms[].name" and all "associated_symptoms" entries MUST be exact strings from VOCAB.
- Pick the closest VOCAB match; never invent new names.
- "interview_quality": "high" if 8+ symptoms covered, "medium" if 4-7, "low" if <4.

VOCAB: {symptom_vocab}

Output this JSON and nothing else:
{{"chief_complaint":"string","symptoms":[{{"name":"string","type":"sharp/dull/throbbing/burning/pressure","severity":1,"duration":"string","triggers":[],"relieving_factors":[]}}],"associated_symptoms":["string"],"medical_history":["string"],"current_medications":["string"],"allergies":["string"],"vital_flags":["string"],"interview_quality":"high/medium/low"}}

TRANSCRIPT:
{transcript}"""


def extract_structured_data(conversation_history):
    transcript = '\n'.join(
        f"{'Patient' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
        for m in conversation_history
    )

    symptom_vocab = _load_symptom_vocab()
    vocab_str = ', '.join(symptom_vocab) if symptom_vocab else ''

    response = client.chat.completions.create(
        model='llama-3.3-70b-versatile',   # 8b reliably fails on long prompts; 70b handles it
        messages=[
            {'role': 'system', 'content': SYSTEM},
            {'role': 'user', 'content': PROMPT.format(
                symptom_vocab=vocab_str,
                transcript=transcript
            )}
        ],
        max_tokens=1500,
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()

    # Strip any accidental markdown fences
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

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