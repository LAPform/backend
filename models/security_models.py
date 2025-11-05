"""
Modèles Flask-Security-Too pour FormForge
"""

from flask_security import UserMixin, RoleMixin
from models.database import DatabaseManager
import json


class User(UserMixin):
    """Modèle utilisateur pour Flask-Security-Too"""

    # Attribut de classe attendu par Flask-Security-Too >= 4.0
    fs_uniquifier = None

    def __init__(self):
        # Pas de paramètre - Flask-Security-Too gère l'instanciation
        # Attribut requis par Flask-Security-Too >= 4.0
        self.fs_uniquifier = None

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

    # Compat FST: méthode d'accès au fs_uniquifier
    def get_fs_uniquifier(self):
        return getattr(self, "fs_uniquifier", None)

    def get_auth_token(self):
        """
        Générer un token d'authentification signé avec itsdangerous
        Le token contient l'ID utilisateur et le fs_uniquifier pour permettre la révocation
        """
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(
            {
                'id': self.id,
                'fs_uniquifier': self.fs_uniquifier or self.id
            },
            salt='auth-token-salt'
        )

    @staticmethod
    def verify_auth_token(token, max_age=3600):
        """
        Vérifier et décoder un token d'authentification
        Retourne l'ID utilisateur si valide, None sinon
        max_age en secondes (défaut: 1h)
        """
        from flask import current_app
        from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            data = serializer.loads(token, salt='auth-token-salt', max_age=max_age)
            return data.get('id')
        except (SignatureExpired, BadSignature):
            return None


class Role(RoleMixin):
    """Modèle de rôle pour Flask-Security-Too"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_by_name(self, name: str):
        query = "SELECT * FROM roles WHERE name = ?"
        results = self.db.execute_query(query, (name,), fetch=True)
        return results[0] if results else None


class SecurityUserDatastore:
    """Datastore personnalisé pour Flask-Security-Too avec SQLite"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        import logging

        self.logger = logging.getLogger(__name__)
        self.logger.info("SecurityUserDatastore initialisé")

    # --- Compatibilité Flask-Security-Too ---
    @property
    def user_model(self):
        """Retourne le modèle utilisateur (wrapper minimal)"""
        return User

    @property
    def role_model(self):
        """Retourne le modèle rôle (wrapper minimal)"""
        return Role

    def get_user(self, identifier: str):
        """API FST: récupérer un utilisateur par identifiant (email ou id)"""
        try:
            if identifier and "@" in str(identifier):
                return self._get_user_by_email(identifier)
            return self._get_user_by_id(identifier)
        except Exception as e:
            self.logger.error(f"Erreur get_user: {e}")
            return None

    def commit(self):
        """API FST: no-op (transactions déjà commitées au niveau des méthodes)"""
        return True

    def find_user(self, **kwargs):
        """Trouver un utilisateur par critères"""
        self.logger.info(f"find_user appelé avec: {kwargs}")
        try:
            if "id" in kwargs:
                result = self._get_user_by_id(kwargs["id"])
                self.logger.info(f"Utilisateur trouvé par ID: {result is not None}")
                return result
            elif "email" in kwargs:
                result = self._get_user_by_email(kwargs["email"])
                self.logger.info(f"Utilisateur trouvé par email: {result is not None}")
                return result
            self.logger.warning("Aucun critère de recherche valide")
            return None
        except Exception as e:
            self.logger.error(f"Erreur dans find_user: {e}")
            raise

    def _get_user_by_id(self, user_id: str):
        """Récupérer un utilisateur par ID"""
        query = "SELECT * FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,), fetch=True)

        if results and len(results) > 0:
            user_data = results[0]
            user = User()
            user.id = user_data["id"]
            user.email = user_data["email"]
            user.name = user_data.get("name", "")
            user.password_hash = user_data["password_hash"]
            user.salt = user_data["salt"]
            user.created_at = user_data["created_at"]
            user.last_login = user_data.get("last_login")
            user.fs_uniquifier = user_data.get("fs_uniquifier")
            # Attributs de tracking Flask-Security-Too
            user.current_login_at = user_data.get("current_login_at")
            user.last_login_at = user_data.get("last_login_at")
            user.current_login_ip = user_data.get("current_login_ip")
            user.last_login_ip = user_data.get("last_login_ip")
            user.login_count = user_data.get("login_count", 0)
            return user
        return None

    def _get_user_by_email(self, email: str):
        """Récupérer un utilisateur par email"""
        query = "SELECT * FROM users WHERE email = ?"
        results = self.db.execute_query(query, (email.lower(),), fetch=True)

        if results and len(results) > 0:
            user_data = results[0]
            user = User()
            user.id = user_data["id"]
            user.email = user_data["email"]
            user.name = user_data.get("name", "")
            user.password_hash = user_data["password_hash"]
            user.salt = user_data["salt"]
            user.created_at = user_data["created_at"]
            user.last_login = user_data.get("last_login")
            user.fs_uniquifier = user_data.get("fs_uniquifier")
            # Attributs de tracking Flask-Security-Too
            user.current_login_at = user_data.get("current_login_at")
            user.last_login_at = user_data.get("last_login_at")
            user.current_login_ip = user_data.get("current_login_ip")
            user.last_login_ip = user_data.get("last_login_ip")
            user.login_count = user_data.get("login_count", 0)
            return user
        return None

    def create_user(self, **kwargs):
        """Créer un nouvel utilisateur - Version simplifiée"""
        self.logger.info(f"create_user appelé avec: {kwargs}")
        try:
            import uuid
            import secrets
            from passlib.hash import pbkdf2_sha256

            user_id = str(uuid.uuid4())
            email = kwargs.get("email", "").lower().strip()
            password = kwargs.get("password", "")
            name = kwargs.get("name", "")

            self.logger.info(f"Création utilisateur: {email}, {name}")

            # Générer un salt (stocké pour compat DB) et hasher le mot de passe via passlib
            self.logger.info("Génération du hash du mot de passe via passlib...")
            salt = secrets.token_hex(16)
            password_hash = pbkdf2_sha256.hash(password)
            self.logger.info("Hash généré avec succès")

            # Insérer dans la base de données
            query = """
                INSERT INTO users (id, email, password_hash, salt, name, fs_uniquifier)
                VALUES (?, ?, ?, ?, ?, ?)
            """

            self.logger.info("Exécution de la requête d'insertion...")
            # Générer fs_uniquifier requis par FST (valeur stable unique)
            fs_uniquifier = secrets.token_urlsafe(32)

            self.db.execute_query(
                query, (user_id, email, password_hash, salt, name, fs_uniquifier)
            )
            self.logger.info("Utilisateur inséré en base avec succès")

            # Créer l'objet utilisateur
            self.logger.info("Création de l'objet utilisateur...")
            user = User()
            user.id = user_id
            user.email = email
            user.name = name
            user.password_hash = password_hash
            user.salt = salt
            user.fs_uniquifier = fs_uniquifier
            # Initialiser les attributs de tracking
            user.current_login_at = None
            user.last_login_at = None
            user.current_login_ip = None
            user.last_login_ip = None
            user.login_count = 0
            self.logger.info(f"Utilisateur créé avec succès: {user_id}")

            # Attribuer par défaut le rôle 'creator' sauf indication contraire
            try:
                default_roles = kwargs.get("roles")
                if not default_roles:
                    self.create_role(
                        name="creator", description="Créateur de questionnaire"
                    )
                    self.add_role_to_user(user, "creator")
                else:
                    # Associer les rôles passés
                    for role_name in default_roles:
                        self.create_role(name=role_name)
                        self.add_role_to_user(user, role_name)
            except Exception as role_e:
                self.logger.warning(f"Attribution rôle par défaut échouée: {role_e}")
            return user
        except Exception as e:
            # Logger l'erreur pour debug
            self.logger.error(f"Erreur création utilisateur: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    def verify_password(self, user, password: str) -> bool:
        """Vérifier le mot de passe d'un utilisateur"""
        from passlib.hash import pbkdf2_sha256

        if not user or not hasattr(user, "password_hash"):
            return False

        # Vérifier via passlib (salt inclus dans le hash stocké)
        try:
            return pbkdf2_sha256.verify(password, user.password_hash)
        except Exception:
            return False

    def update_last_login(self, user):
        """Mettre à jour la dernière connexion"""
        from datetime import datetime

        query = "UPDATE users SET last_login = ? WHERE id = ?"
        self.db.execute_query(query, (datetime.utcnow().isoformat(), user.id))

    def find_role(self, role):
        """Trouver un rôle par nom"""
        try:
            query = "SELECT * FROM roles WHERE name = ?"
            results = self.db.execute_query(query, (role,), fetch=True)
            return results[0] if results else None
        except Exception:
            return None

    def create_role(self, **kwargs):
        """Créer un rôle si absent"""
        try:
            import uuid

            role_id = str(uuid.uuid4())
            name = kwargs.get("name")
            description = kwargs.get("description", "")
            if not name:
                return None

            existing = self.find_role(name)
            if existing:
                return existing

            query = """
                INSERT INTO roles (id, name, description)
                VALUES (?, ?, ?)
            """
            self.db.execute_query(query, (role_id, name, description))
            return {"id": role_id, "name": name, "description": description}
        except Exception:
            return None

    def add_role_to_user(self, user, role):
        """Associer un rôle à un utilisateur"""
        try:
            # role peut être un nom ou un dict
            role_row = self.find_role(role) if isinstance(role, str) else role
            if not role_row:
                role_row = self.create_role(name=str(role))
            if not role_row:
                return False

            query = """
                INSERT OR IGNORE INTO user_roles (user_id, role_id)
                VALUES (?, ?)
            """
            self.db.execute_query(query, (user.id, role_row["id"]))
            return True
        except Exception:
            return False

    def remove_role_from_user(self, user, role):
        """Dissocier un rôle d'un utilisateur"""
        try:
            role_row = self.find_role(role) if isinstance(role, str) else role
            if not role_row:
                return False
            query = "DELETE FROM user_roles WHERE user_id = ? AND role_id = ?"
            self.db.execute_query(query, (user.id, role_row["id"]))
            return True
        except Exception:
            return False

    def get_user_roles(self, user):
        """Récupérer les rôles d'un utilisateur"""
        try:
            query = """
                SELECT r.name FROM roles r
                JOIN user_roles ur ON ur.role_id = r.id
                WHERE ur.user_id = ?
            """
            results = self.db.execute_query(query, (user.id,), fetch=True)
            return [row["name"] for row in results] if results else []
        except Exception:
            return []

    def update_user_password(self, user, new_password: str):
        """Mettre à jour le mot de passe d'un utilisateur"""
        from passlib.hash import pbkdf2_sha256

        try:
            new_hash = pbkdf2_sha256.hash(new_password)
            query = "UPDATE users SET password_hash = ? WHERE id = ?"
            self.db.execute_query(query, (new_hash, user.id))
            user.password_hash = new_hash
            return True
        except Exception:
            return False
