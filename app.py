"""
Application principale FormForge Flask
POC - Google Forms Clone Backend
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from models.database import DatabaseManager
from routes.forms import forms_bp
from routes.questions import questions_bp
from routes.responses import responses_bp
from config import Config


def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # CORS pour les requêtes frontend
    CORS(app)

    # Initialiser la base de données
    app.db = DatabaseManager()
    app.db.init_database()

    # Enregistrer les blueprints
    app.register_blueprint(forms_bp, url_prefix="/api")
    app.register_blueprint(questions_bp, url_prefix="/api")
    app.register_blueprint(responses_bp, url_prefix="/api")

    # Route de santé
    @app.route("/api/health")
    def health():
        return jsonify(
            {
                "status": "healthy",
                "message": "FormForge POC Backend is running",
                "version": "1.0.0",
            }
        )

    # Gestion des erreurs
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app


# Créer l'instance app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
