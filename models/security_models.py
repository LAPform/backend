"""
Modèles Flask-Security-Too pour FormForge
"""

from flask_security import UserMixin, RoleMixin
from models.database import DatabaseManager
import json


class User(UserMixin):
    """Modèle utilisateur pour Flask-Security-Too"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_id(self):
        """Retourner l'ID de l'utilisateur pour Flask-Login"""
        return self.id

    @property
    def is_active(self):
        """Vérifier si l'utilisateur est actif"""
        return True

    @property
    def is_authenticated(self):
        """Vérifier si l'utilisateur est authentifié"""
        return True

    @property
    def is_anonymous(self):
        """Vérifier si l'utilisateur est anonyme"""
        return False

    def get_security_payload(self):
        """Payload pour Flask-Security"""
        return {"id": self.id, "email": self.email, "name": self.name}


class Role(RoleMixin):
    """Modèle de rôle pour Flask-Security-Too"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager


class SecurityUserDatastore:
    """Datastore personnalisé pour Flask-Security-Too avec SQLite"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def find_user(self, **kwargs):
        """Trouver un utilisateur par critères"""
        if "id" in kwargs:
            return self._get_user_by_id(kwargs["id"])
        elif "email" in kwargs:
            return self._get_user_by_email(kwargs["email"])
        return None

    def _get_user_by_id(self, user_id: str):
        """Récupérer un utilisateur par ID"""
        query = "SELECT * FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,), fetch=True)

        if results and len(results) > 0:
            user_data = results[0]
            user = User(self.db)
            user.id = user_data["id"]
            user.email = user_data["email"]
            user.name = user_data.get("name", "")
            user.password_hash = user_data["password_hash"]
            user.salt = user_data["salt"]
            user.created_at = user_data["created_at"]
            user.last_login = user_data.get("last_login")
            return user
        return None

    def _get_user_by_email(self, email: str):
        """Récupérer un utilisateur par email"""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.db.execute_query(query, (email.lower(),), fetch=True)

        if results and len(results) > 0:
            user_data = results[0]
            user = User(self.db)
            user.id = user_data["id"]
            user.email = user_data["email"]
            user.name = user_data.get("name", "")
            user.password_hash = user_data["password_hash"]
            user.salt = user_data["salt"]
            user.created_at = user_data["created_at"]
            user.last_login = user_data.get("last_login")
            return user
        return None

    def create_user(self, **kwargs):
        """Créer un nouvel utilisateur"""
        from models.user import User as UserModel
        import uuid
        import hashlib
        import secrets

        user_id = str(uuid.uuid4())
        email = kwargs.get("email", "").lower().strip()
        password = kwargs.get("password", "")
        name = kwargs.get("name", "")

        # Générer un salt et hasher le mot de passe
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100000
        )
        password_hash = password_hash.hex()

        # Insérer dans la base de données
        query = """
            INSERT INTO users (id, email, password_hash, salt, name)
            VALUES (?, ?, ?, ?, ?)
        """

        self.db.execute_query(query, (user_id, email, password_hash, salt, name))

        # Créer l'objet utilisateur
        user = User(self.db)
        user.id = user_id
        user.email = email
        user.name = name
        user.password_hash = password_hash
        user.salt = salt
        return user

    def verify_password(self, user, password: str) -> bool:
        """Vérifier le mot de passe d'un utilisateur"""
        import hashlib

        if not user or not hasattr(user, "password_hash") or not hasattr(user, "salt"):
            return False

        # Hasher le mot de passe fourni avec le salt de l'utilisateur
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), user.salt.encode(), 100000
        )
        password_hash = password_hash.hex()

        return password_hash == user.password_hash

    def update_last_login(self, user):
        """Mettre à jour la dernière connexion"""
        from datetime import datetime

        query = "UPDATE users SET last_login = ? WHERE id = ?"
        self.db.execute_query(query, (datetime.utcnow().isoformat(), user.id))

    def find_role(self, role):
        """Trouver un rôle (non implémenté pour le POC)"""
        return None

    def create_role(self, **kwargs):
        """Créer un rôle (non implémenté pour le POC)"""
        return None

    def add_role_to_user(self, user, role):
        """Ajouter un rôle à un utilisateur (non implémenté pour le POC)"""
        pass

    def remove_role_from_user(self, user, role):
        """Retirer un rôle d'un utilisateur (non implémenté pour le POC)"""
        pass

    def get_user_roles(self, user):
        """Récupérer les rôles d'un utilisateur (non implémenté pour le POC)"""
        return []
