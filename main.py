import telebot
import json
from datetime import datetime, time
import threading
import time as t

BOT_TOKEN = "8451492674:AAHBjQMa2YaPHPNN7SyMf3zOODPR6cZP0W4"

bot = telebot.TeleBot(BOT_TOKEN)

CONFIG_FILE = "config.json"


def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


config = load_config()
allowed_user = config["allowed_user"]


# ============= DAILY SENDER ================

def daily_sender():
    while True:
        cfg = load_config()
        hh, mm = cfg["send_time"].split(":")
        now = datetime.now().strftime("%H:%M")

        if now == f"{hh}:{mm}":
            bot.send_message(cfg["allowed_user"], cfg["message_text"])
            t.sleep(60)  # чтобы не отправлял повторно в ту же минуту

        t.sleep(1)


threading.Thread(target=daily_sender, daemon=True).start()


# ============= ACCESS CONTROL =============

def check_access(message):
    return message.from_user.id == allowed_user


# ============= COMMANDS ===================

@bot.message_handler(commands=["start"])
def start(message):
    if not check_access(message):
        return
    bot.reply_to(message, "Панель управления:\n"
                          "/settext – изменить текст\n"
                          "/settime – изменить время\n"
                          "/show – показать текущий конфиг")


@bot.message_handler(commands=["show"])
def show_config(message):
    if not check_access(message):
        return
    cfg = load_config()
    bot.reply_to(message, f"Текущее сообщение:\n{cfg['message_text']}\n\n"
                          f"Время отправки: {cfg['send_time']}")


@bot.message_handler(commands=["settext"])
def set_text(message):
    if not check_access(message):
        return
    bot.reply_to(message, "Введите новый текст сообщения:")

    bot.register_next_step_handler(message, save_new_text)


def save_new_text(message):
    if not check_access(message):
        return
    cfg = load_config()
    cfg["message_text"] = message.text
    save_config(cfg)
    bot.reply_to(message, "Текст обновлён!")


@bot.message_handler(commands=["settime"])
def set_time(message):
    if not check_access(message):
        return

    bot.reply_to(message, "Введите новое время (формат HH:MM):")
    bot.register_next_step_handler(message, save_new_time)


def save_new_time(message):
    if not check_access(message):
        return

    new_time = message.text.strip()

    try:
        datetime.strptime(new_time, "%H:%M")
    except:
        bot.reply_to(message, "Ошибка! Введите время в формате HH:MM")
        return

    cfg = load_config()
    cfg["send_time"] = new_time
    save_config(cfg)

    bot.reply_to(message, f"Время отправки обновлено на {new_time}")


# ============= RUN BOT ====================

bot.infinity_polling()
