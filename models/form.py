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

    def create(
        self,
        title: str,
        description: str = None,
        settings: Dict = None,
        created_by: str = None,
    ) -> str:
        """Créer un nouveau formulaire"""
        form_id = str(uuid.uuid4())
        settings = settings or {}

        query = """
            INSERT INTO forms (id, title, description, settings, created_by, status)
            VALUES (?, ?, ?, ?, ?, 'draft')
        """

        self.db.execute_query(
            query, (form_id, title, description, json.dumps(settings), created_by)
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

    def get_by_id_and_user(self, form_id: str, user_id: str) -> Optional[Dict]:
        """Récupérer un formulaire par ID et utilisateur (vérification de propriété)"""
        query = "SELECT * FROM forms WHERE id = ? AND created_by = ?"
        results = self.db.execute_query(query, (form_id, user_id), fetch=True)

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

    def is_owner(self, form_id: str, user_id: str) -> bool:
        """Vérifier si un utilisateur est propriétaire d'un formulaire"""
        query = "SELECT COUNT(*) as count FROM forms WHERE id = ? AND created_by = ?"
        results = self.db.execute_query(query, (form_id, user_id), fetch=True)
        return results and len(results) > 0 and results[0]["count"] > 0

    def get_all(
        self, limit: int = 100, offset: int = 0, user_id: str = None
    ) -> List[Dict]:
        """Récupérer tous les formulaires d'un utilisateur"""
        if user_id:
            query = """
                SELECT * FROM forms 
                WHERE created_by = ?
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (user_id, limit, offset)
        else:
            query = """
                SELECT * FROM forms 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """
            params = (limit, offset)

        results = self.db.execute_query(query, params, fetch=True)
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

    def publish(self, form_id: str) -> Optional[str]:
        """Finaliser et publier un formulaire - Génère un token public unique"""
        import secrets

        # Vérifier que le formulaire existe
        form = self.get_by_id(form_id)
        if not form:
            return None

        # Générer un token public unique (32 caractères hex = 16 octets)
        public_token = secrets.token_urlsafe(
            24
        )  # 32 caractères alphanumériques URL-safe

        # Vérifier l'unicité du token (rare mais possible)
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                query = """
                    UPDATE forms 
                    SET status = 'published', 
                        public_token = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """
                rows_affected = self.db.execute_query(query, (public_token, form_id))
                if rows_affected > 0:
                    return public_token
            except Exception:
                # Token déjà utilisé, générer un nouveau
                if attempt < max_attempts - 1:
                    public_token = secrets.token_urlsafe(24)
                    continue
                return None

        return None

    def get_public_link(self, form_id: str) -> Optional[str]:
        """Récupérer ou générer le lien public d'un formulaire publié"""
        form = self.get_by_id(form_id)
        if not form:
            return None

        # Si déjà publié avec un token, retourner le token
        if form.get("status") == "published" and form.get("public_token"):
            return form.get("public_token")

        # Sinon, publier le formulaire et retourner le token
        public_token = self.publish(form_id)
        return public_token

    def get_by_public_token(self, public_token: str) -> Optional[Dict]:
        """Récupérer un formulaire publié par son token public"""
        query = "SELECT * FROM forms WHERE public_token = ? AND status = 'published'"
        results = self.db.execute_query(query, (public_token,), fetch=True)

        if results and len(results) > 0:
            form_data = results[0]
            # Désérialiser les settings JSON
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
