import os
import json
import logging
import asyncio
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
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'bexo50')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

# =============== إصلاح المشكلة 5: معالجة آمنة للمشرفين ===============
MODERATORS = []
moderators_str = os.getenv('MODERATORS', '')
if moderators_str:
    for id_str in moderators_str.split(','):
        id_str = id_str.strip()
        if id_str and id_str.isdigit():
            MODERATORS.append(int(id_str))

# ملفات التخزين
VIDEOS_FILE = 'videos.json'
PLAYLISTS_FILE = 'playlists.json'
STATS_FILE = 'stats.json'
USERS_FILE = 'users.json'

# =============== إصلاح المشكلة 4: قفل للملفات (File I/O Lock) ===============
_file_lock = asyncio.Lock()

# =============== دوال التخزين مع القفل ===============

async def load_videos_async():
    async with _file_lock:
        if os.path.exists(VIDEOS_FILE):
            with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_playlists_async():
    async with _file_lock:
        if os.path.exists(PLAYLISTS_FILE):
            with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_stats_async():
    async with _file_lock:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_users_async():
    async with _file_lock:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def save_videos_async(videos):
    async with _file_lock:
        with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)

async def save_playlists_async(playlists):
    async with _file_lock:
        with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=2)

async def save_stats_async(stats):
    async with _file_lock:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

async def save_users_async(users):
    async with _file_lock:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

# =============== دوال التحميل المتزامنة (للبداية) ===============

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

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
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

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# تحميل البيانات
videos = load_videos()
playlists = load_playlists()
stats = load_stats()
users = load_users()

# =============== دوال الإحصائيات ===============

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

# =============== دوال المستخدمين ===============

def save_user(user_id, username=None, first_name=None):
    if str(user_id) not in users:
        users[str(user_id)] = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'joined_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        save_users(users)
    else:
        users[str(user_id)]['last_active'] = datetime.now().isoformat()
        if username:
            users[str(user_id)]['username'] = username
        if first_name:
            users[str(user_id)]['first_name'] = first_name
        save_users(users)

def get_all_users():
    return list(users.keys())

# =============== دوال الصلاحيات ===============

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_moderator(user_id):
    return user_id in MODERATORS

def is_staff(user_id):
    return is_admin(user_id) or is_moderator(user_id)

# =============== دوال البداية ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    save_user(user_id, username, first_name)
    context.user_data.clear()
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📢 الإذاعة", callback_data='admin_broadcast')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🔰 العلامة المائية", callback_data='admin_watermark')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 مرحباً أيها الأدمن!\n\n"
            f"📹 عدد المقاطع: {len(videos)}\n"
            f"📂 عدد القوائم: {len(playlists)}\n"
            f"👥 المستخدمين: {len(get_all_users())}\n"
            f"👀 المشاهدات: {sum(s.get('views', 0) for s in stats.values())}",
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
            f"👋 مرحباً أيها المشرف!\n\n"
            f"📹 عدد المقاطع: {len(videos)}\n"
            f"📂 عدد القوائم: {len(playlists)}",
            reply_markup=reply_markup
        )
        return
    
    # للمستخدم العادي
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context)
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"⚠️ **للوصول إلى المحتوى، يرجى الاشتراك في قناتنا أولاً!**\n\n"
                f"📢 **قناتنا:** @{CHANNEL_USERNAME}\n\n"
                f"🔹 بعد الاشتراك، اضغط على زر التحقق.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_staff(user_id):
        context.user_data.clear()
        await update.message.reply_text("✅ تم الإلغاء!")
        await start(update, context)

# =============== دوال عرض المستخدم ===============

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    keyboard = []
    
    if playlists:
        for name in playlists.keys():
            count = len(playlists[name])
            keyboard.append([InlineKeyboardButton(f"📂 {name} ({count})", callback_data=f'playlist_{name}')])
    
    if videos:
        keyboard.append([InlineKeyboardButton("🎬 جميع المقاطع", callback_data='all_videos')])
    
    if not videos and not playlists:
        keyboard.append([InlineKeyboardButton("⚠️ لا توجد مقاطع", callback_data='no_videos')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎥 **القوائم والمقاطع المتاحة:**\n\nاختر ما تريد مشاهدته:"
    
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
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_user_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"🎥 **جميع المقاطع** ({len(videos)})", reply_markup=reply_markup)

# =============== دوال الرجوع ===============

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    context.user_data.clear()
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📢 الإذاعة", callback_data='admin_broadcast')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🔰 العلامة المائية", callback_data='admin_watermark')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            f"👋 مرحباً أيها الأدمن!\n\n📹 عدد المقاطع: {len(videos)}\n📂 عدد القوائم: {len(playlists)}\n👥 المستخدمين: {len(get_all_users())}\n👀 المشاهدات: {sum(s.get('views', 0) for s in stats.values())}",
            reply_markup=reply_markup
        )
    elif is_moderator(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            f"👋 مرحباً أيها المشرف!\n\n📹 عدد المقاطع: {len(videos)}\n📂 عدد القوائم: {len(playlists)}",
            reply_markup=reply_markup
        )
    else:
        await show_user_menu(update, context, edit=True)

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_user_menu(update, context, edit=True)

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
                    [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                    [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    f"⚠️ **يجب الاشتراك في القناة لمشاهدة المقاطع!**\n\n"
                    f"📢 **قناتنا:** @{CHANNEL_USERNAME}",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
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
            logger.error(f"Error sending video: {e}")
            await query.message.reply_text(f"⚠️ حدث خطأ في إرسال الفيديو!")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== دوال التحقق من الاشتراك ===============

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context, edit=True)
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق مرة أخرى", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"❌ **لم تشترك بعد!**\n\n📢 @{CHANNEL_USERNAME}",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.answer("حدث خطأ!", show_alert=True)

# =============== دوال إدارة المقاطع ===============

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
        f"📊 **لوحة تحكم الأدمن**\n\n📹 عدد المقاطع: {len(videos)}\n📂 عدد القوائم: {len(playlists)}",
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
        "📤 **إضافة مقطع جديد**\n\n1️⃣ أرسل **اسم** المقطع\n2️⃣ ثم أرسل **الفيديو**\n\n🔄 للإلغاء أرسل /cancel"
    )

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_video_name':
        video_name = update.message.text.strip()
        
        if video_name in videos:
            await update.message.reply_text(f"⚠️ يوجد مقطع بنفس الاسم '{video_name}'")
            return
        
        context.user_data['video_name'] = video_name
        context.user_data['admin_action'] = 'waiting_video_file'
        await update.message.reply_text(f"✅ تم حفظ الاسم: **{video_name}**\n\n📤 أرسل الفيديو الآن")

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    # التحقق من السياق أولاً
    if context.user_data.get('admin_action') == 'waiting_video_file':
        if update.message.video:
            try:
                file_id = update.message.video.file_id
                video_name = context.user_data.get('video_name', f'مقطع {len(videos) + 1}')
                
                videos[video_name] = file_id
                save_videos(videos)
                
                context.user_data['admin_action'] = None
                context.user_data['video_name'] = None
                
                await update.message.reply_text(
                    f"✅ **تم إضافة المقطع بنجاح!**\n\n"
                    f"📌 الاسم: **{video_name}**\n"
                    f"📹 عدد المقاطع الآن: {len(videos)}"
                )
            except Exception as e:
                logger.error(f"Error saving video: {e}")
                await update.message.reply_text("⚠️ حدث خطأ أثناء حفظ الفيديو!")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال **فيديو** وليس نص أو صورة.")

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
    await query.message.edit_text("❌ **اختر المقطع للحذف:**", reply_markup=reply_markup)

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
        
        for playlist_name in list(playlists.keys()):
            if video_name in playlists[playlist_name]:
                playlists[playlist_name].remove(video_name)
                save_playlists(playlists)
        
        await query.message.edit_text(f"✅ تم حذف **{video_name}** بنجاح!")
        await admin_panel(update, context)
    else:
        await query.answer("❌ المقطع غير موجود!", show_alert=True)

async def admin_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    
    text = "📋 **قائمة المقاطع:**\n\n"
    for i, name in enumerate(videos.keys(), 1):
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
    await query.message.edit_text(
        f"⚠️ **تحذير!**\n\nهل أنت متأكد من حذف جميع المقاطع؟\n📹 عدد المقاطع: {len(videos)}",
        reply_markup=reply_markup
    )

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    videos.clear()
    save_videos(videos)
    
    for playlist_name in list(playlists.keys()):
        playlists[playlist_name] = []
        save_playlists(playlists)
    
    await query.message.edit_text("✅ تم حذف جميع المقاطع بنجاح!")
    await admin_panel(update, context)

# =============== دوال إدارة القوائم ===============

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
        f"📂 **إدارة القوائم**\n\n📂 عدد القوائم: {len(playlists)}\n📹 عدد المقاطع الكلي: {len(videos)}",
        reply_markup=reply_markup
    )

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_playlist_name'
    await query.message.edit_text(
        "📂 **إنشاء قائمة جديدة**\n\n✏️ أرسل **اسم القائمة**\nمثال: أجمل_الأهداف\n\n🔄 للإلغاء أرسل /cancel"
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
    await query.message.edit_text("📂 **اختر القائمة لإضافة مقطع لها:**", reply_markup=reply_markup)

async def select_playlist_for_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    playlist_name = query.data.replace('select_playlist_', '')
    context.user_data['selected_playlist'] = playlist_name
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع! أضف مقاطع أولاً.")
        return
    
    keyboard = []
    for video_name in videos.keys():
        if video_name not in playlists.get(playlist_name, []):
            keyboard.append([InlineKeyboardButton(f"➕ {video_name}", callback_data=f'add_video_to_{playlist_name}_{video_name}')])
    
    if not keyboard:
        await query.message.edit_text(f"✅ جميع المقاطع موجودة في **{playlist_name}**!")
        return
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"📂 **إضافة مقطع لقائمة {playlist_name}:**", reply_markup=reply_markup)

# =============== إصلاح المشكلة 2: تحسين pattern للقوائم ===============

async def add_video_to_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مقطع محدد لقائمة - مُصلح للتعامل مع المسافات"""
    query = update.callback_query
    await query.answer()
    
    # استخراج البيانات من callback_data
    data = query.data.replace('add_video_to_', '')
    
    # فصل اسم القائمة واسم المقطع باستخدام rsplit (آخر جزء هو اسم المقطع)
    parts = data.rsplit('_', 1)
    
    if len(parts) != 2:
        await query.answer("⚠️ حدث خطأ في البيانات!", show_alert=True)
        return
    
    playlist_name = parts[0]
    video_name = parts[1]
    
    if playlist_name in playlists:
        if video_name not in playlists[playlist_name]:
            playlists[playlist_name].append(video_name)
            save_playlists(playlists)
            
            await query.message.edit_text(
                f"✅ تم إضافة **{video_name}** إلى **{playlist_name}**!\n"
                f"📂 عدد المقاطع في القائمة: {len(playlists[playlist_name])}"
            )
            await admin_playlists(update, context)
        else:
            await query.answer("⚠️ هذا المقطع موجود بالفعل!", show_alert=True)

# =============== إصلاح المشكلة 3: تحسين معالجة حالة الإذاعة ===============

async def handle_broadcast_photo_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_broadcast_photo_caption':
        text = update.message.text.strip()
        photo_file_id = context.user_data.get('broadcast_photo')
        
        if text == '/skip':
            text = None
        
        await send_broadcast(update, context, photo=photo_file_id, caption=text)
        context.user_data['admin_action'] = None
        context.user_data['broadcast_photo'] = None

async def handle_broadcast_video_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_broadcast_video_caption':
        text = update.message.text.strip()
        video_file_id = context.user_data.get('broadcast_video')
        
        if text == '/skip':
            text = None
        
        await send_broadcast(update, context, video=video_file_id, caption=text)
        context.user_data['admin_action'] = None
        context.user_data['broadcast_video'] = None

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
    await query.message.edit_text("❌ **اختر القائمة للحذف:**", reply_markup=reply_markup)

async def delete_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    playlist_name = query.data.replace('delete_playlist_', '')
    
    if playlist_name in playlists:
        del playlists[playlist_name]
        save_playlists(playlists)
        
        await query.message.edit_text(f"✅ تم حذف القائمة **{playlist_name}** بنجاح!")
        await admin_playlists(update, context)
    else:
        await query.answer("❌ القائمة غير موجودة!", show_alert=True)

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
        if videos_list:
            text += f"   📌 {', '.join(videos_list[:3])}"
            if len(videos_list) > 3:
                text += f" ... و{len(videos_list) - 3} أخرى"
            text += "\n"
        text += "\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== دوال القوائم الفرعية ===============

async def create_sub_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم رئيسية!", show_alert=True)
        return
    
    keyboard = []
    for name in playlists.keys():
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=f'sub_parent_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("📂 **اختر القائمة الرئيسية للقائمة الفرعية:**", reply_markup=reply_markup)

async def select_sub_parent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parent_name = query.data.replace('sub_parent_', '')
    context.user_data['parent_playlist'] = parent_name
    context.user_data['admin_action'] = 'waiting_sub_playlist_name'
    
    await query.message.edit_text(
        f"📂 **قائمة فرعية في: {parent_name}**\n\n✏️ أرسل اسم القائمة الفرعية:\nمثال: أهداف_2024\n\n🔄 للإلغاء أرسل /cancel"
    )

async def handle_sub_playlist_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_sub_playlist_name':
        sub_name = update.message.text.strip()
        parent_name = context.user_data.get('parent_playlist')
        
        if not sub_name:
            await update.message.reply_text("⚠️ يرجى إرسال اسم صحيح!")
            return
        
        if not parent_name or parent_name not in playlists:
            await update.message.reply_text("⚠️ حدث خطأ! القائمة الرئيسية غير موجودة.")
            return
        
        full_name = f"{parent_name} › {sub_name}"
        
        if full_name in playlists:
            await update.message.reply_text(f"⚠️ توجد قائمة بنفس الاسم '{sub_name}' في {parent_name}")
            return
        
        playlists[full_name] = []
        save_playlists(playlists)
        
        context.user_data['admin_action'] = None
        context.user_data['parent_playlist'] = None
        
        await update.message.reply_text(
            f"✅ **تم إنشاء القائمة الفرعية!**\n\n📌 الاسم: **{sub_name}**\n📂 ضمن القائمة: **{parent_name}**"
        )

# =============== دوال ترتيب القوائم ===============

async def reorder_playlist_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        if playlists[name]:
            keyboard.append([InlineKeyboardButton(f"↕️ {name} ({len(playlists[name])})", callback_data=f'reorder_{name}')])
    
    if not keyboard:
        await query.message.edit_text("⚠️ جميع القوائم فارغة!")
        return
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text("↕️ **اختر قائمة لترتيب مقاطعها:**", reply_markup=reply_markup)

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
            "✅ تم الانتهاء من ترتيب القائمة!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]])
        )
        return
    
    current_video = videos_list[index]
    
    keyboard = []
    if index > 0:
        keyboard.append([InlineKeyboardButton("⬆️ لأعلى", callback_data=f'move_up_{index}')])
    if index < len(videos_list) - 1:
        keyboard.append([InlineKeyboardButton("⬇️ لأسفل", callback_data=f'move_down_{index}')])
    
    keyboard.append([InlineKeyboardButton("✅ تخطي", callback_data='skip_reorder')])
    keyboard.append([InlineKeyboardButton("🔙 إنهاء", callback_data='finish_reorder')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"📂 **ترتيب القائمة: {playlist_name}**\n\n"
    text += f"📌 المقطع الحالي ({index + 1}/{len(videos_list)}):\n"
    text += f"🎬 **{current_video}**\n\n"
    text += "استخدم الأزرار لتغيير ترتيب المقطع:"
    
    if edit and update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

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
        "✅ تم حفظ الترتيب الجديد للقائمة!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]])
    )

# =============== دوال عرض القوائم للمستخدم ===============

# =============== إصلاح المشكلة 2: تحسين pattern للقوائم ===============

async def show_playlist_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    playlist_name = query.data.replace('playlist_', '')
    
    if playlist_name not in playlists:
        await query.message.edit_text("⚠️ القائمة غير موجودة!")
        return
    
    videos_list = playlists[playlist_name]
    
    # البحث عن القوائم الفرعية
    sub_playlists = []
    for name in playlists.keys():
        if name.startswith(f"{playlist_name} › "):
            sub_playlists.append(name)
    
    keyboard = []
    
    for sub_name in sub_playlists:
        display_name = sub_name.replace(f"{playlist_name} › ", "")
        count = len(playlists[sub_name])
        keyboard.append([InlineKeyboardButton(f"📂 {display_name} ({count})", callback_data=f'playlist_{sub_name}')])
    
    for video_name in videos_list:
        if video_name in videos:
            keyboard.append([InlineKeyboardButton(f"🎬 {video_name}", callback_data=f'play_{video_name}')])
    
    if not keyboard:
        await query.message.edit_text(f"📂 **{playlist_name}**\n\n⚠️ هذه القائمة فارغة!")
        return
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_user_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        f"📂 **{playlist_name}**\n\n"
        f"📹 عدد المقاطع: {len(videos_list)}\n"
        f"📂 قوائم فرعية: {len(sub_playlists)}\n\n"
        "اختر المقطع أو القائمة:",
        reply_markup=reply_markup
    )

# =============== دوال الإذاعة ===============

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 رسالة نصية", callback_data='broadcast_text')],
        [InlineKeyboardButton("🖼️ صورة + نص", callback_data='broadcast_photo')],
        [InlineKeyboardButton("🎬 فيديو + نص", callback_data='broadcast_video')],
        [InlineKeyboardButton("📊 عدد المستخدمين", callback_data='broadcast_stats')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    user_count = len(get_all_users())
    await query.message.edit_text(
        f"📢 **لوحة الإذاعة**\n\n👥 عدد المستخدمين المسجلين: {user_count}",
        reply_markup=reply_markup
    )

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_broadcast_text'
    await query.message.edit_text(
        "📝 **إذاعة نصية**\n\n✏️ أرسل النص الذي تريد إذاعته:\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_broadcast_photo'
    await query.message.edit_text(
        "🖼️ **إذاعة مع صورة**\n\n1️⃣ أرسل **الصورة**\n2️⃣ ثم أرسل **النص**\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_broadcast_video'
    await query.message.edit_text(
        "🎬 **إذاعة مع فيديو**\n\n1️⃣ أرسل **الفيديو**\n2️⃣ ثم أرسل **النص**\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    user_count = len(get_all_users())
    text = f"📊 **إحصائيات المستخدمين**\n\n👥 عدد المستخدمين: {user_count}\n"
    
    if user_count > 0:
        text += "\n🆕 **آخر 5 مستخدمين:**\n"
        sorted_users = sorted(users.items(), key=lambda x: x[1].get('joined_at', ''), reverse=True)
        for i, (uid, data) in enumerate(sorted_users[:5], 1):
            name = data.get('first_name', 'مجهول')
            username = data.get('username', '')
            text += f"{i}. {name} (@{username})\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_broadcast')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== دوال استقبال وإرسال الإذاعة ===============

async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_broadcast_text':
        text = update.message.text.strip()
        
        if not text:
            await update.message.reply_text("⚠️ يرجى إرسال نص صحيح!")
            return
        
        await send_broadcast(update, context, text=text)
        context.user_data['admin_action'] = None

async def handle_broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_broadcast_photo':
        if update.message.photo:
            photo_file_id = update.message.photo[-1].file_id
            context.user_data['broadcast_photo'] = photo_file_id
            context.user_data['admin_action'] = 'waiting_broadcast_photo_caption'
            await update.message.reply_text("✅ تم استلام الصورة!\n\n📝 أرسل النص المرافق (أو /skip للتخطي):")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال صورة!")

async def handle_broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_broadcast_video':
        if update.message.video:
            video_file_id = update.message.video.file_id
            context.user_data['broadcast_video'] = video_file_id
            context.user_data['admin_action'] = 'waiting_broadcast_video_caption'
            await update.message.reply_text("✅ تم استلام الفيديو!\n\n📝 أرسل النص المرافق (أو /skip للتخطي):")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال فيديو!")

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE, text=None, photo=None, video=None, caption=None):
    user_ids = get_all_users()
    total = len(user_ids)
    
    if total == 0:
        await update.message.reply_text("⚠️ لا يوجد مستخدمين!")
        return
    
    msg = await update.message.reply_text(f"📢 جاري إرسال الإذاعة...\n👥 المستخدمين: {total}")
    
    success = 0
    failed = 0
    
    for uid in user_ids:
        try:
            user_id = int(uid)
            
            if photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=photo,
                    caption=caption or text or "📢 إذاعة من البوت"
                )
            elif video:
                await context.bot.send_video(
                    chat_id=user_id,
                    video=video,
                    caption=caption or text or "📢 إذاعة من البوت"
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=text or "📢 إذاعة من البوت"
                )
            success += 1
        except Exception as e:
            failed += 1
            logger.error(f"Failed to send broadcast to {uid}: {e}")
    
    await msg.edit_text(
        f"✅ **تم إرسال الإذاعة!**\n\n"
        f"✅ نجح: {success}\n"
        f"❌ فشل: {failed}\n"
        f"👥 المجموع: {total}"
    )

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
    
    sorted_videos = sorted(stats.items(), key=lambda x: x[1].get('views', 0), reverse=True)
    top_videos = sorted_videos[:3]
    
    text = f"📊 **الإحصائيات**\n\n"
    text += f"📹 المقاطع: {len(videos)}\n"
    text += f"📂 القوائم: {len(playlists)}\n"
    text += f"👥 المستخدمين: {len(get_all_users())}\n"
    text += f"👀 المشاهدات: {total_views}\n"
    text += f"👤 مستخدمين فريدين: {len(total_users)}\n\n"
    
    if top_videos:
        text += "🏆 **أكثر المقاطع مشاهدة:**\n"
        for i, (name, data) in enumerate(top_videos, 1):
            text += f"{i}. {name} - {data.get('views', 0)} مشاهدة\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== دوال العلامة المائية ===============

async def admin_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
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
    
    await query.message.edit_text(
        f"🔰 **إدارة العلامة المائية**\n\nالحالة: {status}",
        reply_markup=reply_markup
    )

async def watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_watermark_image'
    await query.message.edit_text(
        "🖼️ **إضافة علامة مائية (صورة)**\n\nأرسل صورة PNG شفافة\n🔄 للإلغاء أرسل /cancel"
    )

async def watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_watermark_text'
    await query.message.edit_text(
        "📝 **إضافة علامة مائية (نص)**\n\nأرسل النص المطلوب\nمثال: @bexo50\n\n🔄 للإلغاء أرسل /cancel"
    )

async def handle_watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_watermark_text':
        text = update.message.text.strip()
        
        if not text:
            await update.message.reply_text("⚠️ يرجى إرسال نص صحيح!")
            return
        
        with open('watermark_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        
        context.user_data['admin_action'] = None
        
        await update.message.reply_text(
            f"✅ **تم تعيين العلامة المائية النصية!**\n\n"
            f"📝 النص: `{text}`"
        )

async def handle_watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_watermark_image':
        if update.message.photo:
            try:
                photo_file = await update.message.photo[-1].get_file()
                await photo_file.download_to_drive('watermark.png')
                
                context.user_data['admin_action'] = None
                
                await update.message.reply_text(
                    "✅ **تم تعيين العلامة المائية الصورية!**"
                )
            except Exception as e:
                logger.error(f"Error saving watermark image: {e}")
                await update.message.reply_text("⚠️ حدث خطأ أثناء حفظ الصورة!")
        else:
            await update.message.reply_text("⚠️ يرجى إرسال **صورة** بصيغة PNG.")

async def watermark_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    
    removed = []
    for file in ['watermark.png', 'watermark_text.txt']:
        if os.path.exists(file):
            os.remove(file)
            removed.append(file)
    
    if removed:
        await query.message.edit_text(
            f"✅ **تم إزالة العلامة المائية!**\n\n🗑️ تم حذف: {', '.join(removed)}"
        )
    else:
        await query.message.edit_text(
            "ℹ️ **لا توجد علامة مائية لإزالتها!**"
        )

# =============== معالج الرسائل الشامل ===============

# =============== إصلاح المشكلة 3: تحسين معالجة حالة الإذاعة ===============

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    admin_action = context.user_data.get('admin_action')
    
    # معالجة الإذاعة النصية
    if admin_action == 'waiting_broadcast_text':
        await handle_broadcast_text(update, context)
        return
    
    # معالجة نص الصورة للإذاعة
    if admin_action == 'waiting_broadcast_photo_caption':
        await handle_broadcast_photo_caption(update, context)
        return
    
    # معالجة نص الفيديو للإذاعة
    if admin_action == 'waiting_broadcast_video_caption':
        await handle_broadcast_video_caption(update, context)
        return
    
    # معالجة اسم القائمة
    if admin_action == 'waiting_playlist_name':
        playlist_name = update.message.text.strip()
        
        if not playlist_name:
            await update.message.reply_text("⚠️ يرجى إرسال اسم صحيح!")
            return
        
        if playlist_name in playlists:
            await update.message.reply_text(f"⚠️ توجد قائمة بنفس الاسم '{playlist_name}'")
            return
        
        playlists[playlist_name] = []
        save_playlists(playlists)
        
        context.user_data['admin_action'] = None
        
        await update.message.reply_text(
            f"✅ **تم إنشاء القائمة بنجاح!**\n\n📌 الاسم: **{playlist_name}**\n📂 القائمة فارغة حالياً"
        )
        return
    
    # معالجة اسم القائمة الفرعية
    if admin_action == 'waiting_sub_playlist_name':
        await handle_sub_playlist_name(update, context)
        return
    
    # معالجة اسم المقطع
    if admin_action == 'waiting_video_name':
        await handle_video_name(update, context)
        return
    
    # معالجة نص العلامة المائية
    if admin_action == 'waiting_watermark_text':
        await handle_watermark_text(update, context)
        return

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
    application.add_handler(CallbackQueryHandler(select_sub_parent, pattern='^sub_parent_'))
    application.add_handler(CallbackQueryHandler(add_to_playlist, pattern='^add_to_playlist$'))
    application.add_handler(CallbackQueryHandler(select_playlist_for_add, pattern='^select_playlist_'))
    application.add_handler(CallbackQueryHandler(add_video_to_playlist_callback, pattern='^add_video_to_'))
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
    
    # الإذاعة
    application.add_handler(CallbackQueryHandler(admin_broadcast, pattern='^admin_broadcast$'))
    application.add_handler(CallbackQueryHandler(broadcast_text, pattern='^broadcast_text$'))
    application.add_handler(CallbackQueryHandler(broadcast_photo, pattern='^broadcast_photo$'))
    application.add_handler(CallbackQueryHandler(broadcast_video, pattern='^broadcast_video$'))
    application.add_handler(CallbackQueryHandler(broadcast_stats, pattern='^broadcast_stats$'))
    
    # العلامة المائية
    application.add_handler(CallbackQueryHandler(admin_watermark, pattern='^admin_watermark$'))
    application.add_handler(CallbackQueryHandler(watermark_image, pattern='^watermark_image$'))
    application.add_handler(CallbackQueryHandler(watermark_text, pattern='^watermark_text$'))
    application.add_handler(CallbackQueryHandler(watermark_remove, pattern='^watermark_remove$'))
    
    # =============== إصلاح المشكلة 1: معالجة وسائط غير متداخلة ===============
    # معالجة الفيديو - نتحقق من السياق أولاً داخل الدالة
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    application.add_handler(MessageHandler(filters.VIDEO, handle_broadcast_video))
    
    # معالجة الصور - نتحقق من السياق أولاً داخل الدالة
    application.add_handler(MessageHandler(filters.PHOTO, handle_watermark_image))
    application.add_handler(MessageHandler(filters.PHOTO, handle_broadcast_photo))
    
    # معالجة النصوص
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
