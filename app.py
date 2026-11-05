import streamlit as st
import pandas as pd
from datetime import datetime
from config import APP_ENV, KL_TZ, logger
from database import get_spendings, save_manual_edits, inject_ai_records
from ai_agent import extract_text_from_file, process_bank_statement
from datetime import datetime

# Startup Log
logger.info(f"Starting Finance App UI in {APP_ENV.upper()} mode")

st.set_page_config(layout="wide", page_title=f"Finance Tracker ({APP_ENV.upper()})")
st.title(f"Personal Finance Live Tracker & AI Extractor [{APP_ENV.upper()}]")

# --- SECTION 1: LIVE DB EDITOR ---
st.header("1. View, Edit, & Delete Existing Spending")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(datetime.now(KL_TZ).year, datetime.now(KL_TZ).month, 1))
with col2:
    end_date = st.date_input("End Date", datetime.now(KL_TZ).date())

# Cache the DB call locally in the UI layer
@st.cache_data(ttl=5)
def load_data(start, end):
    return get_spendings(start, end)

df_current = load_data(start_date, end_date)
edited_df = st.data_editor(df_current, num_rows="dynamic", use_container_width=True, key="db_editor")

if st.button("Save Database Changes", type="primary"):
    save_manual_edits(edited_df, start_date, end_date)
    st.success("Database updated successfully!")
    st.rerun()

st.divider()

# --- SECTION 2: AI BANK STATEMENT UPLOAD ---
st.header("2. AI Bank Statement Injection")
uploaded_file = st.file_uploader("Upload Bank Statement (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file is not None:
    if st.button("Run AI Extraction"):
        logger.info(f"Running AI extraction on uploaded file: {uploaded_file.name}")
        with st.spinner("AI is analyzing your bank statement..."):
            try:
                text_content = extract_text_from_file(uploaded_file)
                parsed_data = process_bank_statement(text_content)
                
                st.session_state['ai_extracted'] = pd.DataFrame(parsed_data)
                logger.info(f"AI extraction successful. Found {len(parsed_data)} records.")
            except Exception as e:
                logger.error(f"AI Extraction failed: {e}")
                st.error(f"AI Extraction failed: {e}")

# Review & Inject Phase
if 'ai_extracted' in st.session_state and not st.session_state['ai_extracted'].empty:
    st.subheader("Review AI Extracted Data")
    st.info("Edit any mistakes made by the AI before injecting into the database.")
    
    ai_edited_df = st.data_editor(st.session_state['ai_extracted'], num_rows="dynamic", use_container_width=True)
    
    if st.button("Confirm & Inject to Database"):
        ai_edited_df['is_ai_extracted'] = True
        
        inject_ai_records(ai_edited_df)
        
        st.success(f"{len(ai_edited_df)} records injected into TimescaleDB successfully!")
        st.session_state['ai_extracted'] = pd.DataFrame()
        st.rerun()