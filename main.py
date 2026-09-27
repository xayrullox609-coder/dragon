import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
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
    VIP_PRICE_COINS,
    SERVICE_NAMES,
)

from database import (
    init_db,
    initialize_prices,
    add_user,
    get_user,
    get_balance,
    add_coins,
    remove_coins,
    save_star_purchase,
    payment_exists,
    create_order,
    get_order,
    get_user_orders,
    get_top_users,
    get_service_price,
    set_service_price,
    get_user_count,
    get_order_count,
    get_pending_order_count,
    get_total_coins,
    get_all_users,
    update_order_status,
    set_vip,
    is_vip,
    set_referrer,
    add_referral,
    add_admin_log,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
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
# STAR PAKETLARI
# ============================================================

STAR_PACKAGES = {
    1: 10,
    5: 50,
    10: 100,
    25: 250,
    50: 500,
    100: 1000,
}


# ============================================================
# XIZMATLAR
# ============================================================

SERVICES = {
    "subscribers": {
        "name": "👤 Obunachi",
        "unit": 1000,
        "price_default": 100,
    },

    "reactions": {
        "name": "❤️ Reaksiya",
        "unit": 1000,
        "price_default": 200,
    },

    "views": {
        "name": "👁 Ko‘rish",
        "unit": 1000,
        "price_default": 100,
    },
}


# ============================================================
# BUYURTMA HOLATLARI
# ============================================================

STATUS_NAMES = {
    "pending": "⏳ Kutilmoqda",
    "processing": "⚙️ Jarayonda",
    "completed": "✅ Bajarildi",
    "cancelled": "❌ Bekor qilindi",
}


# ============================================================
# FSM HOLATLARI
# ============================================================

class OrderState(StatesGroup):

    waiting_target = State()

    waiting_quantity = State()

    confirming = State()


class AdminState(StatesGroup):

    waiting_user_id = State()

    waiting_coins = State()

    waiting_price = State()

    waiting_order_id = State()

    waiting_status = State()

    waiting_broadcast = State()


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
# ORQAGA TUGMASI
# ============================================================

def back_button():

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
# ADMIN MENYU
# ============================================================

def admin_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📊 Statistika",
                    callback_data="admin_stats"
                )
            ],

            [
                InlineKeyboardButton(
                    text="👥 Foydalanuvchilar",
                    callback_data="admin_users"
                ),

                InlineKeyboardButton(
                    text="📦 Buyurtmalar",
                    callback_data="admin_orders"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="💰 Tanga berish",
                    callback_data="admin_add_coins"
                ),

                InlineKeyboardButton(
                    text="➖ Tanga olish",
                    callback_data="admin_remove_coins"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="💵 Narxlar",
                    callback_data="admin_prices"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⚙️ Buyurtma statusi",
                    callback_data="admin_status"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="📢 Reklama",
                    callback_data="admin_broadcast"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Asosiy menyu",
                    callback_data="back_main"
                )
            ],
        ]
    )


# ============================================================
# ADMIN TEKSHIRISH
# ============================================================

def is_admin(user_id: int) -> bool:

    return user_id in ADMIN_IDS


# ============================================================
# START
# ============================================================

@dp.message(CommandStart())
async def start_handler(
    message: Message,
    state: FSMContext
):

    await state.clear()

    user = message.from_user

    if not user:
        return

    add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name
    )

    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    command_args = None

    if message.text:

        parts = message.text.split(
            maxsplit=1
        )

        if len(parts) == 2:
            command_args = parts[1]

    if command_args:

        if command_args.startswith("ref_"):

            try:

                referrer_id = int(
                    command_args.replace(
                        "ref_",
                        "",
                        1
                    )
                )

                if referrer_id != user.id:

                    success = set_referrer(
                        telegram_id=user.id,
                        referrer_id=referrer_id
                    )

                    if success:

                        referral_saved = add_referral(
                            inviter_id=referrer_id,
                            invited_id=user.id,
                            bonus=REFERRAL_BONUS
                        )

                        if referral_saved:

                            add_coins(
                                telegram_id=referrer_id,
                                amount=REFERRAL_BONUS,
                                history_type="referral",
                                description="Referral bonusi"
                            )

                            try:

                                await bot.send_message(
                                    referrer_id,
                                    "🎉 <b>Yangi referral!</b>\n\n"
                                    f"👤 Sizning havolangiz orqali "
                                    f"yangi foydalanuvchi qo‘shildi.\n\n"
                                    f"🎁 Bonus: "
                                    f"<b>{REFERRAL_BONUS} 🪙</b>",
                                    parse_mode="HTML"
                                )

                            except Exception as e:

                                logger.warning(
                                    "Referral xabari yuborilmadi: %s",
                                    e
                                )

            except ValueError:

                pass

    # --------------------------------------------------------
    # START MATNI
    # --------------------------------------------------------

    text = (
        "🎉 <b>Nakrutka Bot</b>ga xush kelibsiz!\n\n"

        "Bu bot orqali xizmatlarga buyurtma "
        "berishingiz mumkin.\n\n"

        "👤 Obunachi\n"
        "❤️ Reaksiya\n"
        "👁 Ko‘rish\n\n"

        "💰 Avval balansingizni to‘ldiring, "
        "keyin kerakli xizmatni tanlang."
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
async def id_handler(
    message: Message
):

    if not message.from_user:
        return

    await message.answer(
        "🆔 <b>Sizning Telegram ID'ingiz:</b>\n\n"
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

    user_id = callback.from_user.id

    balance = get_balance(
        user_id
    )

    vip = is_vip(
        user_id
    )

    status = "👑 VIP" if vip else "👤 Oddiy"

    text = (
        "💰 <b>Balansingiz</b>\n\n"

        f"🪙 Tanga: <b>{balance:,}</b>\n"

        f"⭐ Kurs: <b>1 ⭐ = "
        f"{STARS_TO_COINS} 🪙</b>\n"

        f"👑 Status: <b>{status}</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⭐ Stars orqali to‘ldirish",
                    callback_data="stars"
                )
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ],
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
        "⭐ <b>Stars orqali tanga sotib olish</b>\n\n"

        f"💱 1 ⭐ = {STARS_TO_COINS} 🪙\n\n"

        "Kerakli paketni tanlang:"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="⭐ 1 → 🪙 10",
                    callback_data="buy_stars_1"
                ),

                InlineKeyboardButton(
                    text="⭐ 5 → 🪙 50",
                    callback_data="buy_stars_5"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 10 → 🪙 100",
                    callback_data="buy_stars_10"
                ),

                InlineKeyboardButton(
                    text="⭐ 25 → 🪙 250",
                    callback_data="buy_stars_25"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⭐ 50 → 🪙 500",
                    callback_data="buy_stars_50"
                ),

                InlineKeyboardButton(
                    text="⭐ 100 → 🪙 1000",
                    callback_data="buy_stars_100"
                ),
            ],

            [
                InlineKeyboardButton(
                    text="⬅️ Orqaga",
                    callback_data="back_main"
                )
            ],
        ]
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# STARS INVOICE
# ============================================================

@dp.callback_query(
    F.data.startswith("buy_stars_")
)
async def buy_stars_handler(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    try:

        stars = int(
            callback.data.replace(
                "buy_stars_",
                "",
                1
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
        f"coins_{user_id}_{stars}_{coins}"
    )

    prices = [
        LabeledPrice(
            label=f"{coins:,} 🪙 Tanga",
            amount=stars
        )
    ]

    try:

        await bot.send_invoice(
            chat_id=user_id,

            title=f"{coins:,} 🪙 Tanga",

            description=(
                f"{stars} Stars evaziga "
                f"{coins:,} tanga."
            ),

            payload=payload,

            currency="XTR",

            prices=prices
        )

        await callback.answer()

    except Exception as e:

        logger.exception(
            "Invoice xatosi"
        )

        await callback.answer(
            "❌ To‘lov oynasini ochib bo‘lmadi.",
            show_alert=True
        )


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
            error_message="❌ Noto‘g‘ri to‘lov."
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
            error_message="❌ To‘lov ma'lumotlari noto‘g‘ri."
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
            error_message="❌ Paket topilmadi."
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
# MUVAFFAQIYATLI STARS TO‘LOVI
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

    user_id = message.from_user.id

    payload = payment.invoice_payload

    try:

        parts = payload.split("_")

        payload_user_id = int(parts[1])
        stars = int(parts[2])
        coins = int(parts[3])

    except (
        ValueError,
        IndexError
    ):

        await message.answer(
            "❌ To‘lov ma'lumotlarida xatolik."
        )

        return

    if payload_user_id != user_id:

        return

    if stars not in STAR_PACKAGES:

        return

    if STAR_PACKAGES[stars] != coins:

        return

    charge_id = (
        payment.telegram_payment_charge_id
    )

    if payment_exists(
        charge_id
    ):

        await message.answer(
            "ℹ️ Bu to‘lov allaqachon hisoblangan."
        )

        return

    saved = save_star_purchase(
        telegram_id=user_id,
        stars=stars,
        coins=coins,
        telegram_payment_charge_id=charge_id,
        provider_payment_charge_id=(
            payment.provider_payment_charge_id
        )
    )

    if not saved:

        await message.answer(
            "ℹ️ Bu to‘lov allaqachon qayd etilgan."
        )

        return

    add_coins(
        telegram_id=user_id,
        amount=coins,
        history_type="stars",
        description=f"{stars} Stars xaridi"
    )

    new_balance = get_balance(
        user_id
    )

    await message.answer(
        "✅ <b>To‘lov muvaffaqiyatli!</b>\n\n"

        f"⭐ To‘langan: <b>{stars} Stars</b>\n"

        f"🪙 Qo‘shildi: <b>{coins:,} tanga</b>\n\n"

        f"💰 Yangi balans: "
        f"<b>{new_balance:,} 🪙</b>",

        reply_markup=main_menu(),

        parse_mode="HTML"
    )

    logger.info(
        "Stars payment: user=%s stars=%s coins=%s",
        user_id,
        stars,
        coins
    )


# ============================================================
# ORQAGA
# ============================================================

@dp.callback_query(
    F.data == "back_main"
)
async def back_main_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "🏠 <b>Asosiy menyu</b>\n\n"
        "Kerakli xizmatni tanlang:",

        reply_markup=main_menu(),

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
    callback: CallbackQuery,
    state: FSMContext
):

    service = callback.data.replace(
        "service_",
        "",
        1
    )

    if service not in SERVICES:

        await callback.answer(
            "❌ Xizmat topilmadi.",
            show_alert=True
        )

        return

    service_info = SERVICES[service]

    price = get_service_price(
        service,
        service_info["price_default"]
    )

    await state.clear()

    await state.update_data(
        service=service
    )

    await state.set_state(
        OrderState.waiting_target
    )

    text = (
        f"{service_info['name']} <b>buyurtmasi</b>\n\n"

        f"💰 Narx: <b>{price} 🪙</b> / "
        f"{service_info['unit']} dona\n\n"

        "🔗 <b>Havolani yuboring:</b>\n\n"

        "Masalan:\n"
        "<code>https://t.me/example</code>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_order"
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
# HAVOLA QABUL QILISH
# ============================================================

@dp.message(
    OrderState.waiting_target
)
async def order_target_handler(
    message: Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❌ Iltimos, havolani matn ko‘rinishida yuboring."
        )

        return

    target = message.text.strip()

    # Juda uzun yoki bo'sh havolalarni qabul qilmaslik
    if len(target) < 5:

        await message.answer(
            "❌ Havola juda qisqa.\n\n"
            "Iltimos, to‘liq havolani yuboring."
        )

        return

    if len(target) > 500:

        await message.answer(
            "❌ Havola juda uzun."
        )

        return

    await state.update_data(
        target=target
    )

    data = await state.get_data()

    service = data.get(
        "service"
    )

    if service not in SERVICES:

        await state.clear()

        await message.answer(
            "❌ Xizmat topilmadi.",
            reply_markup=main_menu()
        )

        return

    service_info = SERVICES[service]

    await state.set_state(
        OrderState.waiting_quantity
    )

    text = (
        f"{service_info['name']}\n\n"

        f"🔗 Havola:\n"
        f"<code>{target}</code>\n\n"

        "🔢 <b>Nechta kerak?</b>\n\n"

        f"Masalan: <code>100</code>\n\n"

        f"📌 Minimal miqdor: <b>10</b>\n"
        f"📌 Maksimal miqdor: <b>100000</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_order"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================================
# MIQDOR QABUL QILISH
# ============================================================

@dp.message(
    OrderState.waiting_quantity
)
async def order_quantity_handler(
    message: Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❌ Miqdorni raqam bilan yuboring."
        )

        return

    raw_quantity = message.text.strip()

    # Faqat raqam
    if not raw_quantity.isdigit():

        await message.answer(
            "❌ Miqdor faqat raqam bo‘lishi kerak.\n\n"
            "Masalan: <code>100</code>",
            parse_mode="HTML"
        )

        return

    quantity = int(
        raw_quantity
    )

    # Minimal miqdor
    if quantity < 10:

        await message.answer(
            "❌ Minimal miqdor: <b>10</b>.",
            parse_mode="HTML"
        )

        return

    # Maksimal miqdor
    if quantity > 100000:

        await message.answer(
            "❌ Maksimal miqdor: <b>100000</b>.",
            parse_mode="HTML"
        )

        return

    data = await state.get_data()

    service = data.get(
        "service"
    )

    target = data.get(
        "target"
    )

    if not service or not target:

        await state.clear()

        await message.answer(
            "❌ Buyurtma ma'lumotlari topilmadi.",
            reply_markup=main_menu()
        )

        return

    if service not in SERVICES:

        await state.clear()

        await message.answer(
            "❌ Xizmat topilmadi.",
            reply_markup=main_menu()
        )

        return

    service_info = SERVICES[service]

    # --------------------------------------------------------
    # NARX HISOBLASH
    # --------------------------------------------------------

    price_per_unit = get_service_price(
        service,
        service_info["price_default"]
    )

    unit = service_info["unit"]

    # Masalan:
    # 1000 dona = 100 tanga
    # 500 dona = 50 tanga

    total_price = (
        quantity * price_per_unit
    ) / unit

    # Kasr chiqsa yuqoriga yaxlitlash
    total_price = int(
        total_price
    )

    if total_price < 1:
        total_price = 1

    await state.update_data(
        quantity=quantity,
        price=total_price
    )

    await state.set_state(
        OrderState.confirming
    )

    balance = get_balance(
        message.from_user.id
    )

    enough = (
        balance >= total_price
    )

    if enough:

        balance_text = (
            f"✅ Balansingiz yetarli.\n"
            f"💰 Balans: <b>{balance:,} 🪙</b>"
        )

        confirm_button = InlineKeyboardButton(
            text="✅ Buyurtmani tasdiqlash",
            callback_data="confirm_order"
        )

    else:

        need = (
            total_price - balance
        )

        balance_text = (
            f"❌ Balansingiz yetarli emas.\n"
            f"💰 Balans: <b>{balance:,} 🪙</b>\n"
            f"➕ Yetishmaydi: <b>{need:,} 🪙</b>"
        )

        confirm_button = InlineKeyboardButton(
            text="⭐ Balansni to‘ldirish",
            callback_data="stars"
        )

    text = (
        "📦 <b>Buyurtmani tekshiring</b>\n\n"

        f"🛠 Xizmat: <b>{service_info['name']}</b>\n\n"

        f"🔗 Havola:\n"
        f"<code>{target}</code>\n\n"

        f"🔢 Miqdor: <b>{quantity:,}</b>\n"

        f"💵 Narx: <b>{total_price:,} 🪙</b>\n\n"

        f"{balance_text}\n\n"

        "Buyurtmani tasdiqlaysizmi?"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                confirm_button
            ],

            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="cancel_order"
                )
            ]
        ]
    )

    await message.answer(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# ============================================================
# BUYURTMANI TASDIQLASH
# ============================================================

@dp.callback_query(
    F.data == "confirm_order"
)
async def confirm_order_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    user_id = callback.from_user.id

    data = await state.get_data()

    service = data.get(
        "service"
    )

    target = data.get(
        "target"
    )

    quantity = data.get(
        "quantity"
    )

    price = data.get(
        "price"
    )

    # Ma'lumotlar tekshiriladi
    if not all([
        service,
        target,
        quantity,
        price is not None
    ]):

        await state.clear()

        await callback.message.edit_text(
            "❌ Buyurtma ma'lumotlari "
            "topilmadi.",
            reply_markup=main_menu()
        )

        await callback.answer()

        return

    # Xizmat tekshiriladi
    if service not in SERVICES:

        await state.clear()

        await callback.message.edit_text(
            "❌ Xizmat mavjud emas.",
            reply_markup=main_menu()
        )

        await callback.answer()

        return

    # Narx qayta hisoblanadi
    # Foydalanuvchi FSM ma'lumotini o'zgartirib
    # noto'g'ri narx yubora olmasligi uchun.

    service_info = SERVICES[service]

    current_price = get_service_price(
        service,
        service_info["price_default"]
    )

    real_price = int(
        (quantity * current_price)
        / service_info["unit"]
    )

    if real_price < 1:
        real_price = 1

    price = real_price

    # Balansni qayta tekshirish
    balance = get_balance(
        user_id
    )

    if balance < price:

        await callback.answer(
            "❌ Balansingiz yetarli emas.",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # TANGANI YECHISH
    # --------------------------------------------------------

    removed = remove_coins(
        telegram_id=user_id,
        amount=price,
        history_type="order",
        description=(
            f"{SERVICES[service]['name']} "
            f"buyurtmasi"
        )
    )

    if not removed:

        await callback.answer(
            "❌ Balansdan tanga yechilmadi.",
            show_alert=True
        )

        return

    # --------------------------------------------------------
    # BUYURTMA YARATISH
    # --------------------------------------------------------

    order_id = create_order(
        telegram_id=user_id,
        service=service,
        target=target,
        quantity=quantity,
        price=price
    )

    if not order_id:

        # Agar buyurtma yaratilmasa,
        # tangani qaytaramiz.

        add_coins(
            telegram_id=user_id,
            amount=price,
            history_type="refund",
            description="Buyurtma yaratilmadi — qaytarildi"
        )

        await state.clear()

        await callback.message.edit_text(
            "❌ Buyurtma yaratishda xatolik.\n\n"
            "🪙 Tangalaringiz qaytarildi.",
            reply_markup=main_menu()
        )

        await callback.answer()

        return

    # --------------------------------------------------------
    # FSM TOZALASH
    # --------------------------------------------------------

    await state.clear()

    new_balance = get_balance(
        user_id
    )

    service_name = SERVICES[service]["name"]

    # --------------------------------------------------------
    # FOYDALANUVCHIGA NATIJA
    # --------------------------------------------------------

    text = (
        "✅ <b>Buyurtma qabul qilindi!</b>\n\n"

        f"🆔 Buyurtma: <code>#{order_id}</code>\n"

        f"🛠 Xizmat: <b>{service_name}</b>\n"

        f"🔢 Miqdor: <b>{quantity:,}</b>\n"

        f"💰 To‘lov: <b>{price:,} 🪙</b>\n\n"

        "📊 Status: <b>⏳ Kutilmoqda</b>\n\n"

        f"💰 Qolgan balans: "
        f"<b>{new_balance:,} 🪙</b>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📦 Buyurtmalarim",
                    callback_data="my_orders"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🏠 Asosiy menyu",
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

    await callback.answer(
        "✅ Buyurtma yaratildi!"
    )


# ============================================================
# BUYURTMANI BEKOR QILISH
# ============================================================

@dp.callback_query(
    F.data == "cancel_order"
)
async def cancel_order_handler(
    callback: CallbackQuery,
    state: FSMContext
):

    await state.clear()

    await callback.message.edit_text(
        "❌ <b>Buyurtma bekor qilindi.</b>\n\n"
        "Asosiy menyudan kerakli bo‘limni tanlang.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer(
        "Buyurtma bekor qilindi."
    )


# ============================================================
# BUYURTMALARIM
# ============================================================

@dp.callback_query(
    F.data == "my_orders"
)
async def my_orders_handler(
    callback: CallbackQuery
):

    user_id = callback.from_user.id

    orders = get_user_orders(
        telegram_id=user_id,
        limit=10
    )

    if not orders:

        text = (
            "📦 <b>Buyurtmalarim</b>\n\n"
            "Hozircha buyurtmalaringiz yo‘q."
        )

        await callback.message.edit_text(
            text,
            reply_markup=back_button(),
            parse_mode="HTML"
        )

        await callback.answer()

        return

    lines = [
        "📦 <b>So‘nggi buyurtmalaringiz</b>\n"
    ]

    for order in orders:

        service = SERVICES.get(
            order["service"],
            {}
        )

        service_name = service.get(
            "name",
            order["service"]
        )

        status = STATUS_NAMES.get(
            order["status"],
            order["status"]
        )

        lines.append(
            f"🆔 <code>#{order['id']}</code>\n"
            f"🛠 {service_name}\n"
            f"🔢 {order['quantity']:,}\n"
            f"💰 {order['price']:,} 🪙\n"
            f"📊 {status}\n"
            f"━━━━━━━━━━━━"
        )

    text = "\n".join(
        lines
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# ============================================================
# BUYURTMA TAFSILOTI
# ============================================================

@dp.callback_query(
    F.data.startswith("order_")
)
async def order_details_handler(
    callback: CallbackQuery
):

    try:

        order_id = int(
            callback.data.replace(
                "order_",
                "",
                1
            )
        )

    except ValueError:

        await callback.answer(
            "❌ Buyurtma ID xato.",
            show_alert=True
        )

        return

    order = get_order(
        order_id
    )

    if not order:

        await callback.answer(
            "❌ Buyurtma topilmadi.",
            show_alert=True
        )

        return

    if order["telegram_id"] != callback.from_user.id:

        await callback.answer(
            "❌ Bu buyurtma sizniki emas.",
            show_alert=True
        )

        return

    service = SERVICES.get(
        order["service"],
        {}
    )

    service_name = service.get(
        "name",
        order["service"]
    )

    status = STATUS_NAMES.get(
        order["status"],
        order["status"]
    )

    text = (
        "📦 <b>Buyurtma tafsilotlari</b>\n\n"

        f"🆔 ID: <code>#{order['id']}</code>\n"

        f"🛠 Xizmat: <b>{service_name}</b>\n"

        f"🔗 Havola:\n"
        f"<code>{order['target']}</code>\n\n"

        f"🔢 Miqdor: <b>{order['quantity']:,}</b>\n"

        f"💰 Narx: <b>{order['price']:,} 🪙</b>\n"

        f"📊 Status: <b>{status}</b>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()