"""
Modèle Form pour FormForge
"""

import uuid
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from .database import DatabaseManager


class Form:
    """Modèle pour les formulaires"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(self, title: str, description: str = None, settings: Dict = None) -> str:
        """Créer un nouveau formulaire"""
        form_id = str(uuid.uuid4())
        settings = settings or {}

        query = """
            INSERT INTO forms (id, title, description, settings)
            VALUES (?, ?, ?, ?)
        """

        self.db.execute_query(
            query, (form_id, title, description, json.dumps(settings))
        )
        return form_id

    def get_by_id(self, form_id: str) -> Optional[Dict]:
        """Récupérer un formulaire par ID"""
        query = "SELECT * FROM forms WHERE id = ?"
        results = self.db.execute_query(query, (form_id,), fetch=True)

        if results and len(results) > 0:
            form_data = results[0]  # Premier résultat
            # Désérialiser les settings JSON de manière sécurisée
            settings_str = form_data.get("settings", "{}")
            if settings_str and settings_str != "{}":
                try:
                    form_data["settings"] = json.loads(settings_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    form_data["settings"] = {}
            else:
                form_data["settings"] = {}
            return form_data
        return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Récupérer tous les formulaires"""
        query = """
            SELECT * FROM forms 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        """
        results = self.db.execute_query(query, (limit, offset), fetch=True)
        forms = []
        for row in results:
            form_data = dict(row)
            # Désérialiser les settings JSON de manière sécurisée
            settings_str = form_data.get("settings", "{}")
            if settings_str and settings_str != "{}":
                try:
                    form_data["settings"] = json.loads(settings_str)
                except (json.JSONDecodeError, TypeError, ValueError):
                    form_data["settings"] = {}
            else:
                form_data["settings"] = {}
            forms.append(form_data)
        return forms

    def update(
        self,
        form_id: str,
        title: str = None,
        description: str = None,
        settings: Dict = None,
    ) -> bool:
        """Mettre à jour un formulaire"""
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if settings is not None:
            updates.append("settings = ?")
            params.append(json.dumps(settings))

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(form_id)

        query = f"""
            UPDATE forms 
            SET {', '.join(updates)}
            WHERE id = ?
        """

        rows_affected = self.db.execute_query(query, tuple(params))
        return rows_affected > 0

    def delete(self, form_id: str) -> bool:
        """Supprimer un formulaire"""
        query = "DELETE FROM forms WHERE id = ?"
        rows_affected = self.db.execute_query(query, (form_id,))
        return rows_affected > 0

    def get_with_questions(self, form_id: str) -> Optional[Dict]:
        """Récupérer un formulaire avec ses questions"""
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Récupération formulaire avec questions: {form_id}")

            # Récupérer le formulaire
            form = self.get_by_id(form_id)
            if not form:
                logger.warning(f"Formulaire non trouvé: {form_id}")
                return None

            # Récupérer les questions
            questions_query = """
                SELECT * FROM questions 
                WHERE form_id = ? 
                ORDER BY order_index
            """
            logger.info(f"Exécution requête questions pour form_id: {form_id}")
            questions = self.db.execute_query(questions_query, (form_id,), fetch=True)
            logger.info(f"Questions trouvées: {len(questions) if questions else 0}")

            # Traiter les questions avec désérialisation JSON sécurisée
            processed_questions = []
            if questions:  # Vérifier que questions n'est pas None
                logger.info(f"Traitement de {len(questions)} questions")
                for q in questions:
                    question_data = dict(q)
                    # Désérialiser les options JSON de manière sécurisée
                    options_str = question_data.get("options", "[]")
                    if options_str and options_str != "[]":
                        try:
                            question_data["options"] = json.loads(options_str)
                        except (json.JSONDecodeError, TypeError, ValueError) as e:
                            logger.warning(
                                f"Erreur désérialisation options: {e}, valeur: {options_str}"
                            )
                            question_data["options"] = []
                    else:
                        question_data["options"] = []

                    # Désérialiser la validation JSON de manière sécurisée
                    validation_str = question_data.get("validation", "{}")
                    if validation_str and validation_str != "{}":
                        try:
                            question_data["validation"] = json.loads(validation_str)
                        except (json.JSONDecodeError, TypeError, ValueError) as e:
                            logger.warning(
                                f"Erreur désérialisation validation: {e}, valeur: {validation_str}"
                            )
                            question_data["validation"] = {}
                    else:
                        question_data["validation"] = {}

                    processed_questions.append(question_data)

            form["questions"] = processed_questions
            logger.info(f"Formulaire récupéré avec succès: {form_id}")
            return form

        except Exception as e:
            logger.error(f"Erreur dans get_with_questions: {e}")
            raise

    def get_stats(self, form_id: str) -> Dict:
        """Récupérer les statistiques d'un formulaire"""
        # Compter les réponses
        responses_query = "SELECT COUNT(*) as total FROM responses WHERE form_id = ?"
        responses_result = self.db.execute_query(
            responses_query, (form_id,), fetch=True
        )
        total_responses = (
            responses_result[0]["total"]
            if responses_result and len(responses_result) > 0
            else 0
        )

        # Compter les questions
        questions_query = "SELECT COUNT(*) as total FROM questions WHERE form_id = ?"
        questions_result = self.db.execute_query(
            questions_query, (form_id,), fetch=True
        )
        total_questions = (
            questions_result[0]["total"]
            if questions_result and len(questions_result) > 0
            else 0
        )

        return {
            "total_questions": total_questions,
            "total_responses": total_responses,
            "form_id": form_id,
        }
