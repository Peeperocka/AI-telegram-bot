import sqlite3
import os
from functools import wraps

from aiogram import types
from aiogram.exceptions import TelegramAPIError
from dotenv import load_dotenv
from typing import Optional, List, Tuple, Dict

load_dotenv()
DATABASE_FILE = os.getenv('DATABASE_FILE', 'bot_data.db')
DEFAULT_DAILY_QUOTA = int(os.getenv('DEFAULT_DAILY_QUOTA', '20'))


def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    return conn


def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_models (
            model_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            rating INTEGER NOT NULL DEFAULT 1000
        )
    """)
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            quota_limit INTEGER NOT NULL DEFAULT {DEFAULT_DAILY_QUOTA},
            quota_used INTEGER NOT NULL DEFAULT 0,
            last_reset_date TEXT NOT NULL DEFAULT (date('now'))
        )
    """, )

    conn.commit()
    conn.close()
    print(f"Database table 'ai_models' ensured in '{DATABASE_FILE}'")


def add_model_if_not_exists(model_id: str, display_name: str, initial_rating: int = 1000):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO ai_models (model_id, display_name, rating)
            VALUES (?, ?, ?)
        """, (model_id, display_name, initial_rating))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Added model to DB: {model_id}")

    except sqlite3.Error as e:
        print(f"Database error adding model {model_id}: {e}")
    finally:
        conn.close()


def get_model_rating(model_id: str) -> Optional[int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT rating FROM ai_models WHERE model_id = ?", (model_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Database error getting rating for {model_id}: {e}")
        return None
    finally:
        conn.close()


def update_model_rating(model_id: str, new_rating: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ai_models SET rating = ? WHERE model_id = ?", (new_rating, model_id))
        conn.commit()
        if cursor.rowcount == 0:
            print(f"Warning: Tried to update rating for non-existent model_id: {model_id}")
    except sqlite3.Error as e:
        print(f"Database error updating rating for {model_id}: {e}")
    finally:
        conn.close()


def get_models_sorted_by_rating(limit: Optional[int] = None) -> List[Tuple[str, str, int]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT model_id, display_name, rating FROM ai_models ORDER BY rating DESC"
        if limit:
            query += f" LIMIT {int(limit)}"
        cursor.execute(query)
        return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database error retrieving sorted models: {e}")
        return []
    finally:
        conn.close()


def register_or_check_user(user_id: int):
    conn = get_db_connection()
    try:
        with conn:
            _ensure_user_exists_and_reset_quota(user_id, conn)
    except sqlite3.Error as e:
        print(f"Database error during user check/registration for user {user_id}: {e}")
    finally:
        conn.close()


def drop_ai_models_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DROP TABLE IF EXISTS ai_models")
        conn.commit()
        print(f"Table 'ai_models' dropped from '{DATABASE_FILE}'")
    except sqlite3.Error as e:
        print(f"Error dropping table 'ai_models': {e}")
    finally:
        conn.close()


def _ensure_user_exists_and_reset_quota(user_id: int, conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (user_id, quota_limit, quota_used, last_reset_date)
        VALUES (?, ?, 0, date('now'))
    """, (user_id, DEFAULT_DAILY_QUOTA))
    cursor.execute("""
        UPDATE users
        SET quota_used = 0, last_reset_date = date('now')
        WHERE user_id = ? AND last_reset_date != date('now')
    """, (user_id,))


def can_afford_cost(user_id: int, cost: int) -> bool:
    if cost <= 0:
        return True

    conn = get_db_connection()
    can_afford = False
    try:
        with conn:
            _ensure_user_exists_and_reset_quota(user_id, conn)
            cursor = conn.cursor()
            cursor.execute("SELECT quota_used, quota_limit FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                quota_used, quota_limit = result
                can_afford = (quota_limit - quota_used) >= cost
            else:
                print(f"Error: User {user_id} not found after ensuring existence in can_afford_cost.")
    except sqlite3.Error as e:
        print(f"Database error checking affordability for user {user_id}, cost {cost}: {e}")
    finally:
        conn.close()
    return can_afford


def consume_quota(user_id: int, cost: int) -> bool:
    if cost <= 0:
        print(f"Attempted to consume non-positive quota cost ({cost}) for user {user_id}. Action skipped.")
        return True

    conn = get_db_connection()
    consumed = False
    try:
        with conn:
            _ensure_user_exists_and_reset_quota(user_id, conn)
            cursor = conn.cursor()
            cursor.execute("""
                 UPDATE users
                 SET quota_used = quota_used + ?
                 WHERE user_id = ? AND (quota_limit - quota_used) >= ?
             """, (cost, user_id, cost))
            if cursor.rowcount > 0:
                consumed = True
    except sqlite3.Error as e:
        print(f"Database error consuming quota for user {user_id}, cost {cost}: {e}")
    finally:
        conn.close()

    if consumed:
        print(f"Consumed {cost} quota for user {user_id}")
    else:
        print(f"Quota limit reached or error for user {user_id} when trying to consume cost {cost}")

    return consumed


def get_user_quota_info(user_id: int) -> Optional[Dict[str, int]]:
    conn = get_db_connection()
    info = None
    try:
        with conn:
            _ensure_user_exists_and_reset_quota(user_id, conn)
            cursor = conn.cursor()
            cursor.execute("SELECT quota_limit, quota_used FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if result:
                info = {"limit": result[0], "used": result[1]}
    except sqlite3.Error as e:
        print(f"Database error getting quota info for user {user_id}: {e}")
    finally:
        conn.close()
    return info


def quota_check(cost: int):
    if not isinstance(cost, int) or cost < 0:
        raise ValueError("Стоимость квоты должна быть неотрицательным целым числом.")

    def decorator(handler):
        @wraps(handler)
        async def wrapper(update: types.Update, *args, **kwargs):
            user = None
            reply_method = None

            if isinstance(update, types.Message):
                user = update.from_user
                reply_method = update.reply
            elif isinstance(update, types.CallbackQuery):
                user = update.from_user
                if update.message:
                    reply_method = update.message.reply
                else:
                    reply_method = update.answer

            if not user or not reply_method:
                print(
                    f"Quota check decorator: Can't get user or reply method from update type {type(update)}. Skipping check.")
                return await handler(update, *args, **kwargs)

            user_id = user.id

            if not can_afford_cost(user_id, cost):
                print(f"Проверка квоты не пройдена для пользователя {user_id}. Требуется: {cost}")
                quota_info = get_user_quota_info(user_id)
                limit = quota_info.get('limit', DEFAULT_DAILY_QUOTA) if quota_info else DEFAULT_DAILY_QUOTA
                reply_text = f"❌ Ваш дневной лимит запросов ({limit}) исчерпан. Попробуйте завтра."

                try:
                    await reply_method(reply_text)
                except TelegramAPIError as e:
                    print(f"Ошибка отправки сообщения об исчерпании лимита пользователю {user_id}: {e}")
                return

            print(f"Проверка квоты пройдена для пользователя {user_id}. Требуется: {cost}. Продолжаем.")
            return await handler(update, *args, **kwargs)

        return wrapper

    return decorator
