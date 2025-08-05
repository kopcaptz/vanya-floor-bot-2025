import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = "8346136918:AAHwREKIctQJSuWWBySju7naWT_FiDdJBwo"

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# File Upload Configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
UPLOAD_FOLDER = '/tmp/vanya_uploads'
ALLOWED_EXTENSIONS = {'.zip'}

# Analysis Configuration
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
SUPPORTED_AUDIO_FORMATS = {'.m4a', '.ogg', '.mp3'}

# Pricing Configuration (in ILS - Israeli Shekels)
BASE_PRICES = {
    'parquet': 150,    # ₪ per sq.m
    'laminate': 80,    # ₪ per sq.m  
    'tiles': 120,      # ₪ per sq.m
    'linoleum': 60,    # ₪ per sq.m
    'unknown': 100     # ₪ per sq.m default
}

CONDITION_MULTIPLIERS = {
    'excellent': 1.0,
    'good': 1.2,
    'fair': 1.5,
    'poor': 2.0,
    'unknown': 1.3
}

# Ivan's Contact Information
IVAN_CONTACT = {
    'name': 'Иван',
    'phone': '+972 52-477-2115',
    'business': 'Ремонт полов и паркета'
}

