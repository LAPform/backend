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

        # Configuration des limites par route (PRODUCTION - LIMITES SÉCURISÉES)
        self.limits = {
            # Routes d'authentification (strictes)
            "auth_register": {"requests": 5, "window": 300},  # 5 req/5min
            "auth_login": {"requests": 10, "window": 300},  # 10 req/5min
            "auth_verify": {"requests": 20, "window": 300},  # 20 req/5min
            "auth_signup": {"requests": 5, "window": 300},  # 5 req/5min
            "auth_signin": {"requests": 10, "window": 300},  # 10 req/5min
            "auth_me": {"requests": 30, "window": 300},  # 30 req/5min
            
            # Routes de formulaires (modérées)
            "forms_create": {"requests": 20, "window": 3600},  # 20 req/h
            "forms_get": {"requests": 100, "window": 3600},  # 100 req/h
            "forms_update": {"requests": 30, "window": 3600},  # 30 req/h
            "forms_delete": {"requests": 10, "window": 3600},  # 10 req/h
            "forms_stats": {"requests": 50, "window": 3600},  # 50 req/h
            
            # Routes de questions (modérées)
            "questions_create": {"requests": 50, "window": 3600},  # 50 req/h
            "questions_get": {"requests": 200, "window": 3600},  # 200 req/h
            "questions_update": {"requests": 50, "window": 3600},  # 50 req/h
            "questions_delete": {"requests": 20, "window": 3600},  # 20 req/h
            
            # Routes de réponses (plus permissives pour soumission publique)
            "responses_submit": {"requests": 100, "window": 3600},  # 100 req/h
            "responses_get": {"requests": 200, "window": 3600},  # 200 req/h
            
            # Routes de fichiers (strictes)
            "files_upload": {"requests": 20, "window": 3600},  # 20 req/h
            "files_download": {"requests": 100, "window": 3600},  # 100 req/h
            
            # Routes de monitoring (strictes)
            "monitoring_performance": {"requests": 30, "window": 3600},  # 30 req/h
            "monitoring_health": {"requests": 60, "window": 3600},  # 60 req/h
            "monitoring_system": {"requests": 10, "window": 3600},  # 10 req/h (admin)
            "monitoring_dashboard": {"requests": 50, "window": 3600},  # 50 req/h
            
            # Routes générales
            "health": {"requests": 1000, "window": 3600},  # 1000 req/h
            "default": {"requests": 100, "window": 3600},  # 100 req/h par défaut
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
            if isinstance(response, tuple) and len(response) >= 2:
                # Si c'est une réponse avec status code
                headers = rate_limiter.get_rate_limit_headers(route_name)
                if len(response) == 2:
                    return response[0], response[1], headers
                else:
                    # Fusionner avec les headers existants
                    existing_headers = response[2] if len(response) > 2 else {}
                    existing_headers.update(headers)
                    return response[0], response[1], existing_headers
            else:
                # Si c'est juste la réponse
                return response

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
