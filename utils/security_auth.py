"""
Système d'authentification avec Flask-Security-Too uniquement
"""

from flask import request, jsonify, current_app
from flask_security import current_user
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """Décorateur pour protéger les routes avec système de session manuel"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request, session
        import hashlib
        import time

        # Vérifier la session manuelle
        user_id = session.get("user_id")
        user_token = session.get("user_token")
        token_timestamp = session.get("token_timestamp", 0)
        current_time = int(time.time())

        # NOUVELLE FONCTIONNALITÉ : Rotation automatique des tokens
        if user_id and user_token and token_timestamp:
            # Renouveler le token s'il a plus de 30 minutes
            if current_time - token_timestamp > 1800:  # 30 minutes
                # Créer un nouveau token
                user_email = session.get("user_email", "")
                new_timestamp = current_time
                new_token_data = f"{user_id}:{user_email}:{new_timestamp}"
                new_token = hashlib.sha256(new_token_data.encode()).hexdigest()

                # Mettre à jour la session
                session["user_token"] = new_token
                session["token_timestamp"] = new_timestamp

                # Log de la rotation
                logger.info(
                    f"Token renouvelé automatiquement pour l'utilisateur {user_id}"
                )

        # Vérifier l'authentification via session ou token
        if not user_id or not user_token:
            # Vérifier le header Authorization si pas de session
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                if len(token) == 64:  # SHA256 = 64 caractères hex
                    if session.get("user_token") == token:
                        user_id = session.get("user_id")
                        # Vérifier l'expiration (1 heure)
                        if current_time - token_timestamp > 3600:  # Token expiré
                            session.pop("user_id", None)
                            session.pop("user_token", None)
                            session.pop("token_timestamp", None)
                            return (
                                jsonify(
                                    {
                                        "success": False,
                                        "error": "Token expiré",
                                        "message": "Votre session a expiré, veuillez vous reconnecter",
                                    }
                                ),
                                401,
                            )
                    else:
                        return (
                            jsonify(
                                {
                                    "success": False,
                                    "error": "Token invalide",
                                    "message": "Token non reconnu",
                                }
                            ),
                            401,
                        )
                else:
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
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Authentification requise",
                            "message": "Vous devez être connecté pour accéder à cette ressource",
                        }
                    ),
                    401,
                )

        # Vérifier l'expiration du token même si la session existe
        if current_time - token_timestamp > 3600:  # Token expiré
            session.pop("user_id", None)
            session.pop("user_token", None)
            session.pop("token_timestamp", None)
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Token expiré",
                        "message": "Votre session a expiré, veuillez vous reconnecter",
                    }
                ),
                401,
            )

        # Vérifier que l'utilisateur existe toujours
        try:
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)
            user = datastore.find_user(id=user_id)

            if not user:
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

        except Exception as e:
            logger.error(f"Erreur vérification utilisateur: {e}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Erreur de vérification",
                        "message": "Impossible de vérifier l'utilisateur",
                    }
                ),
                401,
            )

        # Stocker l'user_id dans les kwargs pour l'utiliser dans la fonction
        kwargs["authenticated_user_id"] = user_id
        return f(*args, **kwargs)

    return decorated_function


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
