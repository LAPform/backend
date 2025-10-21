"""
Modèle Form pour FormForge
"""

import uuid
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
            VALUES (%s, %s, %s, %s)
        """

        self.db.execute_query(query, (form_id, title, description, settings))
        return form_id

    def get_by_id(self, form_id: str) -> Optional[Dict]:
        """Récupérer un formulaire par ID"""
        query = "SELECT * FROM forms WHERE id = %s"
        result = self.db.execute_query(query, (form_id,), fetch=True)

        if result:
            return dict(result)
        return None

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Récupérer tous les formulaires"""
        query = """
            SELECT * FROM forms 
            ORDER BY created_at DESC 
            LIMIT %s OFFSET %s
        """
        results = self.db.execute_query(query, (limit, offset), fetch=True)
        return [dict(row) for row in results]

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
            updates.append("title = %s")
            params.append(title)

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if settings is not None:
            updates.append("settings = %s")
            params.append(settings)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(form_id)

        query = f"""
            UPDATE forms 
            SET {', '.join(updates)}
            WHERE id = %s
        """

        rows_affected = self.db.execute_query(query, tuple(params))
        return rows_affected > 0

    def delete(self, form_id: str) -> bool:
        """Supprimer un formulaire"""
        query = "DELETE FROM forms WHERE id = %s"
        rows_affected = self.db.execute_query(query, (form_id,))
        return rows_affected > 0

    def get_with_questions(self, form_id: str) -> Optional[Dict]:
        """Récupérer un formulaire avec ses questions"""
        # Récupérer le formulaire
        form = self.get_by_id(form_id)
        if not form:
            return None

        # Récupérer les questions
        questions_query = """
            SELECT * FROM questions 
            WHERE form_id = %s 
            ORDER BY order_index
        """
        questions = self.db.execute_query(questions_query, (form_id,), fetch=True)

        form["questions"] = [dict(q) for q in questions]
        return form

    def get_stats(self, form_id: str) -> Dict:
        """Récupérer les statistiques d'un formulaire"""
        # Compter les réponses
        responses_query = "SELECT COUNT(*) as total FROM responses WHERE form_id = %s"
        total_responses = self.db.execute_query(responses_query, (form_id,), fetch=True)

        # Compter les questions
        questions_query = "SELECT COUNT(*) as total FROM questions WHERE form_id = %s"
        total_questions = self.db.execute_query(questions_query, (form_id,), fetch=True)

        return {
            "total_questions": total_questions["total"] if total_questions else 0,
            "total_responses": total_responses["total"] if total_responses else 0,
            "form_id": form_id,
        }
