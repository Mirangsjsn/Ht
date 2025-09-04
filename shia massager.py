from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import logging
import asyncio
import re
import google.generativeai as genai

# ---------------------- تنظیمات ----------------------

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8382244442:AAG7GuULm2stKvFrEQMuv2I-wAjhHzQKCFg"
GEMINI_API_KEY = "AIzaSyB06-1uQlW6YfZ__SaJkziAnkvL3VUlmpM"  # جایگزین با کلید واقعی Gemini

GROUP_FILE = "groups.json"
ENEMIES_FILE = "enemies.json"
KEYWORDS_FILE = "keywords.json"

ADMIN_IDS = [6008938490]
MANAGER_TAGS = ["@connections01", "@SABERTA313", "@Shiaa_ghost1", "@TheShiningBlueWhale_Bot"]

# پیکربندی Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# ---------------------- مدیریت فایل ----------------------

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Load data
group_chat_ids = load_json(GROUP_FILE)
enemies = load_json(ENEMIES_FILE)
keywords = load_json(KEYWORDS_FILE)

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ---------------------- منوی دکمه‌ها ----------------------

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("➕ افزودن گروه", callback_data="add_group")],
        [InlineKeyboardButton("📋 لیست گروه‌ها", callback_data="list_groups")],
        [InlineKeyboardButton("📨 ارسال پیام", callback_data="send_message")],
        [InlineKeyboardButton("🧪 تست گروه", callback_data="test_group")],
        [InlineKeyboardButton("🚀 حمله (Attack)", callback_data="attack")],
        [InlineKeyboardButton("🔪 مدیریت دشمنان", callback_data="manage_enemies")],
        [InlineKeyboardButton("📝 مدیریت کلمات حساس", callback_data="manage_keywords")],
        [InlineKeyboardButton("💬 چت با Gemini", callback_data="chat_ai")],
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

# ---------------------- استارت ----------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔️ شما اجازه استفاده از این ربات را ندارید.")
        return
    await update.message.reply_text(
        "🤖 ربات حرفه‌ای فعال شد!\nاز دکمه‌ها برای کار با ربات استفاده کنید:",
        reply_markup=main_menu_keyboard()
    )

# ---------------------- شناسایی دشمن ----------------------

async def detect_enemy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or update.message.from_user.first_name

    if user_id in enemies:  
        if not enemies[user_id].get("tagged", False):  
            tags = " ".join(MANAGER_TAGS)  
            await update.message.reply_text(f"⚠️ دشمن شناسایی شد: @{username}\n{tags}")  
            enemies[user_id]["tagged"] = True  
            save_json(ENEMIES_FILE, enemies)  
    
    msg_text = update.message.text.lower()  
    for kw in keywords:  
        if kw.lower() in msg_text:  
            if user_id not in enemies:  
                enemies[user_id] = {"name": username, "tagged": True}  
                save_json(ENEMIES_FILE, enemies)  
            tags = " ".join(MANAGER_TAGS)  
            await update.message.reply_text(f"⚠️ کلمه حساس شناسایی شد: @{username}\n{tags}")  
            break

# ---------------------- چت با Gemini AI ----------------------

async def chat_with_gemini(message: str) -> str:
    try:
        # استفاده از مدل Gemini Pro
        model = genai.GenerativeModel('gemini-pro')
        
        # تولید پاسخ
        response = model.generate_content(f"لطفاً به زبان فارسی پاسخ دهید: {message}")
        
        return response.text
        
    except Exception as e:
        logger.error(f"خطا در ارتباط با Gemini: {e}")
        return f"❌ خطا در دریافت پاسخ از Gemini: {str(e)}"

# ---------------------- حمله به کاربر ----------------------

async def attack_user(target_user_id: str, message: str, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(target_user_id)
        for i in range(3):  # ارسال 3 پیام (کمتر برای جلوگیری از اسپم)
            try:
                await context.bot.send_message(chat_id=target_id, text=f"{message} ({i+1})")
                await asyncio.sleep(2)  # تاخیر بیشتر
            except Exception as e:
                logger.error(f"خطا در ارسال پیام حمله: {e}")
                return False
        return True
    except ValueError:
        return False

# ---------------------- هندلر دکمه‌ها ----------------------

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):    
        await query.edit_message_text("⛔️ شما اجازه استفاده ندارید.")    
        return    

    if query.data == "add_group":  
        await query.edit_message_text("➕ لطفاً آیدی عددی گروه را ارسال کنید:")  
        context.user_data["mode"] = "add_group_id"  
    
    elif query.data == "list_groups":  
        if not group_chat_ids:  
            await query.edit_message_text("📭 هیچ گروهی ذخیره نشده است!")  
        else:  
            text = "📋 لیست گروه‌ها:\n"    
            for gid, info in group_chat_ids.items():    
                text += f"- {info['title']} (ID: {gid})\n"  
            await query.edit_message_text(text)  
    
    elif query.data == "send_message":  
        await query.edit_message_text("📝 لطفاً متن پیام را برای ارسال به همه گروه‌ها ارسال کنید:")  
        context.user_data["mode"] = "send_message"  
    
    elif query.data == "test_group":  
        await query.edit_message_text("🧪 لطفاً آیدی عددی گروه برای تست ارسال کنید:")  
        context.user_data["mode"] = "test_group"  
    
    elif query.data == "attack":  
        await query.edit_message_text("🚀 لطفاً آیدی عددی کاربر برای حمله وارد کنید:")  
        context.user_data["mode"] = "attack_user_id"  
    
    elif query.data == "manage_enemies":  
        await query.edit_message_text("🔪 مدیریت دشمنان:", reply_markup=enemies_menu_keyboard())  
    
    elif query.data == "manage_keywords":  
        await query.edit_message_text("📝 مدیریت کلمات حساس:", reply_markup=keywords_menu_keyboard())  
    
    elif query.data == "chat_ai":  
        await query.edit_message_text("💬 حالت چت با Gemini AI فعال شد. پیام خود را ارسال کنید.")  
        context.user_data["mode"] = "chat_ai"  
    
    elif query.data == "help":  
        help_text = """📖 راهنما ربات:

🚀 ارسال پیام به گروه‌ها - ارسال پیام به تمام گروه‌های ذخیره شده
🔪 مدیریت دشمنان - افزودن، حذف و مشاهده دشمنان
📝 مدیریت کلمات حساس - کلمات برای شناسایی اتوماتیک دشمنان
💬 چت با Gemini - گفتگو با هوش مصنوعی Gemini AI
🧪 تست گروه - آزمایش اتصال به گروه
🚀 حمله - ارسال پیام‌های مکرر به کاربر هدف
"""
        await query.edit_message_text(help_text)

    elif query.data == "back_to_main":  
        await query.edit_message_text(  
            "🤖 ربات حرفه‌ای فعال شد!\nاز دکمه‌ها استفاده کنید:",  
            reply_markup=main_menu_keyboard()  
        )  
    
    elif query.data == "add_enemy":  
        await query.edit_message_text("🔪 لطفاً آیدی عددی دشمن را ارسال کنید:")  
        context.user_data["mode"] = "add_enemy"  
    
    elif query.data == "list_enemies":  
        if not enemies:  
            await query.edit_message_text("📭 هیچ دشمنی ثبت نشده است!")  
        else:  
            text_list = "📋 لیست دشمنان:\n"  
            for eid, info in enemies.items():  
                text_list += f"- آیدی: {eid}, نام: {info.get('name','ناشناس')}\n"  
            await query.edit_message_text(text_list)  
    
    elif query.data == "remove_enemy":  
        await query.edit_message_text("🗑️ لطفاً آیدی عددی دشمن برای حذف ارسال کنید:")  
        context.user_data["mode"] = "remove_enemy"  
    
    elif query.data == "add_keyword":  
        await query.edit_message_text("📝 لطفاً کلمه حساس جدید را ارسال کنید:")  
        context.user_data["mode"] = "add_keyword"  
    
    elif query.data == "list_keywords":  
        if not keywords:  
            await query.edit_message_text("📭 هیچ کلمه‌ای ذخیره نشده است!")  
        else:  
            text_list = "📋 لیست کلمات حساس:\n"  
            for kw in keywords:  
                text_list += f"- {kw}\n"  
            await query.edit_message_text(text_list)  
    
    elif query.data == "remove_keyword":  
        await query.edit_message_text("🗑️ لطفاً کلمه حساس برای حذف ارسال کنید:")  
        context.user_data["mode"] = "remove_keyword"

# ---------------------- هندلر پیام‌ها ----------------------

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_admin(user_id):  
        await detect_enemy(update, context)  
        return  

    mode = context.user_data.get("mode")  
    text = update.message.text  

    if not mode:  
        return  

    # ---------- مدیریت گروه‌ها ----------  
    if mode == "add_group_id":  
        if not re.match(r'^-?\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد!")  
            return  
        context.user_data["new_group_id"] = text  
        context.user_data["mode"] = "add_group_name"  
        await update.message.reply_text("➕ حالا نام گروه را ارسال کنید:")  
    
    elif mode == "add_group_name":  
        gid = context.user_data.pop("new_group_id")  
        group_chat_ids[gid] = {"title": text}  
        save_json(GROUP_FILE, group_chat_ids)  
        context.user_data["mode"] = None  
        await update.message.reply_text(f"✅ گروه '{text}' با آیدی {gid} اضافه شد.")  
    
    elif mode == "send_message":  
        success = 0  
        failed = 0  
        for gid in group_chat_ids:  
            try:  
                await context.bot.send_message(chat_id=int(gid), text=text)  
                success += 1  
            except Exception as e:  
                logger.error(f"خطا در ارسال پیام به {gid}: {e}")  
                failed += 1  
        context.user_data["mode"] = None  
        await update.message.reply_text(f"✅ ارسال پیام تکمیل شد:\n✅ موفق: {success}\n❌ ناموفق: {failed}")  
    
    elif mode == "test_group":  
        if not re.match(r'^-?\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد!")  
            return  
        try:  
            await context.bot.send_message(chat_id=int(text), text="✅ تست موفق بود! این گروه برای ربات قابل دسترسی است.")  
            await update.message.reply_text(f"✅ پیام تست به {text} ارسال شد.")  
        except Exception as e:  
            await update.message.reply_text(f"❌ خطا در ارسال: {e}")  
        context.user_data["mode"] = None  

    # ---------- حمله به کاربر ----------  
    elif mode == "attack_user_id":  
        if not re.match(r'^-?\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد!")  
            return  
        context.user_data["attack_target"] = text  
        context.user_data["mode"] = "attack_message"  
        await update.message.reply_text("🚀 لطفاً متن پیام برای حمله ارسال کنید:")  
    
    elif mode == "attack_message":  
        target_id = context.user_data.pop("attack_target")  
        await update.message.reply_text("🚀 شروع حمله...")  
        success = await attack_user(target_id, text, context)  
        if success:  
            await update.message.reply_text(f"✅ حمله به کاربر {target_id} تکمیل شد!")  
        else:  
            await update.message.reply_text("❌ خطا در حمله به کاربر!")  
        context.user_data["mode"] = None  

    # ---------- مدیریت دشمنان ----------  
    elif mode == "add_enemy":  
        if not re.match(r'^\d+$', text):  
            await update.message.reply_text("❌ آیدی باید عددی باشد!")  
            return  
        enemy_id = str(text)  
        enemies[enemy_id] = {"name": "ناشناس", "tagged": False}  
        save_json(ENEMIES_FILE, enemies)  
        context.user_data["mode"] = None  
        await update.message.reply_text(f"✅ دشمن با آیدی {enemy_id} اضافه شد.")  
    
    elif mode == "remove_enemy":  
        enemy_id = str(text)  
        if enemy_id in enemies:  
            del enemies[enemy_id]  
            save_json(ENEMIES_FILE, enemies)  
            await update.message.reply_text(f"✅ دشمن با آیدی {enemy_id} حذف شد.")  
        else:  
            await update.message.reply_text("❌ دشمنی با این آیدی یافت نشد!")  
        context.user_data["mode"] = None  

    # ---------- مدیریت کلمات حساس ----------  
    elif mode == "add_keyword":  
        keywords[text] = {"active": True}  
        save_json(KEYWORDS_FILE, keywords)  
        context.user_data["mode"] = None  
        await update.message.reply_text(f"✅ کلمه حساس '{text}' اضافه شد.")  
    
    elif mode == "remove_keyword":  
        if text in keywords:  
            del keywords[text]  
            save_json(KEYWORDS_FILE, keywords)  
            await update.message.reply_text(f"✅ کلمه حساس '{text}' حذف شد.")  
        else:  
            await update.message.reply_text("❌ کلمه یافت نشد!")  
        context.user_data["mode"] = None  

    # ---------- چت با Gemini AI ----------  
    elif mode == "chat_ai":  
        await update.message.reply_chat_action("typing")  
        response = await chat_with_gemini(text)  
        await update.message.reply_text(f"💬 Gemini AI:\n\n{response}")  
        # حالت چت باقی می‌ماند برای ادامه گفتگو

# ---------------------- اجرای اصلی ----------------------

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("🤖 ربات با Gemini AI در حال اجرا است...")  
    app.run_polling()

if __name__ == "__main__":
    main()