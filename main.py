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
    Defaults,
)
import uuid
import asyncio
import os
import logging

# Loglama tənzimləmələri
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Token
TOKEN = "8368620933:AAFieyUAF5Myo4oWudG6PeXZB1Co1ywUYA8"

# ================== SECRET STORAGE ==================
# Mesajları yaddaşda saxlamaq üçün lüğət
SECRETS: dict[str, dict[str, str]] = {}

# ================== INLINE QUERY ==================
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.inline_query:
        return
    
    query = update.inline_query.query.strip()
    if not query:
        return
    
    # Format: @bot_username @istifadeci mesaj
    parts = query.split(" ", 1)
    if len(parts) < 2:
        return
    
    target = parts[0].lstrip("@").lower()
    secret_text = parts[1][:4000] # Telegram limit
    
    # Unikal ID yaradırıq
    secret_id = str(uuid.uuid4())
    
    # Mesajı yaddaşa yazırıq
    SECRETS[secret_id] = {
        "target": target,
        "secret": secret_text,
        "sender": update.inline_query.from_user.full_name
    }
    
    # Düyməni yaradırıq
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="👁 Gizli mesajı aç", callback_data=f"open|{secret_id}")]
    ])
    
    # İnline nəticəni hazırlayırıq
    result = InlineQueryResultArticle(
        id=secret_id,
        title="🔒 Gizli Mesaj Hazırdır",
        description=f"Alıcı: @{target}",
        input_message_content=InputTextMessageContent(
            message_text=f"🔐 @{target} üçün gizli mesaj var.\n\n*(Yalnız @{target} oxuya bilər)*",
            parse_mode="Markdown"
        ),
        reply_markup=keyboard,
    )
    
    # Cavabı göndəririk (cache_time=0 vacibdir ki, köhnə mesajlar qalmasın)
    await update.inline_query.answer(results=[result], cache_time=0, is_personal=True)

# ================== OPEN SECRET ==================
async def open_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    
    if not query.data.startswith("open|"):
        return
    
    secret_id = query.data.split("|", 1)[1]
    data = SECRETS.get(secret_id)
    
    if not data:
        await query.answer("Bağışlayın, bu mesaj artıq silinib və ya tapılmadı ❌", show_alert=True)
        return
    
    user = query.from_user
    uid = str(user.id)
    uname = (user.username or "").lower()
    target = data["target"]
    secret_text = data["secret"]
    
    # Alıcı yoxlaması (ID və ya Username ilə)
    if uid != target and uname != target:
        await query.answer("Siz bu mesajın alıcısı deyilsiniz! ✋😘", show_alert=True)
        return
    
    # Mesajı popup (alert) kimi göstəririk
    await query.answer(f"🔒 Gizli Mesaj:\n\n{secret_text}", show_alert=True)
    
    # Oxunduqdan sonra yaddaşdan silirik (bir dəfəlik mesaj)
    SECRETS.pop(secret_id, None)
    
    # Mesajın görünüşünü yeniləyirik
    try:
        await query.edit_message_text(
            text=f"✅ Mesaj oxundu: {user.full_name}\n(Mesaj sistemdən silindi 🗑)",
            reply_markup=None
        )
    except Exception as e:
        logging.error(f"Edit xətası: {e}")

# ================== MAIN ==================
def main():
    # Defolt tənzimləmələr
    defaults = Defaults(parse_mode="HTML", disable_web_page_preview=True)
    
    app = ApplicationBuilder().token(TOKEN).defaults(defaults).build()
    
    # Handlerləri əlavə edirik
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(open_secret))
    
    print("🤖 Bot təkmilləşdirilmiş rejimdə 7/24 işləyir...")
    # drop_pending_updates=True köhnə yığılıb qalmış mesajları təmizləyir
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
