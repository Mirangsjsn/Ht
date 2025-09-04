from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import logging
import asyncio
import re
import random
import datetime
from typing import Dict, List, Any

# ---------------------- تنظیمات ----------------------

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8382244442:AAHLxq1gCOmRWjMVkHPTPERBwAx2Bwht4HE"

GROUP_FILE = "groups.json"
ENEMIES_FILE = "enemies.json"
KEYWORDS_FILE = "keywords.json"
ATTACK_WORDS_FILE = "attack_words.json"
DEFAULT_GROUP_FILE = "default_group.json"

ADMIN_IDS = [6008938490]
MANAGER_TAGS = ["@connections01", "@SABERTA313", "@Shiaa_ghost1", "@TheShiningBlueWhale_Bot"]

# ---------------------- مدیریت فایل ----------------------

def load_json(file_path: str) -> Dict:
    """بارگذاری داده از فایل JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file_path: str, data: Dict) -> None:
    """ذخیره داده در فایل JSON"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Load data
group_chat_ids = load_json(GROUP_FILE)
enemies = load_json(ENEMIES_FILE)
keywords = load_json(KEYWORDS_FILE)
attack_words = load_json(ATTACK_WORDS_FILE)
default_group = load_json(DEFAULT_GROUP_FILE)

def is_admin(user_id: int) -> bool:
    """بررسی آیا کاربر ادمین است"""
    return user_id in ADMIN_IDS

def log_action(action: str, user_id: int, details: str = "") -> None:
    """ثبت لاگ اقدامات"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {action} - User: {user_id}"
    if details:
        log_message += f" - Details: {details}"
    logger.info(log_message)

# ---------------------- منوی دکمه‌ها ----------------------

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه", callback_data="add_group")],
        [InlineKeyboardButton("📋 لیست گروه‌ها", callback_data="list_groups")],

        [InlineKeyboardButton("⭐ گروه پیشفرض", callback_data="set_default_group")],
        [InlineKeyboardButton("📨 ارسال پیام", callback_data="send_message")],
        [InlineKeyboardButton("🧪 تست گروه", callback_data="test_group")],
        [InlineKeyboardButton("🚀 حمله (Attack)", callback_data="attack")],
        [InlineKeyboardButton("🔪 مدیریت دشمنان", callback_data="manage_enemies")],
        [InlineKeyboardButton("📝 مدیریت کلمات حساس", callback_data="manage_keywords")],
        [InlineKeyboardButton("⚔️ مدیریت کلمات حمله", callback_data="manage_attack_words")],

        [InlineKeyboardButton("📊 آمار ربات", callback_data="stats")],
        [InlineKeyboardButton("📖 راهنما", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def enemies_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ افزودن دشمن", callback_data="add_enemy")],
        [InlineKeyboardButton("📋 لیست دشمنان", callback_data="list_enemies")],
        [InlineKeyboardButton("🗑️ حذف دشمن", callback_data="remove_enemy")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def keywords_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کلمه حساس", callback_data="add_keyword")],
        [InlineKeyboardButton("📋 لیست کلمات", callback_data="list_keywords")],
        [InlineKeyboardButton("🗑️ حذف کلمه", callback_data="remove_keyword")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def attack_words_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ افزودن کلمات حمله", callback_data="add_attack_words")],
        [InlineKeyboardButton("📋 لیست کلمات حمله", callback_data="list_attack_words")],
        [InlineKeyboardButton("🗑️ حذف همه کلمات", callback_data="clear_attack_words")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ---------------------- استارت ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("⛔️ شما اجازه استفاده از این ربات را ندارید.")
        log_action("ACCESS_DENIED", user_id, "Non-admin tried to use bot")
        return
    
    log_action("BOT_START", user_id)
    
    # نمایش گروه پیشفرض اگر وجود دارد
    welcome_text = "🤖 ربات حرفه‌ای فعال شد!\nاز دکمه‌ها برای کار با ربات استفاده کنید:"
    
    if default_group:
        group_id = list(default_group.keys())[0]
        group_info = default_group[group_id]
        welcome_text += f"\n\n⭐ گروه پیشفرض: {group_info.get('title', 'بدون نام')} ({group_id})"
    
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard())

# ---------------------- شناسایی دشمن ----------------------

async def detect_enemy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شناسایی خودکار دشمنان بر اساس کلمات حساس"""
    # اگر پیام از یک گروه باشد، بررسی نکنیم
    if update.message.chat.type != "private":
        return
        
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or update.message.from_user.first_name
    user_fullname = f"{update.message.from_user.first_name} {update.message.from_user.last_name or ''}".strip()

    # بررسی کلمات حساس
    msg_text = update.message.text.lower() if update.message.text else ""
    
    detected_keywords = []
    for kw in keywords:  
        if kw.lower() in msg_text:  
            detected_keywords.append(kw)
            if user_id not in enemies:  
                enemies[user_id] = {
                    "name": username,
                    "fullname": user_fullname,
                    "tagged": False, 
                    "reason": f"کلمه حساس: {kw}",
                    "detected_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }  
                save_json(ENEMIES_FILE, enemies)
                log_action("ENEMY_DETECTED", int(user_id), f"Keyword: {kw}")
    
    if detected_keywords and not enemies[user_id].get("tagged", False):  
        tags = " ".join(MANAGER_TAGS)  
        await update.message.reply_text(
            f"⚠️ کلمه حساس شناسایی شد!\n"
            f"👤 کاربر: @{username} ({user_fullname})\n"
            f"🔍 کلمات: {', '.join(detected_keywords)}\n"
            f"🆔 آیدی: {user_id}\n\n"
            f"{tags}"
        )  
        enemies[user_id]["tagged"] = True  
        save_json(ENEMIES_FILE, enemies)

# ---------------------- حمله به کاربر ----------------------

async def attack_user(target_username: str, count: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ارسال پیام‌های حمله به کاربر"""
    try:
        success_count = 0
        
        # بررسی وجود گروه پیشفرض
        if not default_group:
            logger.error("هیچ گروه پیشفرضی تنظیم نشده است")
            return False
            
        group_id = list(default_group.keys())[0]
        group_info = default_group[group_id]
        
        for i in range(count):  # ارسال تعداد مشخص پیام
            try:
                # انتخاب یک کلمه رندوم از لیست کلمات حمله
                if attack_words:
                    random_word = random.choice(list(attack_words.keys()))
                    message = f"@{target_username} {random_word}"
                else:
                    message = f"@{target_username} 🚀"
                
                # اضافه کردن تأخیر تصادفی برای جلوگیری از تشخیص اسپم
                delay = random.uniform(2, 5)
                await asyncio.sleep(delay)
                
                # ارسال در گروه پیشفرض
                await context.bot.send_message(
                    chat_id=int(group_id), 
                    text=f"{message}\n\n[{i+1}/{count}]"
                )
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"خطا در ارسال پیام حمله: {e}")
                continue
                
        return success_count > 0
    except Exception as e:
        logger.error(f"خطا در حمله: {e}")
        return False

# ---------------------- ارسال پیام به گروه‌ها ----------------------

async def broadcast_to_groups(message: str, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, int]:
    """ارسال پیام به تمام گروه‌های ذخیره شده"""
    success = 0
    failed = 0
    failed_groups = []
    
    for gid, group_info in group_chat_ids.items():
        try:
            await context.bot.send_message(chat_id=int(gid), text=message)
            success += 1
            await asyncio.sleep(0.3)  # تاخیر بین ارسال پیام‌ها
        except Exception as e:
            logger.error(f"خطا در ارسال به گروه {gid}: {e}")
            failed += 1
            failed_groups.append(f"{group_info.get('title', 'Unknown')} ({gid})")
            
    return {"success": success, "failed": failed, "failed_groups": failed_groups}

# ---------------------- هندلر دکمه‌ها ----------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):    
        await query.edit_message_text("⛔️ شما اجازه استفاده ندارید.")    
        log_action("BUTTON_ACCESS_DENIED", user_id)
        return    

    log_action("BUTTON_CLICK", user_id, f"Button: {query.data}")

    if query.data == "add_group":  
        await query.edit_message_text("➕ لطفاً آیدی عددی گروه را ارسال کنید (مثال: -1001511872349):", reply_markup=back_keyboard())  
        context.user_data["mode"] = "add_group_id"  
    
    elif query.data == "list_groups":  
        if not group_chat_ids:  
            await query.edit_message_text("📭 هیچ گروهی ذخیره نشده است!", reply_markup=back_keyboard())  
        else:  
            text = "📋 لیست گروه‌ها:\n\n"    
            for gid, info in group_chat_ids.items():    
                text += f"🏷️ {info.get('title', 'بدون نام')}\n🆔 {gid}\n\n"  
            await query.edit_message_text(text, reply_markup=back_keyboard())  
    
    elif query.data == "remove_group":  
        await query.edit_message_text("🗑️ لطفاً آیدی عددی گروه برای حذف ارسال کنید:", reply_markup=back_keyboard())  
        context.user_data["mode"] = "remove_group"  
    
    elif query.data == "set_default_group":  
        if not group_chat_ids:  
            await query.edit_message_text("📭 هیچ گروهی ذخیره نشده است! ابتدا یک گروه اضافه کنید.", reply_markup=back_keyboard())  
        else:  
            text = "⭐ انتخاب گروه پیشفرض:\n\n"    
            for gid, info in group_chat_ids.items():    
                is_default = " ✅" if gid in default_group else ""
                text += f"🏷️ {info.get('title', 'بدون نام')}{is_default}\n🆔 {gid}\n\n"  
            
            text += "\nلطفاً آیدی گروه را برای تنظیم به عنوان پیشفرض ارسال کنید:"
            await query.edit_message_text(text, reply_markup=back_keyboard())  
            context.user_data["mode"] = "set_default_group"  
    
    elif query.data == "send_message":  
        await query.edit_message_text("📝 لطفاً متن پیام را برای ارسال به همه گروه‌ها ارسال کنید:", reply_markup=back_keyboard())  
        context.user_data["mode"] = "send_message"  
    
    elif query.data == "test_group":  
        await query.edit_message_text("🧪 لطفاً آیدی عددی گروه برای تست ارسال کنید (مثال: -1001511872349):", reply_markup=back_keyboard())  
        context.user_data["mode"] = "test_group"  
    
    elif query.data == "attack":  
        # بررسی وجود گروه پیشفرض
        if not default_group:
            await query.edit_message_text(
                "❌ هیچ گروه پیشفرضی تنظیم نشده است!\n"
                "لطفاً ابتدا از منوی اصلی یک گروه پیشفرض تنظیم کنید.",
                reply_markup=back_keyboard()
            )
            return
            
        group_id = list(default_group.keys())[0]
        group_info = default_group[group_id]
        
        await query.edit_message_text(
            f"🚀 لطفاً یوزرنیم کاربر برای حمله وارد کنید (بدون @):\n\n"
            f"مثال: username123\n\n"
            f"⭐ گروه پیشفرض: {group_info.get('title', 'بدون نام')} ({group_id})",
            reply_markup=back_keyboard()
        )  
        context.user_data["mode"] = "attack_username"  
    
    elif query.data == "manage_enemies":  
        await query.edit_message_text("🔪 مدیریت دشمنان:", reply_markup=enemies_menu_keyboard())  
    
    elif query.data == "manage_keywords":  
        await query.edit_message_text("📝 مدیریت کلمات حساس:", reply_markup=keywords_menu_keyboard())  
    
    elif query.data == "manage_attack_words":  
        await query.edit_message_text("⚔️ مدیریت کلمات حمله:", reply_markup=attack_words_menu_keyboard())  
    
    elif query.data == "stats":  
        stats_text = f"""
📊 آمار ربات:

👥 گروه‌ها: {len(group_chat_ids)}
⭐ گروه پیشفرض: {'تنظیم شده' if default_group else 'تنظیم نشده'}
🎯 دشمنان: {len(enemies)}
🔑 کلمات حساس: {len(keywords)}
⚔️ کلمات حمله: {len(attack_words)}
🕒 آخرین بروزرسانی: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
        await query.edit_message_text(stats_text, reply_markup=back_keyboard())
    
    elif query.data == "help":  
        help_text = """📖 راهنما ربات:

🚀 ارسال پیام به گروه‌ها - ارسال پیام به تمام گروه‌های ذخیره شده
⭐ گروه پیشفرض - تنظیم گروه برای حمله‌های پیشفرض
🔪 مدیریت دشمنان - افزودن، حذف و مشاهده دشمنان
📝 مدیریت کلمات حساس - کلمات برای شناسایی اتوماتیک دشمنان
⚔️ مدیریت کلمات حمله - کلمات برای استفاده در حمله
🧪 تست گروه - آزمایش اتصال به گروه
🚀 حمله - ارسال پیام‌های مکرر به کاربر هدف در گروه پیشفرض
📊 آمار - مشاهده آمار ربات



⚠️ توجه: این ربات فقط برای ادمین‌ها قابل استفاده است.
"""
        await query.edit_message_text(help_text, reply_markup=back_keyboard())

    elif query.data == "cancel_operation":  
        if "mode" in context.user_data:
            del context.user_data["mode"]
        await query.edit_message_text("✅ عملیات لغو شد.", reply_markup=main_menu_keyboard())  
    
    elif query.data == "back_to_main":  
        if "mode" in context.user_data:
            del context.user_data["mode"]
        await query.edit_message_text(  
            "🤖 ربات حرفه‌ای فعال شد!\nاز دکمه‌ها استفاده کنید:",  
            reply_markup=main_menu_keyboard()  
        )  
    
    elif query.data == "add_enemy":  
        await query.edit_message_text("🔪 لطفاً یوزرنیم دشمن را ارسال کنید (بدون @):", reply_markup=back_keyboard())  
        context.user_data["mode"] = "add_enemy"  
    
    elif query.data == "list_enemies":  
        if not enemies:  
            await query.edit_message_text("📭 هیچ دشمنی ثبت نشده است!", reply_markup=back_keyboard())  
        else:  
            text_list = "📋 لیست دشمنان:\n\n"  
            for eid, info in enemies.items():  
                text_list += f"👤 {info.get('name', 'ناشناس')}\n🆔 {eid}\n📅 {info.get('detected_at', 'تاریخ نامعلوم')}\n\n"  
            await query.edit_message_text(text_list, reply_markup=back_keyboard())  
    
    elif query.data == "remove_enemy":  
        await query.edit_message_text("🗑️ لطفاً آیدی عددی دشمن برای حذف ارسال کنید:", reply_markup=back_keyboard())  
        context.user_data["mode"] = "remove_enemy"  
    
    elif query.data == "add_keyword":  
        await query.edit_message_text("📝 لطفاً کلمه حساس جدید را ارسال کنید:", reply_markup=back_keyboard())  
        context.user_data["mode"] = "add_keyword"  
    
    elif query.data == "list_keywords":  
        if not keywords:  
            await query.edit_message_text("📭 هیچ کلمه‌ای ذخیره نشده است!", reply_markup=back_keyboard())  
        else:  
            text_list = "📋 لیست کلمات حساس:\n\n"  
            for kw in keywords:  
                text_list += f"🔸 {kw}\n"  
            await query.edit_message_text(text_list, reply_markup=back_keyboard())  
    
    elif query.data == "remove_keyword":  
        await query.edit_message_text("🗑️ لطفاً کلمه حساس برای حذف ارسال کنید:", reply_markup=back_keyboard())  
        context.user_data["mode"] = "remove_keyword"
    
    elif query.data == "add_attack_words":  
        await query.edit_message_text(
            "⚔️ لطفاً کلمات حمله را ارسال کنید (هر خط یک کلمه):\n\n"
            "مثال:\n"
            "کلمه اول\n"
            "کلمه دوم\n"
            "کلمه سوم",
            reply_markup=back_keyboard()
        )  
        context.user_data["mode"] = "add_attack_words"  
    
    elif query.data == "list_attack_words":  
        if not attack_words:  
            await query.edit_message_text("📭 هیچ کلمه حمله‌ای ذخیره نشده است!", reply_markup=back_keyboard())  
        else:  
            text_list = "📋 لیست کلمات حمله:\n\n"  
            for word in attack_words:  
                text_list += f"⚡ {word}\n"  
            await query.edit_message_text(text_list, reply_markup=back_keyboard())  
    
    elif query.data == "clear_attack_words":  
        attack_words.clear()
        save_json(ATTACK_WORDS_FILE, attack_words)
        await query.edit_message_text("✅ تمام کلمات حمله حذف شدند.", reply_markup=back_keyboard())

# ---------------------- هندلر پیام‌ها ----------------------

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # همیشه دشمن‌یابی انجام شود
    await detect_enemy(update, context)
    
    if not is_admin(user_id):  
        return  

    mode = context.user_data.get("mode")  
    text = update.message.text.strip()  

    if not mode:  
        return  

    # ---------- مدیریت گروه‌ها ----------  
    if mode == "add_group_id":  
        if not re.match(r'^-?\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد! (مثال: -1001511872349 یا 123456789)")  
            return  
        context.user_data["new_group_id"] = text  
        context.user_data["mode"] = "add_group_name"  
        await update.message.reply_text("➕ حالا نام گروه را ارسال کنید:")  
    
    elif mode == "add_group_name":  
        gid = context.user_data.pop("new_group_id")  
        group_chat_ids[gid] = {"title": text, "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
        save_json(GROUP_FILE, group_chat_ids)  
        context.user_data["mode"] = None  
        log_action("GROUP_ADDED", user_id, f"Group: {text} ({gid})")
        await update.message.reply_text(f"✅ گروه '{text}' با آیدی {gid} اضافه شد.", reply_markup=main_menu_keyboard())  
    
    elif mode == "remove_group":  
        if text in group_chat_ids:  
            group_name = group_chat_ids[text].get("title", "بدون نام")
            del group_chat_ids[text]  
            save_json(GROUP_FILE, group_chat_ids)  
            
            # اگر گروه پیشفرض بود، آن را نیز حذف کن
            if text in default_group:
                del default_group[text]
                save_json(DEFAULT_GROUP_FILE, default_group)
                
            log_action("GROUP_REMOVED", user_id, f"Group: {group_name} ({text})")
            await update.message.reply_text(f"✅ گروه '{group_name}' با آیدی {text} حذف شد.", reply_markup=main_menu_keyboard())  
        else:  
            await update.message.reply_text("❌ گروهی با این آیدی یافت نشد!", reply_markup=main_menu_keyboard())  
        context.user_data["mode"] = None  
    
    elif mode == "set_default_group":  
        if text in group_chat_ids:  
            # حذف گروه پیشفرض قبلی
            default_group.clear()
            
            # تنظیم گروه پیشفرض جدید
            group_info = group_chat_ids[text]
            default_group[text] = group_info
            save_json(DEFAULT_GROUP_FILE, default_group)
            
            context.user_data["mode"] = None  
            log_action("DEFAULT_GROUP_SET", user_id, f"Group: {group_info.get('title', 'بدون نام')} ({text})")
            await update.message.reply_text(
                f"✅ گروه پیشفرض تنظیم شد:\n"
                f"🏷️ {group_info.get('title', 'بدون نام')}\n"
                f"🆔 {text}",
                reply_markup=main_menu_keyboard()
            )  
        else:  
            await update.message.reply_text("❌ گروهی با این آیدی یافت نشد!", reply_markup=main_menu_keyboard())  
    
    elif mode == "send_message":  
        await update.message.reply_text("📨 در حال ارسال پیام به همه گروه‌ها...")  
        result = await broadcast_to_groups(text, context)  
        context.user_data["mode"] = None  
        
        response_text = f"✅ ارسال پیام تکمیل شد:\n✅ موفق: {result['success']}\n❌ ناموفق: {result['failed']}"
        
        if result['failed_groups']:
            response_text += f"\n\n❌ گروه‌های ناموفق:\n" + "\n".join(result['failed_groups'][:5])
            if len(result['failed_groups']) > 5:
                response_text += f"\n... و {len(result['failed_groups']) - 5} گروه دیگر"
                
        await update.message.reply_text(response_text, reply_markup=main_menu_keyboard())  
    
    elif mode == "test_group":  
        if not re.match(r'^-?\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد! (مثال: -1001511872349 یا 123456789)")  
            return  
        try:  
            await context.bot.send_message(chat_id=int(text), text="✅ تست موفق بود! این گروه برای ربات قابل دسترسی است.")  
            log_action("GROUP_TESTED", user_id, f"Group: {text} - Success")
            await update.message.reply_text(f"✅ پیام تست به {text} ارسال شد.", reply_markup=main_menu_keyboard())  
        except Exception as e:  
            log_action("GROUP_TESTED", user_id, f"Group: {text} - Failed: {e}")
            await update.message.reply_text(f"❌ خطا در ارسال: {e}", reply_markup=main_menu_keyboard())  
        context.user_data["mode"] = None  

    # ---------- حمله به کاربر ----------  
    elif mode == "attack_username":  
        # حذف @ اگر وجود داشت
        username = text.replace('@', '').strip()
        if not username:
            await update.message.reply_text("❌ یوزرنیم نمی‌تواند خالی باشد!")
            return
            
        context.user_data["attack_username"] = username  
        context.user_data["mode"] = "attack_count"  
        await update.message.reply_text("🔢 لطفاً تعداد پیام‌های حمله را وارد کنید:")  
    
    elif mode == "attack_count":  
        try:
            count = int(text)
            if count <= 0 or count > 50:
                await update.message.reply_text("❌ تعداد باید بین 1 تا 50 باشد!")
                return
                
            username = context.user_data["attack_username"]
            group_id = list(default_group.keys())[0]
            group_info = default_group[group_id]
            
            await update.message.reply_text("🚀 شروع حمله...")  
            success = await attack_user(username, count, context)  
            
            if success:  
                log_action("ATTACK_SUCCESS", user_id, f"Target: @{username}, Count: {count}, Group: {group_id}")
                await update.message.reply_text(
                    f"✅ حمله به کاربر @{username} تکمیل شد!\n"
                    f"📊 تعداد: {count} پیام\n"
                    f"👥 گروه: {group_info.get('title', 'بدون نام')} ({group_id})",
                    reply_markup=main_menu_keyboard()
                )  
            else:  
                log_action("ATTACK_FAILED", user_id, f"Target: @{username}")
                await update.message.reply_text("❌ خطا در حمله به کاربر!", reply_markup=main_menu_keyboard())  
            context.user_data["mode"] = None  
        except ValueError:
            await update.message.reply_text("❌ تعداد باید عدد باشد!")

    # ---------- مدیریت دشمنان ----------  
    elif mode == "add_enemy":  
        # حذف @ اگر وجود داشت
        username = text.replace('@', '').strip()
        if not username:
            await update.message.reply_text("❌ یوزرنیم نمی‌تواند خالی باشد!")
            return
            
        enemy_id = f"@{username}"  
        enemies[enemy_id] = {
            "name": username, 
            "tagged": False,
            "added_manually": True,
            "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }  
        save_json(ENEMIES_FILE, enemies)  
        context.user_data["mode"] = None  
        log_action("ENEMY_ADDED", user_id, f"Enemy: @{username}")
        await update.message.reply_text(f"✅ دشمن @{username} اضافه شد.", reply_markup=main_menu_keyboard())  
    
    elif mode == "remove_enemy":  
        enemy_id = text  
        if enemy_id in enemies:  
            enemy_name = enemies[enemy_id].get("name", "ناشناس")
            del enemies[enemy_id]  
            save_json(ENEMIES_FILE, enemies)  
            log_action("ENEMY_REMOVED", user_id, f"Enemy: {enemy_name} ({enemy_id})")
            await update.message.reply_text(f"✅ دشمن {enemy_id} حذف شد.", reply_markup=main_menu_keyboard())  
        else:  
            await update.message.reply_text("❌ دشمنی با این آیدی یافت نشد!", reply_markup=main_menu_keyboard())  
        context.user_data["mode"] = None  

    # ---------- مدیریت کلمات حساس ----------  
    elif mode == "add_keyword":  
        if text in keywords:  
            await update.message.reply_text("⚠️ این کلمه قبلاً اضافه شده است!", reply_markup=main_menu_keyboard())  
        else:  
            keywords[text] = {
                "active": True,
                "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }  
            save_json(KEYWORDS_FILE, keywords)  
            log_action("KEYWORD_ADDED", user_id, f"Keyword: {text}")
            await update.message.reply_text(f"✅ کلمه حساس '{text}' اضافه شد.", reply_markup=main_menu_keyboard())  
        context.user_data["mode"] = None  
    
    elif mode == "remove_keyword":  
        if text in keywords:  
            del keywords[text]  
            save_json(KEYWORDS_FILE, keywords)  
            log_action("KEYWORD_REMOVED", user_id, f"Keyword: {text}")
            await update.message.reply_text(f"✅ کلمه حساس '{text}' حذف شد.", reply_markup=main_menu_keyboard())  
        else:  
            await update.message.reply_text("❌ کلمه یافت نشد!", reply_markup=main_menu_keyboard())  
        context.user_data["mode"] = None  

    # ---------- مدیریت کلمات حمله ----------  
    elif mode == "add_attack_words":  
        lines = text.split('\n')
        added_count = 0
        
        for line in lines:
            word = line.strip()
            if word and word not in attack_words:
                attack_words[word] = {
                    "added_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                added_count += 1
        
        save_json(ATTACK_WORDS_FILE, attack_words)
        context.user_data["mode"] = None  
        log_action("ATTACK_WORDS_ADDED", user_id, f"Count: {added_count}")
        await update.message.reply_text(
            f"✅ {added_count} کلمه حمله اضافه شد.\n"
            f"📊 کل کلمات: {len(attack_words)}",
            reply_markup=main_menu_keyboard()
        )

# ---------------------- دستورات اضافی ----------------------

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو عملیات جاری"""
    if not is_admin(update.effective_user.id):
        return
        
    if "mode" in context.user_data:
        del context.user_data["mode"]
        log_action("OPERATION_CANCELLED", update.effective_user.id)
    await update.message.reply_text("✅ عملیات جاری لغو شد.", reply_markup=main_menu_keyboard())

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار ربات"""
    if not is_admin(update.effective_user.id):
        return
        
    default_group_info = ""
    if default_group:
        group_id = list(default_group.keys())[0]
        group_info = default_group[group_id]
        default_group_info = f"⭐ گروه پیشفرض: {group_info.get('title', 'بدون نام')} ({group_id})"
    else:
        default_group_info = "⭐ گروه پیشفرض: تنظیم نشده"
        
    stats_text = f"""
📊 آمار ربات:

👥 گروه‌ها: {len(group_chat_ids)}
{default_group_info}
🎯 دشمنان: {len(enemies)}
🔑 کلمات حساس: {len(keywords)}
⚔️ کلمات حمله: {len(attack_words)}
🕒 آخرین بروزرسانی: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

💾 حافظه مصرفی:
• گروه‌ها: {len(str(group_chat_ids))} کاراکتر
• دشمنان: {len(str(enemies))} کاراکتر
• کلمات: {len(str(keywords))} کاراکتر
• کلمات حمله: {len(str(attack_words))} کاراکتر
"""
    log_action("STATS_VIEWED", update.effective_user.id)
    await update.message.reply_text(stats_text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ارسال پیام به همه گروه‌ها از طریق دستور"""
    if not is_admin(update.effective_user.id):
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ لطفاً پیام را بعد از دستور وارد کنید: /broadcast <پیام>")
        return
        
    message = " ".join(context.args)
    await update.message.reply_text("📨 در حال ارسال پیام به همه گروه‌ها...")
    
    result = await broadcast_to_groups(message, context)
    log_action("BROADCAST", update.effective_user.id, f"Success: {result['success']}, Failed: {result['failed']}")
    
    response_text = f"✅ ارسال کامل شد:\n✅ موفق: {result['success']}\n❌ ناموفق: {result['failed']}"
    await update.message.reply_text(response_text)

# ---------------------- اجرای اصلی ----------------------

def main():
    """تابع اصلی اجرای ربات"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # نمایش اطلاعات راه‌اندازی
    logger.info("🤖 ربات در حال اجرا است...")  
    print("=" * 50)
    print("✅ ربات با موفقیت راه‌اندازی شد!")
    print(f"👮 ادمین‌ها: {ADMIN_IDS}")
    print(f"👥 گروه‌های ذخیره شده: {len(group_chat_ids)}")
    print(f"⭐ گروه پیشفرض: {'تنظیم شده' if default_group else 'تنظیم نشده'}")
    print(f"🎯 دشمنان شناسایی شده: {len(enemies)}")
    print(f"🔑 کلمات حساس: {len(keywords)}")
    print(f"⚔️ کلمات حمله: {len(attack_words)}")
    print(f"🏷️ تگ‌های مدیر: {MANAGER_TAGS}")
    print("=" * 50)
    
    # راه‌اندازی ربات
    app.run_polling()

if __name__ == "__main__":
    main()