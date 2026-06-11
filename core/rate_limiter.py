from __future__ import annotations

import hashlib
import hmac
import logging
import os
import sqlite3
import time
from dataclasses import dataclass

from core import db

logger = logging.getLogger("gunicorn.error")

EXPORT_RATE_LIMITS = {
    "pdf": {
        "limit": int(os.environ.get("TABCAD_PDF_LIMIT_PER_HOUR", "10")),
        "window_seconds": int(os.environ.get("TABCAD_PDF_LIMIT_WINDOW_SECONDS", "3600")),
        "cooldown_seconds": int(os.environ.get("TABCAD_PDF_COOLDOWN_SECONDS", "20")),
    },
    "stl": {
        "limit": int(os.environ.get("TABCAD_STL_LIMIT_PER_HOUR", "20")),
        "window_seconds": int(os.environ.get("TABCAD_STL_LIMIT_WINDOW_SECONDS", "3600")),
        "cooldown_seconds": int(os.environ.get("TABCAD_STL_COOLDOWN_SECONDS", "10")),
    },
}


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0
    remaining: int = 0
    reason: str = ""


def _hash_identity(identity: str) -> str:
    payload = identity.encode("utf-8")
    if db.TOKEN_SECRET:
        digest = hmac.new(db.TOKEN_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    else:
        digest = hashlib.sha256(payload).hexdigest()
    return digest


def get_client_ip() -> str:
    """Возвращает IP из Flask request, учитывая reverse proxy headers."""
    try:
        from flask import request

        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip() or "unknown"
        return request.remote_addr or "unknown"
    except RuntimeError:
        return "unknown"


def _rate_identity(user_token: str | None, client_ip: str | None) -> str:
    normalized = db.normalize_token(user_token)
    if normalized:
        user_id = db.register_or_get_user(normalized)
        if user_id:
            return _hash_identity(f"user:{user_id}")
    return _hash_identity(f"ip:{client_ip or 'unknown'}")


def check_export_rate_limit(
    action: str,
    user_token: str | None,
    client_ip: str | None = None,
) -> RateLimitResult:
    """Проверяет и записывает попытку тяжёлого экспорта."""
    config = EXPORT_RATE_LIMITS[action]
    limit = config["limit"]
    window_seconds = config["window_seconds"]
    cooldown_seconds = config["cooldown_seconds"]

    if db.is_admin_token(user_token):
        return RateLimitResult(allowed=True, remaining=limit)

    now = int(time.time())
    window_start = now - window_seconds
    identity = _rate_identity(user_token, client_ip or get_client_ip())

    try:
        with sqlite3.connect(db.DB_PATH, timeout=5, isolation_level=None) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "DELETE FROM rate_limit_events WHERE created_at < ?",
                (now - max(window_seconds * 2, 86400),),
            )

            last_row = conn.execute(
                """
                SELECT created_at FROM rate_limit_events
                WHERE action = ? AND identity = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (action, identity),
            ).fetchone()
            if last_row and now - int(last_row[0]) < cooldown_seconds:
                retry_after = cooldown_seconds - (now - int(last_row[0]))
                conn.commit()
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=retry_after,
                    reason="cooldown",
                )

            count = conn.execute(
                """
                SELECT COUNT(*) FROM rate_limit_events
                WHERE action = ? AND identity = ? AND created_at >= ?
                """,
                (action, identity, window_start),
            ).fetchone()[0]
            if count >= limit:
                oldest_row = conn.execute(
                    """
                    SELECT created_at FROM rate_limit_events
                    WHERE action = ? AND identity = ? AND created_at >= ?
                    ORDER BY created_at ASC
                    LIMIT 1
                    """,
                    (action, identity, window_start),
                ).fetchone()
                retry_after = window_seconds
                if oldest_row:
                    retry_after = max(1, window_seconds - (now - int(oldest_row[0])))
                conn.commit()
                return RateLimitResult(
                    allowed=False,
                    retry_after_seconds=retry_after,
                    reason="window",
                )

            conn.execute(
                """
                INSERT INTO rate_limit_events (action, identity, created_at)
                VALUES (?, ?, ?)
                """,
                (action, identity, now),
            )
            conn.commit()
            return RateLimitResult(allowed=True, remaining=max(0, limit - count - 1))
    except sqlite3.Error as exc:
        logger.warning("Rate limiter failed for %s export: %s", action, exc)
        return RateLimitResult(allowed=False, reason="storage_error")
