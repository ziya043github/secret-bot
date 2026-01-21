from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    InlineQueryHandler,
    CallbackQueryHandler,
)
import uuid
import asyncio

TOKEN = "8368620933:AAFrZYOFoVcQF6luL4Mv-N3xTTjiSi0SvAQ"

# ================== SECRET STORAGE ==================

SECRETS: dict[str, dict[str, str]] = {}

# ================== INLINE QUERY ==================

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.inline_query:
        return

    q = update.inline_query.query.strip()
    if not q:
        return

    parts = q.split(" ", 1)
    if len(parts) < 2:
        return

    target = parts[0].lstrip("@").lower()
    secret = parts[1][:4000]  # limit

    secret_id = str(uuid.uuid4())

    SECRETS[secret_id] = {
        "target": target,
        "secret": secret,
    }

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            text="👁 Gizli mesaj aç",
            callback_data=f"open|{secret_id}"
        )]]
    )

    result = InlineQueryResultArticle(
        id=secret_id,
        title="🔒 Gizli mesaj",
        description=f"{target} üçün gizli mesaj",
        input_message_content=InputTextMessageContent(
            message_text=f"🔐 {target} üçün gizli mesaj var"
        ),
        reply_markup=keyboard,
    )

    await update.inline_query.answer(
        results=[result],
        cache_time=0,
        is_personal=True,
    )

# ================== OPEN SECRET ==================

async def open_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    await query.answer()  # Telegram timeout olmasın

    if not query.data.startswith("open|"):
        return

    secret_id = query.data.split("|", 1)[1]
    data = SECRETS.get(secret_id)

    if not data:
        await query.answer("Mesaj tapılmadı ❌", show_alert=True)
        return

    target = data["target"]
    secret = data["secret"]

    user = query.from_user
    uid = str(user.id)
    uname = (user.username or "").lower()

    # ❌ başqası açmağa çalışsa
    if uid != target and uname != target:
        await query.answer("Balam sən açma 😘", show_alert=True)
        return

    # ✅ gizli mesaj popup
    await query.answer(secret, show_alert=True)

    # 🗑 bir dəfə oxundu → sil
    SECRETS.pop(secret_id, None)

    await asyncio.sleep(0.1)

    # ✏️ inline mesajı edit et
    try:
        await query.edit_message_text(
            text=f"👁 Oxundu: {user.full_name or user.first_name}"
        )
    except:
        pass

# ================== MAIN ==================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(open_secret))

    print("🤖 Bot işləyir...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
