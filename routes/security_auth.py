"""
Routes d'authentification avec Flask-Security-Too
"""

from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user
from utils.security_auth import SecurityAuthManager, require_auth
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
import logging

logger = logging.getLogger(__name__)

security_auth_bp = Blueprint("security_auth", __name__)


@security_auth_bp.route("/auth/test", methods=["GET"])
def test_auth():
    """Endpoint de test simple pour l'authentification"""
    return jsonify({
        "success": True,
        "message": "Endpoint d'authentification accessible",
        "timestamp": "2024-01-15T10:30:00Z"
    })


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
        
        return jsonify({
            "success": True,
            "message": "Utilisateur créé avec succès",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }), 201
        
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
        return jsonify({
            "success": True,
            "message": "Connexion réussie",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name
            }
        }), 200
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test connexion: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/register", methods=["POST"])
@rate_limit("auth_register")
def register():
    """Créer un nouveau compte utilisateur avec Flask-Security - Version simplifiée"""
    try:
        data = request.get_json()

        # Validation des champs requis
        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Validation de l'email
        if not SecurityAuthManager.validate_email(email):
            return jsonify({"error": "Format d'email invalide"}), 400

        # Validation du mot de passe
        is_valid, message = SecurityAuthManager.validate_password_strength(password)
        if not is_valid:
            return jsonify({"error": message}), 400

        # Validation du nom
        if name and len(name) > 100:
            return jsonify({"error": "Le nom ne peut pas dépasser 100 caractères"}), 400

        # Vérifier si l'utilisateur existe déjà
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        existing_user = datastore.find_user(email=email)

        if existing_user:
            return jsonify({"error": "Un compte avec cet email existe déjà"}), 409

        # Créer le nouvel utilisateur
        try:
            user = datastore.create_user(email=email, password=password, name=name)

            # Connecter l'utilisateur automatiquement
            if SecurityAuthManager.login_user_safe(user):
                api_logger.user_registered(user.id, email)

                return (
                    jsonify(
                        {
                            "success": True,
                            "message": "Compte créé avec succès",
                            "user": {
                                "id": user.id,
                                "email": user.email,
                                "name": user.name,
                            },
                        }
                    ),
                    201,
                )
            else:
                return jsonify({"error": "Erreur lors de la connexion"}), 500

        except Exception as e:
            logger.error(f"Erreur création utilisateur: {e}")
            return jsonify({"error": f"Erreur lors de la création du compte: {str(e)}"}), 500

    except Exception as e:
        logger.error(f"Erreur inscription: {e}")
        return jsonify({"error": f"Erreur interne du serveur: {str(e)}"}), 500


@security_auth_bp.route("/auth/login", methods=["POST"])
@rate_limit("auth_login")
def login():
    """Connexion utilisateur avec Flask-Security"""
    try:
        data = request.get_json()

        # Validation des champs requis
        if not data or "email" not in data or "password" not in data:
            return SecurityAuthManager.create_error_response(
                "Email et mot de passe requis", 400
            )

        email = data["email"].lower().strip()
        password = data["password"]

        # Validation de l'email
        if not SecurityAuthManager.validate_email(email):
            return SecurityAuthManager.create_error_response(
                "Format d'email invalide", 400
            )

        # Trouver l'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        user = datastore.find_user(email=email)

        if not user:
            api_logger.authentication_failed(
                email, "User not found", request.remote_addr
            )
            return SecurityAuthManager.create_error_response(
                "Identifiants invalides", 401
            )

        # Vérifier le mot de passe
        if not datastore.verify_password(user, password):
            api_logger.authentication_failed(
                email, "Invalid password", request.remote_addr
            )
            return SecurityAuthManager.create_error_response(
                "Identifiants invalides", 401
            )

        # Connecter l'utilisateur
        if SecurityAuthManager.login_user_safe(user):
            # Mettre à jour la dernière connexion
            datastore.update_last_login(user)
            api_logger.authentication_success(user.id, email, "login")

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
        else:
            return SecurityAuthManager.create_error_response(
                "Erreur lors de la connexion", 500
            )

    except Exception as e:
        logger.error(f"Erreur connexion: {e}")
        return SecurityAuthManager.create_error_response(
            "Erreur interne du serveur", 500
        )


@security_auth_bp.route("/auth/logout", methods=["POST"])
@require_auth
def logout():
    """Déconnexion utilisateur"""
    try:
        if SecurityAuthManager.logout_user_safe():
            return jsonify({"success": True, "message": "Déconnexion réussie"}), 200
        else:
            return SecurityAuthManager.create_error_response(
                "Erreur lors de la déconnexion", 500
            )

    except Exception as e:
        logger.error(f"Erreur déconnexion: {e}")
        return SecurityAuthManager.create_error_response(
            "Erreur interne du serveur", 500
        )


@security_auth_bp.route("/auth/me", methods=["GET"])
@require_auth
@rate_limit("auth_me")
def get_current_user():
    """Récupérer les informations de l'utilisateur actuel"""
    try:
        user_info = SecurityAuthManager.get_current_user()

        if user_info:
            return jsonify({"success": True, "user": user_info}), 200
        else:
            return SecurityAuthManager.create_error_response(
                "Utilisateur non trouvé", 404
            )

    except Exception as e:
        logger.error(f"Erreur récupération utilisateur: {e}")
        return SecurityAuthManager.create_error_response(
            "Erreur interne du serveur", 500
        )


@security_auth_bp.route("/auth/change-password", methods=["POST"])
@require_auth
@rate_limit("auth_change_password")
def change_password():
    """Changer le mot de passe de l'utilisateur"""
    try:
        data = request.get_json()

        if not data or "current_password" not in data or "new_password" not in data:
            return SecurityAuthManager.create_error_response(
                "Mot de passe actuel et nouveau mot de passe requis", 400
            )

        current_password = data["current_password"]
        new_password = data["new_password"]

        # Validation du nouveau mot de passe
        is_valid, message = SecurityAuthManager.validate_password_strength(new_password)
        if not is_valid:
            return SecurityAuthManager.create_error_response(message, 400)

        # Vérifier le mot de passe actuel
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        if not datastore.verify_password(current_user, current_password):
            return SecurityAuthManager.create_error_response(
                "Mot de passe actuel incorrect", 401
            )

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
        return SecurityAuthManager.create_error_response(
            "Erreur interne du serveur", 500
        )
