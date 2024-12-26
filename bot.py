from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import os
import random

# Premi del gacha e relative probabilità
gacha_items = {
    "✨ Super Rare Item ✨": 5,   # 5% di probabilità
    "⭐ Rare Item ⭐": 20,        # 20% di probabilità
    "🔹 Common Item 🔹": 75      # 75% di probabilità
}

def gacha(update: Update, context: CallbackContext) -> None:
    """Comando /gacha per fare un'estrazione."""
    user = update.effective_user
    roll = random.randint(1, 100)  # Numero casuale tra 1 e 100
    total = 0
    for item, chance in gacha_items.items():
        total += chance
        if roll <= total:
            update.message.reply_text(f"🎉 {user.first_name}, hai ottenuto: {item}!")
            return
    update.message.reply_text("Oh no, nessun premio questa volta! 😢")

def start(update: Update, context: CallbackContext) -> None:
    """Comando /start per iniziare."""
    update.message.reply_text(
        "🎰 Benvenuto nel Gacha Bot!\n"
        "Usa /gacha per fare un'estrazione e scoprire cosa ottieni!"
    )

def main():
    """Avvia il bot."""
    # Token del bot (dal sistema)
    TOKEN = "7738376099:AAEUYsk7rBblS2FVv6IoLPwVyCDHG_XHStc"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Aggiungi i comandi
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("gacha", gacha))

    # Avvia il polling
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
