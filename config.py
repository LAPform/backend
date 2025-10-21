"""
Configuration pour l'application FormForge Flask
"""

import os
from pathlib import Path


class Config:
    """Configuration de base"""

    # Clé secrète Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Configuration base de données
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "sqlite:///formforge_poc.db"
    )

    # Configuration upload
    UPLOAD_FOLDER = "static/uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Configuration CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]

    # Mode debug
    DEBUG = os.environ.get("FLASK_ENV") == "development"

    @staticmethod
    def init_app(app):
        """Initialisation de l'application"""
        # Créer les dossiers nécessaires
        os.makedirs("static/uploads", exist_ok=True)
        os.makedirs("data", exist_ok=True)


class DevelopmentConfig(Config):
    """Configuration de développement"""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuration de production"""

    DEBUG = False
    TESTING = False

    # Sécurité renforcée en production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestingConfig(Config):
    """Configuration de test"""

    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"


# Configuration par défaut
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": ProductionConfig,
}
