import sqlite3
from datetime import datetime
from typing import Optional


# ============================================================
# DATABASE
# ============================================================

DB_NAME = "nakrutka.db"


def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def now():
    return datetime.utcnow().isoformat()


# ============================================================
# INIT DATABASE
# ============================================================

def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER UNIQUE NOT NULL,

            username TEXT,

            first_name TEXT,

            coins INTEGER DEFAULT 0,

            is_vip INTEGER DEFAULT 0,

            referred_by INTEGER DEFAULT NULL,

            referral_count INTEGER DEFAULT 0,

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # REFERRALS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            inviter_id INTEGER NOT NULL,

            invited_id INTEGER UNIQUE NOT NULL,

            bonus INTEGER DEFAULT 0,

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # STAR PURCHASES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS star_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER NOT NULL,

            stars INTEGER NOT NULL,

            coins INTEGER NOT NULL,

            telegram_payment_charge_id TEXT UNIQUE,

            provider_payment_charge_id TEXT,

            status TEXT DEFAULT 'completed',

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # ORDERS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER NOT NULL,

            service TEXT NOT NULL,

            target TEXT NOT NULL,

            quantity INTEGER NOT NULL,

            price INTEGER NOT NULL,

            status TEXT DEFAULT 'pending',

            external_order_id TEXT DEFAULT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # SERVICE PRICES
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_prices (
            service TEXT PRIMARY KEY,

            price INTEGER NOT NULL
        )
    """)

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,

            value TEXT
        )
    """)

    # --------------------------------------------------------
    # BALANCE HISTORY
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER NOT NULL,

            amount INTEGER NOT NULL,

            type TEXT NOT NULL,

            description TEXT,

            created_at TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # ADMIN LOGS
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            admin_id INTEGER NOT NULL,

            action TEXT NOT NULL,

            target_user INTEGER,

            amount INTEGER DEFAULT 0,

            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ============================================================
# USER
# ============================================================

def add_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users (
            telegram_id,
            username,
            first_name,
            coins,
            is_vip,
            referral_count,
            created_at
        )
        VALUES (?, ?, ?, 0, 0, 0, ?)
    """, (
        telegram_id,
        username,
        first_name,
        now()
    ))

    cursor.execute("""
        UPDATE users
        SET username = ?,
            first_name = ?
        WHERE telegram_id = ?
    """, (
        username,
        first_name,
        telegram_id
    ))

    conn.commit()
    conn.close()


def get_user(
    telegram_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    ))

    user = cursor.fetchone()

    conn.close()

    return user


# ============================================================
# ALL USERS
# ============================================================

def get_all_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        ORDER BY id ASC
    """)

    users = cursor.fetchall()

    conn.close()

    return users


# ============================================================
# BALANCE
# ============================================================

def get_balance(
    telegram_id: int
) -> int:

    user = get_user(
        telegram_id
    )

    if not user:
        return 0

    return int(
        user["coins"] or 0
    )


def add_coins(
    telegram_id: int,
    amount: int,
    history_type: str = "add",
    description: str = ""
):

    if amount <= 0:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET coins = coins + ?
        WHERE telegram_id = ?
    """, (
        amount,
        telegram_id
    ))

    if cursor.rowcount == 0:

        conn.close()

        return False

    cursor.execute("""
        INSERT INTO balance_history (
            telegram_id,
            amount,
            type,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        amount,
        history_type,
        description,
        now()
    ))

    conn.commit()
    conn.close()

    return True


def remove_coins(
    telegram_id: int,
    amount: int,
    history_type: str = "remove",
    description: str = ""
):

    if amount <= 0:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT coins
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    ))

    user = cursor.fetchone()

    if not user:

        conn.close()

        return False

    balance = int(
        user["coins"] or 0
    )

    if balance < amount:

        conn.close()

        return False

    cursor.execute("""
        UPDATE users
        SET coins = coins - ?
        WHERE telegram_id = ?
    """, (
        amount,
        telegram_id
    ))

    cursor.execute("""
        INSERT INTO balance_history (
            telegram_id,
            amount,
            type,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        -amount,
        history_type,
        description,
        now()
    ))

    conn.commit()
    conn.close()

    return True


# ============================================================
# VIP
# ============================================================

def set_vip(
    telegram_id: int,
    value: bool
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_vip = ?
        WHERE telegram_id = ?
    """, (
        1 if value else 0,
        telegram_id
    ))

    conn.commit()
    conn.close()


def is_vip(
    telegram_id: int
) -> bool:

    user = get_user(
        telegram_id
    )

    if not user:
        return False

    return bool(
        user["is_vip"]
    )


# ============================================================
# REFERRAL
# ============================================================

def set_referrer(
    telegram_id: int,
    referrer_id: int
):

    if telegram_id == referrer_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT referred_by
        FROM users
        WHERE telegram_id = ?
    """, (
        telegram_id,
    ))

    user = cursor.fetchone()

    if not user:

        conn.close()

        return False

    if user["referred_by"] is not None:

        conn.close()

        return False

    cursor.execute("""
        SELECT telegram_id
        FROM users
        WHERE telegram_id = ?
    """, (
        referrer_id,
    ))

    inviter = cursor.fetchone()

    if not inviter:

        conn.close()

        return False

    cursor.execute("""
        UPDATE users
        SET referred_by = ?
        WHERE telegram_id = ?
    """, (
        referrer_id,
        telegram_id
    ))

    cursor.execute("""
        UPDATE users
        SET referral_count = referral_count + 1
        WHERE telegram_id = ?
    """, (
        referrer_id,
    ))

    conn.commit()
    conn.close()

    return True


def add_referral(
    inviter_id: int,
    invited_id: int,
    bonus: int
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO referrals (
                inviter_id,
                invited_id,
                bonus,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            inviter_id,
            invited_id,
            bonus,
            now()
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return False

    conn.close()

    return True


# ============================================================
# STAR PURCHASE
# ============================================================

def payment_exists(
    telegram_payment_charge_id: str
) -> bool:

    if not telegram_payment_charge_id:
        return False

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM star_purchases
        WHERE telegram_payment_charge_id = ?
    """, (
        telegram_payment_charge_id,
    ))

    result = cursor.fetchone()

    conn.close()

    return result is not None


def save_star_purchase(
    telegram_id: int,
    stars: int,
    coins: int,
    telegram_payment_charge_id: Optional[str] = None,
    provider_payment_charge_id: Optional[str] = None
):

    if payment_exists(
        telegram_payment_charge_id
    ):
        return False

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO star_purchases (
                telegram_id,
                stars,
                coins,
                telegram_payment_charge_id,
                provider_payment_charge_id,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, 'completed', ?)
        """, (
            telegram_id,
            stars,
            coins,
            telegram_payment_charge_id,
            provider_payment_charge_id,
            now()
        ))

        conn.commit()

    except sqlite3.IntegrityError:

        conn.close()

        return False

    conn.close()

    return True


# ============================================================
# ORDER
# ============================================================

def create_order(
    telegram_id: int,
    service: str,
    target: str,
    quantity: int,
    price: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (
            telegram_id,
            service,
            target,
            quantity,
            price,
            status,
            external_order_id,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, 'pending', NULL, ?, ?)
    """, (
        telegram_id,
        service,
        target,
        quantity,
        price,
        now(),
        now()
    ))

    order_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return order_id


def get_order(
    order_id: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id = ?
    """, (
        order_id,
    ))

    order = cursor.fetchone()

    conn.close()

    return order


def update_order_status(
    order_id: int,
    status: str
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET status = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        status,
        now(),
        order_id
    ))

    conn.commit()
    conn.close()


def set_external_order_id(
    order_id: int,
    external_order_id: str
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE orders
        SET external_order_id = ?,
            updated_at = ?
        WHERE id = ?
    """, (
        external_order_id,
        now(),
        order_id
    ))

    conn.commit()
    conn.close()


def get_user_orders(
    telegram_id: int,
    limit: int = 10
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        telegram_id,
        limit
    ))

    orders = cursor.fetchall()

    conn.close()

    return orders


def get_pending_orders(
    limit: int = 50
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE status = 'pending'
        ORDER BY id ASC
        LIMIT ?
    """, (
        limit,
    ))

    orders = cursor.fetchall()

    conn.close()

    return orders


# ============================================================
# SERVICE PRICES
# ============================================================

def set_service_price(
    service: str,
    price: int
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO service_prices (
            service,
            price
        )
        VALUES (?, ?)

        ON CONFLICT(service)
        DO UPDATE SET price = excluded.price
    """, (
        service,
        price
    ))

    conn.commit()
    conn.close()


def get_service_price(
    service: str,
    default: int = 1
) -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT price
        FROM service_prices
        WHERE service = ?
    """, (
        service,
    ))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return default

    return int(
        row["price"]
    )


def initialize_prices():

    default_prices = {
        "subscribers": 1,
        "reactions": 2,
        "views": 1,
    }

    for service, price in default_prices.items():

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT service
            FROM service_prices
            WHERE service = ?
        """, (
            service,
        ))

        exists = cursor.fetchone()

        conn.close()

        if not exists:

            set_service_price(
                service,
                price
            )


# ============================================================
# RATING
# ============================================================

def get_top_users(
    limit: int = 10
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            telegram_id,
            username,
            first_name,
            coins
        FROM users
        ORDER BY coins DESC
        LIMIT ?
    """, (
        limit,
    ))

    users = cursor.fetchall()

    conn.close()

    return users


# ============================================================
# STATISTICS
# ============================================================

def get_user_count() -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM users
    """)

    result = cursor.fetchone()

    conn.close()

    return int(
        result["count"]
    )


def get_order_count() -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM orders
    """)

    result = cursor.fetchone()

    conn.close()

    return int(
        result["count"]
    )


def get_pending_order_count() -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM orders
        WHERE status = 'pending'
    """)

    result = cursor.fetchone()

    conn.close()

    return int(
        result["count"]
    )


def get_total_coins() -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(
            SUM(coins),
            0
        ) AS total
        FROM users
    """)

    result = cursor.fetchone()

    conn.close()

    return int(
        result["total"]
    )


# ============================================================
# ADMIN LOG
# ============================================================

def add_admin_log(
    admin_id: int,
    action: str,
    target_user: Optional[int] = None,
    amount: int = 0
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO admin_logs (
            admin_id,
            action,
            target_user,
            amount,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        admin_id,
        action,
        target_user,
        amount,
        now()
    ))

    conn.commit()
    conn.close()