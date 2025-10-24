"""
Utilitaires de sécurité pour FormForge
"""

import html
import re
from typing import Any, Optional


def escape_html(text: Any) -> str:
    """
    Échapper les caractères HTML pour éviter le XSS
    
    Args:
        text: Texte à échapper (peut être None, str, int, etc.)
    
    Returns:
        str: Texte échappé sécurisé
    """
    if text is None:
        return ""
    
    # Convertir en string si nécessaire
    text_str = str(text)
    
    # Échapper les caractères HTML dangereux
    escaped = html.escape(text_str, quote=True)
    
    return escaped


def sanitize_user_input(text: str, max_length: int = 255) -> str:
    """
    Sanitiser l'entrée utilisateur pour éviter les injections
    
    Args:
        text: Texte à sanitiser
        max_length: Longueur maximale autorisée
    
    Returns:
        str: Texte sanitisé
    """
    if not text:
        return ""
    
    # Limiter la longueur
    text = text[:max_length]
    
    # Supprimer les caractères de contrôle
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Échapper HTML
    text = escape_html(text)
    
    return text.strip()


def validate_safe_string(text: str) -> bool:
    """
    Valider qu'une chaîne ne contient pas de contenu malveillant
    
    Args:
        text: Texte à valider
    
    Returns:
        bool: True si le texte est sûr
    """
    if not text:
        return True
    
    # Patterns dangereux à détecter
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Scripts
        r'javascript:',                # JavaScript URLs
        r'on\w+\s*=',                 # Event handlers
        r'<iframe[^>]*>',             # Iframes
        r'<object[^>]*>',             # Objects
        r'<embed[^>]*>',              # Embeds
        r'<link[^>]*>',                # Links
        r'<meta[^>]*>',                # Meta tags
    ]
    
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            return False
    
    return True


def create_safe_response(data: dict) -> dict:
    """
    Créer une réponse JSON sécurisée en échappant tous les champs texte
    
    Args:
        data: Dictionnaire de données
    
    Returns:
        dict: Dictionnaire sécurisé
    """
    safe_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = escape_html(value)
        elif isinstance(value, dict):
            safe_data[key] = create_safe_response(value)
        elif isinstance(value, list):
            safe_data[key] = [
                escape_html(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            safe_data[key] = value
    
    return safe_data