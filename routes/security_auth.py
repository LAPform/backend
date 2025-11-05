"""
Routes d'authentification avec Flask-Security-Too uniquement
"""

from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user, auth_required
from utils.security_auth import SecurityAuthManager, require_auth, require_token_auth
from utils.rate_limiter import rate_limit
from utils.security_validators import escape_html
from utils.audit_logger import audit_auth
import logging

logger = logging.getLogger(__name__)

security_auth_bp = Blueprint("security_auth", __name__)


@security_auth_bp.route("/auth/signup", methods=["POST"])
@rate_limit("auth_signup")
@audit_auth("signup")
def signup():
    """Créer un nouveau compte utilisateur"""
    print("=" * 80, flush=True)
    print(">>> SIGNUP ENDPOINT REACHED <<<", flush=True)
    print("=" * 80, flush=True)
    try:
        print(">>> Getting JSON data...", flush=True)
        data = request.get_json()
        print(f">>> Data received: {bool(data)}", flush=True)

        # Debug logging
        logger.info(f"Signup attempt - data received: {bool(data)}")

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Validation email
        if not SecurityAuthManager.validate_email(email):
            return jsonify({"error": "Email invalide"}), 400

        # Validation mot de passe renforcée
        is_valid, message = SecurityAuthManager.validate_password_strength(password)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Créer l'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        # Vérifier si l'utilisateur existe
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"error": "Utilisateur déjà existant"}), 409

        # Créer l'utilisateur
        user = datastore.create_user(email=email, password=password, name=name)

        # Générer un token d'authentification Flask-Security-Too
        try:
            login_user(user)
            logger.info("User logged in successfully")
            auth_token = user.get_auth_token()
            logger.info(f"Token generated successfully: {auth_token[:20]}...")
        except Exception as token_error:
            logger.error(f"ERREUR GÉNÉRATION TOKEN: {token_error}", exc_info=True)
            return jsonify({"error": f"Erreur génération token: {str(token_error)}"}), 500

        # Créer une réponse sécurisée
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(user.name),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user": user_data,
                    "authentication_token": auth_token,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Erreur inscription: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback complet: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@security_auth_bp.route("/auth/signin", methods=["POST"])
@rate_limit("auth_signin")
@audit_auth("signin")
def signin():
    """Connexion utilisateur avec Flask-Security-Too"""
    try:
        # Parsing JSON avec fallback
        data = request.get_json(silent=True)
        if not data and request.data:
            try:
                import json as _json

                data = _json.loads(request.data.decode("utf-8"))
            except Exception:
                data = None

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        # Vérifier l'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        user = datastore.find_user(email=email)

        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 401

        # Vérifier le mot de passe
        if not datastore.verify_password(user, password):
            return jsonify({"error": "Mot de passe incorrect"}), 401

        # Connexion avec Flask-Security-Too
        try:
            login_user(user)
            logger.info("User logged in successfully for signin")

            # Générer un token d'authentification
            auth_token = user.get_auth_token()
            logger.info(f"Token generated successfully: {auth_token[:20]}...")
        except Exception as token_error:
            logger.error(f"ERREUR GÉNÉRATION TOKEN (signin): {token_error}", exc_info=True)
            return jsonify({"error": f"Erreur génération token: {str(token_error)}"}), 500

        # Créer une réponse sécurisée
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(getattr(user, "name", "")),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Connexion réussie",
                    "user": user_data,
                    "authentication_token": auth_token,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Erreur connexion: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback complet: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@security_auth_bp.route("/auth/logout", methods=["POST"])
@auth_required("token", "session")
def logout():
    """Déconnexion utilisateur"""
    try:
        logout_user()
        return jsonify({"success": True, "message": "Déconnexion réussie"}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {e}")
        return jsonify({"error": "Erreur interne"}), 500


@security_auth_bp.route("/auth/me", methods=["GET"])
@require_token_auth
def get_current_user(authenticated_user_id=None):
    """Récupérer les informations de l'utilisateur actuel"""
    try:
        # Charger l'utilisateur depuis l'ID authentifié
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        user = datastore._get_user_by_id(authenticated_user_id)

        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        # Créer une réponse sécurisée
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(getattr(user, "name", "")),
        }

        return jsonify({"success": True, "user": user_data})

    except Exception as e:
        logger.error(f"Erreur récupération utilisateur: {e}")
        return jsonify({"error": "Erreur interne"}), 500


@security_auth_bp.route("/auth/change-password", methods=["POST"])
@require_token_auth
def change_password(authenticated_user_id=None):
    """Changer le mot de passe de l'utilisateur"""
    try:
        data = request.get_json()

        if not data or "current_password" not in data or "new_password" not in data:
            return (
                jsonify(
                    {"error": "Mot de passe actuel et nouveau mot de passe requis"}
                ),
                400,
            )

        current_password = data["current_password"]
        new_password = data["new_password"]

        # Validation du nouveau mot de passe
        is_valid, message = SecurityAuthManager.validate_password_strength(new_password)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Charger l'utilisateur depuis l'ID authentifié
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        user = datastore._get_user_by_id(authenticated_user_id)

        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        # Vérifier le mot de passe actuel
        if not datastore.verify_password(user, current_password):
            return jsonify({"error": "Mot de passe actuel incorrect"}), 401

        # Mettre à jour le mot de passe
        datastore.update_user_password(user, new_password)

        return (
            jsonify({"success": True, "message": "Mot de passe modifié avec succès"}),
            200,
        )

    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {e}")
        return jsonify({"error": "Erreur interne"}), 500


# Endpoint de test simple (toujours disponible)
@security_auth_bp.route("/auth/test", methods=["GET"])
def test_auth():
    """Endpoint de test simple pour l'authentification"""
    return jsonify(
        {
            "success": True,
            "message": "Endpoint d'authentification accessible",
            "system": "Flask-Security-Too",
        }
    )
