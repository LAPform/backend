"""
Système d'authentification avec Flask-Security-Too et tokens SHA256 stateless
"""

from flask import request, jsonify, current_app
from flask_security import current_user, login_user, logout_user
from functools import wraps
import logging
import hashlib
import time
from datetime import datetime, timedelta
from utils.audit_logger import audit_logger

logger = logging.getLogger(__name__)


def require_auth(f):
    """Décorateur pour protéger les routes avec tokens SHA256 stateless"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"🔍 AUTH: Début authentification pour route: {request.endpoint}")
        logger.info(f"🔍 AUTH: Méthode: {request.method}, URL: {request.url}")

        # 0) Accepter la session Flask-Security-Too (cookie) si déjà authentifié
        try:
            if current_user.is_authenticated and hasattr(current_user, "id"):
                logger.info(
                    f"🔍 AUTH: Session FST détectée - user_id={current_user.id}"
                )
                kwargs["authenticated_user_id"] = current_user.id
                return f(*args, **kwargs)
        except Exception as e:
            logger.warning(f"🔍 AUTH: Impossible d'utiliser current_user: {e}")

        # Vérifier le header Authorization ou récupérer token via fallback (query/body)
        auth_header = request.headers.get("Authorization")
        logger.info(
            f"🔍 AUTH: Header Authorization: {auth_header[:20] if auth_header else 'None'}..."
        )

        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Fallback: query param ?token=... ou corps JSON {"token": "..."}
            token = request.args.get("token")
            if not token and request.method in ["POST", "PUT", "PATCH"]:
                body = None
                try:
                    body = request.get_json(silent=True)
                except Exception:
                    body = None
                if isinstance(body, dict):
                    token = body.get("token")

        if not token:
            logger.warning(f"🔍 AUTH: Aucun token fourni (header/query/body)")
            audit_logger.log_security_event(
                event_type="unauthorized_access_attempt",
                details={
                    "reason": "missing_token",
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "ip": request.remote_addr,
                },
                severity="medium",
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Authentification requise",
                        "message": "Token manquant (Authorization/paramètre token/corps)",
                    }
                ),
                401,
            )
        logger.info(f"🔍 AUTH: Token extrait: {token[:10]}...{token[-10:]}")

        # Vérifier le format du token (64 caractères hex pour SHA256)
        if len(token) != 64:
            logger.warning(
                f"🔍 AUTH: Token de longueur invalide: {len(token)} caractères"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Format de token invalide",
                        "message": "Token malformé",
                    }
                ),
                401,
            )

        try:
            logger.info(f"🔍 AUTH: Début validation du token")

            # Vérifier que l'utilisateur existe toujours
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)
            logger.info(f"🔍 AUTH: SecurityUserDatastore initialisé")

            # Vérifier si le token est valide et non expiré
            user_id = _validate_sha256_token(token)
            logger.info(f"🔍 AUTH: Résultat validation token: user_id = {user_id}")

            if not user_id:
                logger.warning(f"🔍 AUTH: Token invalide ou expiré")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Token invalide ou expiré",
                            "message": "Token non reconnu ou expiré",
                        }
                    ),
                    401,
                )

            # Vérifier que l'utilisateur existe toujours
            logger.info(f"🔍 AUTH: Vérification existence utilisateur: {user_id}")
            user = datastore.find_user(id=user_id)
            logger.info(f"🔍 AUTH: Utilisateur trouvé: {user is not None}")

            if not user:
                logger.warning(f"🔍 AUTH: Utilisateur non trouvé en base")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Utilisateur non trouvé",
                            "message": "L'utilisateur n'existe plus",
                        }
                    ),
                    401,
                )

            # Stocker l'user_id dans les kwargs pour l'utiliser dans la fonction
            kwargs["authenticated_user_id"] = user_id
            logger.info(f"🔍 AUTH: Authentification réussie pour user_id: {user_id}")
            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"🔍 AUTH: Erreur authentification: {e}")
            import traceback

            logger.error(f"🔍 AUTH: Traceback: {traceback.format_exc()}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Erreur d'authentification",
                        "message": "Erreur interne du serveur",
                    }
                ),
                500,
            )

    return decorated_function


def _validate_sha256_token(token):
    """Valider un token SHA256 et retourner l'user_id"""
    try:
        logger.info(f"🔍 AUTH: Début validation token SHA256")
        logger.info(f"🔍 AUTH: Token reçu: {token[:10]}...{token[-10:]}")

        from models.database import DatabaseManager

        db = DatabaseManager()
        logger.info(f"🔍 AUTH: DatabaseManager initialisé")

        # Vérifier si la table active_tokens existe
        try:
            # Test de l'existence de la table
            db.execute_query("SELECT COUNT(*) FROM active_tokens LIMIT 1", fetch=True)
            logger.info(f"🔍 AUTH: Table active_tokens existe")
        except Exception as table_error:
            # Table n'existe pas, la créer
            logger.info(f"🔍 AUTH: Table active_tokens n'existe pas, création en cours")
            logger.info(f"🔍 AUTH: Erreur table: {table_error}")
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS active_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """
            )
            logger.info(f"🔍 AUTH: Table active_tokens créée avec succès")

        # Nettoyer les tokens expirés (maintenance)
        try:
            deleted_count = db.execute_query(
                "DELETE FROM active_tokens WHERE expires_at <= datetime('now')"
            )
            logger.info(
                f"🔍 AUTH: Nettoyage tokens expirés - {deleted_count} tokens supprimés"
            )
        except Exception as cleanup_error:
            logger.warning(f"🔍 AUTH: Erreur nettoyage tokens expirés: {cleanup_error}")

        # Vérifier si le token existe et n'est pas expiré
        query = """
            SELECT user_id, expires_at 
            FROM active_tokens 
            WHERE token = ? AND expires_at > datetime('now')
        """

        logger.info(f"🔍 AUTH: Exécution requête de validation")
        result = db.execute_query(query, (token,), fetch=True)
        logger.info(f"🔍 AUTH: Résultat requête: {result}")

        if result and len(result) > 0:
            user_id = result[0]["user_id"]
            expires_at = result[0]["expires_at"]
            logger.info(
                f"🔍 AUTH: Token valide trouvé - user_id: {user_id}, expires_at: {expires_at}"
            )
            return user_id

        logger.warning(f"🔍 AUTH: Token non trouvé ou expiré")
        return None

    except Exception as e:
        logger.error(f"🔍 AUTH: Erreur validation token: {e}")
        import traceback

        logger.error(f"🔍 AUTH: Traceback: {traceback.format_exc()}")
        return None


def require_ownership(f):
    """Décorateur pour vérifier la propriété d'un formulaire"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"success": False, "error": "Authentification requise"}), 401

        # Vérifier la propriété du formulaire si form_id est dans les kwargs
        if "form_id" in kwargs:
            from models.form import Form

            form_model = Form(current_app.db)
            form = form_model.get_by_id(kwargs["form_id"])

            if not form:
                return (
                    jsonify({"success": False, "error": "Formulaire non trouvé"}),
                    404,
                )

            if form.get("created_by") != current_user.id:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Accès non autorisé",
                            "message": "Vous n'avez pas les droits sur ce formulaire",
                        }
                    ),
                    403,
                )

        return f(*args, **kwargs)

    return decorated_function


class SecurityAuthManager:
    """Gestionnaire d'authentification avec Flask-Security-Too"""

    @staticmethod
    def get_current_user():
        """Récupérer l'utilisateur actuel"""
        if current_user.is_authenticated:
            return {
                "id": current_user.id,
                "email": current_user.email,
                "name": getattr(current_user, "name", ""),
                "created_at": getattr(current_user, "created_at", ""),
                "last_login": getattr(current_user, "last_login", ""),
            }
        return None

    # Fonctions login_user_safe et logout_user_safe supprimées - non utilisées

    @staticmethod
    def create_user_response(user):
        """Créer une réponse JSON pour un utilisateur"""
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": getattr(user, "name", ""),
                "created_at": getattr(user, "created_at", ""),
                "last_login": getattr(user, "last_login", ""),
            },
        }

    @staticmethod
    def create_error_response(message, status_code=400):
        """Créer une réponse d'erreur standardisée"""
        return jsonify({"success": False, "error": message}), status_code

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Valider la force d'un mot de passe"""
        import re

        if len(password) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caractères"

        if not re.search(r"[A-Z]", password):
            return False, "Le mot de passe doit contenir au moins une majuscule"

        if not re.search(r"[a-z]", password):
            return False, "Le mot de passe doit contenir au moins une minuscule"

        if not re.search(r"\d", password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial"

        return True, "Mot de passe valide"

    @staticmethod
    def validate_email(email: str) -> bool:
        """Valider un email"""
        import re

        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None
