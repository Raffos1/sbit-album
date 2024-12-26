from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import random

# Premi del gacha e relative probabilità
gacha_items = {
    "✨ Super Rare Item ✨": 5,   # 5% di probabilità
    "⭐ Rare Item ⭐": 20,        # 20% di probabilità
    "🔹 Common Item 🔹": 75      # 75% di probabilità
}

async def gacha(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /gacha per fare un'estrazione."""
    user = update.effective_user
    roll = random.randint(1, 100)  # Numero casuale tra 1 e 100
    total = 0
    for item, chance in gacha_items.items():
        total += chance
        if roll <= total:
            await update.message.reply_text(f"🎉 {user.first_name}, hai ottenuto: {item}!")
            return
    await update.message.reply_text("Oh no, nessun premio questa volta! 😢")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start per iniziare."""
    await update.message.reply_text(
        "🎰 Benvenuto nel Gacha Bot!\n"
        "Usa /gacha per fare un'estrazione e scoprire cosa ottieni!"
    )

def main():
    """Avvia il bot."""
    # Token e URL del webhook
    TOKEN = os.environ.get("TELEGRAM_TOKEN")
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN non configurato!")
    
    APP_URL = os.environ.get("APP_URL")
    if not APP_URL:
        raise RuntimeError("APP_URL non configurato!")

    # Crea l'applicazione
    application = Application.builder().token(TOKEN).build()

    # Aggiungi i comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gacha", gacha))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
