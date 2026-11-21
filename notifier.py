import os
import logging
import requests

def send_telegram_alert(message: str):
    """Sends a formatted message to your Telegram chat."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        # Fail silently so a Telegram outage never crashes your finance app
        pass

class TelegramErrorHandler(logging.Handler):
    """Automatically forwards any logger.error() call to Telegram."""
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            log_entry = self.format(record)
            send_telegram_alert(f"🚨 *App Error Alert*\n```\n{log_entry}\n```")