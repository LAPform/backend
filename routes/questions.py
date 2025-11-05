"""
Routes API pour la gestion des questions
"""

from flask import Blueprint, request, jsonify, current_app
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

questions_bp = Blueprint("questions", __name__)


@questions_bp.route("/forms/<form_id>/questions", methods=["POST"])
@require_token_auth
@rate_limit("questions_create")
def create_question(form_id, authenticated_user_id=None):
    """Créer une nouvelle question - Version simplifiée pour debug"""
    try:
        logger.info(f"🔍 ROUTE: Début create_question")
        logger.info(f"🔍 ROUTE: form_id: {form_id}")

        data = request.get_json()
        logger.info(f"🔍 ROUTE: Données reçues: {data}")
        logger.info(f"🔍 ROUTE: Type de données: {type(data)}")

        # Validation basique
        if not data or "type" not in data or "text" not in data:
            return jsonify({"error": "Données manquantes"}), 400

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
            return (
                jsonify(
                    {
                        "error": f"Type invalide. Types autorisés: {', '.join(valid_types)}"
                    }
                ),
                400,
            )

        # Validation texte simple
        if not data["text"] or len(data["text"]) < 1 or len(data["text"]) > 500:
            return jsonify({"error": "Texte invalide (1-500 caractères)"}), 400

        # Vérifier que le formulaire existe
        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

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

        return (
            jsonify(
                {
                    "success": True,
                    "question_id": question_id,
                    "message": "Question créée avec succès",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"❌ ROUTE: ERREUR dans create_question!")
        logger.error(f"❌ ROUTE: Type d'erreur: {type(e).__name__}")
        logger.error(f"❌ ROUTE: Message d'erreur: {str(e)}")
        logger.error(f"❌ ROUTE: form_id: {form_id}")
        logger.error(f"❌ ROUTE: data: {data}")
        import traceback

        logger.error(f"❌ ROUTE: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500


@questions_bp.route("/questions/<question_id>", methods=["GET"])
@require_token_auth
@rate_limit("questions_get")
def get_question(question_id, authenticated_user_id=None):
    """Récupérer une question par ID"""
    try:
        from models.database import DatabaseManager

        db = DatabaseManager()
        question_model = Question(db)
        question = question_model.get_by_id(question_id)

        if not question:
            return jsonify({"error": "Question non trouvée"}), 404

        return jsonify({"success": True, "question": question})

    except Exception as e:
        logger.error(f"Erreur récupération question: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/questions/<question_id>", methods=["PUT"])
@require_token_auth
@rate_limit("questions_update")
def update_question(question_id, authenticated_user_id=None):
    """Mettre à jour une question"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Données requises"}), 400

        from models.database import DatabaseManager

        db = DatabaseManager()
        question_model = Question(db)

        # Vérifier que la question existe
        existing_question = question_model.get_by_id(question_id)
        if not existing_question:
            return jsonify({"error": "Question non trouvée"}), 404

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
            return jsonify({"error": "Erreur lors de la mise à jour"}), 500

        logger.info(f"Question mise à jour: {question_id}")

        return jsonify({"success": True, "message": "Question mise à jour avec succès"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur mise à jour question: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/questions/<question_id>", methods=["DELETE"])
@require_token_auth
@rate_limit("questions_delete")
def delete_question(question_id, authenticated_user_id=None):
    """Supprimer une question"""
    try:
        from models.database import DatabaseManager

        db = DatabaseManager()
        question_model = Question(db)

        # Vérifier que la question existe
        existing_question = question_model.get_by_id(question_id)
        if not existing_question:
            return jsonify({"error": "Question non trouvée"}), 404

        # Supprimer
        success = question_model.delete(question_id)

        if not success:
            return jsonify({"error": "Erreur lors de la suppression"}), 500

        logger.info(f"Question supprimée: {question_id}")

        return jsonify({"success": True, "message": "Question supprimée avec succès"})

    except Exception as e:
        logger.error(f"Erreur suppression question: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/forms/<form_id>/questions", methods=["GET"])
@require_token_auth
@rate_limit("questions_get")
def list_questions(form_id, authenticated_user_id=None):
    """Lister toutes les questions d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        question_model = Question(db)
        questions = question_model.get_by_form_id(form_id)

        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        logger.error(f"Erreur liste questions: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/forms/<form_id>/questions/reorder", methods=["PUT"])
@require_token_auth
def reorder_questions(form_id, authenticated_user_id=None):
    """Réorganiser les questions d'un formulaire"""
    try:
        data = request.get_json()

        if not data or "questions" not in data:
            return jsonify({"error": "Liste des questions requise"}), 400

        # Vérifier que le formulaire existe
        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Réorganiser
        from models.database import DatabaseManager

        db = DatabaseManager()
        question_model = Question(db)
        success = question_model.reorder(form_id, data["questions"])

        if not success:
            return jsonify({"error": "Erreur lors de la réorganisation"}), 500

        logger.info(f"Questions réorganisées pour le formulaire: {form_id}")

        return jsonify(
            {"success": True, "message": "Questions réorganisées avec succès"}
        )

    except Exception as e:
        logger.error(f"Erreur réorganisation questions: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/questions/<question_id>/validate", methods=["POST"])
@require_token_auth
def validate_question_response(question_id, authenticated_user_id=None):
    """Valider une réponse à une question"""
    try:
        data = request.get_json()

        if not data or "response" not in data:
            return jsonify({"error": "Réponse requise"}), 400

        from models.database import DatabaseManager

        db = DatabaseManager()
        question_model = Question(db)
        validation_result = question_model.validate_response(
            question_id, data["response"]
        )

        return jsonify({"success": True, "validation": validation_result})

    except Exception as e:
        logger.error(f"Erreur validation réponse: {e}")
        return jsonify({"error": str(e)}), 500
