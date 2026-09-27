import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
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
# ASOSIY MENYU
# ============================================================

def main_menu():

    keyboard = InlineKeyboardMarkup(
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

    return keyboard


# ============================================================
# ORQAGA TUGMASI
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
async def start_handler(message: Message):

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
        "💰 Balansingizni to‘ldirib, kerakli xizmatni "
        "tanlang."
    )

    await message.answer(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# ============================================================
# /ID
# ============================================================

@dp.message(Command("id"))
async def id_handler(message: Message):

    if not message.from_user:
        return

    await message.answer(
        f"🆔 Sizning Telegram ID'ingiz:\n\n"
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
        "📌 Bu xizmat uchun buyurtma berish "
        "bo‘limi keyingi bosqichda ulanadi.\n\n"
        "Hozircha xizmat tanlandi."
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
# BUYURTMA HOZIRCHA
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
        "Buyurtma berish tizimi keyingi bosqichda "
        "to‘liq ulanadi.\n\n"
        "Unda:\n"
        "🔗 Havola yuborish\n"
        "🔢 Miqdor tanlash\n"
        "💰 Narx hisoblash\n"
        "✅ Buyurtmani tasdiqlash\n"
        "📊 Buyurtma holatini ko‘rish\n\n"
        "hammasi ishlaydi."
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
            "🏆 <b>Reyting</b>\n\n"
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

    username = me.username

    link = (
        f"https://t.me/{username}"
        f"?start=ref_{user.id}"
    )

    db_user = get_user(
        user.id
    )

    count = 0

    if db_user:
        count = db_user["referral_count"] or 0

    text = (
        "👥 <b>Do‘stlarni taklif qilish</b>\n\n"
        f"🎁 Har bir taklif uchun: "
        f"<b>{REFERRAL_BONUS} 🪙</b>\n\n"
        f"👥 Taklif qilganlaringiz: <b>{count}</b>\n\n"
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
        "VIP tizimi keyingi bosqichda ulanadi.\n\n"
        "VIP orqali maxsus imkoniyatlar "
        "berishimiz mumkin."
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# BUYURTMALARIM
# ============================================================

@dp.callback_query(F.data == "my_orders")
async def my_orders_handler(
    callback: CallbackQuery
):

    text = (
        "📦 <b>Buyurtmalarim</b>\n\n"
        "Sizning buyurtmalaringiz keyingi "
        "bosqichda shu yerda ko‘rsatiladi."
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

    text = (
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Kerakli xizmatni tanlang:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# ADMIN TEKSHIRISH
# ============================================================

def is_admin(
    telegram_id: int
) -> bool:

    return telegram_id in ADMIN_IDS


# ============================================================
# /ADMIN
# ============================================================

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

    text = (
        "🛠 <b>ADMIN PANEL</b>\n\n"
        "Admin panel funksiyalari keyingi "
        "bosqichlarda ulanadi."
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )


# ============================================================
# UNKNOWN COMMAND
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
# STARTUP
# ============================================================

async def main():

    logger.info(
        "Database ishga tushirilmoqda..."
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