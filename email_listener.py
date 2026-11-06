import imaplib
import email
import time
import pandas as pd
from bs4 import BeautifulSoup
from config import EMAIL_IMAP_SERVER, EMAIL_ACCOUNT, EMAIL_APP_PASSWORD, BANK_EMAIL_SENDER, logger
from ai_agent import process_bank_statement
from database import inject_ai_records

def get_email_body(msg):
    """Extracts plain text from the email payload."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                return part.get_payload(decode=True).decode()
            elif content_type == "text/html":
                html = part.get_payload(decode=True).decode()
                return BeautifulSoup(html, "html.parser").get_text(separator="\n")
    else:
        content = msg.get_payload(decode=True).decode()
        if msg.get_content_type() == "text/html":
            return BeautifulSoup(content, "html.parser").get_text(separator="\n")
        return content
    return ""

def check_inbox():
    try:
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(EMAIL_IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, EMAIL_APP_PASSWORD)
        mail.select('inbox')

        # Search for UNREAD emails from the specific bank sender
        search_query = f'(UNREAD FROM "{BANK_EMAIL_SENDER}")'
        status, messages = mail.search(None, search_query)
        
        if status != 'OK' or not messages[0]:
            mail.logout()
            return

        email_ids = messages[0].split()
        logger.info(f"Found {len(email_ids)} new bank emails to process.")

        for e_id in email_ids:
            # Fetch the email
            res, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Extract text and send to Gemini
                    text_content = get_email_body(msg)
                    logger.info("Extracting data via Gemini...")
                    
                    try:
                        parsed_data = process_bank_statement(text_content)
                        if parsed_data:
                            # Convert to DataFrame, flag as AI, and inject
                            df = pd.DataFrame(parsed_data)
                            df['is_ai_extracted'] = True
                            inject_ai_records(df)
                            
                            # Mark email as read only if injection succeeds
                            mail.store(e_id, '+FLAGS', '\Seen')
                    except Exception as e:
                        logger.error(f"Failed to process email {e_id}: {e}")
                        
        mail.logout()
        
    except Exception as e:
        logger.error(f"Email Listener Error: {e}")

if __name__ == "__main__":
    logger.info("Starting Background Email Listener...")
    while True:
        check_inbox()
        # Wait 60 seconds before checking again
        time.sleep(60)