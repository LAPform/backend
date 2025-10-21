"""
Modèle User pour FormForge
"""

import uuid
import hashlib
import secrets
from typing import Optional, Dict
from datetime import datetime, timedelta
from .database import DatabaseManager


class User:
    """Modèle pour les utilisateurs"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, email: str, password: str, name: str = None) -> str:
        """Créer un nouvel utilisateur"""
        user_id = str(uuid.uuid4())

        # Hacher le mot de passe
        salt = secrets.token_hex(16)
        hashed_password = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        )

        query = """
            INSERT INTO users (id, email, password_hash, salt, name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query, (user_id, email, hashed_password.hex(), salt, name, datetime.now())
        )
        return user_id

    def get_by_email(self, email: str) -> Optional[Dict]:
        """Récupérer un utilisateur par email"""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.db.execute_query(query, (email,), fetch=True)

        if results and len(results) > 0:
            return results[0]
        return None

    def get_by_id(self, user_id: str) -> Optional[Dict]:
        """Récupérer un utilisateur par ID"""
        query = "SELECT * FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,), fetch=True)

        if results and len(results) > 0:
            return results[0]
        return None

    def verify_password(self, email: str, password: str) -> Optional[Dict]:
        """Vérifier le mot de passe d'un utilisateur"""
        user = self.get_by_email(email)
        if not user:
            return None

        # Vérifier le mot de passe
        salt = user["salt"]
        hashed_password = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        )

        if hashed_password.hex() == user["password_hash"]:
            return user
        return None

    def update_last_login(self, user_id: str) -> bool:
        """Mettre à jour la dernière connexion"""
        query = "UPDATE users SET last_login = ? WHERE id = ?"
        rows_affected = self.db.execute_query(query, (datetime.now(), user_id))
        return rows_affected > 0

    def get_user_forms(self, user_id: str) -> list:
        """Récupérer les formulaires d'un utilisateur"""
        query = """
            SELECT * FROM forms 
            WHERE created_by = ? 
            ORDER BY created_at DESC
        """
        results = self.db.execute_query(query, (user_id,), fetch=True)
        return results if results else []
