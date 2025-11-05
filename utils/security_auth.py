"""
Système d'authentification simplifié avec Flask-Security-Too uniquement
"""

from flask import jsonify
from flask_security import current_user
from functools import wraps


def require_auth(f):
    """
    Décorateur de compatibilité qui redirige vers Flask-Security-Too
    Utilise auth_required de Flask-Security-Too en interne
    """
    from flask_security import auth_required
    from flask import request
    import logging

    logger = logging.getLogger(__name__)

    @wraps(f)
    @auth_required("token", "session")
    def decorated_function(*args, **kwargs):
        # Debug: Logger les headers reçus
        logger.info(f">>> REQUIRE_AUTH: Headers received: {dict(request.headers)}")
        logger.info(f">>> REQUIRE_AUTH: Current user authenticated: {current_user.is_authenticated}")
        logger.info(f">>> REQUIRE_AUTH: Current user ID: {current_user.id if current_user.is_authenticated else 'None'}")

        # Injecter l'ID utilisateur dans les kwargs pour compatibilité
        kwargs["authenticated_user_id"] = current_user.id
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
            from flask import current_app
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
