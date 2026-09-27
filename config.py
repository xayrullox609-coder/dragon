import os

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# BOT SOZLAMALARI
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi. .env fayliga BOT_TOKEN=... yozing."
    )


# ============================================================
# ADMINLAR
# ============================================================

def get_admin_ids():
    raw = os.getenv("ADMIN_IDS", "").strip()

    if not raw:
        return []

    result = []

    for item in raw.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            result.append(int(item))
        except ValueError:
            pass

    return result


ADMIN_IDS = get_admin_ids()


# ============================================================
# WEB SERVER
# ============================================================

WEB_HOST = os.getenv(
    "WEB_HOST",
    "0.0.0.0"
)

WEB_PORT = int(
    os.getenv(
        "PORT",
        "8080"
    )
)


# ============================================================
# BAZA
# ============================================================

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "nakrutka.db"
)


# ============================================================
# VALYUTA
# ============================================================

# 1 Telegram Star = 10 tanga
STARS_TO_COINS = 10


# ============================================================
# BOSHLANG'ICH BALANS
# ============================================================

START_COINS = 0


# ============================================================
# REFERRAL
# ============================================================

REFERRAL_BONUS = 10


# ============================================================
# VIP
# ============================================================

VIP_PRICE_COINS = 1000


# ============================================================
# XIZMATLAR
# ============================================================

SERVICE_SUBSCRIBERS = "subscribers"
SERVICE_REACTIONS = "reactions"
SERVICE_VIEWS = "views"


# ============================================================
# XIZMAT NOMLARI
# ============================================================

SERVICE_NAMES = {
    SERVICE_SUBSCRIBERS: "👤 Obunachi",
    SERVICE_REACTIONS: "❤️ Reaksiya",
    SERVICE_VIEWS: "👁 Ko‘rish",
}


# ============================================================
# DEFAULT NARXLAR
# ============================================================

# Keyinchalik admin panel orqali o'zgartirish mumkin.
DEFAULT_SERVICE_PRICES = {
    SERVICE_SUBSCRIBERS: 1,
    SERVICE_REACTIONS: 2,
    SERVICE_VIEWS: 1,
}


# ============================================================
# BUYURTMA HOLATLARI
# ============================================================

ORDER_PENDING = "pending"
ORDER_PROCESSING = "processing"
ORDER_COMPLETED = "completed"
ORDER_CANCELLED = "cancelled"


# ============================================================
# LOG SOZLAMALARI
# ============================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)