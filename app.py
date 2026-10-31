import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import PyPDF2
import json
import os
import logging
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# --- INITIALIZATION & CONFIGURATION ---
load_dotenv()
APP_ENV = os.getenv("APP_ENV", "local")
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
ai_client = OpenAI(api_key=OPENAI_API_KEY)

# --- TIMEZONE & LOGGING SETUP ---
kl_tz = pytz.timezone('Asia/Kuala_Lumpur')

class KLFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=kl_tz)
        return dt.timetuple()

logger = logging.getLogger("finance_app")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = KLFormatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S MYT')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.info(f"Starting Finance App in {APP_ENV.upper()} mode")

# --- AI AGENT PROMPT ---
AI_SYSTEM_PROMPT = """
You are a financial AI agent. Extract transactions from the provided bank statement text.
Map each transaction strictly to the following JSON structure. 
Return ONLY a raw JSON list of objects, no markdown blocks, no extra text.
Format:
[
  {
    "time": "YYYY-MM-DD HH:MM:SS",
    "amount": 125.50,
    "category": "Food",
    "subcategory": "Groceries",
    "merchant": "Whole Foods",
    "description": "Weekly groceries"
  }
]
Categories and subcategories must EXACTLY match this list (if unsure, use "Uncategorized", "Uncategorized"):
Housing: Mortgage or rent, Property taxes, Household repairs, Homeowners association (HOA) fees, Furnishings
Transportation: Car payment, Car warranty, Gas, Tires, Maintenance and oil changes, Parking fees, Repairs, Registration and DMV Fees, Public transit, Rideshare/Taxis, Tolls
Food: Groceries, Restaurants, Coffee shops
Utilities: Electricity, Water, Garbage, Phones, Cable, Internet
Clothing: Adults clothing, Adults shoes, Childrens clothing, Childrens shoes, Dry cleaning/Laundry
Medical/Healthcare: Primary care, Dental care, Specialty care, Urgent care, Medications, Medical devices, Therapy/Mental health, Vision/Contacts
Insurance: Health insurance, Homeowners or renters insurance, Home warranty or protection plan, Auto insurance, Life insurance, Disability insurance, Pet insurance
Household Items/Supplies: Toiletries, Laundry detergent, Dishwasher detergent, Cleaning supplies, Tools
Personal: Gym memberships, Haircuts, Salon services, Cosmetics, Subscriptions, Spa/Massage
Family/Childcare: Babysitter, Daycare/Tuition, Toys/Activities
Pets: Pet food, Vet care, Pet supplies/Toys
Debt: Personal loans, Student loans, Credit cards
Retirement: Financial planning, Investing
Education: Childrens college, Your college, School supplies, Books
Savings: Emergency fund, Big purchases, Other savings
Gifts/Donations: Birthday, Anniversary, Wedding, Christmas, Special occasion, Charities
Entertainment: Alcohol and/or bars, Games, Movies, Concerts, Vacations, Subscriptions, Hobbies
Fees/Taxes: Bank fees, Late fees, Income tax
"""

st.set_page_config(layout="wide", page_title=f"Finance Tracker ({APP_ENV.upper()})")
st.title(f"Personal Finance Live Tracker & AI Extractor [{APP_ENV.upper()}]")

# --- SECTION 1: LIVE DB EDITOR ---
st.header("1. View, Edit, & Delete Existing Spending")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(datetime.now(kl_tz).year, datetime.now(kl_tz).month, 1))
with col2:
    end_date = st.date_input("End Date", datetime.now(kl_tz).date())

@st.cache_data(ttl=5)
def load_data(start, end):
    query = f"""
        SELECT id, time, amount, category, subcategory, merchant, description 
        FROM spendings 
        WHERE time >= '{start}' AND time <= '{end} 23:59:59'
        ORDER BY time DESC;
    """
    return pd.read_sql(query, engine)

df_current = load_data(start_date, end_date)
edited_df = st.data_editor(df_current, num_rows="dynamic", use_container_width=True, key="db_editor")

if st.button("Save Database Changes", type="primary"):
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM spendings WHERE time >= '{start_date}' AND time <= '{end_date} 23:59:59'"))
        if not edited_df.empty:
            edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
    
    logger.info(f"Database updated manually for date range {start_date} to {end_date}.")
    st.success("Database updated successfully!")
    st.rerun()

st.divider()

# --- SECTION 2: AI BANK STATEMENT UPLOAD ---
st.header("2. AI Bank Statement Injection")
uploaded_file = st.file_uploader("Upload Bank Statement (PDF or TXT)", type=["pdf", "txt"])

if uploaded_file is not None:
    text_content = ""
    if uploaded_file.name.endswith(".pdf"):
        reader = PyPDF2.PdfReader(uploaded_file)
        for page in reader.pages:
            text_content += page.extract_text() + "\n"
    else:
        text_content = uploaded_file.read().decode("utf-8")
    
    if st.button("Run AI Extraction"):
        logger.info(f"Running AI extraction on uploaded file: {uploaded_file.name}")
        with st.spinner("AI is analyzing your bank statement..."):
            try:
                response = ai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": AI_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Extract these transactions:\n\n{text_content}"}
                    ],
                    temperature=0.0
                )
                
                raw_json = response.choices[0].message.content.strip()
                if raw_json.startswith("```json"):
                    raw_json = raw_json[7:-3]
                    
                parsed_data = json.loads(raw_json)
                st.session_state['ai_extracted'] = pd.DataFrame(parsed_data)
                logger.info(f"AI extraction successful. Found {len(parsed_data)} records.")
            except Exception as e:
                logger.error(f"AI Extraction failed: {e}")
                st.error(f"AI Extraction failed: {e}")

if 'ai_extracted' in st.session_state and not st.session_state['ai_extracted'].empty:
    st.subheader("Review AI Extracted Data")
    st.info("Edit any mistakes made by the AI before injecting into the database.")
    
    ai_edited_df = st.data_editor(st.session_state['ai_extracted'], num_rows="dynamic", use_container_width=True)
    
    if st.button("Confirm & Inject to Database"):
        ai_edited_df['is_ai_extracted'] = True
        
        # Ensure times are treated correctly based on KL timezone before injection
        if 'time' in ai_edited_df.columns:
            ai_edited_df['time'] = pd.to_datetime(ai_edited_df['time']).dt.tz_localize(kl_tz, ambiguous='NaT', nonexistent='shift_forward').dt.strftime('%Y-%m-%d %H:%M:%S%z')

        with engine.begin() as conn:
            ai_edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
            
        logger.info(f"Injected {len(ai_edited_df)} AI-extracted records into TimescaleDB.")
        st.success(f"{len(ai_edited_df)} records injected into TimescaleDB successfully!")
        st.session_state['ai_extracted'] = pd.DataFrame()
        st.rerun()