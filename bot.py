from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
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
    
    for rarity in ["comune", "rara", "epica", "leggendaria"]:
        # Carte possedute per questa rarità
        owned_cards = user_collections[user_id][rarity]
        if owned_cards:
            collection_message += f"**{rarity.capitalize()}:**\n"
            collection_message += "\n".join(owned_cards) + "\n\n"

    await update.message.reply_text(collection_message, parse_mode="Markdown")

# Funzione per la cancellazione della collezione con conferma
async def reset_collezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /reset_collezione per chiedere conferma per cancellare la collezione."""
    keyboard = [
        [InlineKeyboardButton("Sì, cancella la mia collezione", callback_data="reset_yes")],
        [InlineKeyboardButton("No, annulla", callback_data="reset_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🚨 Sei sicuro di voler cancellare la tua collezione? Questa azione non può essere annullata.",
        reply_markup=reply_markup
    )

# Funzione per gestire la risposta ai bottoni di conferma
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gestisce il callback dei bottoni di conferma cancellazione."""
    query = update.callback_query
    user_id = str(query.from_user.id)
    
    if query.data == "reset_yes":
        if user_id in user_collections:
            # Cancella la collezione dell'utente
            user_collections[user_id] = {
                "comune": [],
                "rara": [],
                "epica": [],
                "leggendaria": []
            }
            save_collections()
            await query.edit_message_text("✅ La tua collezione è stata cancellata con successo. Ora puoi ricominciare da zero!")
        else:
            await query.edit_message_text("❌ Non hai ancora una collezione da cancellare.")
    
    elif query.data == "reset_no":
        await query.edit_message_text("🚫 La cancellazione della collezione è stata annullata.")

# Aggiungi il nuovo comando per resettare la collezione
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!\n"
        "Usa /reset_collezione per cancellare la tua collezione e ricominciare da zero.",
        parse_mode="Markdown"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /apri: Scopri quale carta ottieni!\n"
        "- /collezione: Visualizza la tua collezione!\n"
        "- /reset_collezione: Cancella la tua collezione!\n"
        "- /bash: Iscriviti al Raffo's Birthday Bash!\n"
        "- /about: Informazioni sul bot.\n"
        "- /help: Mostra questo messaggio di aiuto.\n\n"
        "Buona fortuna con la tua collezione! 🌟",
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
    application.add_handler(CommandHandler("reset_collezione", reset_collezione))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CallbackQueryHandler(button))  # Gestione dei bottoni inline

    # Configura il webhook (modifica l'URL del webhook)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8443)),
        webhook_url=f"{APP_URL}/"
    )

if __name__ == "__main__":
    main()
