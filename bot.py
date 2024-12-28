import os
import re
import uuid

import telebot
import yt_dlp
from dotenv import load_dotenv
from telebot import types

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    text = (
        "Привіт! 👋\n"
        "Надішли мені посилання на відео або аудіо, і я допоможу тобі його завантажити. 🚀\n\n"
        "Цей бот дозволяє завантажувати відео або аудіо з таких платформ, як 𝙔𝙤𝙪𝙏𝙪𝙗𝙚, 𝙏𝙞𝙠𝙩𝙤𝙠, 𝙎𝙤𝙪𝙣𝙙𝘾𝙡𝙤𝙪𝙙, 𝙏𝙬𝙞𝙩𝙘𝙝, 𝙁𝙖𝙘𝙚𝙗𝙤𝙤𝙠, 𝙄𝙣𝙨𝙩𝙖𝙜𝙧𝙖𝙢, 𝙏𝙬𝙞𝙩𝙩𝙚𝙧, 𝙑𝙞𝙢𝙚𝙤 та ... "
        "Для інших платформ просто поділися посиланням, і я спробую завантажити контент, якщо це буде можливо."
    )
    bot.reply_to(message, text)

message_data = {}
@bot.message_handler(content_types=["text"])
def get_media_choice(message):

    url_pattern = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"
    if re.match(url_pattern, message.text):
        global message_data
        message_data = {"message": message}

        markup = types.InlineKeyboardMarkup()
        btn_video = types.InlineKeyboardButton("Відео", callback_data="video")
        btn_audio = types.InlineKeyboardButton("Аудіо", callback_data="audio")
        markup.add(btn_video, btn_audio)

        bot.reply_to(message, "Виберіть, що завантажити:", reply_markup=markup)

    else:
        bot.reply_to(message, "На жаль, це не валідне посилання(")

@bot.callback_query_handler(func=lambda call: True)
def callback_download(call):

    message = message_data["message"]
    url = message.text

    if call.data == "video":
        download_media(message, url, media_type="video")
    elif call.data == "audio":
        download_media(message, url, media_type="audio")


def download_media(message, url, media_type):
    unique_name = str(uuid.uuid4())[:4]
    file_extension = "mp4" if media_type == "video" else "mp3"

    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        name = info.get("title", "default_name")
        cleaned_name = " ".join(name.split()[:6])

    downloaded_file_path = f"downloads/{cleaned_name + " " + unique_name}.{file_extension}"

    ydl_opts = {
        "format": "best" if media_type == "video" else "bestaudio",
        "outtmpl": downloaded_file_path,
        "extract_audio": True if media_type == "audio" else False,
    }

    bot.reply_to(message, "Зачекайте, завантажуємо...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as file:
            file.download([url])

        if os.path.exists(downloaded_file_path):
            with open(downloaded_file_path, "rb") as media_file:
                if media_type == "video":
                    bot.send_video(message.chat.id, media_file, reply_to_message_id=message.message_id)
                else:
                    bot.send_audio(message.chat.id, media_file, reply_to_message_id=message.message_id)

            os.remove(downloaded_file_path)
        else:
            bot.reply_to(message, f"Помилка: {media_type} не було завантажено.")

    except Exception:
        bot.reply_to(message, f"Ми не можемо завантажити {media_type}(")


bot.infinity_polling(skip_pending=True)
