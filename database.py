import os
import pytz
import pandas as pd
from sqlalchemy import create_engine, text
from config import DATABASE_URL, logger

# Initialize Database Engine
engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})

def get_spendings(start, end):
    query = f"""
        SELECT id, time, transaction_type, amount, category, subcategory, merchant, description 
        FROM spendings 
        WHERE time >= '{start}' AND time <= '{end} 23:59:59'
        ORDER BY time DESC;
    """
    df = pd.read_sql(query, engine)
    
    # Convert Database UTC time back to Local Time for the UI display
    if not df.empty and 'time' in df.columns:
        tz_str = os.getenv("TZ", "Asia/Kuala_Lumpur")
        
        df['time'] = pd.to_datetime(df['time'])
        
        # If pandas read it as a naive datetime, assume it is UTC (PostgreSQL standard)
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
            
        # Convert to local time, then remove the timezone info so it displays cleanly in the UI
        df['time'] = df['time'].dt.tz_convert(tz_str).dt.tz_localize(None)
        
    return df

def save_manual_edits(edited_df, start_date, end_date):
    # Ensure manual edits made in the UI are localized back to KL_TZ before saving
    if not edited_df.empty and 'time' in edited_df.columns:
        tz_str = os.getenv("TZ", "Asia/Kuala_Lumpur")
        local_tz = pytz.timezone(tz_str)
        
        edited_df['time'] = pd.to_datetime(edited_df['time']).dt.tz_localize(
            local_tz, ambiguous='NaT', nonexistent='shift_forward'
        ).dt.strftime('%Y-%m-%d %H:%M:%S%z')

    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM spendings WHERE time >= '{start_date}' AND time <= '{end_date} 23:59:59'"))
        if not edited_df.empty:
            edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
            
    logger.info(f"Database updated manually for date range {start_date} to {end_date}.")
    check_spending_limits()

def inject_ai_records(ai_edited_df):
    # Dynamically grab the TZ variable from your .env file
    tz_str = os.getenv("TZ", "Asia/Kuala_Lumpur")
    local_tz = pytz.timezone(tz_str)

    # Ensure times are localized correctly based on the TZ environment variable before injection
    if 'time' in ai_edited_df.columns:
        ai_edited_df['time'] = pd.to_datetime(ai_edited_df['time']).dt.tz_localize(
            local_tz, ambiguous='NaT', nonexistent='shift_forward'
        ).dt.strftime('%Y-%m-%d %H:%M:%S%z')

    with engine.begin() as conn:
        ai_edited_df.to_sql('spendings', con=conn, if_exists='append', index=False)
    
    logger.info(f"Injected {len(ai_edited_df)} AI-extracted records into TimescaleDB using {tz_str} timezone.")
    check_spending_limits()

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

# Add this import at the top of database.py
from notifier import send_telegram_alert

def check_spending_limits():
    """Queries TimescaleDB for today's and this month's total expenses and alerts if limits are hit."""
    tz_str = os.getenv("TZ", "Asia/Kuala_Lumpur")
    daily_limit = float(os.getenv("DAILY_SPENDING_LIMIT", 0))
    monthly_limit = float(os.getenv("MONTHLY_ALLOWANCE_LIMIT", 0))

    with engine.connect() as conn:
        daily_total = conn.execute(text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM spendings
            WHERE transaction_type = 'EXPENSE'
              AND (time AT TIME ZONE :tz)::date = (NOW() AT TIME ZONE :tz)::date;
        """), {"tz": tz_str}).scalar()

        monthly_total = conn.execute(text("""
            SELECT COALESCE(SUM(amount), 0)
            FROM spendings
            WHERE transaction_type = 'EXPENSE'
              AND date_trunc('month', time AT TIME ZONE :tz) = date_trunc('month', NOW() AT TIME ZONE :tz);
        """), {"tz": tz_str}).scalar()

    alerts = []
    if daily_limit > 0 and float(daily_total) >= daily_limit:
        alerts.append(f"⚠️ *Daily Limit Hit:* Spent `{daily_total:.2f}` / `{daily_limit:.2f}` today.")

    if monthly_limit > 0 and float(monthly_total) >= monthly_limit:
        alerts.append(f"‼️ *Monthly Allowance Hit:* Spent `{monthly_total:.2f}` / `{monthly_limit:.2f}` this month.")

    if alerts:
        send_telegram_alert("\n".join(alerts))