import os
import html
import logging
from fastapi import FastAPI, Request
import httpx

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = os.environ["GROUP_CHAT_ID"]
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

app = FastAPI(title="Turon Olmaliq Lead Bot")
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

async def tg(method: str, payload: dict):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{TELEGRAM_API}/{method}", json=payload)
        r.raise_for_status()
        return r.json()

def source_from_start(text: str) -> str:
    parts = text.split(maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else "unknown"

@app.get("/")
async def health():
    return {"ok": True, "service": "Turon Olmaliq Lead Bot"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    if WEBHOOK_SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token", "") != WEBHOOK_SECRET:
        return {"ok": False}
    update = await request.json()
    message = update.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return {"ok": True}
    if text.startswith("/start"):
        source = source_from_start(text)
        keyboard = {"inline_keyboard": [[{"text": "📝 Оставить заявку", "callback_data": f"lead:{source[:40]}"}]]}
        await tg("sendMessage", {
            "chat_id": chat_id,
            "text": "📡 <b>Turon Telecom Olmaliq</b>\n\nЗдравствуйте! 👋\nОставьте заявку на подключение домашнего интернета. Наш специалист свяжется с вами.",
            "parse_mode": "HTML", "reply_markup": keyboard
        })
    return {"ok": True}

@app.post("/telegram/callback")
async def telegram_callback(request: Request):
    if WEBHOOK_SECRET and request.headers.get("X-Telegram-Bot-Api-Secret-Token", "") != WEBHOOK_SECRET:
        return {"ok": False}
    update = await request.json()
    cq = update.get("callback_query")
    if not cq:
        return {"ok": True}
    data = cq.get("data", "")
    source = data.removeprefix("lead:") or "unknown"
    await tg("answerCallbackQuery", {"callback_query_id": cq["id"], "text": "Открываем заявку"})
    await tg("sendMessage", {
        "chat_id": cq["message"]["chat"]["id"],
        "text": "📝 <b>Заявка</b>\n\nПервая версия системы подключена.\n📢 Источник QR: <code>" + html.escape(source) + "</code>\n\nСледующим шагом добавим форму имени, телефона, адреса и тарифа.",
        "parse_mode": "HTML"
    })
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
