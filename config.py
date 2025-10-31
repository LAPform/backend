"""
Configuration pour l'application FormForge Flask
"""

import os
from pathlib import Path


class Config:
    """Configuration de base"""

    # Clé secrète Flask - doit être définie via variable d'environnement en production
    # En développement uniquement, utilise une valeur par défaut
    _secret_key = os.environ.get("SECRET_KEY")
    if not _secret_key:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError(
                "SECRET_KEY doit être défini en production via variable d'environnement"
            )
        import warnings

        warnings.warn(
            "SECRET_KEY non défini - utilisation d'une valeur par défaut (développement uniquement)",
            UserWarning,
        )
        _secret_key = "dev-secret-key-change-in-production"

    SECRET_KEY = _secret_key

    # Configuration base de données
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///formforge_poc.db")

    # Configuration upload
    UPLOAD_FOLDER = "static/uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Configuration CORS sécurisée
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Configuration de sécurité
    SECURITY_HEADERS_ENABLED = True
    FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "false").lower() == "true"

    # Configuration des cookies sécurisés
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "true").lower() == "true"
    )
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

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
