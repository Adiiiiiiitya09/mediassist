import os
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv('GROQ_API_KEY'))

SYSTEM_PROMPT = """You are a professional medical intake assistant for MediAssist.
Your ONLY job is to gather detailed symptom information via warm, natural conversation.

Rules (never break these):
1. Ask exactly ONE question at a time.
2. Follow up intelligently based on the patient's answers:
   - 'chest pain' -> 'Is it sharp stabbing or dull pressure/tightness?'
   - 'fever'      -> 'How long, and have you measured your temperature?'
   - 'headache'   -> 'Where exactly - forehead, temples, back of the head?'
3. Gather ALL of: chief complaint, duration, severity (1-10), symptom type,
   triggers, relieving factors, associated symptoms, medical history,
   current medications, allergies.
4. After 10-14 exchanges, when all points are covered, end your final message
   with exactly: [INTERVIEW_COMPLETE]
5. NEVER suggest, hint at, or mention any disease or diagnosis.
6. NEVER say 'it could be X' or 'this sounds like Y'."""

def get_ai_response(conversation_history):
    # Build messages with system prompt
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    messages += conversation_history

    response = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages=messages,
        max_tokens=500
    )

    reply = response.choices[0].message.content
    is_complete = bool(re.search(r'INTERVIEW[\s_]*COMPLETE', reply, re.IGNORECASE))
    # Strip all variations: [INTERVIEW_COMPLETE], **INTERVIEW COMPLETE**, etc.
    clean = re.sub(r'[\[\]*]*\s*INTERVIEW[\s_]*COMPLETE\s*[\[\]*]*', '', reply, flags=re.IGNORECASE).strip()

    if is_complete:
        if not clean:
            clean = 'Thank you for sharing all this information. A doctor will review your case shortly.'
        else:
            clean += '\n\nThank you for sharing all this information. A doctor will review your case shortly.'

    return clean, is_complete