from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import random

# File delle carte organizzati per rarità
CARD_FILES = {
    "comune": "comuni.txt",
    "rara": "rare.txt",
    "epica": "epiche.txt",
    "leggendaria": "leggendarie.txt"
}

# Probabilità per le rarità (in percentuale)
RARITY_PROBABILITIES = {
    "comune": 78,
    "rara": 15,
    "epica": 5,
    "leggendaria": 2
}

async def apri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /apri per aprire una figurina."""
    user = update.effective_user

    # Determina la rarità
    roll = random.randint(1, 100)
    cumulative = 0
    rarity = None
    for r, probability in RARITY_PROBABILITIES.items():
        cumulative += probability
        if roll <= cumulative:
            rarity = r
            break

    if rarity is None:
        await update.message.reply_text("Errore nel calcolo della rarità.")
        return

    # Leggi il file della rarità selezionata
    file_path = CARD_FILES[rarity]
    try:
        with open(file_path, "r") as f:
            cards = f.readlines()
    except FileNotFoundError:
        await update.message.reply_text(f"Il file {file_path} non è stato trovato.")
        return

    # Scegli una carta casuale
    card = random.choice(cards).strip()

    # Invia la risposta all'utente
    await update.message.reply_text(f"🎉 {user.first_name}, hai ottenuto una carta {rarity.upper()}: {card}!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start per iniziare."""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine!\n"
        "Usa /apri per scoprire quale carta ottieni!"
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
    application.add_handler(CommandHandler("apri", apri))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
