from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
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

# Funzione per ottenere la collezione dell'utente (modificata per esempio)
def get_user_collection(user_id):
    # Qui aggiungi il codice per recuperare la collezione dell'utente, per esempio da un database o file
    return {
        "comune": ["Terrons Crew", "Yggi", "Syntherface"],
        "rara": ["y0lT ICARUS 2024"],
        "epica": [],
        "leggendaria": []
    }

# Funzione per cancellare la collezione dell'utente
def delete_user_collection(user_id):
    # Qui aggiungi il codice per cancellare la collezione dell'utente, per esempio dal database o file
    pass

# Comando /sbusta (modificato per aprire un pacchetto di figurine)
async def sbusta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /sbusta per aprire un pacchetto di figurine."""
    user = update.effective_user

    # Determina la rarità
    cards_pulled = {
        "comune": [],
        "rara": [],
        "epica": [],
        "leggendaria": []
    }

    for r, probability in RARITY_PROBABILITIES.items():
        roll = random.randint(1, 100)
        if roll <= probability:
            file_path = CARD_FILES[r]
            try:
                with open(file_path, "r") as f:
                    cards = f.readlines()
                card = random.choice(cards).strip()
                cards_pulled[r].append(card)
            except FileNotFoundError:
                await update.message.reply_text(f"Il file {file_path} non è stato trovato.", parse_mode="Markdown")
                return

    # Costruzione del resoconto
    message = f"🎉 {user.first_name}, hai aperto un pacchetto! Ecco cosa hai trovato:\n\n"
    for rarity, pulled_cards in cards_pulled.items():
        if pulled_cards:
            message += f"**{rarity.upper()}**:\n"
            for card in pulled_cards:
                message += f"✨ {card}\n"
            message += "\n"

    # Invia il messaggio del pacchetto
    await update.message.reply_text(message, parse_mode="Markdown")

# Comando /collezione (modificato per non visualizzare rarità vuote)
async def collezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /collezione per visualizzare le carte raccolte."""
    user = update.effective_user
    user_collezione = get_user_collection(user.id)

    message = f"🌟 Collezione di {user.first_name}:\n\n"

    for rarity, cards in user_collezione.items():
        if cards:
            message += f"**{rarity.upper()}**:\n"
            for card in cards:
                message += f"✨ {card}\n"
            message += "\n"

    # Se la collezione è vuota, mostra un messaggio che non ci sono carte
    if not message.endswith("\n\n"):
        message += "Non hai ancora collezionato carte!\n"

    await update.message.reply_text(message, parse_mode="Markdown")

# Comando /cancellacollezione (con bottoni inline per conferma)
async def cancellacollezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /cancellacollezione per cancellare la collezione."""
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("Sono Sicuro", callback_data="confirm_deletion")],
        [InlineKeyboardButton("No", callback_data="cancel_deletion")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Sei sicuro di voler cancellare la tua collezione? Questa azione è irreversibile.",
        reply_markup=reply_markup
    )

# Gestore della conferma della cancellazione
async def handle_deletion_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce la conferma della cancellazione della collezione."""
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_deletion":
        user = update.effective_user
        # Cancelliamo la collezione dell'utente
        delete_user_collection(user.id)
        await query.edit_message_text("La tua collezione è stata cancellata. Riparti da zero!")
    else:
        await query.edit_message_text("Operazione annullata.")

# Funzione per il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /sbusta per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!",
        parse_mode="Markdown"
    )

# Funzione per il comando /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /sbusta: Scopri quale carta ottieni!\n"
        "- /cancellacollezione: Cancella la tua collezione e riparti da zero.\n"
        "- /collezione: Visualizza la tua collezione di carte.\n"
        "- /help: Mostra questo messaggio di aiuto.\n\n"
        "Buona fortuna con la tua collezione! 🌟",
        parse_mode="Markdown"
    )

# Funzione per il comando /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /about per informazioni sul bot."""
    await update.message.reply_text(
        "Questo bot è stato creato da [@Raffosbaffos](https://t.me/Raffosbaffos)!\n"
        "Per qualsiasi problema, contattatemi direttamente! :D",
        parse_mode="Markdown"
    )

# Funzione principale per avviare il bot
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
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("sbusta", sbusta))  # Modificato qui da /apri a /sbusta
    application.add_handler(CommandHandler("collezione", collezione))
    application.add_handler(CommandHandler("cancellacollezione", cancellacollezione))
    application.add_handler(CallbackQueryHandler(handle_deletion_confirmation, pattern="^(confirm_deletion|cancel_deletion)$"))

    # Avvia il polling
    application.run_polling()

if __name__ == "__main__":
    main()
