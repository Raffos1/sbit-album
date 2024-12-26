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

# Memorizzazione della collezione dell'utente
user_collections = {}

def get_user_collection(user_id):
    """Restituisce la collezione dell'utente, o una nuova se non esiste."""
    if user_id not in user_collections:
        user_collections[user_id] = {
            "comune": set(),
            "rara": set(),
            "epica": set(),
            "leggendaria": set()
        }
    return user_collections[user_id]

async def apri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /apri per aprire 5 figurine."""
    user = update.effective_user
    user_id = user.id

    # Determina le 5 rarità
    drawn_cards = {
        "comune": [],
        "rara": [],
        "epica": [],
        "leggendaria": []
    }

    for _ in range(5):
        roll = random.randint(1, 100)
        cumulative = 0
        rarity = None
        for r, probability in RARITY_PROBABILITIES.items():
            cumulative += probability
            if roll <= cumulative:
                rarity = r
                break

        if rarity is None:
            await update.message.reply_text("Errore nel calcolo della rarità.", parse_mode="Markdown")
            return

        # Leggi il file della rarità selezionata
        file_path = CARD_FILES[rarity]
        try:
            with open(file_path, "r") as f:
                cards = f.readlines()
        except FileNotFoundError:
            await update.message.reply_text(f"Il file {file_path} non è stato trovato.", parse_mode="Markdown")
            return

        # Scegli una carta casuale e aggiungi alla lista delle carte estratte
        card = random.choice(cards).strip()
        drawn_cards[rarity].append(card)

        # Aggiungi la carta alla collezione dell'utente
        collection = get_user_collection(user_id)
        collection[rarity].add(card)

    # Invia il messaggio con tutte le 5 carte estratte
    message = f"🎉 {user.first_name}, hai ottenuto 5 carte!\n\n"
    for rarity, cards in drawn_cards.items():
        message += f"\n{rarity.upper()}:\n" + "\n".join([f"✨ **{card}**" for card in cards])

    await update.message.reply_text(message, parse_mode="Markdown")

async def collezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /collezione per visualizzare tutte le carte raccolte."""
    user = update.effective_user
    user_id = user.id
    collection = get_user_collection(user_id)

    message = f"🌟 **Collezione di {user.first_name}:**\n\n"

    for rarity, cards in collection.items():
        message += f"\n**{rarity.upper()}:**\n" + "\n".join([f"✨ {card}" for card in cards]) + "\n"

    if not any(collection.values()):
        message = f"{user.first_name}, non hai ancora raccolto nessuna carta. Usa /apri per iniziare!"

    await update.message.reply_text(message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quali carte ottieni, oppure /help per scoprire tutti i comandi!",
        parse_mode="Markdown"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /apri: Scopri quali carte ottieni!\n"
        "- /collezione: Visualizza le carte che hai raccolto!\n"
        "- /bash: Iscriviti al Raffo's Birthday Bash!\n"
        "- /about: Informazioni sul bot.\n"
        "- /help: Mostra questo messaggio di aiuto.\n\n"
        "Buona fortuna con la tua collezione! 🌟",
        parse_mode="Markdown"
    )

async def bash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /bash per linkare l'evento."""
    await update.message.reply_text(
        "🎂 **Iscriviti al Raffo's Birthday Bash!** 🎉\n"
        "📅 *700 Euro di Prizepool, Cena gratis e tanto altro!*\n"
        "🤯 *Confermati all'evento: M4E, Meercko, y0lT, GANDIX, Paky e molti altri!*\n"
        "Non perdere questo evento unico nel suo genere!\n\n"
        "👉 [Clicca qui per registrarti!](https://start.gg/raffos)",
        parse_mode="Markdown"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /about per informazioni sul bot."""
    await update.message.reply_text(
        "Questo bot è stato creato da [@Raffosbaffos](https://t.me/Raffosbaffos)!\n"
        "Per qualsiasi problema, contattatemi direttamente! :D",
        parse_mode="Markdown"
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
    application.add_handler(CommandHandler("collezione", collezione))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
