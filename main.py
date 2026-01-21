from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    InlineQueryHandler,
    CallbackQueryHandler,
    ContextTypes,
)
import uuid
import asyncio
import os
import logging

# ================== LOGGING ==================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== TOKEN ==================
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable tapılmadı!")

# ================== SECRET STORAGE ==================
SECRETS = {}

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_username = (await context.bot.get_me()).username
    await update.message.reply_text(
        "🤖 *Secret Message Bot*\n\n"
        "📝 *İstifadə qaydası:*\n"
        f"1️⃣ İstənilən çatda `@{bot_username}` yazın\n"
        "2️⃣ Sonra: `istifadəçi_adı mesajınız`\n"
        "3️⃣ Mesajı seçib göndərin\n\n"
        "💡 *Nümunə:*\n"
        f"`@{bot_username} johndoe Salam, necəsən?`\n\n"
        "🔒 Yalnız göstərilən istifadəçi mesajı görə bilər!",
        parse_mode='Markdown'
    )

# ================== INLINE QUERY ==================
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    
    if not query:
        # Boş sorğuda istifadə təlimatı göstər
        empty_result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="📝 İstifadə qaydası",
            description="istifadəçi_adı mesajınız",
            input_message_content=InputTextMessageContent(
                "❌ Zəhmət olmasa düzgün format istifadə edin:\n"
                "@bot_adı istifadəçi_adı mesajınız"
            )
        )
        await update.inline_query.answer([empty_result], cache_time=10)
        return
    
    parts = query.split(" ", 1)
    if len(parts) < 2:
        # Format səhv
        error_result = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="❌ Format səhvdir",
            description="istifadəçi_adı və mesaj lazımdır",
            input_message_content=InputTextMessageContent(
                "❌ Düzgün format:\n@bot_adı istifadəçi_adı mesajınız"
            )
        )
        await update.inline_query.answer([error_result], cache_time=10)
        return
    
    target = parts[0].lstrip("@").lower()
    secret = parts[1][:4000]  # Max 4000 simvol
    
    secret_id = str(uuid.uuid4())
    SECRETS[secret_id] = {
        "target": target,
        "secret": secret,
        "sender": update.inline_query.from_user.full_name,
    }
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "👁 Gizli mesajı oxu",
            callback_data=f"open|{secret_id}"
        )]
    ])
    
    result = InlineQueryResultArticle(
        id=secret_id,
        title=f"🔒 @{target} üçün gizli mesaj",
        description=f"Mesaj uzunluğu: {len(secret)} simvol",
        input_message_content=InputTextMessageContent(
            f"🔐 **@{target}** üçün gizli mesaj!\n"
            f"👤 Göndərən: {update.inline_query.from_user.full_name}\n\n"
            "⬇️ Oxumaq üçün düyməyə basın",
            parse_mode='Markdown'
        ),
        reply_markup=keyboard,
    )
    
    await update.inline_query.answer([result], cache_time=0)
    logger.info(f"Yeni gizli mesaj: {target} üçün ({len(secret)} simvol)")

# ================== OPEN SECRET ==================
async def open_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    try:
        _, secret_id = query.data.split("|", 1)
        data = SECRETS.get(secret_id)
    except Exception as e:
        logger.error(f"Callback data parse error: {e}")
        await query.answer("❌ Xəta baş verdi", show_alert=True)
        return
    
    if not data:
        await query.answer("❌ Mesaj tapılmadı və ya artıq oxunub", show_alert=True)
        return
    
    target = data["target"]
    
    # İstifadəçi ID və ya username yoxla
    user_matches = (
        str(user.id) == target or 
        (user.username and user.username.lower() == target)
    )
    
    if not user_matches:
        await query.answer(
            "🚫 Bu mesaj sizə aid deyil!\n"
            f"Mesaj @{target} üçün nəzərdə tutulub.",
            show_alert=True
        )
        logger.warning(f"{user.full_name} başqasının mesajını açmağa çalışdı")
        return
    
    # Mesajı göstər
    await query.answer(
        f"📩 Mesaj:\n\n{data['secret']}\n\n"
        f"👤 Göndərən: {data.get('sender', 'Anonim')}",
        show_alert=True
    )
    
    # SECRETS-dən sil
    del SECRETS[secret_id]
    logger.info(f"{user.full_name} gizli mesajı oxudu")
    
    # Mesajı yenilə
    await asyncio.sleep(0.1)
    try:
        await query.edit_message_text(
            f"✅ **Oxundu**\n"
            f"👤 Oxuyan: {user.full_name}\n"
            f"📅 Tarix: {query.message.date.strftime('%Y-%m-%d %H:%M')}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Mesaj yeniləmə xətası: {e}")

# ================== ERROR HANDLER ==================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} səbəb oldu error: {context.error}")

# ================== MAIN ==================
def main():
    # Application builder
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(open_secret))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("🤖 Bot uğurla başladı və sorğular gözləyir...")
    
    # Start polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
