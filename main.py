import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    LabeledPrice,
    PreCheckoutQuery,
)

from config import (
    BOT_TOKEN,
    ADMIN_IDS,
    STARS_TO_COINS,
    REFERRAL_BONUS,
    SERVICE_NAMES,
)

from database import (
    init_db,
    initialize_prices,
    add_user,
    get_user,
    get_balance,
    add_coins,
    save_star_purchase,
    get_top_users,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# BOT
# ============================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# ============================================================
# STARS PAKETLARI
# ============================================================

STAR_PACKAGES = {
    1: 10,
    10: 100,
    50: 500,
    100: 1000,
}


# ============================================================
# ASOSIY MENYU
# ============================================================

def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👤 Obunachi",
                    callback_data="service_subscribers"
                ),
                InlineKeyboardButton(
                    text="❤️ Reaksiya",
                    callback_data="service_reactions"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👁 Ko‘rish",
                    callback_data="service_views"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰 Balans",
                    callback_data="balance"
                ),
                InlineKeyboardButton(
                    text="⭐ Stars",
                    callback_data="stars"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📦 Buyurtmalarim",
                    callback_data="my_orders"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏆 Reyting",
                    callback_data="rating"
                ),
                InlineKeyboardButton(
                    text="👥 Taklif qilish",
                    callback_data="referral"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👑 VIP",
                    callback_data="vip"
                ),
            ],
        ]
    )


# ============================================================
# ORQAGA
# ============================================================

def back_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ]
        ]
    )


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start_handler(
    message: Message
):

    user = message.from_user

    if not user:
        return

    add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    text = (
        "🎉 <b>Nakrutka Bot</b>ga xush kelibsiz!\n\n"
        "Bu yerda Telegram xizmatlariga buyurtma "
        "berishingiz mumkin.\n\n"
        "👤 Obunachi\n"
        "❤️ Reaksiya\n"
        "👁 Ko‘rish\n\n"
        "💰 Balansingizni to‘ldiring va kerakli "
        "xizmatni tanlang."
    )

    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# ============================================================
# ID
# ============================================================

@dp.message(Command("id"))
async def id_handler(
    message: Message
):

    if not message.from_user:
        return

    await message.answer(
        "🆔 Sizning Telegram ID'ingiz:\n\n"
        f"<code>{message.from_user.id}</code>",
        parse_mode="HTML"
    )


# ============================================================
# BALANS
# ============================================================

@dp.callback_query(F.data == "balance")
async def balance_handler(
    callback: CallbackQuery
):

    user = callback.from_user

    balance = get_balance(
        user.id
    )

    db_user = get_user(
        user.id
    )

    vip_status = "👑 VIP" if (
        db_user and db_user["is_vip"]
    ) else "👤 Oddiy"

    text = (
        "💰 <b>Sizning balansingiz</b>\n\n"
        f"🪙 Tanga: <b>{balance:,}</b>\n"
        f"⭐ Kurs: <b>1 ⭐ = {STARS_TO_COINS} 🪙</b>\n"
        f"👑 Status: <b>{vip_status}</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Tanga sotib olish",
                    callback_data="stars"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# STARS MENYUSI
# ============================================================

@dp.callback_query(F.data == "stars")
async def stars_handler(
    callback: CallbackQuery
):

    text = (
        "⭐ <b>Stars orqali tanga olish</b>\n\n"
        f"1 ⭐ = {STARS_TO_COINS} 🪙\n\n"
        "Kerakli paketni tanlang:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ 1 Stars → 10 🪙",
                    callback_data="buy_stars_1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 10 Stars → 100 🪙",
                    callback_data="buy_stars_10"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 50 Stars → 500 🪙",
                    callback_data="buy_stars_50"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ 100 Stars → 1000 🪙",
                    callback_data="buy_stars_100"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# STARS INVOICE YUBORISH
# ============================================================

@dp.callback_query(
    F.data.startswith("buy_stars_")
)
async def buy_stars_handler(
    callback: CallbackQuery
):

    user = callback.from_user

    try:
        stars = int(
            callback.data.replace(
                "buy_stars_",
                ""
            )
        )

    except ValueError:

        await callback.answer(
            "❌ Paket xatosi.",
            show_alert=True
        )

        return

    if stars not in STAR_PACKAGES:

        await callback.answer(
            "❌ Bunday paket mavjud emas.",
            show_alert=True
        )

        return

    coins = STAR_PACKAGES[stars]

    payload = (
        f"coins_{user.id}_{stars}_{coins}"
    )

    prices = [
        LabeledPrice(
            label=f"{coins:,} 🪙 Tanga",
            amount=stars
        )
    ]

    await bot.send_invoice(
        chat_id=user.id,
        title=f"{coins:,} 🪙 Tanga",
        description=(
            f"{stars} Telegram Stars evaziga "
            f"{coins:,} tanga olasiz."
        ),
        payload=payload,
        currency="XTR",
        prices=prices
    )

    await callback.answer()


# ============================================================
# PRE-CHECKOUT
# ============================================================

@dp.pre_checkout_query()
async def pre_checkout_handler(
    query: PreCheckoutQuery
):

    payload = query.invoice_payload

    if not payload.startswith("coins_"):

        await query.answer(
            ok=False,
            error_message="❌ To‘lov ma'lumotlari noto‘g‘ri."
        )

        return

    try:
        parts = payload.split("_")

        user_id = int(parts[1])
        stars = int(parts[2])
        coins = int(parts[3])

    except (
        ValueError,
        IndexError
    ):

        await query.answer(
            ok=False,
            error_message="❌ To‘lov ma'lumotlari buzilgan."
        )

        return

    if user_id != query.from_user.id:

        await query.answer(
            ok=False,
            error_message="❌ Bu to‘lov sizga tegishli emas."
        )

        return

    if stars not in STAR_PACKAGES:

        await query.answer(
            ok=False,
            error_message="❌ Stars paketi topilmadi."
        )

        return

    if STAR_PACKAGES[stars] != coins:

        await query.answer(
            ok=False,
            error_message="❌ Tanga miqdori noto‘g‘ri."
        )

        return

    await query.answer(
        ok=True
    )


# ============================================================
# MUVAFFAQIYATLI TO‘LOV
# ============================================================

@dp.message(
    F.successful_payment
)
async def successful_payment_handler(
    message: Message
):

    payment = message.successful_payment

    if not payment:
        return

    payload = payment.invoice_payload

    try:
        parts = payload.split("_")

        user_id = int(parts[1])
        stars = int(parts[2])
        coins = int(parts[3])

    except (
        ValueError,
        IndexError
    ):

        logger.error(
            "Noto‘g‘ri payment payload: %s",
            payload
        )

        await message.answer(
            "❌ To‘lov ma'lumotlarida xatolik yuz berdi."
        )

        return

    if user_id != message.from_user.id:

        logger.warning(
            "Payment user ID mos kelmadi."
        )

        return

    if stars not in STAR_PACKAGES:

        logger.warning(
            "Noma'lum Stars paketi: %s",
            stars
        )

        return

    if STAR_PACKAGES[stars] != coins:

        logger.warning(
            "Stars/coins mos kelmadi."
        )

        return

    # --------------------------------------------------------
    # TANGANI BALANSGA QO‘SHISH
    # --------------------------------------------------------

    add_coins(
        telegram_id=user_id,
        amount=coins
    )

    # --------------------------------------------------------
    # TO‘LOVNI BAZAGA SAQLASH
    # --------------------------------------------------------

    save_star_purchase(
        telegram_id=user_id,
        stars=stars,
        coins=coins,
        telegram_payment_charge_id=(
            payment.telegram_payment_charge_id
        ),
        provider_payment_charge_id=(
            payment.provider_payment_charge_id
        )
    )

    new_balance = get_balance(
        user_id
    )

    await message.answer(
        "✅ <b>To‘lov muvaffaqiyatli!</b>\n\n"
        f"⭐ To‘langan: <b>{stars} Stars</b>\n"
        f"🪙 Qo‘shildi: <b>{coins:,} tanga</b>\n\n"
        f"💰 Yangi balans: <b>{new_balance:,} tanga</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    logger.info(
        "Payment: user=%s stars=%s coins=%s",
        user_id,
        stars,
        coins
    )


# ============================================================
# XIZMAT TANLASH
# ============================================================

@dp.callback_query(
    F.data.startswith("service_")
)
async def service_handler(
    callback: CallbackQuery
):

    service = callback.data.replace(
        "service_",
        "",
        1
    )

    service_name = SERVICE_NAMES.get(
        service,
        "Xizmat"
    )

    text = (
        f"<b>{service_name}</b>\n\n"
        "📌 Xizmat tanlandi.\n\n"
        "Buyurtma berish uchun tugmani bosing."
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📦 Buyurtma berish",
                    callback_data=f"order_{service}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# BUYURTMA
# ============================================================

@dp.callback_query(
    F.data.startswith("order_")
)
async def order_handler(
    callback: CallbackQuery
):

    service = callback.data.replace(
        "order_",
        "",
        1
    )

    service_name = SERVICE_NAMES.get(
        service,
        "Xizmat"
    )

    text = (
        f"📦 <b>{service_name}</b>\n\n"
        "Buyurtma berish tizimi keyingi "
        "bosqichda ulanadi.\n\n"
        "🔗 Havola\n"
        "🔢 Miqdor\n"
        "💰 Narx\n"
        "✅ Tasdiqlash\n"
        "📊 Status"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# REYTING
# ============================================================

@dp.callback_query(F.data == "rating")
async def rating_handler(
    callback: CallbackQuery
):

    users = get_top_users(
        limit=10
    )

    if not users:

        text = (
            "🏆 <b>TOP 10</b>\n\n"
            "Hozircha reyting bo‘sh."
        )

    else:

        lines = [
            "🏆 <b>TOP 10 foydalanuvchi</b>\n"
        ]

        for index, user in enumerate(
            users,
            start=1
        ):

            name = user["first_name"]

            if not name:
                name = "Foydalanuvchi"

            coins = user["coins"] or 0

            lines.append(
                f"{index}. {name} — "
                f"<b>{coins:,} 🪙</b>"
            )

        text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# REFERRAL
# ============================================================

@dp.callback_query(F.data == "referral")
async def referral_handler(
    callback: CallbackQuery
):

    user = callback.from_user

    me = await bot.get_me()

    if not me.username:

        await callback.answer(
            "❌ Bot username topilmadi.",
            show_alert=True
        )

        return

    link = (
        f"https://t.me/{me.username}"
        f"?start=ref_{user.id}"
    )

    db_user = get_user(
        user.id
    )

    count = 0

    if db_user:
        count = (
            db_user["referral_count"] or 0
        )

    text = (
        "👥 <b>Do‘stlarni taklif qilish</b>\n\n"
        f"🎁 Bonus: <b>{REFERRAL_BONUS} 🪙</b>\n"
        f"👥 Takliflar: <b>{count}</b>\n\n"
        "🔗 Sizning havolangiz:\n"
        f"<code>{link}</code>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# VIP
# ============================================================

@dp.callback_query(F.data == "vip")
async def vip_handler(
    callback: CallbackQuery
):

    text = (
        "👑 <b>VIP</b>\n\n"
        "VIP tizimi keyingi bosqichda ulanadi."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# BUYURTMALAR
# ============================================================

@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(
    callback: CallbackQuery
):

    text = (
        "📦 <b>Buyurtmalarim</b>\n\n"
        "Buyurtmalar ro‘yxati keyingi "
        "bosqichda ulanadi."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ORQAGA
# ============================================================

@dp.callback_query(F.data == "back_main")
async def back_main_handler(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Kerakli xizmatni tanlang:",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ADMIN
# ============================================================

def is_admin(
    telegram_id: int
) -> bool:

    return telegram_id in ADMIN_IDS


@dp.message(Command("admin"))
async def admin_handler(
    message: Message
):

    if not message.from_user:
        return

    if not is_admin(
        message.from_user.id
    ):

        await message.answer(
            "❌ Siz admin emassiz."
        )

        return

    await message.answer(
        "🛠 <b>ADMIN PANEL</b>\n\n"
        "Admin funksiyalari keyingi "
        "bosqichlarda ulanadi.",
        parse_mode="HTML"
    )


# ============================================================
# UNKNOWN
# ============================================================

@dp.message()
async def unknown_message(
    message: Message
):

    await message.answer(
        "👇 Menyudan kerakli bo‘limni tanlang.",
        reply_markup=main_menu()
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    logger.info(
        "Database ishga tushmoqda..."
    )

    init_db()

    initialize_prices()

    logger.info(
        "Database tayyor."
    )

    logger.info(
        "Bot ishga tushmoqda..."
    )

    await dp.start_polling(
        bot
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot to‘xtatildi."
        )