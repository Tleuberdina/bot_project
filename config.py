import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Токен Telegram бота
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Настройки Google API
    GOOGLE_CREDENTIALS_FILE = 'credentials.json'
    
    # Настройки базы данных
    DATABASE_PATH = 'business_processes.db'
    
    # ID Google таблицы (если уже создана)
    GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', '')
