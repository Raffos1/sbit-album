from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import random
import json
from datetime import datetime, timedelta

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

# Funzione per gestire l'apertura delle figurine
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
            "leggendaria": [],
            "last_opened": None,
            "pacchetti_rimanenti": 10,  # Aggiungi pacchetti iniziali
            "last_refill": datetime.now().isoformat()  # Data dell'ultimo ricarico
        }

    # Verifica se l'utente ha pacchetti disponibili
    if user_collections[user_id]["pacchetti_rimanenti"] <= 0:
        await update.message.reply_text("Non hai pacchetti disponibili! Riprova tra poco.", parse_mode="Markdown")
        return

    # Verifica se sono passate 12 ore dall'ultimo ricarico
    last_refill = datetime.fromisoformat(user_collections[user_id]["last_refill"])
    time_diff = datetime.now() - last_refill
    if time_diff >= timedelta(hours=12):
        # Ricarica i pacchetti
        new_packs = min(10, user_collections[user_id]["pacchetti_rimanenti"] + 5)
        user_collections[user_id]["pacchetti_rimanenti"] = new_packs
        user_collections[user_id]["last_refill"] = datetime.now().isoformat()

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
        await update.message.reply_text(f"🎉 Hai ottenuto una carta che hai già!\n✨ **{card}** ✨", parse_mode="Markdown")
        return

    # Aggiungi la carta alla collezione dell'utente
    user_collections[user_id][rarity].append(card)

    # Aggiorna il numero di pacchetti rimanenti
    user_collections[user_id]["pacchetti_rimanenti"] -= 1

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
            f"🎉 Hai ottenuto una carta {rarity.upper()}:\n✨ **{card}** ✨!",
            parse_mode="Markdown"
        )

# Funzione per visualizzare i pacchetti rimanenti
async def pacchetti(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /pacchetti per visualizzare i pacchetti rimanenti dell'utente."""
    user = update.effective_user
    user_id = str(user.id)

    # Verifica se l'utente ha una collezione
    if user_id not in user_collections:
        await update.message.reply_text("Non hai ancora ottenuto nessuna carta!", parse_mode="Markdown")
        return

    # Mostra il numero di pacchetti rimanenti
    remaining_packs = user_collections[user_id]["pacchetti_rimanenti"]
    await update.message.reply_text(f"🎴 **Pacchetti rimanenti:** {remaining_packs}", parse_mode="Markdown")

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
    
    for rarity in ["comune", "rara", "epica", "leggendaria"]:
        # Carte possedute per questa rarità
        owned_cards = user_collections[user_id][rarity]
        if owned_cards:
            # Modifica il nome della rarità per renderlo plurale correttamente
            if rarity == "comune":
                rarity_plural = "Comuni"
            elif rarity == "rara":
                rarity_plural = "Rare"
            elif rarity == "epica":
                rarity_plural = "Epiche"
            elif rarity == "leggendaria":
                rarity_plural = "Leggendarie"
                
            collection_message += f"**{rarity_plural}:**\n"
            # Ordina le carte in base all'ordine nei file
            ordered_cards = [card for card in CARDS[rarity] if card in owned_cards]
            collection_message += "\n".join(ordered_cards) + "\n\n"

    await update.message.reply_text(collection_message, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!",
        parse_mode="Markdown"
    )

# Funzione per resettare la collezione
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /reset per resettare la collezione dell'utente con conferma tramite pulsanti inline.""" 
    user = update.effective_user
    user_id = str(user.id)

    # Resetta la collezione
    user_collections[user_id] = {
        "comune": [],
        "rara": [],
        "epica": [],
        "leggendaria": [],
        "pacchetti_rimanenti": 10,  # Resetta i pacchetti disponibili
        "last_refill": datetime.now().isoformat()  # Resetta la data dell'ultimo ricarico
    }

    save_collections()  # Salva la collezione aggiornata

    await update.message.reply_text(
        "🎉 La tua collezione è stata resettata!",
        parse_mode="Markdown"
    )

# Funzione per gestire i callback dei pulsanti inline
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce i callback dei pulsanti inline."""
    query = update.callback_query
    await query.answer()  # Risponde al clic del pulsante

    user_id = str(query.from_user.id)

    if query.data == "reset_yes":
        # Resetta la collezione dell'utente
        user_collections[user_id] = {
            "comune": [],
            "rara": [],
            "epica": [],
            "leggendaria": [],
            "pacchetti_rimanenti": 10,  # Resetta i pacchetti disponibili
            "last_refill": datetime.now().isoformat()  # Resetta la data dell'ultimo ricarico
        }
        save_collections()  # Salva la collezione aggiornata

        await query.edit_message_text(
            f"🎉 La tua collezione è stata resettata!",
            parse_mode="Markdown"
        )
    elif query.data == "reset_no":
        # Annulla il reset
        await query.edit_message_text(
            f"Operazione di reset annullata.",
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
    application.add_handler(CommandHandler("pacchetti", pacchetti))  # Aggiungi il comando /pacchetti
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("bash", bash))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("reset", reset))
    application.add_handler(CallbackQueryHandler(button))

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
