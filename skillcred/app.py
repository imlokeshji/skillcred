import streamlit as st
import pandas as pd
import json
import os

from dotenv import load_dotenv

from utils import assign_segment_from_columns, generate_discount_code, segment_to_discount
from gemini_integration import make_email_with_gemini
from email_sender import send_email_gmail

load_dotenv()

st.set_page_config(page_title="EmailPromoApp", layout="wide")

# --- Header ---
st.title("📧 Personalized Marketing Email Composor")
st.markdown("Email Generator ")

# --- Sidebar / Settings ---
st.sidebar.header("⚙️ Settings & Data Source")

# Credentials: prefer session values, then .env
if 'sender' not in st.session_state:
    st.session_state['sender'] = os.getenv('EMAIL_USER','')

if 'app_pass' not in st.session_state:
    st.session_state['app_pass'] = os.getenv('EMAIL_PASS','')

sender_input = st.sidebar.text_input("Sender Gmail (optional)", value=st.session_state.get('sender',''))
pass_input = st.sidebar.text_input("Gmail App Password (optional)", value=st.session_state.get('app_pass',''), type='password')

if st.sidebar.button("Save Credentials to Session"):
    st.session_state['sender'] = sender_input.strip()
    st.session_state['app_pass'] = pass_input.strip()
    st.sidebar.success("Saved credentials in session (not on disk).")

st.sidebar.divider()

st.sidebar.subheader("Mode")

# --- Toggle for Demo/Real Mode ---
demo_mode = st.sidebar.toggle("Demo Mode ON (Preview only)", value=True)
if demo_mode:
    data_source_choices = ["Use sample data", "Upload CSV"]
else:
    data_source_choices = ["Fetch from API", "Upload CSV"]

# Data Source
st.sidebar.subheader("Data Source")
data_source = st.sidebar.selectbox("Choose data source", data_source_choices)
customers_df = pd.DataFrame()

if data_source == "Use sample data":
    try:
        customers_df = pd.read_csv("sample_data.csv")
    except Exception:
        customers_df = pd.DataFrame([{'Name':'Demo','Email':'demo@example.com','Segment':'New'}])
elif data_source == "Upload CSV":
    uploaded = st.sidebar.file_uploader("Upload customers CSV (Name,Email,Segment)", type=['csv'])
    if uploaded:
        try:
            customers_df = pd.read_csv(uploaded)
            st.sidebar.success(f"Loaded {len(customers_df)} rows.")
        except Exception as e:
            st.sidebar.error(f"Failed to read CSV: {e}")
elif data_source == "Fetch from API":
    api_url = st.sidebar.text_input("API URL (e.g. https://fakestoreapi.com/users)")
    api_headers = st.sidebar.text_area("Optional headers (JSON)", value='{}', height=100)
    if st.sidebar.button("Fetch Data"):
        if not api_url:
            st.sidebar.error("Enter API URL first.")
        else:
            try:
                import requests
                headers = json.loads(api_headers) if api_headers.strip() else {}
                r = requests.get(api_url, headers=headers, timeout=20)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, list):
                    customers_df = pd.json_normalize(data)
                elif isinstance(data, dict):
                    for key in ('data','items','results','users'):
                        if key in data and isinstance(data[key], list):
                            customers_df = pd.json_normalize(data[key])
                            break
                    else:
                        customers_df = pd.json_normalize(data)
                st.sidebar.success(f"Fetched {len(customers_df)} rows from API.")
            except Exception as e:
                st.sidebar.error(f"API fetch failed: {e}")

# Ensure segment column exists
customers_df = assign_segment_from_columns(customers_df)
st.session_state['customers_df'] = customers_df

# --- Discount rules (segment-based) ---
st.subheader("Discount Rules (by Segment)")
col1, col2, col3, col4 = st.columns(4)
new_pct = col1.number_input("New (%)", 0, 100, 15, step=5)
ret_pct = col2.number_input("Returning (%)", 0, 100, 10, step=5)
loyal_pct = col3.number_input("Loyal (%)", 0, 100, 25, step=5)
inactive_pct = col4.number_input("Inactive (%)", 0, 100, 30, step=5)
rules = {'New': new_pct, 'Returning': ret_pct, 'Loyal': loyal_pct, 'Inactive': inactive_pct, 'Default': 10}

st.markdown("---")

# --- Main Email Generator (primary interface) ---
st.header("✉️ Email Generator")
st.write("Select product, tone and click Generate. Preview appears below.")

product_name = st.text_input("Featured product name", value="Awesome Product")
tone = st.selectbox("Tone", ["friendly","professional","excited","playful"], index=0)

if st.button("Generate Emails"):
    df = st.session_state.get('customers_df', pd.DataFrame())
    if df is None or df.empty:
        st.error("No customer data loaded. Use sidebar to Upload/Fetch or use sample data.")
    else:
        rows = []
        for _, r in df.iterrows():
            name = r.get('Name') if 'Name' in r.index else r.get('name', 'Customer')
            email = r.get('Email') if 'Email' in r.index else r.get('email','')
            segment = r.get('Segment') if 'Segment' in r.index else r.get('segment','New')
            discount_pct = rules.get(segment, rules['Default'])
            discount_text = f"{discount_pct}%"
            code = generate_discount_code(segment)
            subject, body = make_email_with_gemini(name=name, product=product_name, discount=discount_text, tone=tone)
            body = body.replace('{CODE}', code)
            rows.append({'Name':name, 'Email':email, 'Segment':segment, 'Discount':discount_text, 'Code':code, 'Subject':subject, 'Body':body})
        st.session_state['generated'] = pd.DataFrame(rows)
        st.success('Generated emails. Scroll down to preview.')

gen = st.session_state.get('generated')
if gen is not None and not gen.empty:
    st.subheader('Preview & (Optional) Send')
    edited = st.data_editor(gen, num_rows='dynamic', use_container_width=True, height=400)
    st.session_state['generated'] = edited
    if demo_mode:
        st.info('Demo Mode: Emails are only previewed, not sent. Only sample or uploaded CSV is allowed.')
    elif data_source in ["Fetch from API", "Upload CSV"]:
        if st.button('Send All Emails (Real)'):
            sender = st.session_state.get('sender') or os.getenv('EMAIL_USER','')
            app_pass = st.session_state.get('app_pass') or os.getenv('EMAIL_PASS','')
            if not sender or not app_pass:
                st.error('Missing Gmail credentials. Enter them in sidebar and click Save Credentials to Session.')
            else:
                sent = failed = 0
                for _, row in edited.iterrows():
                    try:
                        send_email_gmail(sender, app_pass, row['Email'], row['Subject'], row['Body'])
                        sent += 1
                    except Exception as e:
                        failed += 1
                        st.error(f'Failed for {row.get("Email","")}: {e}')
                st.success(f'Done. Sent: {sent}, Failed: {failed}')
    else:
        st.warning('Real emails are allowed only with API or uploaded CSV in Real Mode.')
