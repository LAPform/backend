"""
Application principale FormForge Flask avec Flask-Security-Too
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security.utils import hash_password

# Configuration du logging structuré
from utils.logging_middleware import (
    LoggingMiddleware,
    setup_logging_config,
    log_application_startup,
)

from models.database import DatabaseManager
from models.security_models import User, Role, SecurityUserDatastore
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

    # CORS pour les requêtes frontend
    CORS(app)

    # Initialiser la base de données
    try:
        app.db = DatabaseManager()
        app.db.init_database()

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

        # Initialiser Flask-Security
        security = Security(app, user_datastore)

        # Configuration des templates (désactivé pour API)
        app.config["SECURITY_EMAIL_SENDER"] = app.config.get(
            "MAIL_DEFAULT_SENDER", "noreply@formforge.com"
        )

        structured_logger.info("Flask-Security-Too initialisé avec succès")

    except Exception as e:
        structured_logger.error("Erreur initialisation Flask-Security-Too", exception=e)
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

    # Route de test sans authentification
    @app.route("/api/test")
    def test():
        """Route de test sans authentification"""
        return jsonify(
            {
                "success": True,
                "message": "API accessible sans authentification",
                "timestamp": "2024-01-15T10:30:00Z",
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
