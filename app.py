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

    # Configuration CORS sécurisée et headers de sécurité
    try:
        from utils.security_middleware import setup_security_middleware

        setup_security_middleware(app)
        logger.info("🔒 Middlewares de sécurité configurés avec succès")
    except Exception as e:
        logger.error(f"Erreur configuration middlewares de sécurité: {e}")
        # Continuer sans les middlewares de sécurité en cas d'erreur
        from flask_cors import CORS

        CORS(app)

    # Configuration du middleware de rate limiting global
    try:
        from utils.rate_limit_middleware import setup_rate_limit_middleware

        setup_rate_limit_middleware(app)
        logger.info("🚦 Middleware de rate limiting configuré avec succès")
    except Exception as e:
        logger.error(f"Erreur configuration middleware rate limiting: {e}")

    # Middleware de diagnostic pour tracer toutes les requêtes
    @app.before_request
    def log_request_info():
        from flask import request
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"🔍 REQUEST: {request.method} {request.url}")
        logger.info(f"🔍 REQUEST: Headers: {dict(request.headers)}")
        logger.info(f"🔍 REQUEST: Remote: {request.remote_addr}")

        if request.method in ["POST", "PUT"]:
            try:
                data = request.get_json()
                logger.info(f"🔍 REQUEST: JSON: {data}")
            except Exception as e:
                logger.info(f"🔍 REQUEST: Raw: {request.get_data()}")

    @app.after_request
    def log_response_info(response):
        from flask import request
        import logging

        logger = logging.getLogger(__name__)

        logger.info(
            f"🔍 RESPONSE: {response.status_code} - {request.method} {request.url}"
        )
        return response

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

        # Configuration minimale pour Flask-Security-Too 5.x - Désactivée pour éviter les conflits
        app.config.update(
            {
                "SECURITY_PASSWORD_HASH": "pbkdf2_sha256",
                "SECURITY_PASSWORD_SALT": app.config.get(
                    "SECURITY_PASSWORD_SALT", "dev-salt"
                ),
                "SECURITY_JSON_ENABLED": True,
                "SECURITY_JSON": True,
                "SECURITY_RETURN_GENERIC_RESPONSES": True,
                "SECURITY_REGISTERABLE": False,  # Désactivé - nous gérons manuellement
                "SECURITY_RECOVERABLE": False,
                "SECURITY_CHANGEABLE": False,  # Désactivé - nous gérons manuellement
                "SECURITY_CONFIRMABLE": False,
                "SECURITY_TRACKABLE": True,
                "SECURITY_SEND_REGISTER_EMAIL": False,
                "SECURITY_SEND_PASSWORD_CHANGE_EMAIL": False,
                "WTF_CSRF_ENABLED": False,
                "SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS": True,
                # Ne pas définir les URLs automatiques pour éviter les conflits
            }
        )

        # Initialiser Flask-Security sans enregistrement automatique des blueprints
        security = Security(app, user_datastore, register_blueprint=False)

        # Configuration des templates (désactivé pour API)
        app.config["SECURITY_EMAIL_SENDER"] = app.config.get(
            "MAIL_DEFAULT_SENDER", "noreply@formforge.com"
        )

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
    app.register_blueprint(security_auth_bp, url_prefix="/api")  # Nouveau blueprint
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

    # Route de diagnostic pour tracer les requêtes
    @app.route("/api/debug/request", methods=["GET", "POST", "PUT", "DELETE"])
    def debug_request():
        """Diagnostic des requêtes entrantes"""
        from flask import request
        import logging

        logger = logging.getLogger(__name__)

        logger.info(f"🔍 DEBUG REQUEST: Méthode: {request.method}")
        logger.info(f"🔍 DEBUG REQUEST: URL: {request.url}")
        logger.info(f"🔍 DEBUG REQUEST: Headers: {dict(request.headers)}")
        logger.info(f"🔍 DEBUG REQUEST: Remote Addr: {request.remote_addr}")
        logger.info(f"🔍 DEBUG REQUEST: User Agent: {request.user_agent}")

        if request.method in ["POST", "PUT"]:
            try:
                data = request.get_json()
                logger.info(f"🔍 DEBUG REQUEST: JSON Data: {data}")
            except Exception as e:
                logger.info(f"🔍 DEBUG REQUEST: Erreur JSON: {e}")
                logger.info(f"🔍 DEBUG REQUEST: Raw Data: {request.get_data()}")

        return jsonify(
            {
                "success": True,
                "message": "Requête reçue et loggée",
                "method": request.method,
                "url": request.url,
                "headers": dict(request.headers),
                "remote_addr": request.remote_addr,
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

    # Route de test pour le rate limiting
    @app.route("/api/test/rate-limit", methods=["GET"])
    @rate_limit("test_rate_limit")
    def test_rate_limit():
        """Test du rate limiting"""
        return jsonify(
            {
                "success": True,
                "message": "Rate limiting test",
                "timestamp": datetime.utcnow().isoformat(),
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
