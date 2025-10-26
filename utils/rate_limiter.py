"""
Système de rate limiting pour FormForge
"""

import time
import hashlib
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Gestionnaire de rate limiting en mémoire"""

    def __init__(self):
        # Stockage en mémoire des compteurs
        self.counters: Dict[str, Dict[str, int]] = {}
        self.windows: Dict[str, Dict[str, float]] = {}

        # Configuration des limites par route (ÉQUILIBRÉE UX/SÉCURITÉ)
        self.limits = {
            # Routes d'authentification (plus permissives)
            "auth_register": {
                "requests": 15,
                "window": 300,
            },  # 15 req/5min (au lieu de 5)
            "auth_login": {
                "requests": 25,
                "window": 300,
            },  # 25 req/5min (au lieu de 10)
            "auth_verify": {
                "requests": 30,
                "window": 300,
            },  # 30 req/5min (au lieu de 20)
            "auth_signup": {
                "requests": 15,
                "window": 300,
            },  # 15 req/5min (au lieu de 5)
            "auth_signin": {
                "requests": 25,
                "window": 300,
            },  # 25 req/5min (au lieu de 10)
            "auth_me": {"requests": 60, "window": 300},  # 60 req/5min (au lieu de 30)
            # Routes de formulaires (plus permissives)
            "forms_create": {
                "requests": 50,
                "window": 3600,
            },  # 50 req/h (au lieu de 20)
            "forms_get": {
                "requests": 200,
                "window": 3600,
            },  # 200 req/h (au lieu de 100)
            "forms_update": {
                "requests": 60,
                "window": 3600,
            },  # 60 req/h (au lieu de 30)
            "forms_delete": {
                "requests": 20,
                "window": 3600,
            },  # 20 req/h (au lieu de 10)
            "forms_stats": {"requests": 80, "window": 3600},  # 80 req/h (au lieu de 50)
            # Routes de questions (plus permissives)
            "questions_create": {
                "requests": 100,
                "window": 3600,
            },  # 100 req/h (au lieu de 50)
            "questions_get": {
                "requests": 300,
                "window": 3600,
            },  # 300 req/h (au lieu de 200)
            "questions_update": {
                "requests": 100,
                "window": 3600,
            },  # 100 req/h (au lieu de 50)
            "questions_delete": {
                "requests": 40,
                "window": 3600,
            },  # 40 req/h (au lieu de 20)
            # Routes de réponses (ajustées légèrement)
            "responses_submit": {
                "requests": 120,
                "window": 3600,
            },  # 120 req/h (au lieu de 100)
            "responses_get": {
                "requests": 250,
                "window": 3600,
            },  # 250 req/h (au lieu de 200)
            # Routes de fichiers (ajustées)
            "files_upload": {
                "requests": 30,
                "window": 3600,
            },  # 30 req/h (au lieu de 20)
            "files_download": {
                "requests": 150,
                "window": 3600,
            },  # 150 req/h (au lieu de 100)
            # Routes de monitoring (ajustées)
            "monitoring_performance": {
                "requests": 50,
                "window": 3600,
            },  # 50 req/h (au lieu de 30)
            "monitoring_health": {
                "requests": 100,
                "window": 3600,
            },  # 100 req/h (au lieu de 60)
            "monitoring_system": {
                "requests": 15,
                "window": 3600,
            },  # 15 req/h (au lieu de 10)
            "monitoring_dashboard": {
                "requests": 80,
                "window": 3600,
            },  # 80 req/h (au lieu de 50)
            # Routes générales
            "health": {"requests": 1000, "window": 3600},  # 1000 req/h (inchangé)
            "default": {"requests": 150, "window": 3600},  # 150 req/h (au lieu de 100)
        }

    def _get_client_id(self) -> str:
        """Obtenir un identifiant unique du client"""
        # Utiliser l'IP réelle si disponible (derrière un proxy)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        # Ajouter l'User-Agent pour plus de précision
        user_agent = request.headers.get("User-Agent", "")

        # Créer un hash unique
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.md5(identifier.encode()).hexdigest()

    def _get_route_key(self, route_name: str) -> str:
        """Obtenir la clé de route pour le rate limiting"""
        return route_name

    def _cleanup_old_entries(self, route_key: str):
        """Nettoyer les anciennes entrées"""
        current_time = time.time()
        window_duration = self.limits.get(route_key, self.limits["default"])["window"]

        # Nettoyer les compteurs expirés
        if route_key in self.counters:
            expired_keys = []
            for client_id, timestamp in self.windows.get(route_key, {}).items():
                if current_time - timestamp > window_duration:
                    expired_keys.append(client_id)

            for client_id in expired_keys:
                self.counters[route_key].pop(client_id, None)
                self.windows[route_key].pop(client_id, None)

    def is_allowed(self, route_name: str) -> Tuple[bool, Dict]:
        """Vérifier si une requête est autorisée"""
        try:
            client_id = self._get_client_id()
            route_key = self._get_route_key(route_name)
            current_time = time.time()

            # Obtenir les limites pour cette route
            limits = self.limits.get(route_key, self.limits["default"])
            max_requests = limits["requests"]
            window_duration = limits["window"]

            # Nettoyer les anciennes entrées
            self._cleanup_old_entries(route_key)

            # Initialiser les compteurs si nécessaire
            if route_key not in self.counters:
                self.counters[route_key] = {}
            if route_key not in self.windows:
                self.windows[route_key] = {}

            # Vérifier si la fenêtre de temps est expirée
            if client_id in self.windows[route_key]:
                window_start = self.windows[route_key][client_id]
                if current_time - window_start > window_duration:
                    # Réinitialiser le compteur
                    self.counters[route_key][client_id] = 0
                    self.windows[route_key][client_id] = current_time

            # Initialiser le compteur si nécessaire
            if client_id not in self.counters[route_key]:
                self.counters[route_key][client_id] = 0
                self.windows[route_key][client_id] = current_time

            # Vérifier la limite
            current_count = self.counters[route_key][client_id]

            if current_count >= max_requests:
                # Calculer le temps d'attente
                window_start = self.windows[route_key][client_id]
                reset_time = window_start + window_duration
                wait_time = int(reset_time - current_time)

                return False, {
                    "limit": max_requests,
                    "remaining": 0,
                    "reset_time": reset_time,
                    "wait_time": wait_time,
                    "window_duration": window_duration,
                }

            # Incrémenter le compteur
            self.counters[route_key][client_id] += 1

            # Retourner les informations de rate limiting
            return True, {
                "limit": max_requests,
                "remaining": max_requests - self.counters[route_key][client_id],
                "reset_time": self.windows[route_key][client_id] + window_duration,
                "window_duration": window_duration,
            }

        except Exception as e:
            logger.error(f"Erreur rate limiting: {e}")
            # En cas d'erreur, autoriser la requête
            return True, {
                "limit": 100,
                "remaining": 99,
                "reset_time": time.time() + 3600,
            }

    def get_rate_limit_headers(self, route_name: str) -> Dict[str, str]:
        """Obtenir les headers de rate limiting"""
        is_allowed, info = self.is_allowed(route_name)

        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(int(info["reset_time"])),
        }

        if not is_allowed:
            headers["Retry-After"] = str(info["wait_time"])

        return headers


# Instance globale du rate limiter
rate_limiter = RateLimiter()


def rate_limit(route_name: str):
    """Décorateur pour appliquer le rate limiting à une route"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Vérifier le rate limiting
            is_allowed, info = rate_limiter.is_allowed(route_name)

            if not is_allowed:
                headers = rate_limiter.get_rate_limit_headers(route_name)
                return (
                    jsonify(
                        {
                            "error": "Rate limit exceeded",
                            "message": f'Too many requests. Limit: {info["limit"]} requests per {info["window_duration"]} seconds',
                            "retry_after": info["wait_time"],
                            "limit": info["limit"],
                            "remaining": info["remaining"],
                            "reset_time": info["reset_time"],
                        }
                    ),
                    429,
                    headers,
                )

            # Ajouter les headers de rate limiting à la réponse
            response = f(*args, **kwargs)
            headers = rate_limiter.get_rate_limit_headers(route_name)

            # Gérer tous les types de réponses Flask
            if isinstance(response, tuple):
                # Tuple (content, status_code) ou (content, status_code, headers)
                if len(response) == 2:
                    return response[0], response[1], headers
                elif len(response) == 3:
                    # Fusionner avec les headers existants
                    existing_headers = (
                        response[2] if isinstance(response[2], dict) else {}
                    )
                    existing_headers.update(headers)
                    return response[0], response[1], existing_headers
                else:
                    return response
            else:
                # Objet Response Flask ou autre
                from flask import Response as FlaskResponse

                if isinstance(response, FlaskResponse):
                    # Ajouter les headers à l'objet Response
                    for key, value in headers.items():
                        response.headers[key] = value
                    return response
                else:
                    # Pour jsonify() et autres, créer une nouvelle Response avec headers
                    from flask import make_response

                    resp = make_response(response)
                    for key, value in headers.items():
                        resp.headers[key] = value
                    return resp

        return decorated_function

    return decorator


def get_rate_limit_info(route_name: str) -> Dict:
    """Obtenir les informations de rate limiting pour une route"""
    is_allowed, info = rate_limiter.is_allowed(route_name)
    return {
        "route": route_name,
        "allowed": is_allowed,
        "limit": info["limit"],
        "remaining": info["remaining"],
        "reset_time": info["reset_time"],
        "window_duration": info["window_duration"],
    }
