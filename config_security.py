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

    # Configuration des sessions pour API REST (simplifiée)
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

    # Configuration des réponses pour API REST
    SECURITY_RETURN_GENERIC_RESPONSES = True
    SECURITY_JSON_ENABLED = True
    SECURITY_JSON = True  # Force les réponses JSON

    # Configuration de l'email (désactivé pour API REST)
    MAIL_SERVER = None
    MAIL_PORT = None
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = "noreply@formforge.com"

    # Configuration des fonctionnalités pour API REST
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = False  # Désactivé pour API REST
    SECURITY_CHANGEABLE = True
    SECURITY_CONFIRMABLE = False  # Désactivé pour API REST
    SECURITY_TRACKABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False  # Pas d'email d'inscription
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False  # Pas d'email de changement
    
    # Configuration pour éviter les erreurs de session
    SECURITY_SESSION_REFRESH_EACH_REQUEST = False
    SECURITY_SESSION_REFRESH_WITHIN = "1 days"

    # Configuration des mots de passe
    SECURITY_PASSWORD_LENGTH_MIN = 8
    SECURITY_PASSWORD_COMPLEXITY_CHECKER = "zxcvbn"  # Validation de complexité activée

    # Configuration des sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Configuration CSRF - Désactivé pour API REST
    WTF_CSRF_ENABLED = False
    WTF_CSRF_TIME_LIMIT = 3600
    SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS = True
    SECURITY_CSRF_COOKIE = None
    SECURITY_CSRF_COOKIE_NAME = None
    
    # Désactiver les templates pour API REST
    SECURITY_TEMPLATE_DIR = None
    SECURITY_LOGIN_USER_TEMPLATE = None
    SECURITY_REGISTER_USER_TEMPLATE = None
    SECURITY_FORGOT_PASSWORD_TEMPLATE = None
    SECURITY_RESET_PASSWORD_TEMPLATE = None
    SECURITY_CHANGE_PASSWORD_TEMPLATE = None

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
