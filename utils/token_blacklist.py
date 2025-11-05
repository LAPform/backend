"""
Système de révocation de tokens (Token Blacklist)
Expert Cybersécurité - 15+ ans d'expérience

Permet de révoquer immédiatement les tokens compromis
sans attendre leur expiration naturelle.

Storage: SQLite avec TTL automatique (cleanup)
"""

import sqlite3
import time
import hashlib
import threading
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class TokenBlacklist:
    """
    Blacklist de tokens révoqués avec persistance SQLite

    Fonctionnalités:
    - Révocation immédiate de tokens
    - Cleanup automatique des tokens expirés
    - Thread-safe pour utilisation en production
    - Audit trail des révocations
    """

    def __init__(self, db_path="data/token_blacklist.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._init_database()

    def _get_connection(self):
        """Obtenir une connexion thread-safe à la base de données"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            # Créer le dossier data si nécessaire
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

            self._local.connection = sqlite3.connect(
                self.db_path,
                timeout=10,
                check_same_thread=False
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_database(self):
        """Initialiser la base de données de blacklist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Table pour stocker les tokens révoqués
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklisted_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_hash TEXT UNIQUE NOT NULL,
                user_id TEXT,
                revoked_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                reason TEXT,
                revoked_by TEXT,
                ip_address TEXT
            )
        """)

        # Index pour optimiser les requêtes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blacklist_token_hash
            ON blacklisted_tokens(token_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blacklist_expires_at
            ON blacklisted_tokens(expires_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_blacklist_user_id
            ON blacklisted_tokens(user_id)
        """)

        conn.commit()
        logger.info("Token blacklist database initialized")

    def _hash_token(self, token: str) -> str:
        """
        Hasher le token avant stockage

        Sécurité: On ne stocke JAMAIS les tokens en clair
        Même dans la blacklist, on stocke seulement le hash
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def revoke_token(
        self,
        token: str,
        user_id: Optional[str] = None,
        expires_at: Optional[float] = None,
        reason: Optional[str] = None,
        revoked_by: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Révoquer un token immédiatement

        Args:
            token: Le token à révoquer
            user_id: ID de l'utilisateur (optionnel)
            expires_at: Timestamp d'expiration du token (pour cleanup auto)
            reason: Raison de la révocation (audit)
            revoked_by: Qui a révoqué le token (audit)
            ip_address: IP de la requête (audit)

        Returns:
            True si révocation réussie, False sinon
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            token_hash = self._hash_token(token)
            current_time = time.time()

            # Si pas d'expiration fournie, définir à 24h par défaut
            if expires_at is None:
                expires_at = current_time + 86400  # 24 heures

            cursor.execute("""
                INSERT OR REPLACE INTO blacklisted_tokens
                (token_hash, user_id, revoked_at, expires_at, reason, revoked_by, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (token_hash, user_id, current_time, expires_at, reason, revoked_by, ip_address))

            conn.commit()

            logger.info(
                f"Token revoked: user_id={user_id}, reason={reason}, "
                f"revoked_by={revoked_by}, ip={ip_address}"
            )

            return True

        except Exception as e:
            logger.error(f"Error revoking token: {e}", exc_info=True)
            return False

    def is_blacklisted(self, token: str) -> bool:
        """
        Vérifier si un token est dans la blacklist

        Returns:
            True si le token est révoqué, False sinon
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            token_hash = self._hash_token(token)
            current_time = time.time()

            # Chercher le token dans la blacklist (non expiré)
            cursor.execute("""
                SELECT id FROM blacklisted_tokens
                WHERE token_hash = ?
                AND expires_at > ?
                LIMIT 1
            """, (token_hash, current_time))

            result = cursor.fetchone()
            is_blacklisted = result is not None

            if is_blacklisted:
                logger.warning(f"Blacklisted token attempted to be used")

            return is_blacklisted

        except Exception as e:
            logger.error(f"Error checking blacklist: {e}", exc_info=True)
            # En cas d'erreur, on assume que le token n'est pas blacklisté
            # (fail open pour ne pas bloquer le service)
            return False

    def revoke_all_user_tokens(self, user_id: str, reason: Optional[str] = None) -> int:
        """
        Révoquer tous les tokens d'un utilisateur

        Utile quand:
        - Changement de mot de passe
        - Compte compromis
        - Déconnexion de tous les appareils

        Returns:
            Nombre de tokens révoqués
        """
        try:
            # Cette fonction est conceptuelle car on ne stocke pas les tokens actifs
            # Dans une vraie implémentation, il faudrait:
            # 1. Soit stocker tous les tokens actifs
            # 2. Soit utiliser un "token generation ID" qui change à la révocation

            # Pour l'instant, on log juste l'intention
            logger.info(f"Revoke all tokens requested for user_id={user_id}, reason={reason}")

            # Une approche alternative: incrémenter un "token_version" dans la table users
            # et vérifier que le token contient la bonne version

            return 0  # Placeholder

        except Exception as e:
            logger.error(f"Error revoking all user tokens: {e}", exc_info=True)
            return 0

    def cleanup_expired(self) -> int:
        """
        Nettoyer les tokens expirés de la blacklist

        Cette fonction doit être appelée périodiquement (cron job ou background task)

        Returns:
            Nombre de tokens supprimés
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            current_time = time.time()

            cursor.execute("""
                DELETE FROM blacklisted_tokens
                WHERE expires_at < ?
            """, (current_time,))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired blacklisted tokens")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up blacklist: {e}", exc_info=True)
            return 0

    def get_stats(self) -> dict:
        """
        Obtenir les statistiques de la blacklist

        Utile pour monitoring et debugging
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            current_time = time.time()

            # Nombre total de tokens blacklistés actifs
            cursor.execute("""
                SELECT COUNT(*) as total FROM blacklisted_tokens
                WHERE expires_at > ?
            """, (current_time,))
            total_active = cursor.fetchone()['total']

            # Nombre total incluant expirés
            cursor.execute("SELECT COUNT(*) as total FROM blacklisted_tokens")
            total_all = cursor.fetchone()['total']

            # Nombre d'utilisateurs uniques avec tokens révoqués
            cursor.execute("""
                SELECT COUNT(DISTINCT user_id) as unique_users FROM blacklisted_tokens
                WHERE expires_at > ?
                AND user_id IS NOT NULL
            """, (current_time,))
            unique_users = cursor.fetchone()['unique_users']

            return {
                "total_active_blacklisted": total_active,
                "total_all_time": total_all,
                "unique_users": unique_users,
                "storage": "SQLite (persistent)",
                "status": "healthy"
            }

        except Exception as e:
            logger.error(f"Error getting blacklist stats: {e}", exc_info=True)
            return {"error": str(e), "status": "error"}


# Instance globale de la blacklist
token_blacklist = TokenBlacklist()


def check_token_blacklist(token: str) -> bool:
    """
    Helper function pour vérifier rapidement si un token est blacklisté

    Returns:
        True si le token est révoqué (blacklisté)
    """
    return token_blacklist.is_blacklisted(token)


def revoke_token(token: str, **kwargs) -> bool:
    """
    Helper function pour révoquer rapidement un token

    Returns:
        True si révocation réussie
    """
    return token_blacklist.revoke_token(token, **kwargs)
