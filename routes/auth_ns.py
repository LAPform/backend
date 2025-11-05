"""
Routes d'authentification avec Flask-Security-Too (Flask-RESTx avec Swagger)
"""

from flask import request, current_app
from flask_restx import Namespace, Resource
from flask_security import current_user, login_user, logout_user, auth_required
from utils.security_auth import SecurityAuthManager, require_auth, require_token_auth
from utils.rate_limiter import rate_limit
from utils.security_validators import escape_html
from utils.audit_logger import audit_auth
import logging

logger = logging.getLogger(__name__)

# Créer le namespace
api = Namespace('auth', description='Authentification et gestion des utilisateurs')

# Récupérer les modèles depuis la configuration
def get_models():
    """Récupère les modèles de documentation depuis la config de l'app"""
    return current_app.config.get('API_MODELS', {})


@api.route('/signup')
class Signup(Resource):
    """Inscription d'un nouvel utilisateur"""

    @api.doc('signup',
             description='Créer un nouveau compte utilisateur avec validation de mot de passe renforcée (OWASP)')
    @api.expect(get_models().get('signup'), validate=True)
    @api.response(201, 'Utilisateur créé', get_models().get('auth_response'))
    @api.response(400, 'Validation échouée', get_models().get('error'))
    @api.response(409, 'Utilisateur déjà existant', get_models().get('error'))
    @rate_limit("auth_signup")
    @audit_auth("signup")
    def post(self):
        """Créer un nouveau compte utilisateur"""
        try:
            data = request.get_json()
            logger.info(f"Signup attempt - data received: {bool(data)}")

            if not data or "email" not in data or "password" not in data:
                return {"error": "Email et mot de passe requis"}, 400

            email = data["email"].lower().strip()
            password = data["password"]
            name = data.get("name", "")

            # Validation email
            if not SecurityAuthManager.validate_email(email):
                return {"error": "Email invalide"}, 400

            # Validation mot de passe renforcée
            is_valid, message = SecurityAuthManager.validate_password_strength(password)
            if not is_valid:
                return {"error": message}, 400

            # Créer l'utilisateur
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)

            # Vérifier si l'utilisateur existe
            existing_user = datastore.find_user(email=email)
            if existing_user:
                return {"error": "Utilisateur déjà existant"}, 409

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
                return {"error": f"Erreur génération token: {str(token_error)}"}, 500

            # Créer une réponse sécurisée
            user_data = {
                "id": user.id,
                "email": escape_html(user.email),
                "name": escape_html(user.name),
            }

            return {
                "success": True,
                "message": "Utilisateur créé avec succès",
                "user": user_data,
                "authentication_token": auth_token,
            }, 201

        except Exception as e:
            logger.error(f"Erreur inscription: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback complet: {traceback.format_exc()}")
            return {"error": f"Erreur interne: {str(e)}"}, 500


@api.route('/signin')
class Signin(Resource):
    """Connexion utilisateur"""

    @api.doc('signin',
             description='Authentification utilisateur - Retourne un token d\'authentification valide 1 heure')
    @api.expect(get_models().get('signin'), validate=True)
    @api.response(200, 'Connexion réussie', get_models().get('auth_response'))
    @api.response(400, 'Données manquantes', get_models().get('error'))
    @api.response(401, 'Identifiants invalides', get_models().get('error'))
    @rate_limit("auth_signin")
    @audit_auth("signin")
    def post(self):
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
                return {"error": "Email et mot de passe requis"}, 400

            email = data["email"].lower().strip()
            password = data["password"]

            # Vérifier l'utilisateur
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)
            user = datastore.find_user(email=email)

            if not user:
                return {"error": "Utilisateur non trouvé"}, 401

            # Vérifier le mot de passe
            if not datastore.verify_password(user, password):
                return {"error": "Mot de passe incorrect"}, 401

            # Connexion avec Flask-Security-Too
            try:
                login_user(user)
                logger.info("User logged in successfully for signin")

                # Générer un token d'authentification
                auth_token = user.get_auth_token()
                logger.info(f"Token generated successfully: {auth_token[:20]}...")
            except Exception as token_error:
                logger.error(f"ERREUR GÉNÉRATION TOKEN (signin): {token_error}", exc_info=True)
                return {"error": f"Erreur génération token: {str(token_error)}"}, 500

            # Créer une réponse sécurisée
            user_data = {
                "id": user.id,
                "email": escape_html(user.email),
                "name": escape_html(getattr(user, "name", "")),
            }

            return {
                "success": True,
                "message": "Connexion réussie",
                "user": user_data,
                "authentication_token": auth_token,
            }

        except Exception as e:
            logger.error(f"Erreur connexion: {e}", exc_info=True)
            import traceback
            logger.error(f"Traceback complet: {traceback.format_exc()}")
            return {"error": f"Erreur interne: {str(e)}"}, 500


@api.route('/logout')
class Logout(Resource):
    """Déconnexion utilisateur"""

    @api.doc('logout',
             description='Déconnexion de l\'utilisateur actuel',
             security='Bearer')
    @api.response(200, 'Déconnexion réussie', get_models().get('success'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @auth_required("token", "session")
    def post(self):
        """Déconnexion utilisateur"""
        try:
            logout_user()
            return {"success": True, "message": "Déconnexion réussie"}
        except Exception as e:
            logger.error(f"Erreur déconnexion: {e}")
            return {"error": "Erreur interne"}, 500


@api.route('/me')
class CurrentUser(Resource):
    """Informations de l'utilisateur connecté"""

    @api.doc('get_current_user',
             description='Récupérer les informations de l\'utilisateur actuellement authentifié',
             security='Bearer')
    @api.response(200, 'Informations utilisateur', get_models().get('user_info'))
    @api.response(404, 'Utilisateur non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, authenticated_user_id=None):
        """Récupérer les informations de l'utilisateur actuel"""
        try:
            # Charger l'utilisateur depuis l'ID authentifié
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)
            user = datastore._get_user_by_id(authenticated_user_id)

            if not user:
                return {"error": "Utilisateur non trouvé"}, 404

            # Créer une réponse sécurisée
            user_data = {
                "id": user.id,
                "email": escape_html(user.email),
                "name": escape_html(getattr(user, "name", "")),
            }

            return {"success": True, "user": user_data}

        except Exception as e:
            logger.error(f"Erreur récupération utilisateur: {e}")
            return {"error": "Erreur interne"}, 500


@api.route('/change-password')
class ChangePassword(Resource):
    """Changement de mot de passe"""

    @api.doc('change_password',
             description='Changer le mot de passe de l\'utilisateur connecté avec validation OWASP',
             security='Bearer')
    @api.expect(get_models().get('change_password'), validate=True)
    @api.response(200, 'Mot de passe modifié', get_models().get('success'))
    @api.response(400, 'Validation échouée', get_models().get('error'))
    @api.response(401, 'Mot de passe actuel incorrect', get_models().get('error'))
    @api.response(404, 'Utilisateur non trouvé', get_models().get('error'))
    @require_token_auth
    def post(self, authenticated_user_id=None):
        """Changer le mot de passe de l'utilisateur"""
        try:
            data = request.get_json()

            if not data or "current_password" not in data or "new_password" not in data:
                return {
                    "error": "Mot de passe actuel et nouveau mot de passe requis"
                }, 400

            current_password = data["current_password"]
            new_password = data["new_password"]

            # Validation du nouveau mot de passe
            is_valid, message = SecurityAuthManager.validate_password_strength(new_password)
            if not is_valid:
                return {"error": message}, 400

            # Charger l'utilisateur depuis l'ID authentifié
            from models.security_models import SecurityUserDatastore

            datastore = SecurityUserDatastore(current_app.db)
            user = datastore._get_user_by_id(authenticated_user_id)

            if not user:
                return {"error": "Utilisateur non trouvé"}, 404

            # Vérifier le mot de passe actuel
            if not datastore.verify_password(user, current_password):
                return {"error": "Mot de passe actuel incorrect"}, 401

            # Mettre à jour le mot de passe
            datastore.update_user_password(user, new_password)

            return {"success": True, "message": "Mot de passe modifié avec succès"}

        except Exception as e:
            logger.error(f"Erreur changement mot de passe: {e}")
            return {"error": "Erreur interne"}, 500


@api.route('/test')
class AuthTest(Resource):
    """Endpoint de test simple pour l'authentification"""

    @api.doc('test_auth',
             description='Endpoint de test simple pour vérifier que le système d\'authentification est opérationnel')
    @api.response(200, 'Système opérationnel', get_models().get('success'))
    def get(self):
        """Endpoint de test simple pour l'authentification"""
        return {
            "success": True,
            "message": "Endpoint d'authentification accessible",
            "system": "Flask-Security-Too",
        }
