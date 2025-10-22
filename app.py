"""
Application principale FormForge Flask
POC - Google Forms Clone Backend
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Configuration du logging structuré
from utils.logging_middleware import (
    LoggingMiddleware,
    setup_logging_config,
    log_application_startup,
)

from models.database import DatabaseManager
from routes.forms import forms_bp
from routes.questions import questions_bp
from routes.responses import responses_bp
from routes.docs import docs_bp
from routes.auth import auth_bp
from routes.files import files_bp
from routes.monitoring import monitoring_bp
from config import Config


def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # Configuration du logging structuré
    setup_logging_config(app)

    # Middleware de logging (désactivé temporairement pour éviter les erreurs de contexte)
    # LoggingMiddleware(app)

    # CORS pour les requêtes frontend
    CORS(app)

    # Configuration API simple (sans Flask-RESTX pour éviter les conflits)

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

    # Enregistrer les blueprints
        app.register_blueprint(forms_bp, url_prefix="/api")
        app.register_blueprint(questions_bp, url_prefix="/api")
        app.register_blueprint(responses_bp, url_prefix="/api")
        app.register_blueprint(docs_bp, url_prefix="/api")
        app.register_blueprint(auth_bp, url_prefix="/api")
        app.register_blueprint(files_bp, url_prefix="/api")
        app.register_blueprint(monitoring_bp, url_prefix="/api")

    # Route de santé simple
    @app.route("/api/health")
    def health():
        """Vérifier l'état de l'API"""
        return jsonify(
            {
                "status": "healthy",
                "message": "FormForge POC Backend is running",
                "version": "1.0.0",
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
