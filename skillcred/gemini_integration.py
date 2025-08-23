
import os
from dotenv import load_dotenv
load_dotenv()

try:
    import google.generativeai as genai
except Exception:
    genai = None

def get_model():
    api_key = os.getenv('GEMINI_API_KEY','')
    if genai and api_key:
        try:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-flash')
        except Exception:
            return None
    return None

MODEL = get_model()

def make_email_with_gemini(name: str, product: str, discount: str, tone: str='friendly'):
    prompt = f"""Write a concise {tone} marketing email.
Recipient: {name}
Product: {product}
Discount: {discount}

Return in this exact format:
Subject: <one line subject>
Body:
<3-6 short lines, include a CTA and the discount code placeholder {{CODE}}>"""
    if MODEL:
        try:
            resp = MODEL.generate_content(prompt)
            text = resp.text or ''
            if 'Subject:' in text:
                parts = text.split('Subject:',1)[1].strip().split('\n',1)
                subject = parts[0].strip()
                body = parts[1].strip() if len(parts)>1 else ''
                if body.startswith('Body:'):
                    body = body[5:].strip()
                return subject, body
        except Exception:
            pass
    subject = f"Special {discount} off on {product} for you, {name}!"
    body = f"""Hi {name},

We have an exclusive {discount} on {product} for you. Use code {{CODE}} at checkout. Hurry, limited time!

Best,
Your Store Team
"""
    return subject, body
