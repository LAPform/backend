"""
Routes API pour l'authentification
"""

from flask import Blueprint, request, jsonify, current_app
from models.user import User
from utils.auth import AuthManager
from utils.validators import DataValidator
from utils.security_validators import SecurityValidator
from utils.rate_limiter import rate_limit
from utils.error_handler import error_handler, validate_request_data, ensure_resource_exists
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


def _validate_password_strength(password: str) -> bool:
    """Valider la force d'un mot de passe"""
    import re

    # Au moins 8 caractères
    if len(password) < 8:
        return False

    # Au moins une majuscule
    if not re.search(r"[A-Z]", password):
        return False

    # Au moins une minuscule
    if not re.search(r"[a-z]", password):
        return False

    # Au moins un chiffre
    if not re.search(r"\d", password):
        return False

    # Au moins un caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False

    return True


@auth_bp.route("/auth/register", methods=["POST"])
@rate_limit("auth_register")
def register():
    """Créer un nouveau compte utilisateur"""
    try:
        data = request.get_json()

        # Validation des champs requis
        validation_error = validate_request_data(["email", "password"], data)
        if validation_error:
            return validation_error

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Validation de sécurité des données
        security_validation = SecurityValidator.validate_form_data_security(data)
        if not security_validation["valid"]:
            return error_handler.handle_validation_error(security_validation["errors"])

        # Nettoyer les données
        data = SecurityValidator.sanitize_form_data(data)
        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Validation stricte des données
        validation_errors = []

        # Validation email
        if not DataValidator.validate_email(email):
            validation_errors.append("Format d'email invalide")

        # Validation mot de passe
        if not DataValidator.validate_text_length(password, 8, 128):
            validation_errors.append(
                "Le mot de passe doit contenir entre 8 et 128 caractères"
            )

        # Validation nom (optionnel mais si fourni)
        if name and not DataValidator.validate_text_length(name, 1, 100):
            validation_errors.append("Le nom doit contenir entre 1 et 100 caractères")

        # Vérifier la force du mot de passe
        if not _validate_password_strength(password):
            validation_errors.append(
                "Le mot de passe doit contenir au moins une majuscule, une minuscule, un chiffre et un caractère spécial"
            )

        if validation_errors:
            return error_handler.handle_validation_error(validation_errors)

        # Vérifier si l'utilisateur existe déjà
        user_model = User(current_app.db)
        existing_user = user_model.get_by_email(email)
        if existing_user:
            return error_handler.handle_auth_error('AUTH_EMAIL_ALREADY_EXISTS')

        # Créer l'utilisateur
        user_id = user_model.create(email, password, name)

        # Générer le token
        token = AuthManager.generate_token(user_id, email)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Compte créé avec succès",
                    "token": token,
                    "user": {"id": user_id, "email": email, "name": name},
                }
            ),
            201,
        )

    except Exception as e:
        return error_handler.handle_system_error("user_registration", e)


@auth_bp.route("/auth/login", methods=["POST"])
@rate_limit("auth_login")
def login():
    """Connexion utilisateur"""
    try:
        data = request.get_json()

        # Validation des champs requis
        validation_error = validate_request_data(["email", "password"], data)
        if validation_error:
            return validation_error

        email = data["email"].lower().strip()
        password = data["password"]

        # Validation basique des données
        if not DataValidator.validate_email(email):
            return error_handler.create_error_response('VALIDATION_INVALID_FORMAT', 400, {'field': 'email'})

        if not DataValidator.validate_text_length(password, 1, 128):
            return error_handler.create_error_response('VALIDATION_INVALID_FORMAT', 400, {'field': 'password'})

        # Vérifier les identifiants
        user_model = User(current_app.db)
        user = user_model.verify_password(email, password)

        if not user:
            return error_handler.handle_auth_error('AUTH_INVALID_CREDENTIALS')

        # Mettre à jour la dernière connexion
        user_model.update_last_login(user["id"])

        # Générer le token
        token = AuthManager.generate_token(user["id"], user["email"])

        return jsonify(
            {
                "success": True,
                "message": "Connexion réussie",
                "token": token,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user.get("name", ""),
                },
            }
        )

    except Exception as e:
        return error_handler.handle_system_error("user_login", e)


@auth_bp.route("/auth/me", methods=["GET"])
def get_current_user():
    """Récupérer les informations de l'utilisateur actuel"""
    try:
        from utils.auth import AuthManager

        user = AuthManager.get_current_user()
        if not user:
            return jsonify({"error": "Non authentifié"}), 401

        return jsonify(
            {
                "success": True,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user.get("name", ""),
                    "created_at": user["created_at"],
                    "last_login": user.get("last_login"),
                },
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération utilisateur: {e}")
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/verify", methods=["POST"])
@rate_limit("auth_verify")
def verify_token():
    """Vérifier la validité d'un token"""
    try:
        data = request.get_json()
        token = data.get("token")

        if not token:
            return jsonify({"error": "Token requis"}), 400

        payload = AuthManager.verify_token(token)

        if "error" in payload:
            return jsonify({"error": payload["error"]}), 401

        return jsonify(
            {
                "success": True,
                "valid": True,
                "user_id": payload["user_id"],
                "email": payload["email"],
            }
        )

    except Exception as e:
        logger.error(f"Erreur vérification token: {e}")
        return jsonify({"error": str(e)}), 500
