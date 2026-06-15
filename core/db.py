from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from datetime import datetime

DEFAULT_DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "presets.db")
)
DB_PATH = os.path.normpath(os.environ.get("TABCAD_DB_PATH", DEFAULT_DB_PATH))

TOKEN_SECRET = os.environ.get("TABCAD_TOKEN_SECRET", "")
DEFAULT_PRESET_LIMIT = int(os.environ.get("TABCAD_DEFAULT_PRESET_LIMIT", "50"))
ADMIN_PRESET_LIMIT = int(os.environ.get("TABCAD_ADMIN_PRESET_LIMIT", "1000000"))
EMPTY_USER_RETENTION_DAYS = int(os.environ.get("TABCAD_EMPTY_USER_RETENTION_DAYS", "30"))
CLEANUP_INTERVAL_SECONDS = int(os.environ.get("TABCAD_CLEANUP_INTERVAL_SECONDS", "86400"))
MAX_PRESET_JSON_BYTES = int(os.environ.get("TABCAD_MAX_PRESET_JSON_BYTES", "100000"))

_TOKEN_RE = re.compile(r"^[A-Z0-9]{5}(?:-[A-Z0-9]{5}){3}$")
_last_cleanup_ts = 0.0


def normalize_token(token: str | None) -> str | None:
    """Нормализует код доступа для сравнения и хранения."""
    if not token:
        return None
    value = token.strip().upper().replace(" ", "")
    return value if _TOKEN_RE.fullmatch(value) else None


ADMIN_TOKENS = {
    token
    for token in (
        normalize_token(raw_token)
        for raw_token in os.environ.get("TABCAD_ADMIN_TOKENS", "").split(",")
    )
    if token
}


def is_admin_token(token: str | None) -> bool:
    """Проверяет, является ли код доступа админским."""
    normalized = normalize_token(token)
    return bool(normalized and normalized in ADMIN_TOKENS)


def _hash_token(token: str) -> str:
    """Возвращает необратимый хэш токена; секрет можно задать через env."""
    normalized = normalize_token(token)
    if not normalized:
        raise ValueError("Invalid access token format")
    payload = normalized.encode("utf-8")
    if TOKEN_SECRET:
        digest = hmac.new(TOKEN_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return f"hmac-sha256:{digest}"
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _create_current_schema(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_hash TEXT UNIQUE NOT NULL,
            preset_limit INTEGER NOT NULL DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            parameters TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, name)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_presets_user_name
        ON presets(user_id, name COLLATE NOCASE)
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            identity TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_rate_limit_events_lookup
        ON rate_limit_events(action, identity, created_at)
    """)


def _migrate_legacy_presets(conn: sqlite3.Connection):
    if not _table_exists(conn, "presets"):
        return
    columns = _table_columns(conn, "presets")
    if "user_id" in columns:
        return

    suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    legacy_name = f"presets_legacy_{suffix}"
    conn.execute(f"ALTER TABLE presets RENAME TO {legacy_name}")


def init_db():
    """Создаёт или мигрирует таблицы авторизации и пресетов."""
    global _last_cleanup_ts
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        _migrate_legacy_presets(conn)
        _create_current_schema(conn)
        cleanup_empty_users(conn=conn)
    _last_cleanup_ts = time.time()


def cleanup_empty_users(
    retention_days: int | None = None,
    conn: sqlite3.Connection | None = None,
) -> int:
    """Удаляет старых пользователей без пресетов."""
    days = EMPTY_USER_RETENTION_DAYS if retention_days is None else retention_days
    if days < 0:
        return 0

    query = """
        DELETE FROM users
        WHERE created_at < datetime('now', ?)
          AND (last_used_at IS NULL OR last_used_at < datetime('now', ?))
          AND NOT EXISTS (
              SELECT 1 FROM presets
              WHERE presets.user_id = users.id
          )
    """
    cutoff = f"-{days} days"

    if conn is not None:
        cursor = conn.execute(query, (cutoff, cutoff))
        return cursor.rowcount if cursor.rowcount is not None else 0

    with sqlite3.connect(DB_PATH) as cleanup_conn:
        cleanup_conn.execute("PRAGMA foreign_keys = ON")
        cursor = cleanup_conn.execute(query, (cutoff, cutoff))
        return cursor.rowcount if cursor.rowcount is not None else 0


def maybe_cleanup_empty_users() -> int:
    """Запускает автоочистку не чаще заданного интервала в текущем процессе."""
    global _last_cleanup_ts
    now = time.time()
    if now - _last_cleanup_ts < CLEANUP_INTERVAL_SECONDS:
        return 0
    _last_cleanup_ts = now
    return cleanup_empty_users()


def register_or_get_user(token: str | None) -> int | None:
    """Возвращает user_id для валидного кода доступа, создавая запись при первом входе."""
    maybe_cleanup_empty_users()
    normalized = normalize_token(token)
    if not normalized:
        return None
    token_hash = _hash_token(normalized)
    preset_limit = ADMIN_PRESET_LIMIT if is_admin_token(normalized) else DEFAULT_PRESET_LIMIT
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        row = conn.execute(
            "SELECT id FROM users WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
        if row:
            conn.execute(
                """
                UPDATE users
                SET last_used_at = CURRENT_TIMESTAMP,
                    preset_limit = MAX(preset_limit, ?)
                WHERE id = ?
                """,
                (preset_limit, row[0]),
            )
            return row[0]

        cursor = conn.execute(
            """
            INSERT INTO users (token_hash, preset_limit, last_used_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (token_hash, preset_limit),
        )
        return cursor.lastrowid


def token_exists(token: str | None) -> bool:
    """Проверяет, есть ли уже такой код доступа в базе."""
    normalized = normalize_token(token)
    if not normalized:
        return False
    token_hash = _hash_token(normalized)
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM users WHERE token_hash = ?",
            (token_hash,),
        ).fetchone()
    return row is not None


def get_preset_limit(user_id: int) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT preset_limit FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return int(row[0]) if row else DEFAULT_PRESET_LIMIT


def save_preset(user_id: int, name: str, parameters: dict):
    """Сохраняет или перезаписывает пресет конкретного пользователя."""
    params_json = json.dumps(parameters, ensure_ascii=False)
    if len(params_json.encode("utf-8")) > MAX_PRESET_JSON_BYTES:
        raise ValueError("Preset is too large")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            INSERT INTO presets (user_id, name, parameters, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, name) DO UPDATE SET
                parameters = excluded.parameters,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, name, params_json))


def load_preset(user_id: int, name: str) -> dict | None:
    """Загружает пресет пользователя по имени."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT parameters FROM presets WHERE user_id = ? AND name = ?",
            (user_id, name),
        ).fetchone()
    return json.loads(row[0]) if row else None


def get_all_preset_names(user_id: int) -> list:
    """Возвращает список имён сохранённых пресетов пользователя."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT name FROM presets WHERE user_id = ? ORDER BY name COLLATE NOCASE ASC",
            (user_id,),
        ).fetchall()
    return [row[0] for row in rows]


def get_preset_names_starting_with(user_id: int, base_name: str) -> list:
    """Возвращает имена пресетов пользователя, начинающиеся с заданного префикса."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT name FROM presets
            WHERE user_id = ? AND name LIKE ?
            ORDER BY name COLLATE NOCASE ASC
            """,
            (user_id, f"{base_name}%"),
        ).fetchall()
    return [row[0] for row in rows]


def preset_exists(user_id: int, name: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM presets WHERE user_id = ? AND name = ?",
            (user_id, name),
        ).fetchone()
    return row is not None


def count_presets(user_id: int) -> int:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM presets WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return int(row[0]) if row else 0


def delete_preset(user_id: int, name: str):
    """Удаляет пресет пользователя по имени."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM presets WHERE user_id = ? AND name = ?",
            (user_id, name),
        )


# Инициализируем БД при импорте модуля.
init_db()
