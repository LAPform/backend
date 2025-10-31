"""
Configuration Flask-Security-Too pour FormForge
"""

import os
from datetime import timedelta


class SecurityConfig:
    """Configuration pour Flask-Security-Too"""

    # Configuration de base
    # SECRET_KEY doit être défini en production via variable d'environnement
    # En développement, utilise une valeur par défaut mais log un avertissement
    _secret_key = os.environ.get("SECRET_KEY")
    if not _secret_key:
        if os.environ.get("FLASK_ENV") == "production":
            raise ValueError(
                "SECRET_KEY doit être défini en production via variable d'environnement"
            )
        # En développement uniquement, utiliser une valeur par défaut
        import warnings

        warnings.warn(
            "SECRET_KEY non défini - utilisation d'une valeur par défaut (développement uniquement)",
            UserWarning,
        )
        _secret_key = "dev-secret-key-change-in-production"

    SECRET_KEY = _secret_key

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

    # Configuration des URLs - Désactivées pour éviter les conflits avec nos routes personnalisées
    # Ne pas définir ces URLs pour éviter que Flask-Security-Too les enregistre automatiquement

    # Configuration des réponses pour API REST
    SECURITY_RETURN_GENERIC_RESPONSES = True
    SECURITY_JSON_ENABLED = True
    SECURITY_JSON = True  # Force les réponses JSON

    # Configuration de l'email (activé pour la réinitialisation de mot de passe)
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@formforge.com")

    # Configuration des fonctionnalités pour API REST
    SECURITY_REGISTERABLE = False  # Désactivé - nous gérons l'inscription manuellement
    SECURITY_RECOVERABLE = True  # Activé pour la réinitialisation de mot de passe
    SECURITY_CHANGEABLE = False  # Désactivé - nous gérons le changement manuellement
    SECURITY_CONFIRMABLE = False  # Désactivé pour API REST
    SECURITY_TRACKABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False  # Pas d'email d'inscription
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False  # Pas d'email de changement
    SECURITY_SEND_PASSWORD_RESET_EMAIL = (
        True  # Activer l'envoi d'email de réinitialisation
    )

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
