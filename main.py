```python
import os
import html
import logging
import secrets
import httpx

from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)

# ============================================================
# TELEGRAM SOZLAMALARI
# ============================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
GROUP_CHAT_ID = os.environ.get("GROUP_CHAT_ID", "")
CHANNEL_USERNAME = "@Turon_WiFi_Olmaliq"
ADMIN_USER_ID = 8345237481
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI(title="Turon Olmaliq Lead Bot")


# ============================================================
# TARIFLAR
# ============================================================

TARIFLAR = {

    "premier80": {
        "nomi": "Premier 80",
        "narxi": "165 000 so‘m/oy",

        "kunduz": "16:00–00:00 — 80 Mbit/s",
        "tun": "00:00–16:00 — 200 Mbit/s",

        "cinerama": "Cinerama Standard",
        "tv": "170+ TV kanallar",
        "film": "30 000+ film va seriallar",
        "multfilm": "1 600+ multfilmlar",
        "uzbek": "1 200+ o‘zbek kontenti",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "82 500 so‘m",
        "oy2": "82 500 so‘m",
        "oy3": "165 000 so‘m/oy",
    },

    "premier100": {
        "nomi": "Premier 100",
        "narxi": "185 000 so‘m/oy",

        # ANIQ TEXNIK MA'LUMOT KEYIN KIRITILADI
        "kunduz": "—",
        "tun": "—",

        "cinerama": "—",
        "tv": "—",
        "film": "—",
        "multfilm": "—",
        "uzbek": "—",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "92 500 so‘m",
        "oy2": "92 500 so‘m",
        "oy3": "185 000 so‘m/oy",
    },

    "ultima200": {
        "nomi": "Ultima 200",
        "narxi": "270 000 so‘m/oy",

        "kunduz": "—",
        "tun": "—",

        "cinerama": "—",
        "tv": "—",
        "film": "—",
        "multfilm": "—",
        "uzbek": "—",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "135 000 so‘m",
        "oy2": "135 000 so‘m",
        "oy3": "270 000 so‘m/oy",
    },

    "ultima300": {
        "nomi": "Ultima 300",
        "narxi": "370 000 so‘m/oy",

        "kunduz": "—",
        "tun": "—",

        "cinerama": "—",
        "tv": "—",
        "film": "—",
        "multfilm": "—",
        "uzbek": "—",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "185 000 so‘m",
        "oy2": "185 000 so‘m",
        "oy3": "370 000 so‘m/oy",
    },

    "ultima500": {
        "nomi": "Ultima 500",
        "narxi": "500 000 so‘m/oy",

        "kunduz": "—",
        "tun": "—",

        "cinerama": "—",
        "tv": "—",
        "film": "—",
        "multfilm": "—",
        "uzbek": "—",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "250 000 so‘m",
        "oy2": "250 000 so‘m",
        "oy3": "500 000 so‘m/oy",
    },

    "ultima1000": {
        "nomi": "Ultima 1000",
        "narxi": "1 000 000 so‘m/oy",

        "kunduz": "—",
        "tun": "—",

        "cinerama": "—",
        "tv": "—",
        "film": "—",
        "multfilm": "—",
        "uzbek": "—",

        "chegirma": "1–2 oyga 50% chegirma",
        "oy1": "500 000 so‘m",
        "oy2": "500 000 so‘m",
        "oy3": "1 000 000 so‘m/oy",
    },

}


# ============================================================
# QR MANBALARI
# ============================================================

QR_MANBALARI = {

    "ehtirom-10": "Ehtirom ko‘chasi, 10-uy",

}


# ============================================================
# VAQTINCHALIK SESSIYALAR
# ============================================================

SESSIONS = {}


def get_session(chat_id: int):

    if chat_id not in SESSIONS:
        SESSIONS[chat_id] = {}

    return SESSIONS[chat_id]


# ============================================================
# TELEGRAM API
# ============================================================

async def telegram(method: str, payload: dict):

    async with httpx.AsyncClient(timeout=20) as client:

        response = await client.post(
            f"{TELEGRAM_API}/{method}",
            json=payload
        )

        response.raise_for_status()

        return response.json()


# ============================================================
# QR MANBASINI ANIQLASH
# ============================================================

def get_source_name(source: str):

    if not source:
        return "Aniqlanmagan"

    if source in QR_MANBALARI:
        return QR_MANBALARI[source]

    return source.replace("-", " ").title()


# ============================================================
# BOSHLANG‘ICH MENYU
# ============================================================

def main_keyboard():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "📝 Ariza qoldirish",
                    "callback_data": "lead:start"
                }
            ],

            [
                {
                    "text": "📶 Tariflarni ko‘rish",
                    "callback_data": "tarif:list"
                }
            ]

        ]
    }


# ============================================================
# TARIFLAR MENYUSI
# ============================================================

def tariffs_keyboard():

    buttons = []

    for key, tarif in TARIFLAR.items():

        buttons.append([
            {
                "text": f"📶 {tarif['nomi']} — {tarif['narxi']}",
                "callback_data": f"tarif:{key}"
            }
        ])

    buttons.append([
        {
            "text": "⬅️ Ortga",
            "callback_data": "back:start"
        }
    ])

    return {
        "inline_keyboard": buttons
    }


# ============================================================
# TARIF TANLASH YOKI O‘TKAZIB YUBORISH
# ============================================================

def tariff_choice_keyboard():

    buttons = []

    for key, tarif in TARIFLAR.items():

        buttons.append([
            {
                "text": f"📶 {tarif['nomi']} — {tarif['narxi']}",
                "callback_data": f"tarif:{key}"
            }
        ])

    buttons.append([
        {
            "text": "📝 Tarif tanlamasdan ariza berish",
            "callback_data": "tarif:none"
        }
    ])

    return {
        "inline_keyboard": buttons
    }


# ============================================================
# TARIF BATAFSIL KARTOCHKASI
# ============================================================

def tariff_detail_keyboard(key: str):

    return {
        "inline_keyboard": [

            [
                {
                    "text": "📝 Ushbu tarifga ulanish",
                    "callback_data": f"lead:tarif:{key}"
                }
            ],

            [
                {
                    "text": "⬅️ Tariflarga qaytish",
                    "callback_data": "tarif:list"
                }
            ],

            [
                {
                    "text": "🏠 Bosh menyu",
                    "callback_data": "back:start"
                }
            ]

        ]
    }


# ============================================================
# START
# ============================================================

async def show_start(chat_id: int, source: str):

    session = get_session(chat_id)

    session.clear()

    session["source"] = source

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": (
                "📡 <b>Turon Telecom Olmaliq</b>\n\n"

                "Assalomu alaykum! 👋\n\n"

                "🏠 Uyingizga tezkor va sifatli "
                "internet ulang.\n\n"

                "Ariza qoldirish yoki tariflarni "
                "ko‘rish uchun quyidagi tugmalardan "
                "birini tanlang."
            ),

            "parse_mode": "HTML",

            "reply_markup": main_keyboard()
        }
    )


# ============================================================
# TARIFLAR RO‘YXATI
# ============================================================

async def show_tariffs(chat_id: int):

    text = (
        "📋 <b>TARIFLAR</b>\n\n"

        "1️⃣ <b>Premier 80</b> — 165 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "2️⃣ <b>Premier 100</b> — 185 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "3️⃣ <b>Ultima 200</b> — 270 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "4️⃣ <b>Ultima 300</b> — 370 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "5️⃣ <b>Ultima 500</b> — 500 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "6️⃣ <b>Ultima 1000</b> — 1 000 000 so‘m\n"
        "🔥 1–2 oyga 50% CHEGIRMA!\n\n"

        "📌 Bizda aksiyalar va maxsus takliflar "
        "muntazam yangilanib turadi.\n\n"

        "👇 <b>O‘zingizga mos tarifni tanlang!</b>"
    )

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": tariffs_keyboard()
        }
    )


# ============================================================
# TARIF BATAFSIL
# ============================================================

async def show_tariff_detail(chat_id: int, key: str):

    if key not in TARIFLAR:
        return

    tarif = TARIFLAR[key]

    text = (
        f"🚀 <b>{html.escape(tarif['nomi'])}</b>\n\n"

        "⚡ <b>Tezlik:</b>\n"
        f"☀️ {html.escape(tarif['kunduz'])}\n"
        f"🌙 {html.escape(tarif['tun'])}\n\n"

        f"🎬 <b>{html.escape(tarif['cinerama'])}</b>\n"
        f"📺 {html.escape(tarif['tv'])}\n"
        f"🎞 {html.escape(tarif['film'])}\n"
        f"🎨 {html.escape(tarif['multfilm'])}\n"
        f"🇺🇿 {html.escape(tarif['uzbek'])}\n\n"

        f"💰 <b>Asosiy narx:</b> "
        f"{html.escape(tarif['narxi'])}\n\n"

        f"🎁 <b>1-oy:</b> {html.escape(tarif['oy1'])}\n"
        f"🎁 <b>2-oy:</b> {html.escape(tarif['oy2'])}\n"
        f"💳 <b>3-oydan:</b> {html.escape(tarif['oy3'])}\n\n"

        f"🔥 <b>{html.escape(tarif['chegirma'])}!</b>\n\n"

        "👇 <b>Ushbu tarifga ulanish uchun tugmani bosing.</b>"
    )

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": tariff_detail_keyboard(key)
        }
    )


# ============================================================
# ISMNI SO‘RASH
# ============================================================

async def ask_name(chat_id: int):

    session = get_session(chat_id)

    session["step"] = "name"

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": (
                "👤 <b>Ismingizni kiriting:</b>"
            ),

            "parse_mode": "HTML"
        }
    )


# ============================================================
# TELEFONNI SO‘RASH
# ============================================================

async def ask_phone(chat_id: int):

    session = get_session(chat_id)

    session["step"] = "phone"

    keyboard = {

        "keyboard": [

            [
                {
                    "text": "📱 Telefon raqamimni yuborish",
                    "request_contact": True
                }
            ]

        ],

        "resize_keyboard": True,

        "one_time_keyboard": True

    }

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": (
                "📱 <b>Telefon raqamingizni yuboring:</b>"
            ),

            "parse_mode": "HTML",

            "reply_markup": keyboard
        }
    )


# ============================================================
# MANZILNI SO‘RASH
# ============================================================

async def ask_address(chat_id: int):

    session = get_session(chat_id)

    session["step"] = "address"

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": (
                "📍 <b>Manzilingizni kiriting.</b>\n\n"
                "Masalan:\n"
                "Ehtirom ko‘chasi, 10-uy, 25-xonadon"
            ),

            "parse_mode": "HTML",

            "reply_markup": {
                "remove_keyboard": True
            }
        }
    )


# ============================================================
# TARIFNI TANLASH / O‘TKAZIB YUBORISH
# ============================================================

async def ask_tariff_or_skip(chat_id: int):

    session = get_session(chat_id)

    session["step"] = "tarif"

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": (
                "📶 <b>Tarifni tanlang</b>\n\n"

                "Agar hozircha tarif tanlamoqchi "
                "bo‘lmasangiz, arizani tarifsiz "
                "ham yuborishingiz mumkin."
            ),

            "parse_mode": "HTML",

            "reply_markup": tariff_choice_keyboard()
        }
    )


# ============================================================
# ARIZANI TASDIQLASH
# ============================================================

async def show_confirmation(chat_id: int):

    session = get_session(chat_id)

    tarif_key = session.get("tarif")

    if tarif_key and tarif_key in TARIFLAR:

        tarif = TARIFLAR[tarif_key]

        tarif_name = tarif["nomi"]
        tarif_price = tarif["narxi"]

    else:

        tarif_name = "Tarif tanlanmagan"
        tarif_price = "—"

    text = (

        "📋 <b>Arizangizni tekshiring</b>\n\n"

        f"👤 Ism: <b>{html.escape(session['name'])}</b>\n"

        f"📱 Telefon: "
        f"<b>{html.escape(session['phone'])}</b>\n"

        f"📍 Manzil: "
        f"<b>{html.escape(session['address'])}</b>\n"

        f"📶 Tarif: "
        f"<b>{html.escape(tarif_name)}</b>\n"

        f"💰 Narxi: "
        f"<b>{html.escape(tarif_price)}</b>\n\n"

        "Hammasi to‘g‘rimi?"
    )

    keyboard = {

        "inline_keyboard": [

            [
                {
                    "text": "✅ Arizani yuborish",
                    "callback_data": "lead:confirm"
                }
            ],

            [
                {
                    "text": "✏️ Qaytadan kiritish",
                    "callback_data": "lead:restart"
                }
            ]

        ]

    }

    await telegram(
        "sendMessage",
        {
            "chat_id": chat_id,

            "text": text,

            "parse_mode": "HTML",

            "reply_markup": keyboard
        }
    )


# ============================================================
# ARIZANI ISHCHI GURUHGA YUBORISH
# ============================================================

async def send_lead_to_group(chat_id: int):

    session = get_session(chat_id)

    tarif_key = session.get("tarif")

    if tarif_key and tarif_key in TARIFLAR:

        tarif = TARIFLAR[tarif_key]

        tarif_name = tarif["nomi"]
        tarif_price = tarif["narxi"]
        tarif_discount = tarif["chegirma"]

    else:

        tarif_name = "Tarif tanlanmagan"
        tarif_price = "—"
        tarif_discount = "—"

    source = session.get(
        "source",
        "unknown"
    )

    source_name = get_source_name(source)

    lead_id = secrets.token_hex(3).upper()

    message = (

        "🔔 <b>YANGI ARIZA</b>\n\n"

        f"🆔 Ariza: <code>#{lead_id}</code>\n\n"

        f"👤 Ism: "
        f"<b>{html.escape(session['name'])}</b>\n"

        f"📱 Telefon: "
        f"<b>{html.escape(session['phone'])}</b>\n"

        f"📍 Manzil: "
        f"<b>{html.escape(session['address'])}</b>\n\n"

        f"📶 Tarif: "
        f"<b>{html.escape(tarif_name)}</b>\n"

        f"💰 Narxi: "
        f"<b>{html.escape(tarif_price)}</b>\n"

        f"🎁 Aksiya: "
        f"<b>{html.escape(tarif_discount)}</b>\n\n"

        f"📢 <b>QR manbasi:</b>\n"
        f"{html.escape(source_name)}\n\n"

        "🟢 <b>Holati: Yangi ariza</b>"
    )

    if GROUP_CHAT_ID:

        await telegram(
            "sendMessage",
            {
                "chat_id": GROUP_CHAT_ID,

                "text": message,

                "parse_mode": "HTML"
            }
        )

        return True

    return False


# ============================================================
# WEBHOOK
# ============================================================

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):

    if WEBHOOK_SECRET:

        secret = request.headers.get(
            "X-Telegram-Bot-Api-Secret-Token",
            ""
        )

        if secret != WEBHOOK_SECRET:

            return {
                "ok": False
            }

    update = await request.json()


    # ========================================================
    # ODDIY XABAR
    # ========================================================

    message = update.get("message")

    if message:

        chat_id = message["chat"]["id"]

        text = message.get(
            "text",
            ""
        ).strip()


        # ----------------------------------------------------
        # POST В КАНАЛ — ТОЛЬКО ДЛЯ АДМИНИСТРАТОРА
        # ----------------------------------------------------

        if text == "/post":

            if chat_id != ADMIN_USER_ID:

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,
                        "text": (
                            "⛔ Bu buyruq faqat "
                            "administrator uchun."
                        )
                    }
                )

                return {
                    "ok": True
                }

            keyboard = {

                "inline_keyboard": [

                    [
                        {
                            "text": "📝 Ariza qoldirish",
                            "url": (
                                "https://t.me/"
                                "TuronTelecomOlmaliqBot"
                                "?start=wifi_olmaliq"
                            )
                        }
                    ]

                ]

            }

            await telegram(
                "sendMessage",
                {
                    "chat_id": CHANNEL_USERNAME,

                    "text": (
                        "📡 <b>Turon Telecom Olmaliq</b>\n\n"

                        "🏠 Uyingizga tezkor va sifatli "
                        "internet ulang!\n\n"

                        "📝 Internet ulash uchun "
                        "ariza qoldiring.\n\n"

                        "Ma’lumotlaringizni qoldiring — "
                        "mutaxassisimiz siz bilan bog‘lanadi.\n\n"

                        "👇 <b>Ariza qoldirish uchun "
                        "tugmani bosing</b>"
                    ),

                    "parse_mode": "HTML",

                    "reply_markup": keyboard
                }
            )

            await telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": "✅ Post kanalga yuborildi."
                }
            )

            return {
                "ok": True
            }


        # ----------------------------------------------------
        # START
        # ----------------------------------------------------

        if text.startswith("/start"):

            parts = text.split(
                maxsplit=1
            )

            source = (
                parts[1]
                if len(parts) == 2
                else "unknown"
            )

            await show_start(
                chat_id,
                source
            )


        # ----------------------------------------------------
        # CHAT ID
        # ----------------------------------------------------

        elif text == "/id":

            await telegram(
                "sendMessage",
                {
                    "chat_id": chat_id,

                    "text": (
                        "🆔 Ushbu chat ID:\n\n"
                        f"<code>{chat_id}</code>"
                    ),

                    "parse_mode": "HTML"
                }
            )


        # ----------------------------------------------------
        # TEST
        # ----------------------------------------------------

        elif text == "/test":

            if GROUP_CHAT_ID:

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": GROUP_CHAT_ID,

                        "text": (
                            "🧪 <b>TEST</b>\n\n"
                            "✅ Turon Olmaliq Lead Bot "
                            "ishlayapti."
                        ),

                        "parse_mode": "HTML"
                    }
                )

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,

                        "text": (
                            "✅ Test xabari ishchi "
                            "guruhga yuborildi."
                        )
                    }
                )

            else:

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,

                        "text": (
                            "⚠️ Ishchi guruh hali "
                            "ulanmagan."
                        )
                    }
                )


        # ----------------------------------------------------
        # MIJOZ FORMASI
        # ----------------------------------------------------

        else:

            session = get_session(
                chat_id
            )

            step = session.get(
                "step"
            )


            # ISM

            if step == "name":

                session["name"] = text

                await ask_phone(
                    chat_id
                )


            # TELEFON

            elif step == "phone":

                contact = message.get(
                    "contact"
                )

                if contact:

                    phone = contact.get(
                        "phone_number"
                    )

                else:

                    phone = text

                session["phone"] = phone

                await ask_address(
                    chat_id
                )


            # MANZIL

            elif step == "address":

                session["address"] = text

                await ask_tariff_or_skip(
                    chat_id
                )


    # ========================================================
    # INLINE TUGMALAR
    # ========================================================

    callback = update.get(
        "callback_query"
    )

    if callback:

        callback_id = callback["id"]

        chat_id = callback["message"]["chat"]["id"]

        data = callback.get(
            "data",
            ""
        )


        await telegram(
            "answerCallbackQuery",
            {
                "callback_query_id": callback_id
            }
        )


        # ----------------------------------------------------
        # ARIZA BOSHLASH
        # ----------------------------------------------------

        if data == "lead:start":

            await ask_name(
                chat_id
            )


        # ----------------------------------------------------
        # TARIFLAR
        # ----------------------------------------------------

        elif data == "tarif:list":

            await show_tariffs(
                chat_id
            )


        # ----------------------------------------------------
        # TARIF TANLASH
        # ----------------------------------------------------

        elif data.startswith("tarif:"):

            key = data.split(
                ":",
                1
            )[1]

            # Tarif tanlamasdan ariza

            if key == "none":

                session = get_session(
                    chat_id
                )

                session["tarif"] = None

                session["step"] = "confirm"

                await show_confirmation(
                    chat_id
                )

            # Aniq tarif

            elif key in TARIFLAR:

                await show_tariff_detail(
                    chat_id,
                    key
                )


        # ----------------------------------------------------
        # TARIFDAN ARIZA BOSHLASH
        # ----------------------------------------------------

        elif data.startswith("lead:tarif:"):

            key = data.split(
                ":",
                2
            )[2]

            if key in TARIFLAR:

                session = get_session(
                    chat_id
                )

                session["tarif"] = key

                await ask_name(
                    chat_id
                )


        # ----------------------------------------------------
        # ORTGA
        # ----------------------------------------------------

        elif data == "back:start":

            source = get_session(
                chat_id
            ).get(
                "source",
                "unknown"
            )

            await show_start(
                chat_id,
                source
            )


        # ----------------------------------------------------
        # QAYTADAN
        # ----------------------------------------------------

        elif data == "lead:restart":

            source = get_session(
                chat_id
            ).get(
                "source",
                "unknown"
            )

            session = get_session(
                chat_id
            )

            session.clear()

            session["source"] = source

            await ask_name(
                chat_id
            )


        # ----------------------------------------------------
        # ARIZANI YUBORISH
        # ----------------------------------------------------

        elif data == "lead:confirm":

            success = await send_lead_to_group(
                chat_id
            )

            if success:

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,

                        "text": (
                            "🎉 <b>Rahmat!</b>\n\n"

                            "Arizangiz muvaffaqiyatli "
                            "qabul qilindi. ✅\n\n"

                            "Tez orada mutaxassisimiz "
                            "siz bilan bog‘lanadi."
                        ),

                        "parse_mode": "HTML"
                    }
                )

            else:

                await telegram(
                    "sendMessage",
                    {
                        "chat_id": chat_id,

                        "text": (
                            "⚠️ Ariza tayyor.\n\n"

                            "Tizim hozircha ishchi "
                            "guruhga ulanmagan."
                        )
                    }
                )


    return {
        "ok": True
    }


# ============================================================
# SERVERNI ISHGA TUSHIRISH
# ============================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )
```
