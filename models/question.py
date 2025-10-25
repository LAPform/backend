"""
Modèle Question pour FormForge
"""

import uuid
import json
from typing import Optional, List, Dict, Any
from .database import DatabaseManager


class Question:
    """Modèle pour les questions"""

    # Types de questions supportés
    QUESTION_TYPES = [
        "text",  # Texte court
        "textarea",  # Texte long
        "email",  # Email
        "phone",  # Téléphone
        "url",  # URL
        "date",  # Date
        "time",  # Heure
        "number",  # Nombre
        "choice",  # Choix simple (radio)
        "multiple_choices",  # Choix multiple
        "checkbox",  # Cases à cocher
        "radio",  # Boutons radio
    ]

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self,
        form_id: str,
        type: str,
        text: str,
        options: List = None,
        required: bool = False,
        validation: Dict = None,
        order_index: int = 0,
    ) -> str:
        """Créer une nouvelle question"""
        if type not in self.QUESTION_TYPES:
            raise ValueError(f"Type de question invalide: {type}")

        question_id = str(uuid.uuid4())
        options = options or []
        validation = validation or {}

        query = """
            INSERT INTO questions (id, form_id, type, text, options, required, validation, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query,
            (
                question_id,
                form_id,
                type,
                text,
                json.dumps(options),
                required,
                json.dumps(validation),
                order_index,
            ),
        )
        return question_id

    def get_by_id(self, question_id: str) -> Optional[Dict]:
        """Récupérer une question par ID"""
        query = "SELECT * FROM questions WHERE id = ?"
        results = self.db.execute_query(query, (question_id,), fetch=True)

        if results and len(results) > 0:
            question_data = results[0]  # Premier résultat
            # Désérialiser les options et validation JSON de manière sécurisée
            options_str = question_data.get("options", "[]")
            if options_str and options_str != "[]":
                try:
                    question_data["options"] = json.loads(options_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    question_data["options"] = []
            else:
                question_data["options"] = []

            validation_str = question_data.get("validation", "{}")
            if validation_str and validation_str != "{}":
                try:
                    question_data["validation"] = json.loads(validation_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    question_data["validation"] = {}
            else:
                question_data["validation"] = {}
            return question_data
        return None

    def get_by_form_id(self, form_id: str) -> List[Dict]:
        """Récupérer toutes les questions d'un formulaire"""
        query = """
            SELECT * FROM questions 
            WHERE form_id = ? 
            ORDER BY order_index
        """
        results = self.db.execute_query(query, (form_id,), fetch=True)
        questions = []
        for row in results:
            question_data = dict(row)
            # Désérialiser les options et validation JSON de manière sécurisée
            options_str = question_data.get("options", "[]")
            if options_str and options_str != "[]":
                try:
                    question_data["options"] = json.loads(options_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    question_data["options"] = []
            else:
                question_data["options"] = []

            validation_str = question_data.get("validation", "{}")
            if validation_str and validation_str != "{}":
                try:
                    question_data["validation"] = json.loads(validation_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    question_data["validation"] = {}
            else:
                question_data["validation"] = {}
            questions.append(question_data)
        return questions

    def update(
        self,
        question_id: str,
        type: str = None,
        text: str = None,
        options: List = None,
        required: bool = None,
        validation: Dict = None,
    ) -> bool:
        """Mettre à jour une question"""
        updates = []
        params = []

        if type is not None:
            if type not in self.QUESTION_TYPES:
                raise ValueError(f"Type de question invalide: {type}")
            updates.append("type = ?")
            params.append(type)

        if text is not None:
            updates.append("text = ?")
            params.append(text)

        if options is not None:
            updates.append("options = ?")
            params.append(json.dumps(options))

        if required is not None:
            updates.append("required = ?")
            params.append(required)

        if validation is not None:
            updates.append("validation = ?")
            params.append(json.dumps(validation))

        if not updates:
            return False

        params.append(question_id)

        query = f"""
            UPDATE questions 
            SET {', '.join(updates)}
            WHERE id = ?
        """

        rows_affected = self.db.execute_query(query, tuple(params))
        return rows_affected > 0

    def delete(self, question_id: str) -> bool:
        """Supprimer une question"""
        query = "DELETE FROM questions WHERE id = ?"
        rows_affected = self.db.execute_query(query, (question_id,))
        return rows_affected > 0

    def reorder(self, form_id: str, question_orders: List[Dict]) -> bool:
        """Réorganiser les questions d'un formulaire"""
        queries = []

        for order_data in question_orders:
            question_id = order_data["question_id"]
            order_index = order_data["order_index"]

            query = """
                UPDATE questions 
                SET order_index = ? 
                WHERE id = ? AND form_id = ?
            """
            queries.append((query, (order_index, question_id, form_id)))

        return self.db.execute_transaction(queries)

    def validate_response(self, question_id: str, response: Any) -> Dict:
        """Valider une réponse selon les règles de la question"""
        question = self.get_by_id(question_id)
        if not question:
            return {"valid": False, "error": "Question not found"}

        validation_rules = question.get("validation", {})
        required = question.get("required", False)

        # Vérifier si la réponse est requise
        if required and (response is None or response == "" or response == []):
            return {"valid": False, "error": "This question is required"}

        # Validation selon le type
        if question["type"] == "email":
            if response and "@" not in str(response):
                return {"valid": False, "error": "Invalid email format"}

        elif question["type"] == "number":
            if (
                response
                and not str(response).replace(".", "").replace("-", "").isdigit()
            ):
                return {"valid": False, "error": "Invalid number format"}

        elif question["type"] == "multiple":
            if response and response not in question.get("options", []):
                return {"valid": False, "error": "Invalid option selected"}

        elif question["type"] == "checkbox":
            if response and not all(
                opt in question.get("options", []) for opt in response
            ):
                return {"valid": False, "error": "Invalid options selected"}

        # Validation personnalisée
        if (
            "min_length" in validation_rules
            and len(str(response)) < validation_rules["min_length"]
        ):
            return {
                "valid": False,
                "error": f'Minimum length: {validation_rules["min_length"]}',
            }

        if (
            "max_length" in validation_rules
            and len(str(response)) > validation_rules["max_length"]
        ):
            return {
                "valid": False,
                "error": f'Maximum length: {validation_rules["max_length"]}',
            }

        return {"valid": True}
