from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import random
import json
import re
import requests
from datetime import datetime, timedelta
from base64 import b64decode, b64encode

GITHUB_REPO = "Raffos1/sbit-album"
GITHUB_FILE_PATH = "user_collections.json"
GITHUB_CODES_FILE_PATH = "codes.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

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

# Collezione utenti
user_collections = {}

# Funzione per caricare le collezioni degli utenti (se si usa un file JSON per persistere i dati)
def load_collections():
    global user_collections
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        content = response.json()
        data = b64decode(content['content']).decode('utf-8')
        user_collections = json.loads(data)
    else:
        print("Nessuna collezione trovata su GitHub. Creazione nuova...")
        
def load_codes_from_github():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CODES_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()
        return json.loads(b64decode(content['content']).decode('utf-8'))
    return {"valid_codes": {}, "used_codes": []}

def save_codes_to_github(codes):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CODES_FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha', None)
    encoded_data = b64encode(json.dumps(codes, indent=4).encode('utf-8')).decode('utf-8')
    payload = {"message": "Aggiornamento codici", "content": encoded_data, "sha": sha}
    requests.put(url, headers=headers, json=payload)

def normalize_filename(text):
    # Rimuove caratteri non validi per i nomi di file
    return re.sub(r'[<>:"/\\|?*]', '', text)
        
def escape_markdown(text):
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

# Funzione per salvare le collezioni degli utenti
def save_collections():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha', None)

    data = json.dumps(user_collections, indent=4)
    encoded_data = b64encode(data.encode('utf-8')).decode('utf-8')

    payload = {
        "message": "Aggiornamento collezioni utenti",
        "content": encoded_data,
        "sha": sha
    }
    
    save_response = requests.put(url, headers=headers, json=payload)
    
    if save_response.status_code == 200:
        print("Collezioni salvate con successo su GitHub.")
    else:
        print(f"Errore nel salvataggio: {save_response.json()}")

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
    try:
        # Inizio funzione, log di debug
        print("Comando /apri attivato.")
        user = update.effective_user
        user_id = str(user.id)  # Usa l'ID dell'utente per identificare la collezione
        print(f"Utente: {user.first_name} (ID: {user_id})")

        # Verifica se l'utente ha già una collezione
        if user_id not in user_collections:
            print("Creazione nuova collezione per l'utente.")
            user_collections[user_id] = {
                "comune": [],
                "rara": [],
                "epica": [],
                "leggendaria": [],
                "last_opened": None,  # Timestamp per l'ultima apertura
                "pack_reserve": 10   # Inizia con 10 pacchetti
            }

        # Recupera i dati dell'utente
        user_data = user_collections[user_id]

        # Inizializza eventuali chiavi mancanti
        user_data.setdefault("pack_reserve", 10)
        user_data.setdefault("last_opened", None)

        # Gestisci la riserva di pacchetti
        last_opened = user_data.get("last_opened")
        if last_opened:
            last_opened_time = datetime.fromisoformat(last_opened)
            time_diff = datetime.now() - last_opened_time
            if time_diff >= timedelta(hours=12):
                # Aggiungi fino a 5 pacchetti ogni 12 ore, senza superare il massimo di 10
                additional_packs = min(5, 10 - user_data["pack_reserve"])
                user_data["pack_reserve"] += additional_packs
                user_data["last_opened"] = datetime.now().isoformat()
        else:
            # Imposta il timestamp iniziale se manca
            user_data["last_opened"] = datetime.now().isoformat()

        # Verifica se ci sono pacchetti disponibili
        if user_data["pack_reserve"] <= 0:
            # Calcola il tempo mancante alla prossima ricarica
            last_opened_time = datetime.fromisoformat(user_data["last_opened"])
            next_refill_time = last_opened_time + timedelta(hours=12)
            time_remaining = next_refill_time - datetime.now()

            # Converti in ore, minuti e secondi
            hours, remainder = divmod(time_remaining.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Messaggio personalizzato
            await update.message.reply_text(
                f"Non hai pacchetti disponibili al momento.\n"
                f"Tempo rimanente per la prossima ricarica: **{hours} ore, {minutes} minuti e {seconds} secondi**.",
                parse_mode="Markdown"
            )
            return

        # Consuma un pacchetto
        user_data["pack_reserve"] -= 1

        # Determina la rarità
        roll = random.randint(1, 100)
        print(f"Roll ottenuto: {roll}")
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

        print(f"Rarità estratta: {rarity}")

        # Scegli una carta casuale
        card = random.choice(CARDS[rarity])
        print(f"Carta estratta: {card}")

        # Verifica se l'utente ha già questa carta
        if card in user_data[rarity]:
            await update.message.reply_text(f"🎉 Hai ottenuto una carta che hai già!\n✨ **{card}** ✨", parse_mode="Markdown")
            return

        # Aggiungi la carta alla collezione dell'utente
        user_data[rarity].append(card)
        save_collections()  # Salva la collezione aggiornata

        # Path per l'immagine della carta
        image_path = os.path.join("immagini", f"{normalize_filename(card)}.png")

        if os.path.isfile(image_path):
            try:
                # Invia il messaggio con immagine e testo formattato
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(image_path, "rb"),
                    caption=f"🎉 {user.first_name}, hai ottenuto una nuova carta {rarity.upper()}:\n✨ **{card}** ✨!",
                    parse_mode="Markdown"
                )
                print("Messaggio con immagine inviato correttamente.")
            except Exception as e:
                # Gestisci eventuali errori durante l'invio
                print(f"Errore durante l'invio dell'immagine: {e}")
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
            print("Messaggio senza immagine inviato correttamente.")
    except Exception as e:
        # Gestisci errori generali e stampa i dettagli
        print(f"Errore generico nella funzione /apri: {e}")
        await update.message.reply_text(
            "Si è verificato un errore durante l'elaborazione del comando. Riprova più tardi!",
            parse_mode="Markdown"
        )

# Comando per visualizzare la collezione dell'utente
async def collezione(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /collezione per visualizzare le carte possedute dall'utente nell'ordine dei file e con le rarità al plurale."""
    user = update.effective_user
    user_id = str(user.id)

    if user_id not in user_collections or not any(user_collections[user_id].values()):
        await update.message.reply_text("Non hai ancora ottenuto nessuna carta!", parse_mode="Markdown")
        return

    # Crea un messaggio con la collezione dell'utente, suddivisa per rarità
    collection_message = f"🎴 **Collezione di {escape_markdown(user.first_name)}:**\n\n"
    
    for rarity in ["comune", "rara", "epica", "leggendaria"]:
        owned_cards = user_collections[user_id][rarity]
        if owned_cards:
            if rarity == "comune":
                rarity_plural = "Comuni"
            elif rarity == "rara":
                rarity_plural = "Rare"
            elif rarity == "epica":
                rarity_plural = "Epiche"
            elif rarity == "leggendaria":
                rarity_plural = "Leggendarie"
                
            collection_message += f"**{rarity_plural}:**\n"
            
            # Escapa ogni carta prima di aggiungerla al messaggio
            ordered_cards = [escape_markdown(card) for card in CARDS[rarity] if card in owned_cards]
            collection_message += "\n".join(ordered_cards) + "\n\n"

    # Usa MarkdownV2 per una formattazione più sicura
    await update.message.reply_text(collection_message, parse_mode="MarkdownV2")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /start per iniziare!"""
    await update.message.reply_text(
        "🎴 Benvenuto nel Bot Raccolta Figurine di SBIT!\n"
        "Usa /apri per scoprire quale carta ottieni, oppure /help per scoprire tutti i comandi!",
        parse_mode="Markdown"
    )

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usa il comando /help per sapere tutto quello che c'è da sapere!"""
    await update.message.reply_text(
        "🎴 **Comandi disponibili:**\n"
        "- /apri: Scopri quale carta ottieni!\n"
        "- /pacchetti: Controlla il numero di pacchetti disponibili.\n"
        "- /collezione: Visualizza la tua collezione!\n"
        "- /riscatta: Riscatta un codice!\n"
        "- /reset: Cancella la tua collezione.\n"
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
    
# Funzione per visualizzare i pacchetti rimanenti
async def pacchetti(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /pacchetti per visualizzare i pacchetti rimanenti dell'utente."""
    user = update.effective_user
    user_id = str(user.id)

    # Verifica se l'utente ha una collezione
    if user_id not in user_collections:
        user_collections[user_id] = {
            "comune": [],
            "rara": [],
            "epica": [],
            "leggendaria": [],
            "last_opened": None,
            "pack_reserve": 10  # Inizia con 10 pacchetti se non esistono dati
        }

    # Recupera i dati dell'utente, assicurandosi che la chiave "pack_reserve" sia presente
    user_data = user_collections[user_id]

    # Imposta "pack_reserve" se manca
    if "pack_reserve" not in user_data:
        user_data["pack_reserve"] = 10  # Imposta un valore di default

    # Recupera il numero di pacchetti rimanenti
    pack_reserve = user_data["pack_reserve"]

    await update.message.reply_text(
        f"🃏 **Aperture rimanenti:** {pack_reserve}",
        parse_mode="Markdown"
    )
    
async def riscatta(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /riscatta per riscattare un codice."""
    user = update.effective_user
    user_id = str(user.id)

    # Verifica se l'utente ha inviato un codice
    if not context.args:
        await update.message.reply_text("Per favore, usa il comando così: /riscatta <codice>")
        return

    code = context.args[0].strip()
    codes = load_codes_from_github()

    # Verifica se il codice è valido
    if code not in codes["valid_codes"]:
        await update.message.reply_text("Codice non valido!")
        return

    # Recupera i codici riscattati dall'utente
    user_used_codes = codes["used_codes"].get(user_id, [])

    # Verifica se l'utente ha già riscattato il codice
    if code in user_used_codes:
        await update.message.reply_text("Hai già riscattato questo codice!")
        return

    # Riscatta il codice e assegna il premio
    reward = codes["valid_codes"][code]
    if reward["reward"] == "10_pacchetti":
        user_collections[user_id]["pack_reserve"] += 10
        await update.message.reply_text("Hai ricevuto 10 pacchetti! 🎉")
    elif reward["reward"] == "carta_esclusiva":
        card_name = reward["card_name"]
        user_collections[user_id]["leggendaria"].append(card_name)
        await update.message.reply_text(f"Hai ricevuto una carta esclusiva: {card_name}! 🎴")

    # Segna il codice come riscattato dall'utente
    if user_id not in codes["used_codes"]:
        codes["used_codes"][user_id] = []
    codes["used_codes"][user_id].append(code)

    # Salva i codici e le collezioni aggiornate
    save_codes_to_github(codes)
    save_collections()

    print(f"L'utente {user_id} ha riscattato il codice {code}.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /about per informazioni sul bot."""
    await update.message.reply_text(
        "Questo bot è stato creato da [@Raffosbaffos](https://t.me/Raffosbaffos)!\n"
        "Per qualsiasi problema, contattatemi direttamente! :D",
        parse_mode="Markdown"
    )
    
# Comando per resettare la collezione
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /reset per resettare la collezione dell'utente con conferma tramite pulsanti inline."""
    user = update.effective_user
    user_id = str(user.id)

    # Assicurati che l'utente abbia una collezione, anche vuota
    if user_id not in user_collections:
        user_collections[user_id] = {
            "comune": [],
            "rara": [],
            "epica": [],
            "leggendaria": []
        }

    # Verifica se l'utente ha carte
    if not any(user_collections[user_id].values()):
        await update.message.reply_text("Non hai ancora ottenuto nessuna carta!", parse_mode="Markdown")
        return

    # Crea i pulsanti inline per confermare il reset
    keyboard = [
        [
            InlineKeyboardButton("Sì", callback_data="reset_yes"),
            InlineKeyboardButton("No", callback_data="reset_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Chiedi conferma
    await update.message.reply_text(
        "Sei sicuro di voler resettare la tua collezione? Questa azione non può essere annullata.",
        reply_markup=reply_markup,
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
            "leggendaria": []
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
    application.add_handler(CommandHandler("pacchetti", pacchetti))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("bash", bash))
    application.add_handler(CommandHandler("riscatta", riscatta))
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