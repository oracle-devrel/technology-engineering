"""
Database module for Sentiment Intelligence.
Manages Oracle Autonomous Database connections using both the select_ai library
(for Select AI Profile and NL2SQL) and oracledb directly (for SQL inserts and DBMS_CLOUD_AI calls).
"""

import logging
import os
import socket
import threading
import time

import oracledb
import select_ai
from select_ai import Profile

from config import settings

logger = logging.getLogger(__name__)

# Startup connect retry policy. Transient DNS/network failures (e.g. an IPv6
# resolver flapping) can make the ADB host momentarily unresolvable even though
# it is reachable seconds later, so retry a few times with a short backoff
# before giving up and letting the app start in a degraded state.
_CONNECT_MAX_ATTEMPTS = 5
_CONNECT_BACKOFF_SECONDS = 3


def _is_transient_network_error(exc: Exception) -> bool:
    """Heuristic: is this a transient DNS/network failure worth retrying?"""
    if isinstance(exc, socket.gaierror):
        return True
    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "nodename nor servname",   # macOS getaddrinfo failure
            "name or service not known",  # Linux getaddrinfo failure
            "temporary failure in name resolution",
            "getaddrinfo",
            "no address associated with hostname",
            "connection refused",
            "connection reset",
            "connection timed out",
            "network is unreachable",
        )
    )

# Global state
_is_connected = False
_select_ai_profile = None
_direct_pool: oracledb.ConnectionPool | None = None
_pool_lock = threading.Lock()


def _connection_params() -> dict:
    """Build connection parameters shared by oracledb and Select AI."""
    conn_params = {
        "user": settings.DB_USER,
        "password": settings.DB_PASSWORD,
        "dsn": settings.DB_DSN,
    }

    if settings.USE_WALLET and settings.WALLET_LOCATION:
        os.environ["TNS_ADMIN"] = settings.WALLET_LOCATION
        conn_params["config_dir"] = settings.WALLET_LOCATION
        conn_params["wallet_location"] = settings.WALLET_LOCATION
        if settings.WALLET_PASSWORD:
            conn_params["wallet_password"] = settings.WALLET_PASSWORD

    return conn_params


async def connect_to_database() -> None:
    """Establish connection to Oracle Autonomous Database via select_ai.connect()."""
    global _is_connected, _select_ai_profile

    if _is_connected and select_ai.is_connected():
        logger.info("Database already connected.")
        return

    logger.info(
        "Connecting to Oracle ADB as %s @ %s (wallet=%s)",
        settings.DB_USER, settings.DB_DSN, settings.USE_WALLET,
    )

    conn_params = _connection_params()
    last_exc: Exception | None = None

    for attempt in range(1, _CONNECT_MAX_ATTEMPTS + 1):
        try:
            select_ai.connect(**conn_params)

            # Cache the Select AI profile and warm the direct SQL pool used by the
            # concurrent pipeline workers.
            _select_ai_profile = Profile.fetch(profile_name=settings.SELECT_AI_PROFILE)
            _get_or_create_pool()
            _is_connected = True

            logger.info("Connected. Select AI profile '%s' loaded.", settings.SELECT_AI_PROFILE)

            # Run lightweight schema migrations
            _run_migrations()
            return

        except Exception as exc:
            _is_connected = False
            last_exc = exc

            if _is_transient_network_error(exc) and attempt < _CONNECT_MAX_ATTEMPTS:
                logger.warning(
                    "Transient network error connecting to ADB (attempt %d/%d): %s — "
                    "retrying in %ds.",
                    attempt, _CONNECT_MAX_ATTEMPTS, exc, _CONNECT_BACKOFF_SECONDS,
                )
                time.sleep(_CONNECT_BACKOFF_SECONDS)
                continue

            logger.error("Failed to connect: %s", exc, exc_info=True)
            raise RuntimeError(f"Database connection failed: {exc}") from exc

    # Defensive: loop always returns or raises above, but keep mypy/readers happy.
    raise RuntimeError(f"Database connection failed: {last_exc}") from last_exc


def get_select_ai_profile() -> Profile:
    """Return a Select AI profile with a healthy connection in this thread.

    select_ai 1.2.x stores connections by process and thread. FastAPI startup and
    request handling are not guaranteed to use the same execution context, and a
    long-lived startup connection can also become stale. Re-establish the library
    connection on demand while keeping the profile proxy cached.
    """
    global _is_connected, _select_ai_profile

    if not select_ai.is_connected():
        logger.info("Select AI connection unavailable in the current context; reconnecting.")
        try:
            select_ai.connect(**_connection_params())
            _select_ai_profile = Profile.fetch(profile_name=settings.SELECT_AI_PROFILE)
            _is_connected = True
        except Exception as exc:
            _is_connected = False
            logger.error("Failed to reconnect Select AI: %s", exc, exc_info=True)
            raise RuntimeError(f"Select AI reconnection failed: {exc}") from exc
    elif _select_ai_profile is None:
        _select_ai_profile = Profile.fetch(profile_name=settings.SELECT_AI_PROFILE)

    return _select_ai_profile


def get_db_connection() -> oracledb.Connection:
    """Acquire a pooled connection for SQL and DBMS_CLOUD_AI calls."""
    return _get_or_create_pool().acquire()


def _get_or_create_pool() -> oracledb.ConnectionPool:
    """Create the direct Oracle pool once, safely across worker threads."""
    global _direct_pool
    if _direct_pool is not None:
        return _direct_pool

    with _pool_lock:
        if _direct_pool is None:
            pool_min = max(0, settings.DB_POOL_MIN)
            pool_max = max(pool_min, settings.DB_POOL_MAX)
            logger.info(
                "Creating Oracle connection pool (min=%d, max=%d).",
                pool_min,
                pool_max,
            )
            _direct_pool = oracledb.create_pool(
                **_connection_params(),
                min=pool_min,
                max=pool_max,
                increment=1,
                getmode=oracledb.POOL_GETMODE_TIMEDWAIT,
                wait_timeout=max(1, settings.DB_POOL_WAIT_TIMEOUT) * 1000,
                ping_interval=60,
            )
    return _direct_pool


async def close_connection() -> None:
    """Close the current Select AI connection and reset global state."""
    global _is_connected, _select_ai_profile, _direct_pool
    try:
        select_ai.disconnect()
    except Exception as exc:
        logger.warning("Failed to close Select AI connection cleanly: %s", exc)
    if _direct_pool is not None:
        try:
            _direct_pool.close(force=True)
        except Exception as exc:
            logger.warning("Failed to close Oracle connection pool cleanly: %s", exc)
        finally:
            _direct_pool = None
    _is_connected = False
    _select_ai_profile = None
    logger.info("Connection state reset.")


def is_connected() -> bool:
    """Return whether the database is currently connected."""
    return _is_connected


def _run_migrations() -> None:
    """Add missing columns to existing tables (idempotent)."""
    stmts = [
        "ALTER TABLE sentiment_alerts ADD (brand VARCHAR2(200))",
        "ALTER TABLE action_recommendations ADD (brand VARCHAR2(200))",
        "ALTER TABLE sentiment_alerts ADD (source_urls CLOB)",
    ]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for sql in stmts:
            try:
                cursor.execute(sql)
                logger.info("Migration OK: %s", sql)
            except oracledb.DatabaseError as exc:
                # ORA-01430: column already exists — ignore
                if exc.args and hasattr(exc.args[0], 'code') and exc.args[0].code == 1430:
                    pass
                else:
                    logger.warning("Migration skipped: %s — %s", sql, exc)
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("Migration runner failed: %s", exc)
