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

logger = logging.getLogger(__name__)


def require_auth(f):
    """Décorateur pour protéger les routes avec tokens SHA256 stateless"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Vérifier le header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Authentification requise",
                        "message": "Token Bearer requis dans l'en-tête Authorization",
                    }
                ),
                401,
            )

        token = auth_header.split(" ")[1]

        # Vérifier le format du token (64 caractères hex pour SHA256)
        if len(token) != 64:
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
            # Décoder le token SHA256 pour extraire les informations
            # Le token contient: user_id:email:timestamp
            # On doit le décoder pour vérifier l'expiration et l'utilisateur

            # Pour un système stateless, on stocke les tokens actifs en base
            # ou on utilise une approche différente

            # Vérifier que l'utilisateur existe toujours
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)

            # Pour l'instant, on va extraire l'user_id du token
            # Dans un vrai système, on aurait une table de tokens actifs
            # ou on décoderait le token pour récupérer les infos

            # Méthode temporaire : chercher l'utilisateur par token dans une table
            # ou décoder le token pour récupérer l'user_id

            # Pour simplifier, on va utiliser une approche hybride
            # On stocke les tokens actifs en mémoire ou en base

            # Vérifier si le token est valide et non expiré
            user_id = _validate_sha256_token(token)

            if not user_id:
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

            # Stocker l'user_id dans les kwargs pour l'utiliser dans la fonction
            kwargs["authenticated_user_id"] = user_id
            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"Erreur authentification: {e}")
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
        from models.database import DatabaseManager

        db = DatabaseManager()

        # Vérifier si le token existe et n'est pas expiré
        query = """
            SELECT user_id, expires_at 
            FROM active_tokens 
            WHERE token = ? AND expires_at > datetime('now')
        """

        result = db.execute_query(query, (token,), fetch=True)

        if result and len(result) > 0:
            return result[0]["user_id"]

        return None

    except Exception as e:
        logger.error(f"Erreur validation token: {e}")
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
