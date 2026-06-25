import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# تفعيل التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = 'bexo50'
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # ضع معرف الأدمن في المتغيرات

# ملف تخزين المقاطع
VIDEOS_FILE = 'videos.json'

# تحميل المقاطع
def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# حفظ المقاطع
def save_videos(videos):
    with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

# تحميل المقاطع
videos = load_videos()

