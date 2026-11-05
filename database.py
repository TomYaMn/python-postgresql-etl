import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL, KL_TZ, logger

# Initialize Database Engine
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

def get_spendings(start, end):
    query = f"""
        SELECT id, time, transaction_type, amount, category, subcategory, merchant, description 
        FROM spendings 
        WHERE time >= '{start}' AND time <= '{end} 23:59:59'
        ORDER BY time DESC;
    """
    return pd.read_sql(query, engine)

def save_manual_edits(edited_df, start_date, end_date):
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM spendings WHERE time >= '{start_date}' AND time <= '{end_date} 23:59:59'"))
        if not edited_df.empty:
            edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
    logger.info(f"Database updated manually for date range {start_date} to {end_date}.")

def inject_ai_records(ai_edited_df):
    # Ensure times are treated correctly based on KL timezone before injection
    if 'time' in ai_edited_df.columns:
        ai_edited_df['time'] = pd.to_datetime(ai_edited_df['time']).dt.tz_localize(KL_TZ, ambiguous='NaT', nonexistent='shift_forward').dt.strftime('%Y-%m-%d %H:%M:%S%z')

    with engine.begin() as conn:
        ai_edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
    
    logger.info(f"Injected {len(ai_edited_df)} AI-extracted records into TimescaleDB.")

def get_category_options():
    """Fetch distinct categories for the dropdown list."""
    query = "SELECT DISTINCT category FROM spending_categories ORDER BY category;"
    df = pd.read_sql(query, engine)
    return df['category'].tolist()

def get_subcategory_options():
    """Fetch distinct subcategories for the dropdown list."""
    query = "SELECT DISTINCT subcategory FROM spending_categories ORDER BY subcategory;"
    df = pd.read_sql(query, engine)
    return df['subcategory'].tolist()