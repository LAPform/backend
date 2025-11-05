"""
Module de sécurité des mots de passe
Expert Cybersécurité - 15+ ans d'expérience

Ce module garantit que TOUS les mots de passe dans l'application
respectent les standards de sécurité OWASP.
"""

import re
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class PasswordSecurityPolicy:
    """
    Politique de sécurité des mots de passe conforme OWASP

    Standards appliqués:
    - Longueur minimale: 8 caractères (OWASP recommande 8-12)
    - Au moins 1 majuscule
    - Au moins 1 minuscule
    - Au moins 1 chiffre
    - Au moins 1 caractère spécial
    - Pas de mots de passe communs (liste noire)
    """

    # Longueur minimale (OWASP: 8-12 caractères minimum)
    MIN_LENGTH = 8
    MAX_LENGTH = 128  # Limite raisonnable pour éviter DoS

    # Liste noire des mots de passe les plus courants (Top 20)
    BLACKLIST = {
        "password", "password123", "123456", "12345678", "qwerty",
        "abc123", "monkey", "letmein", "trustno1", "dragon",
        "baseball", "iloveyou", "master", "sunshine", "ashley",
        "bailey", "shadow", "123123", "654321", "superman"
    }

    @staticmethod
    def validate(password: str) -> tuple[bool, str]:
        """
        Valider un mot de passe selon la politique de sécurité

        Returns:
            (is_valid, message) où message explique l'erreur si invalide
        """
        if not password:
            return False, "Mot de passe requis"

        # Vérifier la longueur minimale
        if len(password) < PasswordSecurityPolicy.MIN_LENGTH:
            return False, f"Mot de passe trop court (minimum {PasswordSecurityPolicy.MIN_LENGTH} caractères)"

        # Vérifier la longueur maximale (protection DoS)
        if len(password) > PasswordSecurityPolicy.MAX_LENGTH:
            return False, f"Mot de passe trop long (maximum {PasswordSecurityPolicy.MAX_LENGTH} caractères)"

        # Vérifier au moins une majuscule
        if not re.search(r"[A-Z]", password):
            return False, "Le mot de passe doit contenir au moins une lettre majuscule"

        # Vérifier au moins une minuscule
        if not re.search(r"[a-z]", password):
            return False, "Le mot de passe doit contenir au moins une lettre minuscule"

        # Vérifier au moins un chiffre
        if not re.search(r"\d", password):
            return False, "Le mot de passe doit contenir au moins un chiffre"

        # Vérifier au moins un caractère spécial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            return False, "Le mot de passe doit contenir au moins un caractère spécial (!@#$%...)"

        # Vérifier contre la liste noire (case insensitive)
        if password.lower() in PasswordSecurityPolicy.BLACKLIST:
            return False, "Ce mot de passe est trop commun et facilement devinable"

        # Vérifier qu'il ne contient pas de mots de la liste noire
        password_lower = password.lower()
        for common_pwd in PasswordSecurityPolicy.BLACKLIST:
            if common_pwd in password_lower:
                return False, "Le mot de passe contient un mot trop commun"

        return True, "Mot de passe valide et sécurisé"

    @staticmethod
    def get_strength_score(password: str) -> int:
        """
        Calculer un score de force du mot de passe (0-100)

        Utilisé pour afficher un indicateur visuel dans le frontend
        """
        if not password:
            return 0

        score = 0

        # Longueur (max 30 points)
        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        # Complexité (max 40 points)
        if re.search(r"[a-z]", password):
            score += 10
        if re.search(r"[A-Z]", password):
            score += 10
        if re.search(r"\d", password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
            score += 10

        # Diversité de caractères (max 20 points)
        unique_chars = len(set(password))
        if unique_chars >= 6:
            score += 10
        if unique_chars >= 10:
            score += 10

        # Pas dans la liste noire (max 10 points)
        if password.lower() not in PasswordSecurityPolicy.BLACKLIST:
            score += 10

        return min(score, 100)


def require_strong_password(field_name="password"):
    """
    Décorateur pour valider automatiquement les mots de passe dans les requêtes

    Usage:
        @require_strong_password("password")
        def signup():
            # Le mot de passe a déjà été validé
            ...

        @require_strong_password("new_password")
        def change_password():
            # Le nouveau mot de passe a déjà été validé
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Récupérer les données JSON
            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "error": "Données manquantes",
                    "message": "Aucune donnée JSON fournie"
                }), 400

            # Récupérer le mot de passe
            password = data.get(field_name)

            if not password:
                return jsonify({
                    "success": False,
                    "error": "Mot de passe manquant",
                    "message": f"Le champ '{field_name}' est requis"
                }), 400

            # Valider le mot de passe
            is_valid, message = PasswordSecurityPolicy.validate(password)

            if not is_valid:
                logger.warning(f"Weak password attempt: {message}")
                return jsonify({
                    "success": False,
                    "error": "Mot de passe faible",
                    "message": message
                }), 400

            # Si validation OK, continuer
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Alias pour compatibilité avec le code existant
def validate_password_strength(password: str) -> tuple[bool, str]:
    """Alias pour PasswordSecurityPolicy.validate"""
    return PasswordSecurityPolicy.validate(password)
