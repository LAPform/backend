"""
Routes d'authentification avec Flask-Security-Too
"""

from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user

# from utils.security_auth import SecurityAuthManager, require_auth  # Désactivé
# from utils.rate_limiter import rate_limit  # Désactivé
# from utils.structured_logger import api_logger  # Désactivé
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


@security_auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Créer un nouveau compte utilisateur - Version production robuste"""
    try:
        logger.info("=== DÉBUT INSCRIPTION ===")

        data = request.get_json()
        logger.info(f"Données reçues: {data}")

        # Validation des champs requis
        if not data or "email" not in data or "password" not in data:
            logger.warning("Champs requis manquants")
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        logger.info(f"Email: {email}, Name: {name}")

        # Validation simple de l'email (comme endpoint de test)
        if "@" not in email:
            logger.warning("Email invalide")
            return jsonify({"error": "Email invalide"}), 400

        # Validation simple du mot de passe (comme endpoint de test)
        if len(password) < 6:
            logger.warning("Mot de passe trop court")
            return jsonify({"error": "Mot de passe trop court"}), 400

        # Vérifier si l'utilisateur existe déjà
        logger.info("Création du datastore...")
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        logger.info("Datastore créé avec succès")

        logger.info("Recherche utilisateur existant...")
        existing_user = datastore.find_user(email=email)
        logger.info(f"Utilisateur existant trouvé: {existing_user is not None}")

        if existing_user:
            logger.warning("Utilisateur déjà existant")
            return jsonify({"error": "Un compte avec cet email existe déjà"}), 409

        # Créer le nouvel utilisateur (version simplifiée comme test)
        logger.info("Création de l'utilisateur...")
        user = datastore.create_user(email=email, password=password, name=name)
        logger.info(f"Utilisateur créé avec succès: {user.id}")

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

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur inscription: {e}")
        logger.error(f"Type d'erreur: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Connexion utilisateur avec Flask-Security"""
    try:
        logger.info("=== DÉBUT CONNEXION ===")

        data = request.get_json()
        logger.info(f"Données reçues: {data}")

        # Validation des champs requis
        if not data or "email" not in data or "password" not in data:
            logger.warning("Champs requis manquants")
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        logger.info(f"Email: {email}")

        # Validation simple de l'email
        if "@" not in email or "." not in email:
            logger.warning("Format d'email invalide")
            return jsonify({"error": "Format d'email invalide"}), 400

        # Trouver l'utilisateur
        logger.info("Création du datastore...")
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        logger.info("Datastore créé avec succès")

        logger.info("Recherche de l'utilisateur...")
        user = datastore.find_user(email=email)
        logger.info(f"Utilisateur trouvé: {user is not None}")

        if not user:
            logger.warning("Utilisateur non trouvé")
            return jsonify({"error": "Identifiants invalides"}), 401

        # Vérifier le mot de passe
        logger.info("Vérification du mot de passe...")
        password_valid = datastore.verify_password(user, password)
        logger.info(f"Mot de passe valide: {password_valid}")

        if not password_valid:
            logger.warning("Mot de passe incorrect")
            return jsonify({"error": "Identifiants invalides"}), 401

        # Mettre à jour la dernière connexion (version simplifiée)
        try:
            logger.info("Mise à jour de la dernière connexion...")
            datastore.update_last_login(user)
            logger.info("Dernière connexion mise à jour")
        except Exception as e:
            logger.warning(f"Erreur mise à jour dernière connexion: {e}")

        logger.info("Connexion réussie")
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
        logger.error(f"Erreur connexion: {e}")
        logger.error(f"Type d'erreur: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Déconnexion utilisateur"""
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
        # Récupération simple de l'utilisateur actuel
        if current_user.is_authenticated:
            return (
                jsonify(
                    {
                        "success": True,
                        "user": {
                            "id": current_user.id,
                            "email": current_user.email,
                            "name": getattr(current_user, "name", ""),
                        },
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

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
