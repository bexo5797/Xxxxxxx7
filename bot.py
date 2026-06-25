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

def is_admin(user_id):
    """التحقق من أن المستخدم أدمن"""
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # إذا كان المستخدم أدمن
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data='admin_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "👋 مرحباً أيها الأدمن!\n\n"
            f"📹 عدد المقاطع: {len(videos)}\n"
            "اختر الإجراء المناسب:",
            reply_markup=reply_markup
        )
        return
    
    # للمستخدم العادي
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # مشترك ✅ - عرض المقاطع
            await show_videos_menu(update, context)
        else:
            # غير مشترك ❌
            keyboard = [
                [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"⚠️ يرجى الاشتراك في القناة أولاً:\n"
                f"👉 @{CHANNEL_USERNAME}",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        await update.message.reply_text("⚠️ حدث خطأ، يرجى المحاولة لاحقاً.")

async def show_videos_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    """عرض قائمة المقاطع للمستخدم"""
    keyboard = []
    
    if videos:
        for name, file_id in videos.items():
            keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
    else:
        keyboard.append([InlineKeyboardButton("⚠️ لا توجد مقاطع", callback_data='no_videos')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎥 **قائمة المقاطع المتاحة:**\n\nاختر المقطع الذي تريد مشاهدته:"
    
    if edit:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم الأدمن"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مقطع جديد", callback_data='admin_add_video')],
        [InlineKeyboardButton("❌ حذف مقطع", callback_data='admin_delete_video')],
        [InlineKeyboardButton("📋 عرض جميع المقاطع", callback_data='admin_list_videos')],
        [InlineKeyboardButton("🗑️ حذف جميع المقاطع", callback_data='admin_delete_all')],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "📊 **لوحة تحكم الأدمن**\n\n"
        f"📹 عدد المقاطع: {len(videos)}\n\n"
        "اختر الإجراء المناسب:",
        reply_markup=reply_markup
    )

async def admin_add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة مقطع جديد"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    # طلب اسم المقطع
    context.user_data['admin_action'] = 'waiting_video_name'
    await query.message.edit_text(
        "📤 **إضافة مقطع جديد**\n\n"
        "1️⃣ أرسل **اسم** المقطع (مثال: مقدمة)\n"
        "2️⃣ ثم أرسل **الفيديو**\n\n"
        "🔄 لإلغاء العملية أرسل /cancel"
    )

async def admin_delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مقطع"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    if not videos:
        await query.answer("⚠️ لا توجد مقاطع لحذفها!", show_alert=True)
        return
    
    # عرض أزرار للمقاطع
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f'delete_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "❌ **حذف مقطع**\n\n"
        "اختر المقطع الذي تريد حذفه:",
        reply_markup=reply_markup
    )

async def admin_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع المقاطع مع معرفاتها"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع حالياً!")
        return
    
    video_list = "📋 **قائمة المقاطع:**\n\n"
    for i, (name, file_id) in enumerate(videos.items(), 1):
        video_list += f"{i}. **{name}**\n"
        video_list += f"   `{file_id[:30]}...`\n\n"
    
    video_list += f"📹 المجموع: {len(videos)} مقطع"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(video_list, reply_markup=reply_markup)

async def admin_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف جميع المقاطع"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم، احذف الكل", callback_data='confirm_delete_all')],
        [InlineKeyboardButton("❌ لا، تراجع", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "⚠️ **تحذير!**\n\n"
        "هل أنت متأكد من حذف جميع المقاطع؟\n"
        f"📹 عدد المقاطع: {len(videos)}",
        reply_markup=reply_markup
    )

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد حذف جميع المقاطع"""
    query = update.callback_query
    await query.answer()
    
    videos.clear()
    save_videos(videos)
    
    await query.message.edit_text("✅ تم حذف جميع المقاطع بنجاح!")
    await admin_panel(update, context)

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم المقطع المرسل من الأدمن"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_video_name':
        video_name = update.message.text.strip()
        
        if video_name in videos:
            await update.message.reply_text(
                f"⚠️ يوجد مقطع بنفس الاسم '{video_name}'\n"
                "يرجى اختيار اسم آخر أو حذف المقطع القديم."
            )
            return
        
        # حفظ الاسم في الجلسة
        context.user_data['video_name'] = video_name
        context.user_data['admin_action'] = 'waiting_video_file'
        
        await update.message.reply_text(
            f"✅ تم حفظ الاسم: **{video_name}**\n\n"
            "📤 الآن أرسل **الفيديو** نفسه:"
        )

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الفيديو المرسل من الأدمن"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_video_file':
        if update.message.video:
            file_id = update.message.video.file_id
            video_name = context.user_data.get('video_name', f'مقطع {len(videos) + 1}')
            
            # حفظ المقطع
            videos[video_name] = file_id
            save_videos(videos)
            
            # تنظيف الجلسة
            context.user_data['admin_action'] = None
            context.user_data['video_name'] = None
            
            await update.message.reply_text(
                f"✅ تم إضافة المقطع بنجاح!\n\n"
                f"📌 الاسم: {video_name}\n"
                f"📹 عدد المقاطع الآن: {len(videos)}\n\n"
                "استخدم /start للعودة للقائمة الرئيسية"
            )
        else:
            await update.message.reply_text(
                "⚠️ يرجى إرسال **فيديو** وليس نص أو صورة.\n"
                "أرسل الفيديو الذي تريد إضافته."
            )

async def delete_video_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف مقطع محدد"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    video_name = query.data.replace('delete_', '')
    
    if video_name in videos:
        del videos[video_name]
        save_videos(videos)
        await query.message.edit_text(f"✅ تم حذف المقطع **{video_name}** بنجاح!")
        await admin_panel(update, context)
    else:
        await query.answer("❌ المقطع غير موجود!", show_alert=True)

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل مقطع فيديو"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    video_name = query.data.replace('play_', '')
    
    # التحقق من الاشتراك للمستخدم العادي
    if not is_admin(user_id):
        try:
            member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                    [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.message.edit_text(
                    f"⚠️ يجب الاشتراك في القناة لمشاهدة المقاطع:\n"
                    f"👉 @{CHANNEL_USERNAME}",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            await query.answer("حدث خطأ، يرجى المحاولة لاحقاً.", show_alert=True)
            return
    
    # إرسال الفيديو
    if video_name in videos:
        try:
            await query.message.reply_video(
                videos[video_name],
                caption=f"🎥 {video_name}"
            )
            logger.info(f"Video '{video_name}' sent to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await query.message.reply_text("⚠️ حدث خطأ في إرسال الفيديو")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """العودة للقائمة الرئيسية"""
    query = update.callback_query
    await query.answer()
    await start(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء العملية الحالية"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        context.user_data['admin_action'] = None
        context.user_data['video_name'] = None
        await update.message.reply_text("✅ تم إلغاء العملية!")
        await start(update, context)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحقق من الاشتراك"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # عرض المقاطع
            keyboard = []
            for name in videos.keys():
                keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.edit_text(
                "✅ تم التحقق! أنت مشترك الآن.\n\n"
                "🎥 اختر المقطع الذي تريد مشاهدته:",
                reply_markup=reply_markup
            )
            logger.info(f"User {user_id} subscribed successfully")
        else:
            await query.answer("❌ لم تشترك بعد، يرجى الاشتراك ثم الضغط على تحقق مرة أخرى.", show_alert=True)
    except Exception as e:
        logger.error(f"Error rechecking: {e}")
        await query.answer("حدث خطأ، يرجى المحاولة لاحقاً.", show_alert=True)

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    application.add_handler(CallbackQueryHandler(admin_list_videos, pattern='^admin_list_videos$'))
    application.add_handler(CallbackQueryHandler(admin_delete_all, pattern='^admin_delete_all$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all$'))
    application.add_handler(CallbackQueryHandler(delete_video_callback, pattern='^delete_'))
    application.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # معالجة رسائل الأدمن
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_name))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode with polling...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
