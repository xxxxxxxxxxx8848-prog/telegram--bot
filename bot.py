import asyncio
import random
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
import google.generativeai as genai

# Load .env file
load_dotenv()

# API Keys (ye environment variables se aayenge Railway se)
TELEGRAM_API_ID = int(os.getenv('TELEGRAM_API_ID', ''))
TELEGRAM_API_HASH = os.getenv('TELEGRAM_API_HASH', '')
TELEGRAM_PHONE = os.getenv('TELEGRAM_PHONE', '')

# Gemini API Keys (dono available hain)
GEMINI_API_KEYS = [
    os.getenv('GEMINI_API_KEY_1', ''),
    os.getenv('GEMINI_API_KEY_2', '')
]

# Telegram Client setup
client = TelegramClient('telegram_session', TELEGRAM_API_ID, TELEGRAM_API_HASH)

# Conversation history (per user)
conversation_history = {}
MAX_HISTORY = 10  # Last 10 messages rakho context ke liye

# Logging setup
LOG_FILE = 'bot_activity.log'

def log_activity(message):
    """Log karo sab kuch"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_message = f'[{timestamp}] {message}'
    print(log_message)
    with open(LOG_FILE, 'a') as f:
        f.write(log_message + '\n')

async def generate_reply(text, user_id, api_key_index=0):
    """
    Gemini API se reply generate karo
    Agar first key fail ho to second try karo
    """
    try:
        genai.configure(api_key=GEMINI_API_KEYS[api_key_index])
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Context banao (last messages)
        context = '\n'.join(conversation_history.get(user_id, [])[-MAX_HISTORY:])
        
        # Prompt
        prompt = f"{context}\nReply naturally in 1-2 sentences, like a real person chatting:"
        
        response = model.generate_content(prompt)
        reply = response.text.strip()
        
        log_activity(f'Reply generated for user {user_id} (API Key {api_key_index + 1})')
        return reply
        
    except Exception as e:
        log_activity(f'API Error with key {api_key_index + 1}: {str(e)}')
        
        # Fallback to second key
        if api_key_index == 0:
            return await generate_reply(text, user_id, api_key_index=1)
        else:
            # Dono fail hua
            return "Sorry, I'm busy right now. Will reply soon! 😊"

@client.on(events.NewMessage(incoming=True, forwards=False))
async def handle_message(event):
    """
    Main message handler
    """
    try:
        user_id = event.sender_id
        message_text = event.raw_text
        
        # Ignore bot's own messages aur empty messages
        if not message_text or event.sender_id is None:
            return
        
        log_activity(f'New message from {user_id}: {message_text[:50]}...')
        
        # Conversation history add karo
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        conversation_history[user_id].append(f'Friend: {message_text}')
        
        # Random delay (60-180 seconds) - natural feel dene ke liye
        delay = random.randint(60, 180)
        log_activity(f'Waiting {delay} seconds before replying to {user_id}')
        await asyncio.sleep(delay)
        
        # Reply generate karo
        reply = await generate_reply(message_text, user_id)
        
        # Reply bhej
        await event.reply(reply)
        
        # History mein add karo
        conversation_history[user_id].append(f'Me: {reply}')
        
        # Keep only last N messages
        if len(conversation_history[user_id]) > MAX_HISTORY * 2:
            conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]
        
        log_activity(f'Reply sent to {user_id}: {reply[:50]}...')
        
    except Exception as e:
        log_activity(f'Error handling message: {str(e)}')

async def main():
    """Main function"""
    log_activity('Starting Telegram bot...')
    
    try:
        # Start client with session (won't ask for OTP if session exists)
        async with client:
            log_activity('Bot connected to Telegram')
            
            # Listen for messages
            log_activity('Bot is now listening for messages...')
            await client.run_until_disconnected()
        
    except Exception as e:
        log_activity(f'Critical error: {str(e)}')
        raise

if __name__ == '__main__':
    asyncio.run(main())