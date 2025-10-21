"""
Application principale FormForge Flask
POC - Google Forms Clone Backend
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restx import Api, Resource, fields
from models.database import DatabaseManager
from routes.forms import forms_bp
from routes.questions import questions_bp
from routes.responses import responses_bp
from routes.docs import docs_bp
from docs.schemas import *
from config import Config


def create_app():
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)

    # Configuration
    app.config.from_object(Config)

    # CORS pour les requêtes frontend
    CORS(app)

    # Initialiser l'API REST avec Swagger
    api = Api(
        app,
        version='1.0.0',
        title='FormForge API',
        description='API REST pour FormForge - Clone de Google Forms',
        doc='/api/docs/',  # URL de la documentation
        prefix='/api'
    )

    # Initialiser la base de données
    app.db = DatabaseManager()
    app.db.init_database()

    # Enregistrer les blueprints
    app.register_blueprint(forms_bp, url_prefix="/api")
    app.register_blueprint(questions_bp, url_prefix="/api")
    app.register_blueprint(responses_bp, url_prefix="/api")
    app.register_blueprint(docs_bp, url_prefix="/api")

    # Route de santé avec documentation
    @api.route('/health')
    class Health(Resource):
        @api.marshal_with(HealthSchema)
        @api.doc('health_check')
        def get(self):
            """Vérifier l'état de l'API"""
            return {
                "status": "healthy",
                "message": "FormForge POC Backend is running",
                "version": "1.0.0",
            }

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
