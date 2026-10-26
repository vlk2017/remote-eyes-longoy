"""Telegram webhook for Garintugarin. Android is not hosted on Render."""
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
OWNER = os.getenv("TELEGRAM_OWNER_ID", "").strip()
URL = os.getenv("RENDER_EXTERNAL_URL", "").strip()
SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET") or hashlib.sha256((TOKEN + ":garintugarin:render:2026").encode()).hexdigest()
if not TOKEN or ":" not in TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
if OWNER and not OWNER.isdigit():
    raise RuntimeError("TELEGRAM_OWNER_ID must be numeric")
if not URL.startswith("https://"):
    raise RuntimeError("RENDER_EXTERNAL_URL must be HTTPS")

def api(method, data, timeout=15):
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + TOKEN + "/" + method,
        data=json.dumps(data, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as e:
        raise RuntimeError("Telegram API HTTP " + str(e.code)) from None
    if not result.get("ok"):
        raise RuntimeError("Telegram API " + method + " error")
    return result["result"]

def reply(chat, text):
    api("sendMessage", {"chat_id": chat, "text": text[:3900]})

def handle(update):
    message = update.get("message") or {}
    user = message.get("from") or {}
    chat = message.get("chat") or {}
    chat_id, user_id = chat.get("id"), user.get("id")
    if not isinstance(chat_id, int) or not isinstance(user_id, int):
        return
    cmd = str(message.get("text") or "").strip().split("@")[0]
    if cmd.startswith("/whoami"):
        reply(chat_id, f"Ваш Telegram ID: {user_id}. Добавьте его в Render как TELEGRAM_OWNER_ID.")
        return
    if not OWNER:
        reply(chat_id, "Бот запущен на Render, но доступ владельца не настроен. Отправьте /whoami и укажите ID в Render.")
        return
    if user_id != int(OWNER) or chat_id != user_id:
        reply(chat_id, "Доступ ограничен владельцем.")
        return
    if cmd.startswith("/start") or cmd.startswith("/help"):
        reply(chat_id, "Garintugarin × MIR SIGNAL\n\n/status — состояние\n/whoami — Telegram ID\n/scan вентиляция — поиск (ожидает Android)\n/scan демонтаж — только внутренняя отделка (ожидает Android)\n/scan продажа — покупатели MIR SIGNAL (ожидает Android)\n\nОблачный бот принимает команды, но Mobilerun пока не подключён. Лиды не выдумываются.")
    elif cmd.startswith("/status"):
        reply(chat_id, "Telegram: Render webhook подключён.\nAndroid/ADB/Mobilerun: не подключены.\nРассылки отключены.")
    elif cmd.startswith("/scan") or cmd.startswith("/inspect"):
        reply(chat_id, "Нет подключённого Android-исполнителя Mobilerun. Поиск не запускался, результатов нет.")
    elif cmd.startswith("/leads") or cmd.startswith("/lead") or cmd.startswith("/approve"):
        reply(chat_id, "Хранилище сигналов пока не подключено к облачному боту. Отправка сообщений отключена.")
    else:
        reply(chat_id, "Неизвестная команда. /help")

def respond(start_response, status, data):
    body = json.dumps(data, ensure_ascii=False).encode()
    start_response(status, [("Content-Type", "application/json; charset=utf-8"), ("Content-Length", str(len(body)))])
    return [body]

def application(env, start_response):
    path, method = env.get("PATH_INFO"), env.get("REQUEST_METHOD")
    if path == "/health" and method == "GET":
        return respond(start_response, "200 OK", {"ok": True, "bot": "Garintugarin", "android": False})
    if path != "/telegram" or method != "POST":
        return respond(start_response, "404 Not Found", {"ok": False})
    if not hmac.compare_digest(env.get("HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN", ""), SECRET):
        return respond(start_response, "403 Forbidden", {"ok": False})
    try:
        size = int(env.get("CONTENT_LENGTH") or "0")
        if size < 1 or size > 512000:
            return respond(start_response, "413 Request Entity Too Large", {"ok": False})
        update = json.loads(env["wsgi.input"].read(size))
        if not isinstance(update, dict):
            raise ValueError("bad body")
    except (ValueError, UnicodeError):
        return respond(start_response, "400 Bad Request", {"ok": False})
    try:
        handle(update)
    except Exception as error:
        print("Webhook failure:", type(error).__name__, file=sys.stderr, flush=True)
        return respond(start_response, "503 Service Unavailable", {"ok": False})
    return respond(start_response, "200 OK", {"ok": True})

def initialize():
    me = api("getMe", {})
    if me.get("username", "").lower() != "garintugarin_bot":
        raise RuntimeError("Wrong bot username")
    api("setWebhook", {
        "url": URL.rstrip("/") + "/telegram",
        "secret_token": SECRET,
        "allowed_updates": ["message"],
        "max_connections": 1
    })
    api("setMyCommands", {"commands": [
        {"command": "start", "description": "Открыть бота"},
        {"command": "whoami", "description": "Показать мой Telegram ID"},
        {"command": "status", "description": "Статус подключений"},
        {"command": "scan", "description": "Проверить доступность поиска"},
        {"command": "help", "description": "Справка"}]})
    print("Garintugarin Telegram webhook configured", flush=True)

initialize()
