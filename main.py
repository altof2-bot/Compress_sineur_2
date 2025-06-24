import os
import requests
import telebot
from flask import Flask
from telebot import types
from keep_alive import keep_alive

# 🔐 Clés perso
BOT_TOKEN = "7632276236:AAEhlnesT3CqUqSOFciE9y82rQCZVJCWRX0"
OPENROUTER_API_KEY = "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"
PROPRIETAIRE_ID = 5116530698  # @FLAKI_47
DEUXIEME_ADMIN_ID = 7622994156

bot = telebot.TeleBot(BOT_TOKEN)

# 📁 Initialisation
for f in ["users.txt", "admins.txt"]:
    if not os.path.exists(f):
        with open(f, "w") as file:
            if f == "admins.txt":
                file.write(f"{PROPRIETAIRE_ID}\n{DEUXIEME_ADMIN_ID}\n")

# Ajout automatique si admins.txt existe déjà mais l'admin n'y est pas
with open("admins.txt", "r+") as f:
    lignes = f.read().splitlines()
    ajout = False
    if str(PROPRIETAIRE_ID) not in lignes:
        lignes.append(str(PROPRIETAIRE_ID))
        ajout = True
    if str(DEUXIEME_ADMIN_ID) not in lignes:
        lignes.append(str(DEUXIEME_ADMIN_ID))
        ajout = True
    if ajout:
        f.seek(0)
        f.write("\n".join(lignes) + "\n")

def est_admin(user_id):
    with open("admins.txt", "r") as f:
        return str(user_id) in f.read().splitlines()

def enregistrer_utilisateur(user_id):
    user_id = str(user_id)
    with open("users.txt", "r+") as f:
        users = f.read().splitlines()
        if user_id not in users:
            f.write(user_id + "\n")

@bot.message_handler(commands=['start'])
def welcome(message):
    enregistrer_utilisateur(message.chat.id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📘 How to Use", url="https://t.me/originstation/36"),
        types.InlineKeyboardButton("🛠️ Mise à jour", url="https://t.me/originstation"),
        types.InlineKeyboardButton("🆘 Support", url="https://t.me/+Jd43PgLV7k8wMDNh")
    )
    texte = (
        "👋 *Bienvenue, voyageur du digital !*\n\n"
        "Tu viens d’entrer dans un espace où chaque mot compte, chaque idée prend vie, "
        "et chaque échange peut devenir quelque chose d’unique ✨\n\n"
        "Exprime-toi librement. Le reste, je m’en occupe... 🚀 poser nous n’importe quelle question et on va vous répondre 🥳"
    )
    bot.send_message(message.chat.id, texte, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, """📘 *Commandes disponibles* :
/start — Accueil
/help — Aide
/image [prompt] — Génère une image stylée
/stats — Voir nombre d’utilisateurs (admin)
/broadcast [msg] — Envoie à tous (admin)
/addadmin [ID] — Ajouter un admin (proprio)
/removeadmin [ID] — Retirer admin (proprio)
""", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats(message):
    if not est_admin(message.from_user.id):
        return bot.reply_to(message, "🔒 Accès réservé aux admins.")
    with open("users.txt", "r") as f:
        total = len(f.readlines())
    bot.reply_to(message, f"👥 Utilisateurs enregistrés : *{total}*", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if not est_admin(message.from_user.id):
        return bot.reply_to(message, "🔒 Seuls les admins peuvent utiliser cette commande.")
    contenu = message.text.replace("/broadcast", "").strip()
    if not contenu:
        return bot.reply_to(message, "✏️ Utilisation : `/broadcast ton_message`", parse_mode="Markdown")
    with open("users.txt", "r") as f:
        utilisateurs = f.readlines()
    count = 0
    for uid in utilisateurs:
        try:
            bot.send_message(uid.strip(), contenu)
            count += 1
        except:
            continue
    bot.reply_to(message, f"✅ Message envoyé à {count} utilisateur(s).")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id != PROPRIETAIRE_ID:
        return bot.reply_to(message, "⛔ Seul le propriétaire peut ajouter un admin.")
    try:
        nouvel_id = message.text.split()[1]
        with open("admins.txt", "r+") as f:
            admins = f.read().splitlines()
            if nouvel_id not in admins:
                f.write(nouvel_id + "\n")
        bot.reply_to(message, f"✅ Admin ajouté : `{nouvel_id}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ Utilisation : `/addadmin ID`", parse_mode="Markdown")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if message.from_user.id != PROPRIETAIRE_ID:
        return bot.reply_to(message, "⛔ Seul le propriétaire peut retirer un admin.")
    try:
        cible = message.text.split()[1]
        with open("admins.txt", "r") as f:
            admins = f.read().splitlines()
        admins = [a for a in admins if a != cible and a != str(PROPRIETAIRE_ID)]
        with open("admins.txt", "w") as f:
            f.write("\n".join(admins) + "\n")
        bot.reply_to(message, f"🗑️ Admin retiré : `{cible}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "⚠️ Utilisation : `/removeadmin ID`", parse_mode="Markdown")

@bot.message_handler(commands=['image'])
def generer_image(message):
    prompt = message.text.replace('/image', '').strip()
    if not prompt:
        return bot.reply_to(message, "✍️ Utilisation : `/image un temple perdu dans la jungle`", parse_mode="Markdown")
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/images/generations",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={"model": "openai/dall-e-3", "prompt": prompt, "size": "512x512"}
        )
        url = res.json()["data"][0]["url"]
        bot.send_photo(message.chat.id, url, caption="🎨 _Création magique signée VerboticaGPT_")
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur image : {e}")

@bot.message_handler(content_types=['photo'])
def analyse_image_envoyee(message):
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        image_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json={
                "model": "openai/gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Agis comme un assistant intelligent. Analyse l’image (devoir, consigne ou question) et réponds clairement."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                "max_tokens": 1500
            }
        )
        contenu = response.json()["choices"][0]["message"]["content"]
        bot.reply_to(message, contenu + "\n\n🧠 _Réponse générée avec VerboticaGPT_")
    except Exception as e:
        bot.reply_to(message, f"❌ Je n’ai pas pu lire cette image. Erreur : {e}")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://replit.com",
                "X-Title": "VerboticaGPT"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": message.text}]
            }
        )
        contenu = r.json()["choices"][0]["message"]["content"]
        signature = "\n\n🤖 _Réponse générée par VerboticaGPT_"
        bot.reply_to(message, contenu + signature)
    except Exception as e:
        bot.reply_to(message, f"❌ Erreur GPT : {e}")

# 🌐 Pour Replit / UptimeRobot
app = Flask(__name__)
@app.route('/')
def home():
    return "🤖 VerboticaGPT est en ligne"

if __name__ == "__main__":
    bot.polling(non_stop=True)
    app.run
