"""
Routes API pour la gestion des questions (Flask-RESTx avec Swagger)
"""

from flask import request, current_app
from flask_restx import Namespace, Resource
from models.question import Question
from models.form import Form
from utils.security_auth import require_token_auth
from utils.validators import DataValidator
from utils.rate_limiter import rate_limit
from utils.error_handler import (
    error_handler,
    validate_request_data,
    ensure_resource_exists,
)
from utils.structured_logger import api_logger
import logging

logger = logging.getLogger(__name__)

# Créer le namespace
api = Namespace('questions', description='Opérations sur les questions de formulaire')

# Récupérer les modèles depuis la configuration
def get_models():
    """Récupère les modèles de documentation"""
    # Utiliser les modèles stockés dans le namespace (évite l'accès à current_app pendant l'import)
    if hasattr(api, '_models'):
        return api._models
    # Fallback pour le développement local
    try:
        return current_app.config.get('API_MODELS', {})
    except RuntimeError:
        return {}


@api.route('/forms/<int:form_id>/questions')
@api.param('form_id', 'L\'identifiant du formulaire')
class QuestionList(Resource):
    """Gestion de la liste des questions d'un formulaire"""

    @api.doc('list_questions',
             description='Liste toutes les questions d\'un formulaire',
             security='Bearer')
    @api.response(200, 'Succès')
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("questions_get")
    def get(self, form_id, authenticated_user_id=None):
        """Lister toutes les questions d'un formulaire"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            question_model = Question(db)
            questions = question_model.get_by_form_id(form_id)

            return {"success": True, "questions": questions}

        except Exception as e:
            logger.error(f"Erreur liste questions: {e}")
            return {"error": str(e)}, 500

    @api.doc('create_question',
             description='Créer une nouvelle question dans un formulaire',
             security='Bearer')
    @api.expect(get_models().get('question_create'), validate=True)
    @api.response(201, 'Question créée', get_models().get('success'))
    @api.response(400, 'Données invalides', get_models().get('error'))
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("questions_create")
    def post(self, form_id, authenticated_user_id=None):
        """Créer une nouvelle question"""
        try:
            logger.info(f"🔍 ROUTE: Début create_question")
            logger.info(f"🔍 ROUTE: form_id: {form_id}")

            data = request.get_json()
            logger.info(f"🔍 ROUTE: Données reçues: {data}")
            logger.info(f"🔍 ROUTE: Type de données: {type(data)}")

            # Validation basique
            if not data or "type" not in data or "text" not in data:
                return {"error": "Données manquantes"}, 400

            # Validation type simple
            valid_types = [
                "text",
                "textarea",
                "email",
                "phone",
                "url",
                "date",
                "time",
                "number",
                "choice",
                "multiple_choice",
                "multiple_choices",
                "checkbox",
                "radio",
                "boolean",
                "scale",
            ]
            if data["type"] not in valid_types:
                return {
                    "error": f"Type invalide. Types autorisés: {', '.join(valid_types)}"
                }, 400

            # Validation texte simple
            if not data["text"] or len(data["text"]) < 1 or len(data["text"]) > 500:
                return {"error": "Texte invalide (1-500 caractères)"}, 400

            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Créer la question
            question_model = Question(db)

            question_id = question_model.create(
                form_id=form_id,
                type=data["type"],
                text=data["text"],
                options=data.get("options", []),
                required=data.get("required", False),
                validation=data.get("validation", {}),
                order_index=data.get("order_index", 0),
            )

            return {
                "success": True,
                "question_id": question_id,
                "message": "Question créée avec succès",
            }, 201

        except Exception as e:
            logger.error(f"❌ ROUTE: ERREUR dans create_question!")
            logger.error(f"❌ ROUTE: Type d'erreur: {type(e).__name__}")
            logger.error(f"❌ ROUTE: Message d'erreur: {str(e)}")
            logger.error(f"❌ ROUTE: form_id: {form_id}")
            import traceback

            logger.error(f"❌ ROUTE: Traceback: {traceback.format_exc()}")
            return {"error": f"Erreur interne: {str(e)}"}, 500


@api.route('/<int:question_id>')
@api.param('question_id', 'L\'identifiant de la question')
class QuestionResource(Resource):
    """Gestion d'une question spécifique"""

    @api.doc('get_question',
             description='Récupérer une question par son ID',
             security='Bearer')
    @api.response(200, 'Succès', get_models().get('question'))
    @api.response(404, 'Question non trouvée', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("questions_get")
    def get(self, question_id, authenticated_user_id=None):
        """Récupérer une question par ID"""
        try:
            from models.database import DatabaseManager

            db = DatabaseManager()
            question_model = Question(db)
            question = question_model.get_by_id(question_id)

            if not question:
                return {"error": "Question non trouvée"}, 404

            return {"success": True, "question": question}

        except Exception as e:
            logger.error(f"Erreur récupération question: {e}")
            return {"error": str(e)}, 500

    @api.doc('update_question',
             description='Mettre à jour une question',
             security='Bearer')
    @api.expect(get_models().get('question_update'))
    @api.response(200, 'Question mise à jour', get_models().get('success'))
    @api.response(404, 'Question non trouvée', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("questions_update")
    def put(self, question_id, authenticated_user_id=None):
        """Mettre à jour une question"""
        try:
            data = request.get_json()

            if not data:
                return {"error": "Données requises"}, 400

            from models.database import DatabaseManager

            db = DatabaseManager()
            question_model = Question(db)

            # Vérifier que la question existe
            existing_question = question_model.get_by_id(question_id)
            if not existing_question:
                return {"error": "Question non trouvée"}, 404

            # Mettre à jour
            success = question_model.update(
                question_id,
                type=data.get("type"),
                text=data.get("text"),
                options=data.get("options"),
                required=data.get("required"),
                validation=data.get("validation"),
            )

            if not success:
                return {"error": "Erreur lors de la mise à jour"}, 500

            logger.info(f"Question mise à jour: {question_id}")

            return {"success": True, "message": "Question mise à jour avec succès"}

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            logger.error(f"Erreur mise à jour question: {e}")
            return {"error": str(e)}, 500

    @api.doc('delete_question',
             description='Supprimer une question',
             security='Bearer')
    @api.response(200, 'Question supprimée', get_models().get('success'))
    @api.response(404, 'Question non trouvée', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("questions_delete")
    def delete(self, question_id, authenticated_user_id=None):
        """Supprimer une question"""
        try:
            from models.database import DatabaseManager

            db = DatabaseManager()
            question_model = Question(db)

            # Vérifier que la question existe
            existing_question = question_model.get_by_id(question_id)
            if not existing_question:
                return {"error": "Question non trouvée"}, 404

            # Supprimer
            success = question_model.delete(question_id)

            if not success:
                return {"error": "Erreur lors de la suppression"}, 500

            logger.info(f"Question supprimée: {question_id}")

            return {"success": True, "message": "Question supprimée avec succès"}

        except Exception as e:
            logger.error(f"Erreur suppression question: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/questions/reorder')
@api.param('form_id', 'L\'identifiant du formulaire')
class QuestionReorder(Resource):
    """Réorganisation des questions"""

    @api.doc('reorder_questions',
             description='Réorganiser l\'ordre des questions dans un formulaire',
             security='Bearer')
    @api.expect(get_models().get('questions_reorder'))
    @api.response(200, 'Questions réorganisées', get_models().get('success'))
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def put(self, form_id, authenticated_user_id=None):
        """Réorganiser les questions d'un formulaire"""
        try:
            data = request.get_json()

            if not data or "questions" not in data:
                return {"error": "Liste des questions requise"}, 400

            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Réorganiser
            question_model = Question(db)
            success = question_model.reorder(form_id, data["questions"])

            if not success:
                return {"error": "Erreur lors de la réorganisation"}, 500

            logger.info(f"Questions réorganisées pour le formulaire: {form_id}")

            return {"success": True, "message": "Questions réorganisées avec succès"}

        except Exception as e:
            logger.error(f"Erreur réorganisation questions: {e}")
            return {"error": str(e)}, 500


@api.route('/<int:question_id>/validate')
@api.param('question_id', 'L\'identifiant de la question')
class QuestionValidation(Resource):
    """Validation des réponses à une question"""

    @api.doc('validate_question_response',
             description='Valider qu\'une réponse respecte les règles de validation d\'une question',
             security='Bearer')
    @api.response(200, 'Validation effectuée', get_models().get('success'))
    @api.response(404, 'Question non trouvée', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def post(self, question_id, authenticated_user_id=None):
        """Valider une réponse à une question"""
        try:
            data = request.get_json()

            if not data or "response" not in data:
                return {"error": "Réponse requise"}, 400

            from models.database import DatabaseManager

            db = DatabaseManager()
            question_model = Question(db)
            validation_result = question_model.validate_response(
                question_id, data["response"]
            )

            return {"success": True, "validation": validation_result}

        except Exception as e:
            logger.error(f"Erreur validation réponse: {e}")
            return {"error": str(e)}, 500
