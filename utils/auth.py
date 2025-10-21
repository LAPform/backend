"""
Utilitaires d'authentification pour FormForge
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models.user import User


class AuthManager:
    """Gestionnaire d'authentification"""

    @staticmethod
    def generate_token(user_id: str, email: str) -> str:
        """Générer un token JWT"""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
        }

        secret_key = os.environ.get("SECRET_KEY", "default-secret-key")
        return jwt.encode(payload, secret_key, algorithm="HS256")

    @staticmethod
    def verify_token(token: str) -> dict:
        """Vérifier un token JWT"""
        try:
            secret_key = os.environ.get("SECRET_KEY", "default-secret-key")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return {"error": "Token expiré"}
        except jwt.InvalidTokenError:
            return {"error": "Token invalide"}

    @staticmethod
    def get_current_user():
        """Récupérer l'utilisateur actuel depuis le token"""
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        payload = AuthManager.verify_token(token)

        if "error" in payload:
            return None

        user_model = User(current_app.db)
        return user_model.get_by_id(payload["user_id"])


def require_auth(f):
    """Décorateur pour protéger les routes"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({"error": "Authentification requise"}), 401
        return f(*args, **kwargs)

    return decorated_function


def require_ownership(f):
    """Décorateur pour vérifier la propriété d'un formulaire"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = AuthManager.get_current_user()
        if not user:
            return jsonify({"error": "Authentification requise"}), 401

        # Vérifier la propriété du formulaire si form_id est dans les kwargs
        if "form_id" in kwargs:
            from models.form import Form

            form_model = Form(current_app.db)
            form = form_model.get_by_id(kwargs["form_id"])

            if not form:
                return jsonify({"error": "Formulaire non trouvé"}), 404

            if form.get("created_by") != user["id"]:
                return jsonify({"error": "Accès non autorisé"}), 403

        return f(*args, **kwargs)

    return decorated_function
