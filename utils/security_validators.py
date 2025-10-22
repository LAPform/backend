"""
Validateurs de sécurité pour FormForge
"""

import re
import html
from typing import Any, Dict, List, Optional
from utils.validators import DataValidator


class SecurityValidator:
    """Classe pour les validations de sécurité"""

    # Patterns dangereux à bloquer
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Scripts
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>',  # Iframes
        r'<object[^>]*>',  # Objects
        r'<embed[^>]*>',  # Embeds
        r'<link[^>]*>',  # Links
        r'<meta[^>]*>',  # Meta tags
        r'<style[^>]*>.*?</style>',  # Styles
        r'<form[^>]*>',  # Forms
        r'<input[^>]*>',  # Inputs
        r'<button[^>]*>',  # Buttons
        r'<select[^>]*>',  # Selects
        r'<textarea[^>]*>',  # Textareas
    ]

    # Caractères SQL dangereux
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|OR|AND)\b)',
        r'(\b(script|javascript|vbscript|onload|onerror|onclick)\b)',
        r'([\'";\\])',
        r'(\b(0x|0X)[0-9a-fA-F]+)',  # Hex values
    ]

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Nettoyer un texte d'entrée"""
        if not isinstance(text, str):
            return str(text)
        
        # Échapper les caractères HTML
        text = html.escape(text)
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les caractères de contrôle
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()

    @staticmethod
    def validate_no_xss(text: str) -> bool:
        """Vérifier qu'un texte ne contient pas de XSS"""
        if not isinstance(text, str):
            return True
        
        text_lower = text.lower()
        
        # Vérifier les patterns dangereux
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        return True

    @staticmethod
    def validate_no_sql_injection(text: str) -> bool:
        """Vérifier qu'un texte ne contient pas d'injection SQL"""
        if not isinstance(text, str):
            return True
        
        text_lower = text.lower()
        
        # Vérifier les patterns d'injection SQL
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        return True

    @staticmethod
    def validate_safe_filename(filename: str) -> bool:
        """Vérifier qu'un nom de fichier est sûr"""
        if not isinstance(filename, str):
            return False
        
        # Caractères interdits dans les noms de fichiers
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        
        for char in dangerous_chars:
            if char in filename:
                return False
        
        # Vérifier la longueur
        if len(filename) > 255:
            return False
        
        # Vérifier qu'il n'y a pas de XSS
        if not SecurityValidator.validate_no_xss(filename):
            return False
        
        return True

    @staticmethod
    def validate_json_structure(data: Any, max_depth: int = 10) -> bool:
        """Vérifier qu'une structure JSON est sûre"""
        if max_depth <= 0:
            return False
        
        if isinstance(data, dict):
            # Vérifier la taille du dictionnaire
            if len(data) > 1000:
                return False
            
            for key, value in data.items():
                # Vérifier la clé
                if not isinstance(key, str):
                    return False
                if not SecurityValidator.validate_no_xss(key):
                    return False
                
                # Vérifier récursivement la valeur
                if not SecurityValidator.validate_json_structure(value, max_depth - 1):
                    return False
        
        elif isinstance(data, list):
            # Vérifier la taille de la liste
            if len(data) > 1000:
                return False
            
            for item in data:
                if not SecurityValidator.validate_json_structure(item, max_depth - 1):
                    return False
        
        elif isinstance(data, str):
            # Vérifier la longueur de la chaîne
            if len(data) > 10000:
                return False
            
            # Vérifier qu'il n'y a pas de XSS
            if not SecurityValidator.validate_no_xss(data):
                return False
        
        return True

    @classmethod
    def validate_form_data_security(cls, form_data: Dict) -> Dict:
        """Valider la sécurité des données de formulaire"""
        errors = []
        
        for field, value in form_data.items():
            if isinstance(value, str):
                # Vérifier XSS
                if not cls.validate_no_xss(value):
                    errors.append(f"Le champ '{field}' contient du contenu potentiellement dangereux")
                
                # Vérifier injection SQL
                if not cls.validate_no_sql_injection(value):
                    errors.append(f"Le champ '{field}' contient des caractères potentiellement dangereux")
                
                # Vérifier la longueur
                if len(value) > 10000:
                    errors.append(f"Le champ '{field}' est trop long")
            
            elif isinstance(value, dict):
                # Vérifier récursivement
                if not cls.validate_json_structure(value):
                    errors.append(f"Le champ '{field}' a une structure invalide")
        
        return {"valid": len(errors) == 0, "errors": errors}

    @staticmethod
    def sanitize_form_data(form_data: Dict) -> Dict:
        """Nettoyer les données de formulaire"""
        sanitized = {}
        
        for field, value in form_data.items():
            if isinstance(value, str):
                sanitized[field] = SecurityValidator.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[field] = SecurityValidator.sanitize_form_data(value)
            elif isinstance(value, list):
                sanitized[field] = [
                    SecurityValidator.sanitize_input(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[field] = value
        
        return sanitized
