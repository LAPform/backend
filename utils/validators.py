"""
Utilitaires de validation pour FormForge
"""

import re
from typing import Any, Dict, List, Optional
from datetime import datetime


class DataValidator:
    """Classe pour valider les données"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Valider un email"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valider un numéro de téléphone"""
        # Supprimer les espaces et caractères spéciaux
        clean_phone = re.sub(r"[^\d+]", "", phone)
        # Vérifier la longueur et le format
        return len(clean_phone) >= 10 and clean_phone.startswith(("+", "0"))

    @staticmethod
    def validate_url(url: str) -> bool:
        """Valider une URL"""
        pattern = r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$"
        return re.match(pattern, url) is not None

    @staticmethod
    def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
        """Valider une date"""
        try:
            datetime.strptime(date_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_time(time_str: str, format: str = "%H:%M") -> bool:
        """Valider une heure"""
        try:
            datetime.strptime(time_str, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_number(
        value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None
    ) -> bool:
        """Valider un nombre"""
        try:
            num = float(value)
            if min_val is not None and num < min_val:
                return False
            if max_val is not None and num > max_val:
                return False
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_text_length(
        text: str, min_length: int = 0, max_length: Optional[int] = None
    ) -> bool:
        """Valider la longueur d'un texte"""
        length = len(text)
        if length < min_length:
            return False
        if max_length is not None and length > max_length:
            return False
        return True

    @staticmethod
    def validate_required(value: Any) -> bool:
        """Valider qu'un champ est requis"""
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
        if isinstance(value, list) and len(value) == 0:
            return False
        return True

    @staticmethod
    def validate_choice(value: Any, choices: List[Any]) -> bool:
        """Valider qu'une valeur est dans une liste de choix"""
        return value in choices

    @staticmethod
    def validate_multiple_choices(values: List[Any], choices: List[Any]) -> bool:
        """Valider que toutes les valeurs sont dans une liste de choix"""
        if not isinstance(values, list):
            return False
        return all(choice in choices for choice in values)

    @staticmethod
    def validate_regex(value: str, pattern: str) -> bool:
        """Valider une valeur avec une regex"""
        try:
            return re.match(pattern, value) is not None
        except re.error:
            return False

    @classmethod
    def validate_form_data(cls, form_data: Dict, validation_rules: Dict) -> Dict:
        """Valider des données de formulaire selon des règles"""
        errors = {}

        for field, rules in validation_rules.items():
            value = form_data.get(field)

            # Vérifier si le champ est requis
            if rules.get("required", False) and not cls.validate_required(value):
                errors[field] = f"{field} est requis"
                continue

            # Si le champ n'est pas requis et vide, passer au suivant
            if not cls.validate_required(value):
                continue

            # Valider selon le type
            field_type = rules.get("type", "text")

            if field_type == "email" and not cls.validate_email(str(value)):
                errors[field] = "Format d'email invalide"

            elif field_type == "phone" and not cls.validate_phone(str(value)):
                errors[field] = "Format de téléphone invalide"

            elif field_type == "url" and not cls.validate_url(str(value)):
                errors[field] = "Format d'URL invalide"

            elif field_type == "date" and not cls.validate_date(str(value)):
                errors[field] = "Format de date invalide"

            elif field_type == "time" and not cls.validate_time(str(value)):
                errors[field] = "Format d'heure invalide"

            elif field_type == "number":
                if not cls.validate_number(value, rules.get("min"), rules.get("max")):
                    errors[field] = "Valeur numérique invalide"

            elif field_type == "text":
                if not cls.validate_text_length(
                    str(value), rules.get("min_length", 0), rules.get("max_length")
                ):
                    errors[field] = "Longueur de texte invalide"

            elif field_type == "choice":
                if not cls.validate_choice(value, rules.get("choices", [])):
                    errors[field] = "Choix invalide"

            elif field_type == "multiple_choices":
                if not cls.validate_multiple_choices(value, rules.get("choices", [])):
                    errors[field] = "Choix multiples invalides"

            elif field_type == "regex":
                if not cls.validate_regex(str(value), rules.get("pattern", "")):
                    errors[field] = "Format invalide"

        return {"valid": len(errors) == 0, "errors": errors}
