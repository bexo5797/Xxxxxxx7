import os
import json
import logging
from datetime import datetime
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
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# صلاحيات متعددة
MODERATORS = [int(id.strip()) for id in os.getenv('MODERATORS', '').split(',') if id.strip()]

# ملفات التخزين
VIDEOS_FILE = 'videos.json'
PLAYLISTS_FILE = 'playlists.json'
STATS_FILE = 'stats.json'

# تحميل البيانات
def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_playlists():
    if os.path.exists(PLAYLISTS_FILE):
        with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_videos(videos):
    with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

def save_playlists(playlists):
    with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(playlists, f, ensure_ascii=False, indent=2)

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# تحميل البيانات
videos = load_videos()
playlists = load_playlists()
stats = load_stats()

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_moderator(user_id):
    return user_id in MODERATORS

def is_staff(user_id):
    return is_admin(user_id) or is_moderator(user_id)

def get_user_role(user_id):
    if is_admin(user_id):
        return "👑 أدمن رئيسي"
    elif is_moderator(user_id):
        return "🛡️ مشرف"
    return "👤 مستخدم"

def increment_view(video_name, user_id):
    if video_name not in stats:
        stats[video_name] = {'views': 0, 'users': []}
    stats[video_name]['views'] += 1
    if user_id not in stats[video_name]['users']:
        stats[video_name]['users'].append(user_id)
    save_stats(stats)

def get_video_stats(video_name):
    if video_name in stats:
        return stats[video_name]
    return {'views': 0, 'users': []}

# =============== دوال القوائم (Playlists) ===============

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    context.user_data['admin_action'] = 'waiting_playlist_name'
    await query.message.edit_text(
        "📂 **إنشاء قائمة جديدة**\n\n✏️ أرسل **اسم القائمة**\n🔄 للإلغاء أرسل /cancel"
    )

async def add_to_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    keyboard = []
    for name in playlists.keys():
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=f'select_playlist_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📂 **اختر القائمة**:", reply_markup=reply_markup)

async def select_playlist_for_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    playlist_name = query.data.replace('select_playlist_', '')
    context.user_data['selected_playlist'] = playlist_name
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    keyboard = []
    for video_name in videos.keys():
        if video_name not in playlists.get(playlist_name, []):
            keyboard.append([InlineKeyboardButton(f"➕ {video_name}", callback_data=f'add_video_to_playlist_{playlist_name}_{video_name}')])
    if not keyboard:
        await query.message.edit_text(f"✅ جميع المقاطع موجودة في **{playlist_name}**!")
        return
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"📂 **إضافة مقطع لقائمة {playlist_name}**:", reply_markup=reply_markup)

async def add_video_to_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parts = query.data.split('_')
    playlist_name = parts[4]
    video_name = parts[5]
    if playlist_name in playlists:
        if video_name not in playlists[playlist_name]:
            playlists[playlist_name].append(video_name)
            save_playlists(playlists)
            await query.message.edit_text(f"✅ تم إضافة **{video_name}** إلى **{playlist_name}**!")
            await admin_playlists(update, context)
        else:
            await query.answer("⚠️ المقطع موجود!", show_alert=True)

async def delete_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    keyboard = []
    for name in playlists.keys():
        keyboard.append([InlineKeyboardButton(f"🗑️ {name} ({len(playlists[name])})", callback_data=f'delete_playlist_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("❌ **حذف قائمة**\n\nاختر القائمة:", reply_markup=reply_markup)

async def delete_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    playlist_name = query.data.replace('delete_playlist_', '')
    if playlist_name in playlists:
        del playlists[playlist_name]
        save_playlists(playlists)
        await query.message.edit_text(f"✅ تم حذف **{playlist_name}**!")
        await admin_playlists(update, context)

async def list_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not playlists:
        await query.message.edit_text("⚠️ لا توجد قوائم!")
        return
    text = "📂 **قائمة القوائم:**\n\n"
    for i, (name, videos_list) in enumerate(playlists.items(), 1):
        text += f"{i}. **{name}** - {len(videos_list)} مقطع\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== دوال المستخدم ===============

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    keyboard = []
    if playlists:
        for name in playlists.keys():
            keyboard.append([InlineKeyboardButton(f"📂 {name} ({len(playlists[name])})", callback_data=f'playlist_{name}')])
    if videos:
        keyboard.append([InlineKeyboardButton("🎬 جميع المقاطع", callback_data='all_videos')])
    if not videos and not playlists:
        keyboard.append([InlineKeyboardButton("⚠️ لا توجد مقاطع", callback_data='no_videos')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎥 **القوائم والمقاطع:**\n\nاختر ما تريد:"
    if edit and update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_all_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_user_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"🎥 **جميع المقاطع** ({len(videos)})", reply_markup=reply_markup)

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_user_menu(update, context, edit=True)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context, edit=True)
        else:
            await query.answer("❌ لم تشترك بعد!", show_alert=True)
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.answer("حدث خطأ!", show_alert=True)

# =============== دوال الأدمن ===============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مقطع", callback_data='admin_add_video')],
        [InlineKeyboardButton("❌ حذف مقطع", callback_data='admin_delete_video')],
        [InlineKeyboardButton("📋 عرض المقاطع", callback_data='admin_list_videos')],
        [InlineKeyboardButton("🗑️ حذف الكل", callback_data='admin_delete_all')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        f"📊 **لوحة الأدمن**\n\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة",
        reply_markup=reply_markup
    )

async def admin_add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    context.user_data['admin_action'] = 'waiting_video_name'
    await query.message.edit_text(
        "📤 **إضافة مقطع**\n\n1️⃣ أرسل **الاسم**\n2️⃣ أرسل **الفيديو**\n\n🔄 /cancel للإلغاء"
    )

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_staff(user_id):
        return
    if context.user_data.get('admin_action') == 'waiting_video_name':
        video_name = update.message.text.strip()
        if video_name in videos:
            await update.message.reply_text(f"⚠️ يوجد مقطع باسم '{video_name}'")
            return
        context.user_data['video_name'] = video_name
        context.user_data['admin_action'] = 'waiting_video_file'
        await update.message.reply_text(f"✅ اسم: **{video_name}**\n📤 أرسل الفيديو الآن")

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_staff(user_id):
        return
    if context.user_data.get('admin_action') == 'waiting_video_file':
        if update.message.video:
            file_id = update.message.video.file_id
            video_name = context.user_data.get('video_name', f'مقطع {len(videos) + 1}')
            videos[video_name] = file_id
            save_videos(videos)
            context.user_data['admin_action'] = None
            context.user_data['video_name'] = None
            await update.message.reply_text(f"✅ تم إضافة **{video_name}**!\n📹 {len(videos)} مقطع")
        else:
            await update.message.reply_text("⚠️ أرسل فيديو وليس نص!")

async def admin_delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not videos:
        await query.answer("⚠️ لا توجد مقاطع!", show_alert=True)
        return
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f'delete_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("❌ **حذف مقطع**", reply_markup=reply_markup)

async def delete_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    video_name = query.data.replace('delete_', '')
    if video_name in videos:
        del videos[video_name]
        save_videos(videos)
        for playlist in playlists.values():
            if video_name in playlist:
                playlist.remove(video_name)
        save_playlists(playlists)
        await query.message.edit_text(f"✅ تم حذف **{video_name}**!")
        await admin_panel(update, context)

async def admin_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    text = "📋 **المقاطع:**\n\n"
    for i, (name, file_id) in enumerate(videos.items(), 1):
        text += f"{i}. **{name}**\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

async def admin_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    keyboard = [
        [InlineKeyboardButton("✅ نعم", callback_data='confirm_delete_all')],
        [InlineKeyboardButton("❌ لا", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"⚠️ **حذف الكل؟**\n📹 {len(videos)} مقطع", reply_markup=reply_markup)

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    videos.clear()
    save_videos(videos)
    await query.message.edit_text("✅ تم حذف الكل!")
    await admin_panel(update, context)

# =============== دوال الإحصائيات ===============

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    total_views = sum(s.get('views', 0) for s in stats.values())
    total_users = set()
    for s in stats.values():
        total_users.update(s.get('users', []))
    text = f"""📊 **الإحصائيات**

📹 المقاطع: {len(videos)}
📂 القوائم: {len(playlists)}
👀 المشاهدات: {total_views}
👥 المستخدمين: {len(total_users)}"""
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== دوال العلامة المائية ===============

async def admin_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    keyboard = [
        [InlineKeyboardButton("🖼️ صورة", callback_data='watermark_image')],
        [InlineKeyboardButton("📝 نص", callback_data='watermark_text')],
        [InlineKeyboardButton("🗑️ إزالة", callback_data='watermark_remove')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    status = "❌ غير مفعلة"
    if os.path.exists('watermark.png'):
        status = "✅ مفعلة (صورة)"
    elif os.path.exists('watermark_text.txt'):
        with open('watermark_text.txt', 'r', encoding='utf-8') as f:
            text = f.read().strip()
        status = f"✅ مفعلة (نص: {text})"
    await query.message.edit_text(f"🔰 **العلامة المائية**\n\nالحالة: {status}", reply_markup=reply_markup)

async def watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    context.user_data['admin_action'] = 'waiting_watermark_image'
    await query.message.edit_text("🖼️ أرسل صورة PNG شفافة\n🔄 /cancel للإلغاء")

async def watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    context.user_data['admin_action'] = 'waiting_watermark_text'
    await query.message.edit_text("📝 أرسل النص المطلوب\n🔄 /cancel للإلغاء")

async def handle_watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if context.user_data.get('admin_action') == 'waiting_watermark_text':
        text = update.message.text.strip()
        with open('watermark_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        context.user_data['admin_action'] = None
        context.user_data['watermark_type'] = 'text'
        await update.message.reply_text(f"✅ تم تعيين النص: `{text}`")

async def handle_watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if context.user_data.get('admin_action') == 'waiting_watermark_image':
        if update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            await photo_file.download_to_drive('watermark.png')
            context.user_data['admin_action'] = None
            context.user_data['watermark_type'] = 'image'
            await update.message.reply_text("✅ تم تعيين الصورة!")
        else:
            await update.message.reply_text("⚠️ أرسل صورة PNG!")

async def watermark_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    for file in ['watermark.png', 'watermark_text.txt']:
        if os.path.exists(file):
            os.remove(file)
    context.user_data['watermark_type'] = None
    await query.message.edit_text("✅ تم إزالة العلامة!")

# =============== دوال إدارة القوائم المتقدمة ===============

async def admin_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    keyboard = [
        [InlineKeyboardButton("➕ إنشاء قائمة", callback_data='create_playlist')],
        [InlineKeyboardButton("📂 قائمة فرعية", callback_data='create_sub_playlist')],
        [InlineKeyboardButton("📝 إضافة مقطع", callback_data='add_to_playlist')],
        [InlineKeyboardButton("↕️ ترتيب المقاطع", callback_data='reorder_playlist_select')],
        [InlineKeyboardButton("❌ حذف قائمة", callback_data='delete_playlist')],
        [InlineKeyboardButton("📋 عرض القوائم", callback_data='list_playlists')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        f"📂 **إدارة القوائم**\n\n📂 {len(playlists)} قائمة\n📹 {len(videos)} مقطع",
        reply_markup=reply_markup
    )

async def create_sub_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    keyboard = []
    for name in playlists.keys():
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=f'sub_playlist_parent_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📂 **اختر القائمة الرئيسية**", reply_markup=reply_markup)

async def select_parent_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    parent_name = query.data.replace('sub_playlist_parent_', '')
    context.user_data['parent_playlist'] = parent_name
    context.user_data['admin_action'] = 'waiting_sub_playlist_name'
    await query.message.edit_text(f"📂 **قائمة فرعية في: {parent_name}**\n\n✏️ أرسل الاسم\n🔄 /cancel للإلغاء")

async def handle_sub_playlist_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id):
        return
    if context.user_data.get('admin_action') == 'waiting_sub_playlist_name':
        sub_name = update.message.text.strip()
        parent_name = context.user_data.get('parent_playlist')
        if not parent_name or parent_name not in playlists:
            await update.message.reply_text("⚠️ خطأ!")
            return
        full_name = f"{parent_name}>{sub_name}"
        if full_name in playlists:
            await update.message.reply_text(f"⚠️ توجد قائمة '{sub_name}'")
            return
        playlists[full_name] = []
        save_playlists(playlists)
        context.user_data['admin_action'] = None
        context.user_data['parent_playlist'] = None
        await update.message.reply_text(f"✅ تم إنشاء **{sub_name}** في **{parent_name}**")

# =============== دوال ترتيب القوائم ===============

async def reorder_playlist_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    keyboard = []
    for name in playlists.keys():
        if playlists[name]:
            keyboard.append([InlineKeyboardButton(f"↕️ {name} ({len(playlists[name])})", callback_data=f'reorder_{name}')])
    if not keyboard:
        await query.message.edit_text("⚠️ جميع القوائم فارغة!")
        return
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("↕️ **اختر قائمة للترتيب**", reply_markup=reply_markup)

async def reorder_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    playlist_name = query.data.replace('reorder_', '')
    if playlist_name not in playlists or not playlists[playlist_name]:
        await query.answer("⚠️ القائمة فارغة!", show_alert=True)
        return
    context.user_data['reorder_playlist'] = playlist_name
    context.user_data['reorder_index'] = 0
    await show_reorder_options(update, context)

async def show_reorder_options(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=True):
    playlist_name = context.user_data.get('reorder_playlist')
    index = context.user_data.get('reorder_index', 0)
    if not playlist_name or playlist_name not in playlists:
        return
    videos_list = playlists[playlist_name]
    if index >= len(videos_list):
        await update.callback_query.message.edit_text(
            "✅ تم الانتهاء!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]])
        )
        return
    current_video = videos_list[index]
    keyboard = []
    if index > 0:
        keyboard.append([
            InlineKeyboardButton("⬆️", callback_data=f'move_up_{index}'),
            InlineKeyboardButton("⬇️", callback_data=f'move_down_{index}')
        ])
    keyboard.append([InlineKeyboardButton("✅ تخطي", callback_data='skip_reorder')])
    keyboard.append([InlineKeyboardButton("🔙 إنهاء", callback_data='finish_reorder')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📂 **{playlist_name}**\n\n📌 {index + 1}/{len(videos_list)}\n🎬 **{current_video}**"
    if edit and update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

async def move_video_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace('move_up_', ''))
    playlist_name = context.user_data.get('reorder_playlist')
    if playlist_name and playlist_name in playlists:
        videos_list = playlists[playlist_name]
        if index > 0:
            videos_list[index], videos_list[index - 1] = videos_list[index - 1], videos_list[index]
            save_playlists(playlists)
            context.user_data['reorder_index'] = index - 1
            await show_reorder_options(update, context)

async def move_video_down(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    index = int(query.data.replace('move_down_', ''))
    playlist_name = context.user_data.get('reorder_playlist')
    if playlist_name and playlist_name in playlists:
        videos_list = playlists[playlist_name]
        if index < len(videos_list) - 1:
            videos_list[index], videos_list[index + 1] = videos_list[index + 1], videos_list[index]
            save_playlists(playlists)
            context.user_data['reorder_index'] = index + 1
            await show_reorder_options(update, context)

async def skip_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['reorder_index'] = context.user_data.get('reorder_index', 0) + 1
    await show_reorder_options(update, context)

async def finish_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['reorder_playlist'] = None
    context.user_data['reorder_index'] = None
    await query.message.edit_text(
        "✅ تم حفظ الترتيب!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]])
    )

# =============== دوال عرض القوائم للمستخدم ===============

async def show_playlist_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    playlist_name = query.data.replace('playlist_', '')
    if playlist_name not in playlists:
        await query.message.edit_text("⚠️ القائمة غير موجودة!")
        return
    videos_list = playlists[playlist_name]
    if not videos_list:
        await query.message.edit_text(f"📂 **{playlist_name}**\n\n⚠️ فارغة!")
        return
    sub_playlists = [name for name in playlists.keys() if name.startswith(f"{playlist_name}>")]
    keyboard = []
    for sub_name in sub_playlists:
        display_name = sub_name.split('>')[-1]
        keyboard.append([InlineKeyboardButton(f"📂 {display_name} ({len(playlists[sub_name])})", callback_data=f'playlist_{sub_name}')])
    for video_name in videos_list:
        if video_name in videos:
            keyboard.append([InlineKeyboardButton(f"🎬 {video_name}", callback_data=f'play_{video_name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='back_to_user_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    path_parts = playlist_name.split('>')
    display_path = " > ".join(path_parts)
    await query.message.edit_text(
        f"📂 **{display_path}**\n\n📹 {len(videos_list)} مقطع\n📂 {len(sub_playlists)} قائمة فرعية",
        reply_markup=reply_markup
    )

# =============== دوال تشغيل الفيديو ===============

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    video_name = query.data.replace('play_', '')
    if not is_staff(user_id):
        try:
            member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("📢 اشترك", url=f'https://t.me/{CHANNEL_USERNAME}')],
                    [InlineKeyboardButton("✅ تحقق", callback_data='check_subscription')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(f"⚠️ اشترك في القناة: @{CHANNEL_USERNAME}", reply_markup=reply_markup)
                return
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.answer("حدث خطأ!", show_alert=True)
            return
    if video_name in videos:
        try:
            increment_view(video_name, user_id)
            caption = f"🎥 {video_name}"
            if os.path.exists('watermark_text.txt'):
                with open('watermark_text.txt', 'r', encoding='utf-8') as f:
                    watermark = f.read().strip()
                caption += f"\n\n🔰 {watermark}"
            await query.message.reply_video(videos[video_name], caption=caption)
        except Exception as e:
            logger.error(f"Error: {e}")
            await query.message.reply_text("⚠️ حدث خطأ!")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== دوال أساسية ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🔰 العلامة المائية", callback_data='admin_watermark')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 مرحباً أيها الأدمن!\n\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة\n👀 {sum(s.get('views', 0) for s in stats.values())} مشاهدة",
            reply_markup=reply_markup
        )
        return
    if is_moderator(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 مرحباً أيها المشرف!\n\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة",
            reply_markup=reply_markup
        )
        return
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context)
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"⚠️ اشترك في القناة: @{CHANNEL_USERNAME}", reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ!")

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_staff(user_id):
        context.user_data.clear()
        await update.message.reply_text("✅ تم الإلغاء!")
        await start(update, context)

# =============== main ===============

def main():
    application = Application.builder().token(TOKEN).build()
    
    # أوامر عامة
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # لوحة الأدمن
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    application.add_handler(CallbackQueryHandler(admin_list_videos, pattern='^admin_list_videos$'))
    application.add_handler(CallbackQueryHandler(admin_delete_all, pattern='^admin_delete_all$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all$'))
    application.add_handler(CallbackQueryHandler(delete_video_callback, pattern='^delete_'))
    
    # القوائم
    application.add_handler(CallbackQueryHandler(admin_playlists, pattern='^admin_playlists$'))
    application.add_handler(CallbackQueryHandler(create_playlist, pattern='^create_playlist$'))
    application.add_handler(CallbackQueryHandler(create_sub_playlist, pattern='^create_sub_playlist$'))
    application.add_handler(CallbackQueryHandler(select_parent_playlist, pattern='^sub_playlist_parent_'))
    application.add_handler(CallbackQueryHandler(add_to_playlist, pattern='^add_to_playlist$'))
    application.add_handler(CallbackQueryHandler(select_playlist_for_add, pattern='^select_playlist_'))
    application.add_handler(CallbackQueryHandler(add_video_to_playlist_callback, pattern='^add_video_to_playlist_'))
    application.add_handler(CallbackQueryHandler(delete_playlist, pattern='^delete_playlist$'))
    application.add_handler(CallbackQueryHandler(delete_playlist_callback, pattern='^delete_playlist_'))
    application.add_handler(CallbackQueryHandler(list_playlists, pattern='^list_playlists$'))
    
    # ترتيب القوائم
    application.add_handler(CallbackQueryHandler(reorder_playlist_select, pattern='^reorder_playlist_select$'))
    application.add_handler(CallbackQueryHandler(reorder_playlist, pattern='^reorder_'))
    application.add_handler(CallbackQueryHandler(move_video_up, pattern='^move_up_'))
    application.add_handler(CallbackQueryHandler(move_video_down, pattern='^move_down_'))
    application.add_handler(CallbackQueryHandler(skip_reorder, pattern='^skip_reorder$'))
    application.add_handler(CallbackQueryHandler(finish_reorder, pattern='^finish_reorder$'))
    
    # المستخدمين
    application.add_handler(CallbackQueryHandler(show_playlist_videos, pattern='^playlist_'))
    application.add_handler(CallbackQueryHandler(show_all_videos, pattern='^all_videos$'))
    application.add_handler(CallbackQueryHandler(back_to_user_menu, pattern='^back_to_user_menu$'))
    application.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # الإحصائيات
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    
    # العلامة المائية
    application.add_handler(CallbackQueryHandler(admin_watermark, pattern='^admin_watermark$'))
    application.add_handler(CallbackQueryHandler(watermark_image, pattern='^watermark_image$'))
    application.add_handler(CallbackQueryHandler(watermark_text, pattern='^watermark_text$'))
    application.add_handler(CallbackQueryHandler(watermark_remove, pattern='^watermark_remove$'))
    
    # معالجة الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_name))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_watermark_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_watermark_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sub_playlist_name))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
