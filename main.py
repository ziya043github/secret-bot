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

# ================== TOKEN ==================

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN tapılmadı")

# ================== START ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot işləyir!\n\n"
        "İstifadə:\n"
        "@bot_adı istifadəçi gizli_mesaj"
    )

# ================== SECRET STORAGE ==================

SECRETS = {}

# ================== INLINE QUERY ==================

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if not query:
        return

    parts = query.split(" ", 1)
    if len(parts) < 2:
        return

    target = parts[0].lstrip("@").lower()
    secret = parts[1][:4000]

    secret_id = str(uuid.uuid4())
    SECRETS[secret_id] = {
        "target": target,
        "secret": secret,
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "👁 Gizli mesaj aç",
            callback_data=f"open|{secret_id}"
        )]
    ])

    result = InlineQueryResultArticle(
        id=secret_id,
        title="🔒 Gizli mesaj",
        description=f"{target} üçün gizli mesaj",
        input_message_content=InputTextMessageContent(
            f"🔐 {target} üçün gizli mesaj var"
        ),
        reply_markup=keyboard,
    )

    await update.inline_query.answer([result], cache_time=0)

# ================== OPEN SECRET ==================

async def open_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        _, secret_id = query.data.split("|", 1)
        data = SECRETS.get(secret_id)
    except:
        data = None

    if not data:
        await query.answer("Mesaj tapılmadı ❌", show_alert=True)
        return

    user = query.from_user
    target = data["target"]

    if str(user.id) != target and (user.username or "").lower() != target:
        await query.answer("Bu sənə aid deyil 😘", show_alert=True)
        return

    await query.answer(data["secret"], show_alert=True)
    del SECRETS[secret_id]

    await asyncio.sleep(0.1)

    try:
        await query.edit_message_text(
            f"👁 Oxundu: {user.full_name}"
        )
    except:
        pass

# ================== MAIN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(open_secret))

    print("🤖 Bot işləyir...")
    app.run_polling()

if __name__ == "__main__":
    main()
