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
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = FastAPI(title="Turon Olmaliq Lead Bot")


# ============================================================
# TARIFLAR
# ============================================================
# Keyinchalik tarif narxini o'zgartirish uchun faqat shu
# bo'limni o'zgartirish kifoya.
#
# Masalan:
# "sodiq" -> tarifning ichki kodi
# "Sodiq" -> mijoz ko'radigan nom
# "175 000 so‘m/oy" -> narxi
# "..." -> qisqa izoh
# ============================================================

TARIFLAR = {

    "sodiq": {
        "nomi": "Sodiq",
        "narxi": "175 000 so‘m/oy",
        "izoh": "Internet + G3 Wi-Fi router + o‘rnatish bepul",
    },

    # Keyinchalik boshqa tariflarni shu yerga qo‘shamiz.
    #
    # "turbo": {
    #     "nomi": "Turbo",
    #     "narxi": "250 000 so‘m/oy",
    #     "izoh": "Yuqori tezlikdagi internet",
    # },

}


# ============================================================
# QR MANBALARI
# ============================================================
# QR kodlar uchun ko'cha + uy.
#
# QR ichida:
# ehtirom-10
#
# Guruhga esa:
# Ehtirom ko‘chasi, 10-uy
#
# Mijoz bu texnik kodni ko'rmaydi.
# ============================================================

QR_MANBALARI = {

    "ehtirom-10": "Ehtirom ko‘chasi, 10-uy",

    # Keyinchalik shu tarzda qo'shamiz:
    #
    # "ehtirom-12": "Ehtirom ko‘chasi, 12-uy",
    # "a-qahhor-7": "A. Qahhor ko‘chasi, 7-uy",
    # "amir-temur-25": "Amir Temur ko‘chasi, 25-uy",

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
# BOSHLANG'ICH MENYU
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
# TARIFLARNI KO'RSATISH
# ============================================================

async def show_tariffs(chat_id: int):

    text = "📶 <b>Tarifni tanlang:</b>\n\n"

    for tarif in TARIFLAR.values():

        text += (
            f"🔹 <b>{html.escape(tarif['nomi'])}</b>\n"
            f"💰 {html.escape(tarif['narxi'])}\n"
            f"ℹ️ {html.escape(tarif['izoh'])}\n\n"
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
# ISMNI SO'RASH
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
# TELEFONNI SO'RASH
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
# MANZILNI SO'RASH
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
# ARIZANI TASDIQLASH
# ============================================================

async def show_confirmation(chat_id: int):

    session = get_session(chat_id)

    tarif = TARIFLAR[session["tarif"]]

    text = (

        "📋 <b>Arizangizni tekshiring</b>\n\n"

        f"👤 Ism: <b>{html.escape(session['name'])}</b>\n"

        f"📱 Telefon: "
        f"<b>{html.escape(session['phone'])}</b>\n"

        f"📍 Manzil: "
        f"<b>{html.escape(session['address'])}</b>\n"

        f"📶 Tarif: "
        f"<b>{html.escape(tarif['nomi'])}</b>\n"

        f"💰 Narxi: "
        f"<b>{html.escape(tarif['narxi'])}</b>\n\n"

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

    tarif = TARIFLAR[session["tarif"]]

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
        f"<b>{html.escape(tarif['nomi'])}</b>\n"

        f"💰 Narxi: "
        f"<b>{html.escape(tarif['narxi'])}</b>\n\n"

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

                session["step"] = "tarif"

                await show_tariffs(
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

        elif data.startswith(
            "tarif:"
        ):

            key = data.split(
                ":",
                1
            )[1]

            if key in TARIFLAR:

                session = get_session(
                    chat_id
                )

                session["tarif"] = key

                session["step"] = "confirm"

                await show_confirmation(
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
