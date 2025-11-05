"""
Système de rate limiting sécurisé et persistant pour FormForge
Utilise SQLite pour la persistance (compatible multi-instances avec database lock)
Alternative à Redis pour déploiement simple sans infrastructure externe

Expert Cybersécurité - 15+ ans d'expérience
"""

import time
import hashlib
import sqlite3
import threading
from typing import Dict, Tuple
from functools import wraps
from flask import request, jsonify
import logging
import os

logger = logging.getLogger(__name__)


class SecureRateLimiter:
    """
    Rate limiter sécurisé avec persistance SQLite

    Avantages vs solution en mémoire:
    - Persistance entre redémarrages
    - Fonctionne avec multiple workers/instances (via DB locks)
    - Cleanup automatique des entrées expirées
    - Audit trail des tentatives de rate limiting
    """

    def __init__(self, db_path="data/rate_limiter.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

        # Configuration des limites par route (ÉQUILIBRÉE SÉCURITÉ/UX)
        self.limits = {
            # Routes d'authentification (strictes pour sécurité)
            "auth_register": {"requests": 10, "window": 300},  # 10 req/5min
            "auth_login": {"requests": 15, "window": 300},     # 15 req/5min
            "auth_verify": {"requests": 20, "window": 300},    # 20 req/5min
            "auth_signup": {"requests": 10, "window": 300},    # 10 req/5min
            "auth_signin": {"requests": 15, "window": 300},    # 15 req/5min
            "auth_me": {"requests": 40, "window": 300},        # 40 req/5min

            # Routes de formulaires (permissives pour UX)
            "forms_create": {"requests": 30, "window": 3600},   # 30 req/h
            "forms_get": {"requests": 150, "window": 3600},     # 150 req/h
            "forms_update": {"requests": 40, "window": 3600},   # 40 req/h
            "forms_delete": {"requests": 15, "window": 3600},   # 15 req/h
            "forms_stats": {"requests": 60, "window": 3600},    # 60 req/h
            "forms_publish": {"requests": 20, "window": 3600},  # 20 req/h
            "forms_public_link": {"requests": 50, "window": 3600},  # 50 req/h
            "forms_public_access": {"requests": 200, "window": 3600},  # 200 req/h (public)

            # Routes de questions
            "questions_create": {"requests": 80, "window": 3600},   # 80 req/h
            "questions_get": {"requests": 200, "window": 3600},     # 200 req/h
            "questions_update": {"requests": 80, "window": 3600},   # 80 req/h
            "questions_delete": {"requests": 30, "window": 3600},   # 30 req/h

            # Routes de réponses (permissives car utilisation intensive)
            "responses_submit": {"requests": 100, "window": 3600},        # 100 req/h
            "responses_submit_public": {"requests": 150, "window": 3600}, # 150 req/h (public)
            "responses_get": {"requests": 200, "window": 3600},           # 200 req/h

            # Routes de fichiers (strictes car coûteux)
            "files_upload": {"requests": 20, "window": 3600},    # 20 req/h
            "files_download": {"requests": 100, "window": 3600}, # 100 req/h

            # Routes de monitoring (très strictes - admin only)
            "monitoring_performance": {"requests": 30, "window": 3600},
            "monitoring_health": {"requests": 60, "window": 3600},
            "monitoring_system": {"requests": 10, "window": 3600},
            "monitoring_dashboard": {"requests": 50, "window": 3600},

            # Routes générales
            "health": {"requests": 500, "window": 3600},  # 500 req/h (monitoring externe)
            "default": {"requests": 100, "window": 3600},  # 100 req/h (fallback)
        }

    def _get_connection(self):
        """Obtenir une connexion thread-safe à la base de données"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # Créer le dossier data si nécessaire
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=10,  # Timeout pour éviter les deadlocks
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_database(self):
        """Initialiser la base de données de rate limiting"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Table pour stocker les compteurs de rate limiting
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                route_key TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                window_start REAL NOT NULL,
                window_end REAL NOT NULL,
                last_request REAL NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(client_id, route_key, window_start)
            )
        """)

        # Index pour optimiser les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_limits_lookup
            ON rate_limits(client_id, route_key, window_end)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_limits_cleanup
            ON rate_limits(window_end)
        """)

        conn.commit()
        logger.info("Rate limiter database initialized")

    def _get_client_id(self) -> str:
        """
        Obtenir un identifiant unique et sécurisé du client

        Utilise plusieurs facteurs pour identifier de manière unique:
        - IP réelle (derrière proxy)
        - User-Agent (fingerprinting basique)
        """
        # Récupérer l'IP réelle (derrière proxy Render/Cloudflare)
        client_ip = request.headers.get("X-Forwarded-For")
        if client_ip:
            # Prendre la première IP (client réel)
            client_ip = client_ip.split(",")[0].strip()
        else:
            client_ip = request.remote_addr or "unknown"

        # Ajouter User-Agent pour fingerprinting
        user_agent = request.headers.get("User-Agent", "")

        # Créer un hash unique mais anonyme
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()

    def _cleanup_expired(self, conn, current_time: float):
        """Nettoyer les entrées expirées"""
        try:
            cursor = conn.cursor()
            # Supprimer les entrées dont la fenêtre est expirée
            cursor.execute("""
                DELETE FROM rate_limits
                WHERE window_end < ?
            """, (current_time,))

            deleted = cursor.rowcount
            if deleted > 0:
                conn.commit()
                logger.debug(f"Cleaned up {deleted} expired rate limit entries")
        except Exception as e:
            logger.error(f"Error cleaning up rate limits: {e}")
            conn.rollback()

    def is_allowed(self, route_name: str) -> Tuple[bool, Dict]:
        """
        Vérifier si une requête est autorisée

        Returns:
            (allowed, info_dict) où info_dict contient les métadonnées
        """
        try:
            client_id = self._get_client_id()
            current_time = time.time()
            conn = self._get_connection()
            cursor = conn.cursor()

            # Obtenir les limites pour cette route
            limits = self.limits.get(route_name, self.limits["default"])
            max_requests = limits["requests"]
            window_duration = limits["window"]

            # Cleanup périodique (toutes les 100 requêtes environ)
            if int(current_time) % 100 == 0:
                self._cleanup_expired(conn, current_time)

            # Chercher l'entrée active pour ce client/route
            cursor.execute("""
                SELECT id, count, window_start, window_end
                FROM rate_limits
                WHERE client_id = ?
                AND route_key = ?
                AND window_end > ?
                ORDER BY window_start DESC
                LIMIT 1
            """, (client_id, route_name, current_time))

            row = cursor.fetchone()

            if row:
                # Entrée existante dans la fenêtre actuelle
                entry_id = row['id']
                count = row['count']
                window_start = row['window_start']
                window_end = row['window_end']

                if count >= max_requests:
                    # Limite atteinte
                    wait_time = int(window_end - current_time)

                    # Logger la tentative bloquée
                    logger.warning(
                        f"Rate limit exceeded for client {client_id[:16]}... "
                        f"on route {route_name} ({count}/{max_requests})"
                    )

                    return False, {
                        "limit": max_requests,
                        "remaining": 0,
                        "reset_time": window_end,
                        "wait_time": wait_time,
                        "window_duration": window_duration,
                    }

                # Incrémenter le compteur
                cursor.execute("""
                    UPDATE rate_limits
                    SET count = count + 1, last_request = ?
                    WHERE id = ?
                """, (current_time, entry_id))
                conn.commit()

                return True, {
                    "limit": max_requests,
                    "remaining": max_requests - count - 1,
                    "reset_time": window_end,
                    "window_duration": window_duration,
                }

            else:
                # Créer une nouvelle entrée
                window_start = current_time
                window_end = current_time + window_duration

                cursor.execute("""
                    INSERT INTO rate_limits
                    (client_id, route_key, count, window_start, window_end, last_request, created_at)
                    VALUES (?, ?, 1, ?, ?, ?, ?)
                """, (client_id, route_name, window_start, window_end, current_time, current_time))
                conn.commit()

                return True, {
                    "limit": max_requests,
                    "remaining": max_requests - 1,
                    "reset_time": window_end,
                    "window_duration": window_duration,
                }

        except Exception as e:
            logger.error(f"Error in rate limiting: {e}", exc_info=True)
            # En cas d'erreur, autoriser la requête (fail open)
            # Mieux que de bloquer tout le service
            return True, {
                "limit": 100,
                "remaining": 99,
                "reset_time": time.time() + 3600,
                "error": str(e)
            }

    def get_rate_limit_headers(self, route_name: str) -> Dict[str, str]:
        """Obtenir les headers de rate limiting pour la réponse"""
        is_allowed, info = self.is_allowed(route_name)

        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(int(info["reset_time"])),
        }

        if not is_allowed:
            headers["Retry-After"] = str(info["wait_time"])

        return headers

    def get_stats(self) -> Dict:
        """Obtenir les statistiques de rate limiting (pour monitoring)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Nombre total d'entrées actives
            cursor.execute("SELECT COUNT(*) as total FROM rate_limits WHERE window_end > ?", (time.time(),))
            total_active = cursor.fetchone()['total']

            # Nombre de clients uniques
            cursor.execute("SELECT COUNT(DISTINCT client_id) as unique_clients FROM rate_limits WHERE window_end > ?", (time.time(),))
            unique_clients = cursor.fetchone()['unique_clients']

            return {
                "total_active_entries": total_active,
                "unique_clients": unique_clients,
                "storage": "SQLite (persistent)",
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Error getting rate limiter stats: {e}")
            return {"error": str(e), "status": "error"}


# Instance globale du rate limiter sécurisé
secure_rate_limiter = SecureRateLimiter()


def rate_limit(route_name: str):
    """
    Décorateur pour appliquer le rate limiting sécurisé à une route

    Usage:
        @rate_limit("auth_login")
        def login():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Vérifier le rate limiting
            is_allowed, info = secure_rate_limiter.is_allowed(route_name)

            if not is_allowed:
                headers = secure_rate_limiter.get_rate_limit_headers(route_name)
                return (
                    jsonify({
                        "success": False,
                        "error": "Rate limit exceeded",
                        "message": f'Too many requests. Limit: {info["limit"]} requests per {info["window_duration"]} seconds',
                        "retry_after": info["wait_time"],
                        "limit": info["limit"],
                        "remaining": info["remaining"],
                        "reset_time": info["reset_time"],
                    }),
                    429,
                    headers,
                )

            # Ajouter les headers de rate limiting à la réponse
            response = f(*args, **kwargs)
            headers = secure_rate_limiter.get_rate_limit_headers(route_name)

            # Gérer tous les types de réponses Flask
            if isinstance(response, tuple):
                if len(response) == 2:
                    return response[0], response[1], headers
                elif len(response) == 3:
                    existing_headers = response[2] if isinstance(response[2], dict) else {}
                    existing_headers.update(headers)
                    return response[0], response[1], existing_headers
                else:
                    return response
            else:
                from flask import Response as FlaskResponse, make_response

                if isinstance(response, FlaskResponse):
                    for key, value in headers.items():
                        response.headers[key] = value
                    return response
                else:
                    resp = make_response(response)
                    for key, value in headers.items():
                        resp.headers[key] = value
                    return resp

        return decorated_function

    return decorator


def get_rate_limit_info(route_name: str) -> Dict:
    """Obtenir les informations de rate limiting pour une route"""
    is_allowed, info = secure_rate_limiter.is_allowed(route_name)
    return {
        "route": route_name,
        "allowed": is_allowed,
        "limit": info["limit"],
        "remaining": info["remaining"],
        "reset_time": info["reset_time"],
        "window_duration": info["window_duration"],
    }
