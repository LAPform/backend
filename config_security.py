"""
Configuration Flask-Security-Too pour FormForge
"""

import os
from datetime import timedelta


class SecurityConfig:
    """Configuration pour Flask-Security-Too"""

    # Configuration de base
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Configuration de sécurité
    SECURITY_PASSWORD_SALT = os.environ.get(
        "SECURITY_PASSWORD_SALT", "dev-salt-change-in-production"
    )
    SECURITY_PASSWORD_HASH = "pbkdf2_sha256"
    SECURITY_PASSWORD_SINGLE_HASH = True

    # Configuration des sessions
    SECURITY_TOKEN_AUTHENTICATION_HEADER = "Authorization"
    SECURITY_TOKEN_AUTHENTICATION_KEY = "token"
    SECURITY_TOKEN_MAX_AGE = 3600  # 1 heure

    # Configuration des URLs
    SECURITY_LOGIN_URL = "/api/auth/login"
    SECURITY_LOGOUT_URL = "/api/auth/logout"
    SECURITY_REGISTER_URL = "/api/auth/register"
    SECURITY_RESET_URL = "/api/auth/reset"
    SECURITY_CHANGE_URL = "/api/auth/change"
    SECURITY_CONFIRM_URL = "/api/auth/confirm"

    # Configuration des réponses
    SECURITY_RETURN_GENERIC_RESPONSES = True
    SECURITY_JSON_ENABLED = True

    # Configuration de l'email (pour le futur)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@formforge.com")

    # Configuration des fonctionnalités
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_CONFIRMABLE = False  # Désactivé pour le POC
    SECURITY_TRACKABLE = True

    # Configuration des mots de passe
    SECURITY_PASSWORD_LENGTH_MIN = 8
    SECURITY_PASSWORD_COMPLEXITY_CHECKER = "zxcvbn"  # Validation de complexité activée

    # Configuration des sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Configuration CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # Configuration des messages
    SECURITY_MSG_INVALID_PASSWORD = ("Mot de passe invalide", "error")
    SECURITY_MSG_PASSWORD_NOT_PROVIDED = ("Mot de passe requis", "error")
    SECURITY_MSG_USER_DOES_NOT_EXIST = ("Utilisateur non trouvé", "error")
    SECURITY_MSG_INVALID_EMAIL_ADDRESS = ("Adresse email invalide", "error")
    SECURITY_MSG_EMAIL_ALREADY_ASSOCIATED = ("Email déjà associé à un compte", "error")
    SECURITY_MSG_PASSWORD_INVALID_LENGTH = ("Mot de passe trop court", "error")
    SECURITY_MSG_LOGIN = ("Connexion réussie", "success")
    SECURITY_MSG_LOGOUT = ("Déconnexion réussie", "success")
    SECURITY_MSG_REGISTER = ("Inscription réussie", "success")
    SECURITY_MSG_RESET = ("Mot de passe réinitialisé", "success")
    SECURITY_MSG_CHANGE = ("Mot de passe modifié", "success")
