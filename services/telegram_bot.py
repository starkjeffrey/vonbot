import requests
import os
import logging

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id: str, message: str):
    """
    Send a message via Telegram Bot API.
    Falls back to logging if token is not set.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        logger.warning(f"TELEGRAM_BOT_TOKEN missing. Mocking message to {chat_id}")
        print(f"--- MOCK TELEGRAM ---\nChat ID: {chat_id}\nMessage: {message}\n---------------------")
        return True

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Telegram message sent to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
        return False
