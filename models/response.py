"""
Modèle Response pour FormForge
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from .database import DatabaseManager


class Response:
    """Modèle pour les réponses"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create(
        self, form_id: str, answers: Dict, user_id: str = None, ip_address: str = None
    ) -> str:
        """Créer une nouvelle réponse"""
        response_id = str(uuid.uuid4())

        query = """
            INSERT INTO responses (id, form_id, answers, user_id, ip_address)
            VALUES (?, ?, ?, ?, ?)
        """

        self.db.execute_query(
            query, (response_id, form_id, answers, user_id, ip_address)
        )
        return response_id

    def get_by_id(self, response_id: str) -> Optional[Dict]:
        """Récupérer une réponse par ID"""
        query = "SELECT * FROM responses WHERE id = ?"
        result = self.db.execute_query(query, (response_id,), fetch=True)

        if result:
            return dict(result)
        return None

    def get_by_form_id(
        self, form_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict]:
        """Récupérer toutes les réponses d'un formulaire"""
        query = """
            SELECT * FROM responses 
            WHERE form_id = ? 
            ORDER BY submitted_at DESC 
            LIMIT ? OFFSET ?
        """
        results = self.db.execute_query(query, (form_id, limit, offset), fetch=True)
        return [dict(row) for row in results]

    def get_count_by_form_id(self, form_id: str) -> int:
        """Compter le nombre de réponses d'un formulaire"""
        query = "SELECT COUNT(*) as total FROM responses WHERE form_id = ?"
        result = self.db.execute_query(query, (form_id,), fetch=True)
        return result["total"] if result else 0

    def get_analytics(self, form_id: str) -> Dict:
        """Récupérer les analytics d'un formulaire"""
        # Statistiques générales
        total_responses = self.get_count_by_form_id(form_id)

        # Réponses par jour (derniers 30 jours)
        daily_query = """
            SELECT DATE(submitted_at) as date, COUNT(*) as count
            FROM responses 
            WHERE form_id = ? 
            AND submitted_at >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(submitted_at)
            ORDER BY date
        """
        daily_stats = self.db.execute_query(daily_query, (form_id,), fetch=True)

        # Réponses par heure
        hourly_query = """
            SELECT EXTRACT(HOUR FROM submitted_at) as hour, COUNT(*) as count
            FROM responses 
            WHERE form_id = ? 
            AND submitted_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY EXTRACT(HOUR FROM submitted_at)
            ORDER BY hour
        """
        hourly_stats = self.db.execute_query(hourly_query, (form_id,), fetch=True)

        return {
            "total_responses": total_responses,
            "daily_stats": [dict(row) for row in daily_stats],
            "hourly_stats": [dict(row) for row in hourly_stats],
        }

    def get_question_analytics(self, form_id: str, question_id: str) -> Dict:
        """Analytics pour une question spécifique"""
        # Récupérer toutes les réponses pour cette question
        query = """
            SELECT json_extract(answers, '$.' || ?) as answer
            FROM responses 
            WHERE form_id = ? 
            AND json_extract(answers, '$.' || ?) IS NOT NULL
        """
        results = self.db.execute_query(
            query, (question_id, form_id, question_id), fetch=True
        )

        answers = [row["answer"] for row in results if row["answer"] is not None]

        if not answers:
            return {"question_id": question_id, "total_answers": 0, "analytics": {}}

        # Analyser les réponses selon le type
        analytics = {}

        # Pour les questions à choix multiples
        if isinstance(answers[0], str) and answers[0] in [
            "option1",
            "option2",
            "option3",
        ]:
            # Compter les occurrences
            from collections import Counter

            counter = Counter(answers)
            analytics["choices"] = dict(counter)
            analytics["most_common"] = counter.most_common(1)[0] if counter else None

        # Pour les questions numériques
        elif all(
            str(answer).replace(".", "").replace("-", "").isdigit()
            for answer in answers
        ):
            numeric_answers = [float(answer) for answer in answers]
            analytics["average"] = sum(numeric_answers) / len(numeric_answers)
            analytics["min"] = min(numeric_answers)
            analytics["max"] = max(numeric_answers)

        # Pour les questions texte
        else:
            analytics["total_text_responses"] = len(answers)
            analytics["average_length"] = sum(
                len(str(answer)) for answer in answers
            ) / len(answers)

        return {
            "question_id": question_id,
            "total_answers": len(answers),
            "analytics": analytics,
        }

    def export_to_csv_data(self, form_id: str) -> List[Dict]:
        """Exporter les données pour CSV"""
        # Récupérer le formulaire avec ses questions
        from .form import Form

        form_model = Form(self.db)
        form_data = form_model.get_with_questions(form_id)

        if not form_data:
            return []

        # Récupérer toutes les réponses
        responses = self.get_by_form_id(
            form_id, limit=10000
        )  # Limite élevée pour export

        # Construire les données CSV
        csv_data = []
        questions = form_data.get("questions", [])

        for response in responses:
            row = {
                "response_id": response["id"],
                "submitted_at": (
                    response["submitted_at"].isoformat()
                    if response["submitted_at"]
                    else ""
                ),
                "user_id": response.get("user_id", ""),
                "ip_address": response.get("ip_address", ""),
            }

            # Ajouter les réponses aux questions
            answers = response.get("answers", {})
            for question in questions:
                question_id = question["id"]
                question_text = question["text"]
                answer = answers.get(question_id, "")

                # Nettoyer le texte pour CSV
                if isinstance(answer, list):
                    answer = "; ".join(str(item) for item in answer)
                else:
                    answer = str(answer)

                row[f"Q{question['order_index']}_{question_text[:50]}"] = answer

            csv_data.append(row)

        return csv_data
