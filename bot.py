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
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'bexo50')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
MODERATORS = [int(id.strip()) for id in os.getenv('MODERATORS', '').split(',') if id.strip()]

# ملفات التخزين
VIDEOS_FILE = 'videos.json'
PLAYLISTS_FILE = 'playlists.json'
STATS_FILE = 'stats.json'
USERS_FILE = 'users.json'

# =============== دوال التخزين ===============

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

# =============== دوال الإحصائيات (مهم جداً) ===============

def increment_view(video_name, user_id):
    """زيادة عدد المشاهدات لمقطع"""
    if video_name not in stats:
        stats[video_name] = {'views': 0, 'users': []}
    stats[video_name]['views'] += 1
    if user_id not in stats[video_name]['users']:
        stats[video_name]['users'].append(user_id)
    save_stats(stats)

def get_video_stats(video_name):
    """الحصول على إحصائيات مقطع"""
    if video_name in stats:
        return stats[video_name]
    return {'views': 0, 'users': []}

# =============== دوال المستخدمين ===============

def save_user(user_id, username=None, first_name=None):
    """حفظ بيانات المستخدم"""
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

# =============== دوال العرض ===============

async def show_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    """عرض قائمة المستخدم"""
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

# =============== دوال البداية ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء البوت"""
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
    
    # للمستخدم العادي - التحقق من الاشتراك
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
                f"🔹 بعد الاشتراك، اضغط على زر التحقق.\n"
                f"🔹 المحتوى حصري للمشتركين فقط.\n\n"
                f"شكراً لدعمك! ❤️",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(
            f"⚠️ **حدث خطأ أثناء التحقق من الاشتراك!**\n\n"
            f"📢 تأكد من الاشتراك في قناتنا:\n"
            f"👉 @{CHANNEL_USERNAME}\n\n"
            f"ثم حاول مرة أخرى."
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    user_id = update.effective_user.id
    if is_staff(user_id):
        context.user_data.clear()
        await update.message.reply_text("✅ تم الإلغاء!")
        await start(update, context)

# =============== دوال تشغيل الفيديو ===============

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل مقطع فيديو"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    video_name = query.data.replace('play_', '')
    
    # التحقق من الاشتراك للمستخدم العادي
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
                    f"📢 **قناتنا:** @{CHANNEL_USERNAME}\n\n"
                    f"🔹 بعد الاشتراك، اضغط على زر التحقق.",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            await query.answer("حدث خطأ في التحقق من الاشتراك!", show_alert=True)
            return
    
    if video_name in videos:
        try:
            # تسجيل المشاهدة
            increment_view(video_name, user_id)
            
            caption = f"🎥 {video_name}"
            
            # إضافة العلامة المائية
            if os.path.exists('watermark_text.txt'):
                with open('watermark_text.txt', 'r', encoding='utf-8') as f:
                    watermark = f.read().strip()
                caption += f"\n\n🔰 {watermark}"
            
            await query.message.reply_video(
                videos[video_name],
                caption=caption
            )
            logger.info(f"Video '{video_name}' sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await query.message.reply_text(
                f"⚠️ **حدث خطأ في إرسال الفيديو!**\n\n"
                f"📌 المقطع: {video_name}\n"
                f"❌ الخطأ: {str(e)[:100]}\n\n"
                f"🔧 تأكد من أن الفيديو بحجم أقل من 50MB\n"
                f"📹 جرب فيديو آخر أو حاول مرة أخرى."
            )
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== دوال التحقق من الاشتراك ===============

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الاشتراك"""
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
                f"❌ **لم تشترك بعد في القناة!**\n\n"
                f"📢 **قناتنا:** @{CHANNEL_USERNAME}\n\n"
                f"🔹 اشترك في القناة ثم اضغط على زر التحقق.\n"
                f"🔹 المحتوى حصري للمشتركين فقط.",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.answer("حدث خطأ في التحقق!", show_alert=True)

# =============== دوال إدارة المقاطع ===============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم الأدمن"""
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
        f"📊 **لوحة تحكم الأدمن**\n\n"
        f"📹 عدد المقاطع: {len(videos)}\n"
        f"📂 عدد القوائم: {len(playlists)}",
        reply_markup=reply_markup
    )

async def admin_add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مقطع جديد"""
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_video_name'
    await query.message.edit_text(
        "📤 **إضافة مقطع جديد**\n\n"
        "1️⃣ أرسل **اسم** المقطع\n"
        "2️⃣ ثم أرسل **الفيديو**\n\n"
        "🔄 للإلغاء أرسل /cancel"
    )

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم المقطع"""
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
    """معالجة الفيديو المرسل"""
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
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
                    f"📹 عدد المقاطع الآن: {len(videos)}\n\n"
                    f"يمكنك الآن إضافته للقوائم أو مشاهدته."
                )
            except Exception as e:
                logger.error(f"Error saving video: {e}")
                await update.message.reply_text(
                    f"⚠️ **حدث خطأ أثناء حفظ الفيديو!**\n\n"
                    f"❌ {str(e)[:100]}\n\n"
                    f"🔧 حاول مرة أخرى أو جرب فيديو آخر."
                )
        else:
            await update.message.reply_text("⚠️ يرجى إرسال **فيديو** وليس نص أو صورة.")

# =============== دوال الرجوع ===============

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة لقائمة المستخدم"""
    query = update.callback_query
    await query.answer()
    await show_user_menu(update, context, edit=True)

async def show_all_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع المقاطع"""
    query = update.callback_query
    await query.answer()
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع حالياً!")
        return
    
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_user_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(f"🎥 **جميع المقاطع** ({len(videos)})", reply_markup=reply_markup)

async def admin_delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مقطع"""
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
    """حذف مقطع محدد"""
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

# =============== دوال إدارة القوائم ===============

async def admin_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة إدارة القوائم"""
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
        f"📂 **إدارة القوائم**\n\n"
        f"📂 عدد القوائم: {len(playlists)}\n"
        f"📹 عدد المقاطع الكلي: {len(videos)}",
        reply_markup=reply_markup
    )

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء قائمة جديدة"""
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_playlist_name'
    await query.message.edit_text(
        "📂 **إنشاء قائمة جديدة**\n\n"
        "✏️ أرسل **اسم القائمة**\n"
        "مثال: أجمل الأهداف\n\n"
        "🔄 للإلغاء أرسل /cancel"
    )

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج كل الرسائل النصية"""
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    admin_action = context.user_data.get('admin_action')
    
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
            f"✅ **تم إنشاء القائمة بنجاح!**\n\n"
            f"📌 الاسم: **{playlist_name}**\n"
            f"📂 القائمة فارغة حالياً\n\n"
            f"يمكنك إضافة مقاطع لها الآن."
        )
        return
    
    # معالجة اسم المقطع
    if admin_action == 'waiting_video_name':
        await handle_video_name(update, context)
        return

# =============== main ===============

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TOKEN).build()
    
    # أوامر عامة
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # لوحة الأدمن
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    application.add_handler(CallbackQueryHandler(delete_video_callback, pattern='^delete_'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    
    # القوائم
    application.add_handler(CallbackQueryHandler(admin_playlists, pattern='^admin_playlists$'))
    application.add_handler(CallbackQueryHandler(create_playlist, pattern='^create_playlist$'))
    
    # المستخدمين
    application.add_handler(CallbackQueryHandler(show_all_videos, pattern='^all_videos$'))
    application.add_handler(CallbackQueryHandler(back_to_user_menu, pattern='^back_to_user_menu$'))
    application.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # معالجة الرسائل
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
