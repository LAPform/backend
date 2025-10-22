"""
Nouveau système d'authentification avec Flask-Security-Too
"""

from flask import request, jsonify, current_app
from flask_security import current_user, login_user, logout_user
from flask_security.utils import hash_password, verify_password
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """Décorateur pour protéger les routes avec Flask-Security"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
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

    @staticmethod
    def login_user_safe(user, remember=False):
        """Connexion sécurisée d'un utilisateur"""
        try:
            login_user(user, remember=remember)
            return True
        except Exception as e:
            logger.error(f"Erreur connexion utilisateur: {e}")
            return False

    @staticmethod
    def logout_user_safe():
        """Déconnexion sécurisée d'un utilisateur"""
        try:
            logout_user()
            return True
        except Exception as e:
            logger.error(f"Erreur déconnexion utilisateur: {e}")
            return False

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
