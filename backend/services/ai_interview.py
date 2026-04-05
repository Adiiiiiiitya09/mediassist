import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

SYSTEM_PROMPT = """You are a professional medical intake assistant for MediAssist.
Your ONLY job is to gather detailed symptom information via warm, natural conversation.

Rules (never break these):
1. Ask exactly ONE question at a time.
2. Follow up intelligently based on the patient's answers:
   - 'chest pain' → 'Is it sharp stabbing or dull pressure/tightness?'
   - 'fever'      → 'How long, and have you measured your temperature?'
   - 'headache'   → 'Where exactly – forehead, temples, back of the head?'
3. Gather ALL of: chief complaint, duration, severity (1-10), symptom type,
   triggers, relieving factors, associated symptoms, medical history,
   current medications, allergies.
4. After 10-14 exchanges, when all points are covered, end your final message
   with exactly: [INTERVIEW_COMPLETE]
5. NEVER suggest, hint at, or mention any disease or diagnosis.
6. NEVER say 'it could be X' or 'this sounds like Y'."""

def get_ai_response(conversation_history):
    response = client.messages.create(
        model='claude-sonnet-4-20250514',
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    reply = response.content[0].text
    is_complete = '[INTERVIEW_COMPLETE]' in reply
    clean = reply.replace('[INTERVIEW_COMPLETE]', '').strip()
    if is_complete:
        clean += '\n\nThank you for sharing all this information. A doctor will review your case shortly.'
    return clean, is_complete
