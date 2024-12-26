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
    await update.message.reply_text(
        f"🎉 {user.first_name}, hai ottenuto una carta {rarity.upper()}:\n✨ **{card}** ✨!"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /apri: Scopri quale carta ottieni!\n"
        "- /bash: Iscriviti al **Raffo's Birthday Bash**!\n"
        "- /about: Informazioni sul bot.\n"
        "- /help: Mostra questo messaggio di aiuto.\n\n"
        "Buona fortuna con la tua collezione! 🌟"
    )

async def bash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /bash per linkare l'evento."""
    await update.message.reply_text(
        "🎉 **Iscriviti al Raffo's Birthday Bash!** 🎂\n"
        "📅 **700 Euro di Prizepool**, cena gratis e tanto altro!\n"
        "Non perdere questo evento unico nel suo genere!\n\n"
        "👉 [Clicca qui per registrarti!](https://start.gg/raffos)"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /about per informazioni sul bot."""
    await update.message.reply_text(
        "🤖 Questo bot è stato creato da **@Raffosbaffos**!\n"
        "Per qualsiasi problema o suggerimento, contattalo direttamente. 😊"
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
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("bash", bash))
    application.add_handler(CommandHandler("about", about))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
