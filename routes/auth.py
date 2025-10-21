"""
Routes API pour l'authentification
"""

from flask import Blueprint, request, jsonify, current_app
from models.user import User
from utils.auth import AuthManager
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Créer un nouveau compte utilisateur"""
    try:
        data = request.get_json()

        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Vérifier si l'utilisateur existe déjà
        user_model = User(current_app.db)
        existing_user = user_model.get_by_email(email)
        if existing_user:
            return jsonify({"error": "Un compte avec cet email existe déjà"}), 400

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
        logger.error(f"Erreur inscription: {e}")
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Connexion utilisateur"""
    try:
        data = request.get_json()

        if not data or not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        # Vérifier les identifiants
        user_model = User(current_app.db)
        user = user_model.verify_password(email, password)

        if not user:
            return jsonify({"error": "Email ou mot de passe incorrect"}), 401

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
        logger.error(f"Erreur connexion: {e}")
        return jsonify({"error": str(e)}), 500


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
