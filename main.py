import telebot
import json
import threading
import time as t
from datetime import datetime

BOT_TOKEN = "8451492674:AAHBjQMa2YaPHPNN7SyMf3zOODPR6cZP0W4"
bot = telebot.TeleBot(BOT_TOKEN)

CONFIG_FILE = "config.json"
LOG_FILE = "log.txt"


# ================= CONFIG =================

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


config = load_config()
allowed_user = config["allowed_user"]


# ============ LOGGING ===============

def log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {text}\n")


# ============ DAILY SENDER (TARGET THREAD) ===============

def daily_sender():
    log("Поток отправки запущен")
    while True:
        try:
            cfg = load_config()
            hh, mm = cfg["send_time"].split(":")
            now = datetime.now().strftime("%H:%M")

            # Отправка по времени
            if now == f"{hh}:{mm}":
                bot.send_message(cfg["allowed_user"], cfg["message_text"])
                log("Сообщение отправлено")
                t.sleep(60)

            t.sleep(1)

        except Exception as e:
            log(f"ОШИБКА в потоке отправки: {e}")
            t.sleep(5)  # пауза чтобы бот не улетел в цикл ошибки


# ============ WATCHDOG ===============

def watchdog():
    log("Watchdog запущен")

    while True:
        global sender_thread

        if not sender_thread.is_alive():
            log("Поток отправки упал! Перезапуск...")
            sender_thread = threading.Thread(target=daily_sender, daemon=True)
            sender_thread.start()
            log("Поток отправки восстановлен")

        t.sleep(3)  # проверять каждые 3 секунды


# Запускаем поток отправки
sender_thread = threading.Thread(target=daily_sender, daemon=True)
sender_thread.start()

# Запускаем watchdog
threading.Thread(target=watchdog, daemon=True).start()


# ========== ACCESS CONTROL ==========

def check_access(message):
    return message.from_user.id == allowed_user


# ========== COMMANDS ===============

@bot.message_handler(commands=["start"])
def start(message):
    if not check_access(message):
        return
    bot.reply_to(message, "Панель управления:\n"
                          "/settext – изменить текст\n"
                          "/settime – изменить время\n"
                          "/show – показать конфиг")


@bot.message_handler(commands=["show"])
def show_config(message):
    if not check_access(message):
        return
    cfg = load_config()
    bot.reply_to(message, f"Текущий текст:\n{cfg['message_text']}\n\n"
                          f"Время: {cfg['send_time']}")


@bot.message_handler(commands=["settext"])
def set_text(message):
    if not check_access(message):
        return
    bot.reply_to(message, "Введите новый текст:")
    bot.register_next_step_handler(message, save_new_text)


def save_new_text(message):
    if not check_access(message):
        return
    cfg = load_config()
    cfg["message_text"] = message.text
    save_config(cfg)
    bot.reply_to(message, "Текст обновлён!")
    log("Текст в config.json обновлён")


@bot.message_handler(commands=["settime"])
def set_time(message):
    if not check_access(message):
        return
    bot.reply_to(message, "Введите время (HH:MM):")
    bot.register_next_step_handler(message, save_new_time)


def save_new_time(message):
    if not check_access(message):
        return

    try:
        datetime.strptime(message.text, "%H:%M")
    except:
        bot.reply_to(message, "Ошибка! Используйте формат HH:MM")
        return

    cfg = load_config()
    cfg["send_time"] = message.text
    save_config(cfg)

    bot.reply_to(message, f"Время обновлено на {message.text}")
    log(f"Время в config.json обновлено на {message.text}")


# ========== START BOT ===============

bot.infinity_polling()
