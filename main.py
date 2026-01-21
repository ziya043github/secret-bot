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
import base64
import json

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("BOT_TOKEN tapılmadı")


def pack_data(target, text):
    data = {"t": target, "m": text}
    raw = json.dumps(data).encode()
    return base64.urlsafe_b64encode(raw).decode()


def unpack_data(encoded):
    raw = base64.urlsafe_b64decode(encoded.encode())
    return json.loads(raw.decode())


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.inline_query.query.strip()
    if not q:
        return

    parts = q.split(" ", 1)
    if len(parts) < 2:
        return

    target = parts[0].lstrip("@").lower()
    secret = parts[1]

    packed = pack_data(target, secret)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👁 Gizli mesaj aç", callback_data=f"open|{packed}")]
    ])

    result = InlineQueryResultArticle(
        id=str(uuid.uuid4()),
        title="🔒 Gizli mesaj",
        description=f"{target} üçün gizli mesaj",
        input_message_content=InputTextMessageContent(
            f"🔐 {target} üçün gizli mesaj var"
        ),
        reply_markup=keyboard,
    )

    await update.inline_query.answer([result], cache_time=0)


async def open_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        _, encoded = query.data.split("|", 1)
        data = unpack_data(encoded)
    except:
        await query.answer("Mesaj tapılmadı ❌", show_alert=True)
        return

    target = data["t"]
    secret = data["m"]

    user = query.from_user
    uid = str(user.id)
    uname = (user.username or "").lower()

    if uid != target and uname != target:
        await query.answer(
            "Bu gizli mesaj sənlik deyil ❌",
            show_alert=True
        )
        return

    # ✅ BURASI ƏSASDIR — QRUPDA AÇILIR, AMMA SADECE O ADAM GÖRÜR
    await query.answer(
        text=secret,
        show_alert=True
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(open_secret))

    print("🤖 Bot işləyir...")
    app.run_polling()


if __name__ == "__main__":
    main()
