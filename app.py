import streamlit as st
import pandas as pd
from datetime import datetime
from config import APP_ENV, KL_TZ, logger
from database import get_spendings, save_manual_edits, inject_ai_records, get_category_options, get_subcategory_options
from ai_agent import extract_text_from_file, process_bank_statement

# Startup Log
logger.info(f"Starting Finance App UI in {APP_ENV.upper()} mode")

st.set_page_config(layout="wide", page_title=f"Finance Tracker ({APP_ENV.upper()})")
st.title(f"Personal Finance Live Tracker & AI Extractor [{APP_ENV.upper()}]")

# --- FETCH DROPDOWN OPTIONS ---
# Cache these so we don't query the DB on every single UI refresh
@st.cache_data(ttl=600)
def load_dropdown_options():
    return {
        "categories": get_category_options(),
        "subcategories": get_subcategory_options(),
        "transaction_types": ["EXPENSE", "INCOME"]
    }

options = load_dropdown_options()

# Define the Streamlit column configuration for the dropdowns
editor_column_config = {
    "transaction_type": st.column_config.SelectboxColumn(
        "Transaction Type",
        help="Select INCOME or EXPENSE",
        options=options["transaction_types"],
        required=True
    ),
    "category": st.column_config.SelectboxColumn(
        "Category",
        help="Select spending or income category",
        options=options["categories"],
        required=True
    ),
    "subcategory": st.column_config.SelectboxColumn(
        "Subcategory",
        help="Select specific subcategory",
        options=options["subcategories"],
        required=True
    )
}

# --- SECTION 1: LIVE DB EDITOR ---
st.header("1. View, Edit, & Delete Existing Spending")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", datetime(datetime.now(KL_TZ).year, datetime.now(KL_TZ).month, 1))
with col2:
    end_date = st.date_input("End Date", datetime.now(KL_TZ).date())

@st.cache_data(ttl=5)
def load_data(start, end):
    return get_spendings(start, end)

df_current = load_data(start_date, end_date)

# Apply the column_config here
edited_df = st.data_editor(
    df_current, 
    num_rows="dynamic", 
    use_container_width=True, 
    key="db_editor",
    column_config=editor_column_config
)

# --- BUTTON ROW ---
# Create a row of columns for the buttons to sit side-by-side
btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])

with btn_col1:
    if st.button("Save Database Changes", type="primary"):
        save_manual_edits(edited_df, start_date, end_date)
        st.success("Database updated successfully!")
        st.rerun()

with btn_col2:
    # Determine if the Compare button should be enabled
    # It requires both current DB data and AI extracted data in the session state
    can_compare = not df_current.empty and 'ai_extracted' in st.session_state and not st.session_state['ai_extracted'].empty
    
    if st.button("Compare Data", type="primary", disabled=not can_compare, use_container_width=True):
        st.session_state['show_comparison'] = True

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
    
    # Apply the same column_config to the AI review table
    ai_edited_df = st.data_editor(
        st.session_state['ai_extracted'], 
        num_rows="dynamic", 
        use_container_width=True,
        column_config=editor_column_config
    )
    
    if st.button("Confirm & Inject to Database"):
        ai_edited_df['is_ai_extracted'] = True
        
        inject_ai_records(ai_edited_df)
        
        st.success(f"{len(ai_edited_df)} records injected into TimescaleDB successfully!")
        st.session_state['ai_extracted'] = pd.DataFrame()
        st.session_state['show_comparison'] = False # Hide comparison on inject
        st.rerun()

# --- SECTION 3: COMPARISON VIEW ---
# This section only renders if the Compare button was clicked
if st.session_state.get('show_comparison', False):
    st.divider()
    st.header("3. Comparison: Database vs. AI Extraction")
    
    # Get the raw dataframes
    db_data = edited_df.copy() # Use edited_df so it compares against your unsaved edits too
    ai_data = st.session_state['ai_extracted'].copy()
    
    try:
        # Extract just the Date (YYYY-MM-DD) for comparison, ignoring hours/minutes/seconds
        db_data['compare_date'] = pd.to_datetime(db_data['time']).dt.date
        ai_data['compare_date'] = pd.to_datetime(ai_data['time']).dt.date
        
        # Ensure amounts are floats for comparison
        db_data['amount'] = db_data['amount'].astype(float)
        ai_data['amount'] = ai_data['amount'].astype(float)

        # Merge on date, amount, category, and subcategory
        # Using an outer join lets us see what's in DB only, AI only, or both
        comparison_df = pd.merge(
            db_data, 
            ai_data, 
            on=['compare_date', 'amount', 'category', 'subcategory'], 
            how='outer', 
            suffixes=('_DB', '_AI'),
            indicator=True
        )
        
        # Clean up the output for display
        # Rename indicator column for clarity
        comparison_df['Source'] = comparison_df['_merge'].map({
            'left_only': 'Only in Database',
            'right_only': 'Only in AI Extraction',
            'both': 'In Both (Matched)'
        })
        
        # Drop the temporary merging columns and internal DB ID
        cols_to_drop = ['_merge', 'compare_date', 'id']
        comparison_df = comparison_df.drop(columns=[c for c in cols_to_drop if c in comparison_df.columns])
        
        # Sort so unmatched items appear at the top
        comparison_df = comparison_df.sort_values(by='Source', ascending=False)
        
        st.info("Transactions are matched based on exact Date, Amount, Category, and Subcategory.")
        st.dataframe(
            comparison_df, 
            use_container_width=True,
            hide_index=True
        )
        
    except Exception as e:
        st.error(f"Could not generate comparison table. Error: {e}")