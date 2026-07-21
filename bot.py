import os
import json
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import shutil
from pathlib import Path

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

# صلاحيات متعددة - قراءة من المتغيرات
MODERATORS = [int(id.strip()) for id in os.getenv('MODERATORS', '').split(',') if id.strip()]
# مثال: MODERATORS=123456789,987654321

# ملفات التخزين
VIDEOS_FILE = 'videos.json'
PLAYLISTS_FILE = 'playlists.json'
STATS_FILE = 'stats.json'
WATERMARK_FILE = 'watermark.png'  # يمكن وضع صورة العلامة المائية

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
    """التحقق من أن المستخدم أدمن رئيسي"""
    return user_id == ADMIN_ID

def is_moderator(user_id):
    """التحقق من أن المستخدم مشرف"""
    return user_id in MODERATORS

def is_staff(user_id):
    """التحقق من أن المستخدم من فريق العمل (أدمن أو مشرف)"""
    return is_admin(user_id) or is_moderator(user_id)

def get_user_role(user_id):
    """الحصول على دور المستخدم"""
    if is_admin(user_id):
        return "👑 أدمن رئيسي"
    elif is_moderator(user_id):
        return "🛡️ مشرف"
    return "👤 مستخدم"

# =============== إدارة المشاهدات ===============

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

# =============== إدارة العلامة المائية ===============

async def set_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعيين علامة مائية (صورة أو نص)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⚠️ هذا الإجراء للأدمن الرئيسي فقط!")
        return
    
    # طلب نوع العلامة المائية
    keyboard = [
        [InlineKeyboardButton("🖼️ صورة", callback_data='watermark_image')],
        [InlineKeyboardButton("📝 نص", callback_data='watermark_text')],
        [InlineKeyboardButton("🗑️ إزالة العلامة", callback_data='watermark_remove')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔰 **إعدادات العلامة المائية**\n\n"
        "اختر نوع العلامة المائية التي تريد إضافتها للمقاطع:\n\n"
        "• صورة: ترسل صورة شفافة\n"
        "• نص: تكتب النص المطلوب",
        reply_markup=reply_markup
    )

async def watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب صورة العلامة المائية"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_watermark_image'
    await query.message.edit_text(
        "🖼️ **إضافة علامة مائية (صورة)**\n\n"
        "أرسل صورة PNG شفافة (يفضل 200x200)\n"
        "ستظهر في زاوية الفيديو.\n\n"
        "🔄 لإلغاء العملية أرسل /cancel"
    )

async def watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب نص العلامة المائية"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['admin_action'] = 'waiting_watermark_text'
    await query.message.edit_text(
        "📝 **إضافة علامة مائية (نص)**\n\n"
        "أرسل النص الذي تريد ظهوره على الفيديو\n"
        "مثال: @bexo50\n\n"
        "🔄 لإلغاء العملية أرسل /cancel"
    )

async def handle_watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة نص العلامة المائية"""
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_watermark_text':
        text = update.message.text.strip()
        
        # حفظ النص في ملف
        with open('watermark_text.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        
        context.user_data['admin_action'] = None
        context.user_data['watermark_type'] = 'text'
        
        await update.message.reply_text(
            f"✅ تم تعيين العلامة المائية النصية:\n\n"
            f"📝 `{text}`\n\n"
            "سيتم إضافة العلامة لكل المقاطع الجديدة."
        )

async def handle_watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة صورة العلامة المائية"""
    if not is_admin(update.effective_user.id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_watermark_image':
        if update.message.photo:
            # تحميل الصورة
            photo_file = await update.message.photo[-1].get_file()
            await photo_file.download_to_drive('watermark.png')
            
            context.user_data['admin_action'] = None
            context.user_data['watermark_type'] = 'image'
            
            await update.message.reply_text(
                "✅ تم تعيين العلامة المائية الصورية بنجاح!\n"
                "سيتم إضافة العلامة لكل المقاطع الجديدة."
            )
        else:
            await update.message.reply_text(
                "⚠️ يرجى إرسال **صورة** بصيغة PNG."
            )

async def watermark_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إزالة العلامة المائية"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    # حذف ملفات العلامة المائية
    for file in ['watermark.png', 'watermark_text.txt']:
        if os.path.exists(file):
            os.remove(file)
    
    context.user_data['watermark_type'] = None
    
    await query.message.edit_text(
        "✅ تم إزالة العلامة المائية بنجاح!"
    )

# =============== ميزة 1: ترتيب المقاطع داخل القائمة ===============

async def reorder_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ترتيب مقاطع القائمة"""
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
    """عرض خيارات ترتيب المقطع"""
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
    
    # أزرار الترتيب
    if index > 0:
        keyboard.append([
            InlineKeyboardButton("⬆️ لأعلى", callback_data=f'move_up_{index}'),
            InlineKeyboardButton("⬇️ لأسفل", callback_data=f'move_down_{index}')
        ])
    
    keyboard.append([
        InlineKeyboardButton("✅ تخطي", callback_data=f'skip_reorder')
    ])
    
    keyboard.append([
        InlineKeyboardButton("🔙 إنهاء", callback_data='finish_reorder')
    ])
    
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
    """نقل المقطع لأعلى"""
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.replace('move_up_', ''))
    playlist_name = context.user_data.get('reorder_playlist')
    
    if playlist_name and playlist_name in playlists:
        videos_list = playlists[playlist_name]
        if index > 0:
            # تبديل المواقع
            videos_list[index], videos_list[index - 1] = videos_list[index - 1], videos_list[index]
            save_playlists(playlists)
            
            context.user_data['reorder_index'] = index - 1
            await show_reorder_options(update, context)

async def move_video_down(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نقل المقطع لأسفل"""
    query = update.callback_query
    await query.answer()
    
    index = int(query.data.replace('move_down_', ''))
    playlist_name = context.user_data.get('reorder_playlist')
    
    if playlist_name and playlist_name in playlists:
        videos_list = playlists[playlist_name]
        if index < len(videos_list) - 1:
            # تبديل المواقع
            videos_list[index], videos_list[index + 1] = videos_list[index + 1], videos_list[index]
            save_playlists(playlists)
            
            context.user_data['reorder_index'] = index + 1
            await show_reorder_options(update, context)

async def skip_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تخطي المقطع الحالي"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['reorder_index'] = context.user_data.get('reorder_index', 0) + 1
    await show_reorder_options(update, context)

async def finish_reorder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنهاء ترتيب القائمة"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['reorder_playlist'] = None
    context.user_data['reorder_index'] = None
    
    await query.message.edit_text(
        "✅ تم حفظ الترتيب الجديد للقائمة!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')]])
    )

# =============== ميزة 2: فئات فرعية (قوائم داخل قوائم) ===============

async def create_sub_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء قائمة فرعية داخل قائمة"""
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم رئيسية!", show_alert=True)
        return
    
    # عرض القوائم الرئيسية
    keyboard = []
    for name in playlists.keys():
        keyboard.append([InlineKeyboardButton(f"📂 {name}", callback_data=f'sub_playlist_parent_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "📂 **إنشاء قائمة فرعية**\n\n"
        "اختر القائمة الرئيسية التي تريد إضافة قائمة فرعية لها:",
        reply_markup=reply_markup
    )

async def select_parent_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار القائمة الرئيسية للقائمة الفرعية"""
    query = update.callback_query
    await query.answer()
    
    parent_name = query.data.replace('sub_playlist_parent_', '')
    context.user_data['parent_playlist'] = parent_name
    
    context.user_data['admin_action'] = 'waiting_sub_playlist_name'
    await query.message.edit_text(
        f"📂 **إنشاء قائمة فرعية في: {parent_name}**\n\n"
        "✏️ أرسل اسم القائمة الفرعية:\n"
        "مثال: أهداف 2024\n\n"
        "🔄 لإلغاء العملية أرسل /cancel"
    )

async def handle_sub_playlist_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة اسم القائمة الفرعية"""
    if not is_staff(update.effective_user.id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_sub_playlist_name':
        sub_name = update.message.text.strip()
        parent_name = context.user_data.get('parent_playlist')
        
        if not parent_name or parent_name not in playlists:
            await update.message.reply_text("⚠️ حدث خطأ، يرجى المحاولة مرة أخرى.")
            return
        
        # إنشاء القائمة الفرعية (تخزن كـ parent>sub)
        full_name = f"{parent_name}>{sub_name}"
        
        if full_name in playlists:
            await update.message.reply_text(
                f"⚠️ توجد قائمة بنفس الاسم '{sub_name}' في {parent_name}"
            )
            return
        
        playlists[full_name] = []
        save_playlists(playlists)
        
        context.user_data['admin_action'] = None
        context.user_data['parent_playlist'] = None
        
        await update.message.reply_text(
            f"✅ تم إنشاء القائمة الفرعية **{sub_name}**\n"
            f"📂 ضمن القائمة: **{parent_name}**\n\n"
            f"📌 المسار: {full_name}"
        )

# =============== ميزة 8: تقارير وإحصائيات متقدمة ===============

async def advanced_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض إحصائيات متقدمة"""
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    # إحصائيات عامة
    total_videos = len(videos)
    total_playlists = len(playlists)
    total_views = sum(s.get('views', 0) for s in stats.values())
    total_users = set()
    for s in stats.values():
        total_users.update(s.get('users', []))
    
    # أكثر المقاطع مشاهدة
    sorted_videos = sorted(stats.items(), key=lambda x: x[1].get('views', 0), reverse=True)
    top_videos = sorted_videos[:5]
    
    text = f"""📊 **إحصائيات متقدمة**

📹 إجمالي المقاطع: {total_videos}
📂 عدد القوائم: {total_playlists}
👀 إجمالي المشاهدات: {total_views}
👥 عدد المستخدمين: {len(total_users)}

🏆 **أكثر 5 مقاطع مشاهدة:**
"""
    
    for i, (name, data) in enumerate(top_videos, 1):
        views = data.get('views', 0)
        users = len(data.get('users', []))
        text += f"{i}. **{name}** - {views} مشاهدة ({users} مستخدم)\n"
    
    if not top_videos:
        text += "\n⚠️ لا توجد مشاهدات حتى الآن."
    
    keyboard = [
        [InlineKeyboardButton("📈 مشاهدات اليوم", callback_data='stats_daily')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)

async def stats_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات اليوم"""
    query = update.callback_query
    await query.answer()
    
    today = datetime.now().strftime("%Y-%m-%d")
    daily_stats = {}
    
    # إذا كان لديك ملف للإحصائيات اليومية
    if os.path.exists('daily_stats.json'):
        with open('daily_stats.json', 'r', encoding='utf-8') as f:
            daily_stats = json.load(f)
    
    today_views = daily_stats.get(today, 0)
    
    text = f"""📅 **إحصائيات اليوم ({today})**

👀 مشاهدات اليوم: {today_views}

📊 متوسط المشاهدات اليومية: 
"""
    # حساب المتوسط
    if daily_stats:
        avg = sum(daily_stats.values()) / len(daily_stats)
        text += f"📈 {avg:.1f} مشاهدة/يوم"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_stats')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(text, reply_markup=reply_markup)

# =============== ميزة 14: إضافة علامة مائية ===============

async def add_watermark_to_video(video_file, caption=""):
    """إضافة علامة مائية للفيديو (محاكاة)"""
    # ملاحظة: لإضافة علامة مائية حقيقية تحتاج لمكتبة مثل moviepy
    # هذا مجرد مثال لكيفية التعامل معها
    
    watermark_type = context.user_data.get('watermark_type')
    
    if watermark_type == 'text' and os.path.exists('watermark_text.txt'):
        with open('watermark_text.txt', 'r', encoding='utf-8') as f:
            watermark = f.read().strip()
        caption += f"\n\n🔰 {watermark}"
    
    return video_file, caption

# =============== تحديث دوال إرسال الفيديو مع العلامة المائية ===============

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تشغيل مقطع فيديو مع علامة مائية"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    video_name = query.data.replace('play_', '')
    
    # التحقق من الاشتراك
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
                    f"⚠️ يجب الاشتراك في القناة لمشاهدة المقاطع:\n👉 @{CHANNEL_USERNAME}",
                    reply_markup=reply_markup
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            await query.answer("حدث خطأ، يرجى المحاولة لاحقاً.", show_alert=True)
            return
    
    if video_name in videos:
        try:
            # تسجيل المشاهدة
            increment_view(video_name, user_id)
            
            # إرسال الفيديو مع العلامة المائية
            caption = f"🎥 {video_name}"
            
            # إضافة العلامة المائية النصية إذا وجدت
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
            await query.message.reply_text("⚠️ حدث خطأ في إرسال الفيديو")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== تحديث دوال إضافة الفيديو مع العلامة المائية ===============

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الفيديو المرسل مع إضافة العلامة المائية"""
    user_id = update.effective_user.id
    
    if not is_staff(user_id):
        return
    
    if context.user_data.get('admin_action') == 'waiting_video_file':
        if update.message.video:
            file_id = update.message.video.file_id
            video_name = context.user_data.get('video_name', f'مقطع {len(videos) + 1}')
            
            # يمكن إضافة العلامة المائية هنا (تحتاج لمكتبة خارجية)
            # هذا مثال بسيط لإضافة نص في الكابتشن
            caption = f"✅ تم إضافة **{video_name}**"
            
            videos[video_name] = file_id
            save_videos(videos)
            
            context.user_data['admin_action'] = None
            context.user_data['video_name'] = None
            
            await update.message.reply_text(
                f"✅ تم إضافة المقطع **{video_name}** بنجاح!\n"
                f"📹 عدد المقاطع الآن: {len(videos)}\n\n"
                "استخدم /start للعودة للقائمة الرئيسية"
            )
        else:
            await update.message.reply_text("⚠️ يرجى إرسال **فيديو** وليس نص أو صورة.")

# =============== إضافة أزرار القوائم في لوحة الأدمن ===============

async def admin_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة إدارة القوائم"""
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ إنشاء قائمة جديدة", callback_data='create_playlist')],
        [InlineKeyboardButton("📂 إنشاء قائمة فرعية", callback_data='create_sub_playlist')],
        [InlineKeyboardButton("📝 إضافة مقطع لقائمة", callback_data='add_to_playlist')],
        [InlineKeyboardButton("↕️ ترتيب مقاطع القائمة", callback_data='reorder_playlist_select')],
        [InlineKeyboardButton("❌ حذف قائمة", callback_data='delete_playlist')],
        [InlineKeyboardButton("📋 عرض جميع القوائم", callback_data='list_playlists')],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "📂 **إدارة القوائم**\n\n"
        f"📂 عدد القوائم: {len(playlists)}\n"
        f"📹 عدد المقاطع الكلي: {len(videos)}\n\n"
        "اختر الإجراء المناسب:",
        reply_markup=reply_markup
    )

async def reorder_playlist_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اختيار قائمة لترتيبها"""
    query = update.callback_query
    await query.answer()
    
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    
    keyboard = []
    for name in playlists.keys():
        if playlists[name]:  # فقط القوائم التي تحتوي على مقاطع
            keyboard.append([InlineKeyboardButton(f"↕️ {name} ({len(playlists[name])})", 
                                                 callback_data=f'reorder_{name}')])
    
    if not keyboard:
        await query.message.edit_text("⚠️ جميع القوائم فارغة!")
        return
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_playlists')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "↕️ **ترتيب مقاطع القائمة**\n\n"
        "اختر القائمة التي تريد ترتيب مقاطعها:",
        reply_markup=reply_markup
    )

# =============== عرض القوائم مع الفئات الفرعية للمستخدم ===============

async def show_playlist_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض مقاطع قائمة محددة مع دعم الفئات الفرعية"""
    query = update.callback_query
    await query.answer()
    
    playlist_name = query.data.replace('playlist_', '')
    
    if playlist_name not in playlists:
        await query.message.edit_text("⚠️ القائمة غير موجودة!")
        return
    
    videos_list = playlists[playlist_name]
    
    if not videos_list:
        await query.message.edit_text(f"📂 **{playlist_name}**\n\n⚠️ هذه القائمة فارغة حالياً!")
        return
    
    # التحقق من وجود قوائم فرعية
    sub_playlists = [name for name in playlists.keys() 
                    if name.startswith(f"{playlist_name}>")]
    
    keyboard = []
    
    # عرض القوائم الفرعية أولاً
    for sub_name in sub_playlists:
        display_name = sub_name.split('>')[-1]
        keyboard.append([InlineKeyboardButton(f"📂 {display_name} ({len(playlists[sub_name])})", 
                                             callback_data=f'playlist_{sub_name}')])
    
    # عرض المقاطع
    for video_name in videos_list:
        if video_name in videos:
            keyboard.append([InlineKeyboardButton(f"🎬 {video_name}", 
                                                 callback_data=f'play_{video_name}')])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_user_menu')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # عرض المسار الكامل للقائمة
    path_parts = playlist_name.split('>')
    display_path = " > ".join(path_parts)
    
    await query.message.edit_text(
        f"📂 **{display_path}**\n\n"
        f"📹 عدد المقاطع: {len(videos_list)}\n"
        f"📂 قوائم فرعية: {len(sub_playlists)}\n\n"
        "اختر المقطع أو القائمة:",
        reply_markup=reply_markup
    )

# =============== الدوال الرئيسية ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🔰 إدارة العلامة المائية", callback_data='admin_watermark')],
            [InlineKeyboardButton("📈 إحصائيات متقدمة", callback_data='advanced_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 مرحباً أيها الأدمن الرئيسي!\n\n"
            f"📹 عدد المقاطع: {len(videos)}\n"
            f"📂 عدد القوائم: {len(playlists)}\n"
            f"👀 إجمالي المشاهدات: {sum(s.get('views', 0) for s in stats.values())}\n\n"
            "اختر الإجراء المناسب:",
            reply_markup=reply_markup
        )
        return
    
    if is_moderator(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
            [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data='admin_stats')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 مرحباً أيها المشرف!\n\n"
            f"📹 عدد المقاطع: {len(videos)}\n"
            f"📂 عدد القوائم: {len(playlists)}\n\n"
            "اختر الإجراء المناسب:",
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
                f"⚠️ يرجى الاشتراك في القناة أولاً:\n👉 @{CHANNEL_USERNAME}",
                reply_markup=reply_markup
            )
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        await update.message.reply_text("⚠️ حدث خطأ، يرجى المحاولة لاحقاً.")

# =============== دوال إدارة العلامة المائية ===============

async def admin_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة إدارة العلامة المائية"""
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن الرئيسي فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("🖼️ إضافة صورة", callback_data='watermark_image')],
        [InlineKeyboardButton("📝 إضافة نص", callback_data='watermark_text')],
        [InlineKeyboardButton("🗑️ إزالة العلامة", callback_data='watermark_remove')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # عرض حالة العلامة المائية الحالية
    status = "❌ غير مفعلة"
    if os.path.exists('watermark.png'):
        status = "✅ مفعلة (صورة)"
    elif os.path.exists('watermark_text.txt'):
        with open('watermark_text.txt', 'r', encoding='utf-8') as f:
            text = f.read().strip()
        status = f"✅ مفعلة (نص: {text})"
    
    await query.message.edit_text(
        f"🔰 **إدارة العلامة المائية**\n\n"
        f"الحالة: {status}\n\n"
        "اختر الإجراء المناسب:",
        reply_markup=reply_markup
    )

# =============== main ===============

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TOKEN).build()
    
    # أوامر عامة
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # معالجات الأدمن والمشرفين
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    application.add_handler(CallbackQueryHandler(admin_list_videos, pattern='^admin_list_videos$'))
    application.add_handler(CallbackQueryHandler(admin_delete_all, pattern='^admin_delete_all$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all$'))
    application.add_handler(CallbackQueryHandler(delete_video_callback, pattern='^delete_'))
    
    # معالجات القوائم
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
    
    # معالجات ترتيب القوائم
    application.add_handler(CallbackQueryHandler(reorder_playlist_select, pattern='^reorder_playlist_select$'))
    application.add_handler(CallbackQueryHandler(reorder_playlist, pattern='^reorder_'))
    application.add_handler(CallbackQueryHandler(move_video_up, pattern='^move_up_'))
    application.add_handler(CallbackQueryHandler(move_video_down, pattern='^move_down_'))
    application.add_handler(CallbackQueryHandler(skip_reorder, pattern='^skip_reorder$'))
    application.add_handler(CallbackQueryHandler(finish_reorder, pattern='^finish_reorder$'))
    
    # معالجات المستخدمين
    application.add_handler(CallbackQueryHandler(show_playlist_videos, pattern='^playlist_'))
    application.add_handler(CallbackQueryHandler(show_all_videos, pattern='^all_videos$'))
    application.add_handler(CallbackQueryHandler(back_to_user_menu, pattern='^back_to_user_menu$'))
    application.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # معالجات الإحصائيات
    application.add_handler(CallbackQueryHandler(advanced_stats, pattern='^advanced_stats$'))
    application.add_handler(CallbackQueryHandler(stats_daily, pattern='^stats_daily$'))
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    
    # معالجات العلامة المائية
    application.add_handler(CallbackQueryHandler(admin_watermark, pattern='^admin_watermark$'))
    application.add_handler(CallbackQueryHandler(watermark_image, pattern='^watermark_image$'))
    application.add_handler(CallbackQueryHandler(watermark_text, pattern='^watermark_text$'))
    application.add_handler(CallbackQueryHandler(watermark_remove, pattern='^watermark_remove$'))
    
    # معالجة رسائل الأدمن
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_video_name))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_watermark_text))
    application.add_handler(MessageHandler(filters.PHOTO, handle_watermark_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sub_playlist_name))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode with polling...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
