from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import random
import json

# File delle carte organizzati per rarità
CARD_FILES = {
    "comune": "comuni.txt",
    "rara": "rare.txt",
    "epica": "epiche.txt",
    "leggendaria": "leggendarie.txt"
}

# Probabilità per le rarità (in percentuale)
RARITY_PROBABILITIES = {
    "comune": 2,
    "rara": 15,
    "epica": 5,
    "leggendaria": 78
}

# Collezione utenti
user_collections = {}

# Funzione per caricare le collezioni degli utenti (se si usa un file JSON per persistere i dati)
def load_collections():
    global user_collections
    if os.path.exists("user_collections.json"):
        with open("user_collections.json", "r") as f:
            user_collections = json.load(f)

# Funzione per salvare le collezioni degli utenti
def save_collections():
    with open("user_collections.json", "w") as f:
        json.dump(user_collections, f)

# Carica le carte dai file di testo
def load_cards():
    cards = {}
    for rarity, file_name in CARD_FILES.items():
        with open(file_name, "r") as file:
            cards[rarity] = [line.strip() for line in file.readlines()]
    return cards

CARDS = load_cards()  # Carica tutte le carte

# Comando per aprire una figurina
async def apri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /apri per aprire una figurina."""
    user = update.effective_user
    user_id = str(user.id)  # Usa l'ID dell'utente per identificare la collezione

    # Verifica se l'utente ha già una collezione
    if user_id not in user_collections:
        user_collections[user_id] = {
            "comune": [],
            "rara": [],
            "epica": [],
            "leggendaria": []
        }

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
        await update.message.reply_text("Errore nel calcolo della rarità.", parse_mode="Markdown")
        return

    # Scegli una carta casuale
    card = random.choice(CARDS[rarity])

    # Verifica se l'utente ha già questa carta
    if card in user_collections[user_id][rarity]:
        # Se l'utente ha già la carta, mostra comunque l'immagine se presente
        image_path = os.path.join("immagini", f"{card}.png")
        if os.path.isfile(image_path):
            try:
                # Invia l'immagine della carta
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(image_path, "rb"),
                    caption=f"🎉 {user.first_name}, hai già questa carta!\n✨ **{card}** ✨",
                    parse_mode="Markdown"
                )
            except Exception as e:
                await update.message.reply_text(f"Errore durante l'invio dell'immagine: {str(e)}\nHai già questa carta: {card}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"🎉 {user.first_name}, hai già questa carta!\n✨ **{card}** ✨", parse_mode="Markdown")
        return

    # Aggiungi la carta alla collezione dell'utente
    user_collections[user_id][rarity].append(card)
    save_collections()  # Salva la collezione aggiornata

    # Path per l'immagine della carta
    image_path = os.path.join("immagini", f"{card}.png")

    if os.path.isfile(image_path):
        try:
            # Invia il messaggio con immagine e testo formattato
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(image_path, "rb"),
                caption=f"🎉 {user.first_name}, hai ottenuto una nuova carta {rarity.upper()}:\n✨ **{card}** ✨!",
                parse_mode="Markdown"
            )
        except Exception as e:
            # Gestisci eventuali errori durante l'invio
            await update.message.reply_text(
                f"Errore durante l'invio dell'immagine: {str(e)}\n"
                f"Hai ottenuto una carta {rarity.upper()}:\n✨**{card}**✨!",
                parse_mode="Markdown"
            )
    else:
        # Invia solo il messaggio testuale con formattazione Markdown
        await update.message.reply_text(
            f"🎉 {user.first_name}, hai ottenuto una carta {rarity.upper()}:\n✨ **{card}** ✨!",
            parse_mode="Markdown"
        )

# Comando per visualizzare la collezione dell'utente
async def collezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /collezione per visualizzare le carte possedute dall'utente."""
    user = update.effective_user
    user_id = str(user.id)

    # Verifica se l'utente ha una collezione
    if user_id not in user_collections or not any(user_collections[user_id].values()):
        await update.message.reply_text("Non hai ancora ottenuto nessuna carta!", parse_mode="Markdown")
        return

    # Crea un messaggio con la collezione dell'utente, suddivisa per rarità
    collection_message = f"🎴 **Collezione di {user.first_name}:**\n\n"
    
    for rarity in ["comune", "rara", "epica", "leggendarie"]:
        # Carte possedute per questa rarità
        owned_cards = user_collections[user_id][rarity]
        if owned_cards:
            collection_message += f"**{rarity.capitalize()}:**\n"
            collection_message += "\n".join(owned_cards) + "\n\n"

    await update.message.reply_text(collection_message, parse_mode="Markdown")

# Comando per cancellare la collezione dell'utente
async def cancellacollezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /cancellacollezione per chiedere conferma prima di cancellare la collezione."""
    user = update.effective_user
    user_id = str(user.id)  # Usa l'ID dell'utente per identificare la collezione

    # Crea i pulsanti inline per confermare o annullare
    keyboard = [
        [
            InlineKeyboardButton("Sono sicuro", callback_data=f"cancella_{user_id}"),
            InlineKeyboardButton("No", callback_data=f"annulla_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Invia il messaggio con la richiesta di conferma
    await update.message.reply_text(
        "Sei sicuro di voler cancellare l'intera tua collezione? Questa azione è irreversibile.",
        reply_markup=reply_markup
    )

# Funzione per gestire la risposta dell'utente (conferma o annullamento)
async def gestione_cancellazione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce la risposta alla cancellazione della collezione."""
    query = update.callback_query
    user_id = query.data.split("_")[1]  # Estrai l'ID dell'utente dal callback data

    # Verifica che l'utente sia lo stesso che ha invocato il comando
    if str(query.from_user.id) == user_id:
        if query.data.startswith("cancella"):
            # Cancella la collezione dell'utente
            if user_id in user_collections:
                del user_collections[user_id]
                save_collections()  # Salva la collezione aggiornata
            await query.answer()
            await query.edit_message_text(
                "La tua collezione è stata cancellata con successo!",
                parse_mode="Markdown"
            )
        elif query.data.startswith("annulla"):
            # Annulla la cancellazione
            await query.answer()
            await query.edit_message_text(
                "Cancellazione della collezione annullata.",
                parse_mode="Markdown"
            )

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!",
        parse_mode="Markdown"
    )

# Comando /help
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /apri: Scopri quale carta ottieni!\n"
        "- /collezione: Visualizza la tua collezione!\n"
        "- /bash: Iscriviti al Raffo's Birthday Bash!\n"
        "- /about: Informazioni sul bot.\n"
        "- /help: Mostra questo messaggio di aiuto.\n\n"
        "Buona fortuna con la tua collezione! 🌟",
        parse_mode="Markdown"
    )

# Comando /bash
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

# Comando /about
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /about per informazioni sul bot."""
    await update.message.reply_text(
        "Questo bot è stato creato da [@Raffosbaffos](https://t.me/Raffosbaffos)!\n"
        "Per qualsiasi problema, contattatemi direttamente! :D\n\n"
        "Inoltre, puoi usare il comando /cancellacollezione per eliminare l'intera tua collezione di carte!",
        parse_mode="Markdown"
    )

def main():
    """Avvia il bot."""
    # Carica le collezioni esistenti
    load_collections()

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
    application.add_handler(CommandHandler("collezione", collezione))
    application.add_handler(CommandHandler("cancellacollezione", cancellacollezione))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("bash", bash))
    application.add_handler(CommandHandler("about", about))

    # Aggiungi il gestore per il callback dei pulsanti inline
    application.add_handler(CallbackQueryHandler(gestione_cancellazione))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
