
# EmailPromoApp_Final

Simple, clean Streamlit app for personalized email campaigns.
Features:
- Main Page: Email Generator (primary functionality visible on open)
- Settings (sidebar): secure credentials via .env or session (no hardcoding)
- Data Source: Upload CSV, Fetch from E‑commerce API, or use Sample data
- Gemini integration (optional): if GEMINI_API_KEY is set in .env, app uses Gemini to generate subject/body
- Segment-based discounts and dynamic discount codes
- Demo Mode (preview only) and Real Send (Gmail SMTP)

## Quick start
1. Extract the ZIP.
2. Create a Python venv (recommended) and install requirements:
   pip install -r requirements.txt
3. (Optional) Copy `.env.example` to `.env` and fill your GEMINI_API_KEY and/or EMAIL_USER and EMAIL_PASS.
4. Run the app:
   - Double-click `run_app.bat` (Windows) OR
   - streamlit run app.py
5. In the app:
   - Use sidebar to enter Gmail credentials (session-only) or load from .env
   - Choose data source (Upload / API / Sample)
   - On main page generate emails and preview them. Keep Demo Mode ON for testing.

## Notes
- Do NOT commit `.env` anywhere public.
- If Gemini key is missing, app falls back to a clean template for reliable demo.
