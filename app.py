"""
Application principale FormForge Flask avec Flask-Security-Too
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_security import Security

# Configuration du logging structuré
from utils.logging_middleware import (
    setup_logging_config,
    log_application_startup,
)

from models.database import DatabaseManager
from models.security_models import SecurityUserDatastore
from routes.forms import forms_bp
from routes.questions import questions_bp
from routes.responses import responses_bp
from routes.docs import docs_bp
from routes.security_auth import security_auth_bp  # Nouveau blueprint
from routes.files import files_bp
from routes.monitoring import monitoring_bp
from config import Config
from config_security import SecurityConfig
from debug_headers_middleware import log_all_requests


def create_app():
    """Factory pour créer l'application Flask avec Flask-Security-Too"""
    app = Flask(__name__)

    # Configuration de base
    app.config.from_object(Config)
    app.config.from_object(SecurityConfig)

    # Configuration du logging structuré
    setup_logging_config(app)

    # Logger pour debug
    logger = logging.getLogger(__name__)

    # Middleware de debug pour logger tous les headers (temporaire)
    log_all_requests(app)

    # Configuration CORS sécurisée et headers de sécurité
    try:
        from utils.security_middleware import setup_security_middleware

        setup_security_middleware(app)
        logger.info("Middlewares de sécurité configurés avec succès")
    except Exception as e:
        logger.error(f"Erreur configuration middlewares de sécurité: {e}")
        # Fallback sécurisé pour CORS - jamais autoriser toutes les origines
        from flask_cors import CORS

        # os est déjà importé au niveau du module (ligne 5)

        # Récupérer les origines autorisées depuis la configuration ou l'environnement
        cors_origins = app.config.get("CORS_ORIGINS", [])
        if isinstance(cors_origins, str):
            cors_origins = [
                origin.strip() for origin in cors_origins.split(",") if origin.strip()
            ]

        # Si aucune origine définie, utiliser des valeurs par défaut sécurisées pour dev
        if not cors_origins:
            cors_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]

        # Toujours configurer CORS avec des origines explicites
        CORS(
            app,
            origins=cors_origins,
            supports_credentials=True,
            max_age=3600,
            allow_headers=[
                "Content-Type",
                "Authorization",
                "Authentication-Token",
                "X-Requested-With",
                "Accept",
            ],
        )
        logger.warning("CORS configuré en mode fallback avec origines limitées")

    # Initialiser la base de données
    try:
        app.db = DatabaseManager()
        app.db.init_database()

        # Rendre la base de données accessible via current_app
        app.config["DATABASE_MANAGER"] = app.db

        # Logger la connexion à la base de données
        from utils.structured_logger import db_logger, structured_logger

        db_logger.connection_established(app.db.database_url)
        structured_logger.info("Base de données initialisée avec succès")
    except Exception as e:
        from utils.structured_logger import structured_logger

        structured_logger.error("Erreur initialisation base de données", exception=e)
        raise

    # Configuration Flask-Security-Too
    try:
        # Créer le datastore personnalisé
        user_datastore = SecurityUserDatastore(app.db)

        # Configuration pour Flask-Security-Too (activation blueprints JSON sous /api/auth)
        app.config.update(
            {
                "SECURITY_PASSWORD_HASH": "pbkdf2_sha256",
                "SECURITY_PASSWORD_SALT": app.config.get(
                    "SECURITY_PASSWORD_SALT", "dev-salt"
                ),
                "SECURITY_JSON_ENABLED": True,
                "SECURITY_JSON": True,
                "SECURITY_URL_PREFIX": "/api/auth",
                "SECURITY_REGISTERABLE": True,
                "SECURITY_RECOVERABLE": True,  # Activé pour la réinitialisation de mot de passe
                "SECURITY_CHANGEABLE": True,
                "SECURITY_RETURN_GENERIC_RESPONSES": True,
                "SECURITY_CONFIRMABLE": False,
                "SECURITY_TRACKABLE": True,
                "SECURITY_SEND_REGISTER_EMAIL": False,
                "SECURITY_SEND_PASSWORD_CHANGE_EMAIL": False,
                "SECURITY_SEND_PASSWORD_RESET_EMAIL": True,  # Activer l'envoi d'email de réinitialisation
                "SECURITY_FLASH_MESSAGES": False,
                "WTF_CSRF_ENABLED": False,
                "SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS": True,
                # Configuration Flask-Mail pour l'envoi d'emails
                "MAIL_SERVER": os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
                "MAIL_PORT": int(os.environ.get("MAIL_PORT", 587)),
                "MAIL_USE_TLS": os.environ.get("MAIL_USE_TLS", "true").lower()
                == "true",
                "MAIL_USE_SSL": os.environ.get("MAIL_USE_SSL", "false").lower()
                == "true",
                "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
                "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD"),
                "MAIL_DEFAULT_SENDER": os.environ.get(
                    "MAIL_DEFAULT_SENDER", "noreply@formforge.com"
                ),
                # Ne pas définir les URLs automatiques pour éviter les conflits
            }
        )

        # Initialiser Flask-Mail pour l'envoi d'emails
        from flask_mail import Mail

        mail = Mail(app)
        app.mail = mail

        # Initialiser Flask-Security et enregistrer ses blueprints
        security = Security(app, user_datastore, register_blueprint=True)

        # Configuration des templates (désactivé pour API)
        app.config["SECURITY_EMAIL_SENDER"] = app.config.get(
            "MAIL_DEFAULT_SENDER", "noreply@formforge.com"
        )

        # Configuration logging Flask-Security (WARNING uniquement en production)
        try:
            import logging as _logging

            fst_logger = _logging.getLogger("flask_security")
            log_level = _logging.WARNING if os.environ.get("FLASK_ENV") == "production" else _logging.INFO
            fst_logger.setLevel(log_level)
        except Exception as _e:
            pass

        # Seed des rôles par défaut si absents
        try:
            for role_name, description in [
                ("admin", "Administrateur - tous les droits"),
                ("creator", "Créateur de questionnaire"),
                ("respondent", "Répondant de questionnaire"),
            ]:
                if not user_datastore.find_role(role_name):
                    user_datastore.create_role(name=role_name, description=description)
        except Exception as se:
            structured_logger.warning("Seed des rôles échoué", error=str(se))

        structured_logger.info("Flask-Security-Too initialisé avec succès")

    except Exception as e:
        structured_logger.error("Erreur initialisation Flask-Security-Too", exception=e)
        structured_logger.error(f"Détails de l'erreur: {str(e)}")
        raise

    # Enregistrer les blueprints
    app.register_blueprint(forms_bp, url_prefix="/api")
    app.register_blueprint(questions_bp, url_prefix="/api")
    app.register_blueprint(responses_bp, url_prefix="/api")
    app.register_blueprint(docs_bp, url_prefix="/api")
    app.register_blueprint(security_auth_bp, url_prefix="/api")
    app.register_blueprint(files_bp, url_prefix="/api")
    app.register_blueprint(monitoring_bp, url_prefix="/api")

    # Route de santé simple
    @app.route("/api/health")
    def health():
        """Vérifier l'état de l'API"""
        return jsonify(
            {
                "status": "healthy",
                "message": "FormForge POC Backend with Flask-Security-Too is running",
                "version": "2.0.0",
                "security": "Flask-Security-Too",
            }
        )


    # Route de test des headers de sécurité
    @app.route("/api/security/headers", methods=["GET"])
    def test_security_headers():
        """Tester les headers de sécurité"""
        from flask import request

        return jsonify(
            {
                "success": True,
                "message": "Headers de sécurité actifs",
                "headers": dict(request.headers),
                "security_info": {
                    "https": request.is_secure,
                    "user_agent": request.headers.get("User-Agent", "Unknown"),
                    "origin": request.headers.get("Origin", "None"),
                    "referer": request.headers.get("Referer", "None"),
                },
            }
        )

    # Logger le démarrage de l'application
    log_application_startup(app)

    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        from utils.structured_logger import structured_logger

        structured_logger.warning("404 Error", error=str(error))
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        from utils.structured_logger import structured_logger

        structured_logger.error("500 Error", error=str(error))
        return jsonify({"error": "Internal server error", "details": str(error)}), 500

    return app


# Créer l'instance app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
