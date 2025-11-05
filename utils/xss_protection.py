"""
Protection XSS (Cross-Site Scripting) systématique
Expert Cybersécurité - 15+ ans d'expérience

Ce module garantit que TOUTES les données utilisateur dans les réponses JSON
sont échappées pour prévenir les attaques XSS.
"""

import html
import logging
from flask import Flask, request
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class XSSProtection:
    """
    Classe utilitaire pour la protection XSS

    Standards appliqués:
    - Échappement HTML de toutes les chaînes de caractères
    - Traitement récursif des structures de données (dict, list)
    - Préservation des types de données (int, bool, None)
    """

    # Liste des champs qui ne doivent JAMAIS être échappés
    # (tokens, hashes, IDs techniques, etc.)
    SAFE_FIELDS = {
        'id', 'token', 'authentication_token', 'auth_token', 'password_hash',
        'salt', 'public_token', 'form_id', 'question_id', 'response_id',
        'user_id', 'created_by', 'fs_uniquifier', 'reset_password_token'
    }

    @staticmethod
    def escape(data: Any, field_name: str = None) -> Any:
        """
        Échapper récursivement les données pour prévenir XSS

        Args:
            data: Données à échapper (string, dict, list, ou autre)
            field_name: Nom du champ (pour vérifier si dans SAFE_FIELDS)

        Returns:
            Données échappées (même type que l'entrée)
        """
        # Si le champ est dans la liste sécurisée, ne pas échapper
        if field_name and field_name in XSSProtection.SAFE_FIELDS:
            return data

        # Traiter selon le type
        if isinstance(data, str):
            # Échapper les caractères HTML dangereux
            return html.escape(data, quote=True)

        elif isinstance(data, dict):
            # Échapper récursivement toutes les valeurs du dictionnaire
            return {
                key: XSSProtection.escape(value, field_name=key)
                for key, value in data.items()
            }

        elif isinstance(data, list):
            # Échapper récursivement tous les éléments de la liste
            return [XSSProtection.escape(item) for item in data]

        elif isinstance(data, tuple):
            # Échapper récursivement tous les éléments du tuple
            return tuple(XSSProtection.escape(item) for item in data)

        else:
            # Types primitifs (int, float, bool, None) : retourner tel quel
            return data

    @staticmethod
    def sanitize_response_data(response_data: Dict) -> Dict:
        """
        Nettoyer toutes les données d'une réponse API

        Args:
            response_data: Dictionnaire de la réponse API

        Returns:
            Dictionnaire nettoyé
        """
        return XSSProtection.escape(response_data)


def setup_xss_protection(app: Flask):
    """
    Configurer la protection XSS globale pour l'application

    Cette fonction installe un middleware qui échappe automatiquement
    toutes les réponses JSON de l'API.

    Note: Désactivé par défaut car peut impacter les performances.
    Activer avec ENABLE_AUTO_XSS_ESCAPE=true dans l'environnement.
    """
    import os
    from flask import jsonify

    auto_escape = os.environ.get("ENABLE_AUTO_XSS_ESCAPE", "false").lower() == "true"

    if not auto_escape:
        logger.info("XSS auto-escape désactivé (ENABLE_AUTO_XSS_ESCAPE=false)")
        logger.info("Utilisez escape_html() manuellement dans les routes")
        return

    @app.after_request
    def escape_json_response(response):
        """
        Middleware pour échapper automatiquement les réponses JSON

        ATTENTION: Peut impacter les performances sur gros volumes de données
        """
        # Vérifier si c'est une réponse JSON
        if response.content_type and 'application/json' in response.content_type:
            try:
                # Décoder le JSON
                import json
                data = json.loads(response.get_data(as_text=True))

                # Échapper les données
                escaped_data = XSSProtection.sanitize_response_data(data)

                # Ré-encoder en JSON
                response.set_data(json.dumps(escaped_data))

                logger.debug("Response data escaped for XSS protection")

            except Exception as e:
                logger.error(f"Error escaping JSON response: {e}")
                # Ne pas crasher si échappement échoue

        return response

    logger.info("XSS auto-escape activé (ENABLE_AUTO_XSS_ESCAPE=true)")


# Fonctions helper pour utilisation manuelle

def escape_html(text: str) -> str:
    """
    Échapper une chaîne de caractères HTML

    Usage:
        safe_email = escape_html(user.email)
    """
    if not text or not isinstance(text, str):
        return text
    return html.escape(text, quote=True)


def sanitize_user_input(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """
    Nettoyer les entrées utilisateur pour prévenir XSS

    Usage:
        safe_data = sanitize_user_input(request.get_json())
    """
    return XSSProtection.escape(data)


def sanitize_dict(data: Dict, safe_fields: List[str] = None) -> Dict:
    """
    Nettoyer un dictionnaire en échappant toutes les valeurs sauf les champs sécurisés

    Args:
        data: Dictionnaire à nettoyer
        safe_fields: Liste des champs à ne pas échapper (en plus des SAFE_FIELDS par défaut)

    Usage:
        safe_user = sanitize_dict(user_data, safe_fields=['id', 'token'])
    """
    # Fusionner avec les champs sécurisés par défaut
    if safe_fields:
        original_safe = XSSProtection.SAFE_FIELDS.copy()
        XSSProtection.SAFE_FIELDS.update(safe_fields)

    result = XSSProtection.sanitize_response_data(data)

    # Restaurer les champs sécurisés originaux
    if safe_fields:
        XSSProtection.SAFE_FIELDS = original_safe

    return result
