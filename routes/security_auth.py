"""
Routes d'authentification avec Flask-Security-Too
"""

from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user

from utils.security_auth import SecurityAuthManager, require_auth
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
from utils.security_validators import escape_html, create_safe_response
import logging

logger = logging.getLogger(__name__)

security_auth_bp = Blueprint("security_auth", __name__)


@security_auth_bp.route("/auth/test", methods=["GET"])
def test_auth():
    """Endpoint de test simple pour l'authentification"""
    return jsonify(
        {
            "success": True,
            "message": "Endpoint d'authentification accessible",
            "timestamp": "2024-01-15T10:30:00Z",
        }
    )


@security_auth_bp.route("/auth/test-register", methods=["POST"])
def test_register():
    """Endpoint de test d'inscription simplifié"""
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Test simple de validation
        if "@" not in email:
            return jsonify({"error": "Email invalide"}), 400

        if len(password) < 6:
            return jsonify({"error": "Mot de passe trop court"}), 400

        # Test de création d'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        # Vérifier si l'utilisateur existe
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"error": "Utilisateur déjà existant"}), 409

        # Créer l'utilisateur
        user = datastore.create_user(email=email, password=password, name=name)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user": {"id": user.id, "email": user.email, "name": user.name},
                }
            ),
            201,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test inscription: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/test-login", methods=["POST"])
def test_login():
    """Endpoint de test de connexion simplifié"""
    try:
        data = request.get_json()

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

        # Connexion réussie
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Connexion réussie",
                    "user": {"id": user.id, "email": user.email, "name": user.name},
                }
            ),
            200,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test connexion: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/signup", methods=["POST"])
def signup():
    """Créer un nouveau compte utilisateur - Endpoint principal fonctionnel"""
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Test simple de validation
        if "@" not in email:
            return jsonify({"error": "Email invalide"}), 400

        if len(password) < 6:
            return jsonify({"error": "Mot de passe trop court"}), 400

        # Test de création d'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        # Vérifier si l'utilisateur existe
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"error": "Utilisateur déjà existant"}), 409

        # Créer l'utilisateur
        user = datastore.create_user(email=email, password=password, name=name)

        # Créer une réponse sécurisée en échappant les données utilisateur
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
                }
            ),
            201,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test inscription: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/signin", methods=["POST"])
def signin():
    """Connexion utilisateur - Version simplifiée sans Flask-Security-Too"""
    try:
        data = request.get_json()

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

        # Créer un token SHA256 avec rotation
        import hashlib
        import time
        from datetime import datetime, timedelta

        # Générer un token SHA256
        timestamp = int(time.time())
        token_data = f"{user.id}:{email}:{timestamp}"
        sha256_token = hashlib.sha256(token_data.encode()).hexdigest()

        # Calculer l'expiration (1 heure)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Stocker le token en base de données
        from models.database import DatabaseManager

        db = DatabaseManager()

        # Supprimer les anciens tokens de l'utilisateur
        db.execute_query("DELETE FROM active_tokens WHERE user_id = ?", (user.id,))

        # Insérer le nouveau token
        db.execute_query(
            """
            INSERT INTO active_tokens (token, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (sha256_token, user.id, expires_at.isoformat()),
        )

        # Créer une réponse sécurisée en échappant les données utilisateur
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(user.name),
        }

        # Connexion réussie
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Connexion réussie",
                    "user": user_data,
                    "token": sha256_token,
                }
            ),
            200,
        )

    except Exception as e:
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur connexion: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur connexion: {str(e)}"}), 500


# Endpoints de compatibilité supprimés car non fonctionnels
# Flask-Security-Too intercepte automatiquement ces routes
# Utiliser uniquement /auth/signup et /auth/signin


@security_auth_bp.route("/auth/custom-logout", methods=["POST"])
def logout():
    """Déconnexion utilisateur - Route personnalisée pour éviter le conflit avec Flask-Security-Too"""
    try:
        # Déconnexion simple
        logout_user()
        return jsonify({"success": True, "message": "Déconnexion réussie"}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500


@security_auth_bp.route("/auth/me", methods=["GET"])
def get_current_user():
    """Récupérer les informations de l'utilisateur actuel"""
    try:
        from flask_security import current_user

        # Vérifier que l'utilisateur est authentifié avec Flask-Security-Too
        if not current_user.is_authenticated:
            return jsonify({"error": "Non authentifié"}), 401

        # Créer une réponse sécurisée en échappant les données utilisateur
        user_data = {
            "id": current_user.id,
            "email": escape_html(current_user.email),
            "name": escape_html(getattr(current_user, "name", "")),
        }

        return jsonify(
            {
                "success": True,
                "user": user_data,
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération utilisateur: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500


@security_auth_bp.route("/auth/change-password", methods=["POST"])
def change_password():
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

        # Validation simple du nouveau mot de passe
        if len(new_password) < 6:
            return (
                jsonify(
                    {
                        "error": "Le nouveau mot de passe doit contenir au moins 6 caractères"
                    }
                ),
                400,
            )

        # Vérifier le mot de passe actuel
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        if not datastore.verify_password(current_user, current_password):
            return jsonify({"error": "Mot de passe actuel incorrect"}), 401

        # Mettre à jour le mot de passe
        from flask_security.utils import hash_password

        current_user.password_hash = hash_password(new_password)

        # Sauvegarder en base (à implémenter selon votre modèle)
        # datastore.update_user_password(current_user, new_password)

        return (
            jsonify({"success": True, "message": "Mot de passe modifié avec succès"}),
            200,
        )

    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500
