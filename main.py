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

import os
from telegram.ext import ApplicationBuilder, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise Exception("BOT_TOKEN tapılmadı")

async def start(update, context):
    await update.message.reply_text("Bot işləyir ✅")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()


# burdan aşağı bot kodun davam edir



# ================== SECRET STORAGE ==================

SECRETS = {}  # secret_id -> {target, secret}

# ================== INLINE QUERY ==================

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.inline_query.query.strip()
    if not q:
        return

    parts = q.split(" ", 1)
    if len(parts) < 2:
        return

    target = parts[0].lstrip("@").lower()
    secret = parts[1]

    # 🔒 istəsən limit qoya bilərsən (məs: 4000)
    if len(secret) > 4000:
        secret = secret[:4000]

    secret_id = str(uuid.uuid4())

    SECRETS[secret_id] = {
        "target": target,
        "secret": secret,
    }

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(
            "👁 Gizli mesaj aç",
            callback_data=f"open|{secret_id}"
        )]]
    )

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

    try:
        _, secret_id = query.data.split("|", 1)
        data = SECRETS.get(secret_id)
    except:
        data = None

    if not data:
        await query.answer("Mesaj tapılmadı ❌", show_alert=True)
        return

    target = data["target"]
    secret = data["secret"]

    user = query.from_user
    uid = str(user.id)
    uname = (user.username or "").lower()

    # ❌ Başqası açmağa çalışsa
    if uid != target and uname != target:
        await query.answer("Balam sən açma 😘", show_alert=True)
        return

    # ✅ GİZLİ MESAJ POPUP
    await query.answer(secret, show_alert=True)

    # 🗑 1 dəfə oxundu → sil
    del SECRETS[secret_id]

    # ⏱ kiçik delay
    await asyncio.sleep(0.1)

    # ✅ INLINE MESAJI EDİT ET
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
    app.run_polling()

if __name__ == "__main__":
    main()


