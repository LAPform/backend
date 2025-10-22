"""
Routes API pour la gestion des questions
"""

from flask import Blueprint, request, jsonify, current_app
from models.question import Question
from models.form import Form
from utils.auth import require_auth
from utils.validators import DataValidator
import logging

logger = logging.getLogger(__name__)

questions_bp = Blueprint("questions", __name__)


@questions_bp.route("/forms/<form_id>/questions", methods=["POST"])
@require_auth
def create_question(form_id):
    """Créer une nouvelle question"""
    try:
        data = request.get_json()
        logger.info(f"Creating question for form {form_id} with data: {data}")

        # Validation des données requises
        if not data or "type" not in data or "text" not in data:
            logger.error("Missing required fields: type and text")
            return jsonify({"error": "Type and text are required"}), 400

        # Validation stricte des données
        validation_errors = []
        
        # Validation type de question
        valid_types = ["text", "email", "phone", "url", "date", "time", "number", "choice", "multiple_choices", "checkbox", "radio", "textarea"]
        if data["type"] not in valid_types:
            validation_errors.append(f"Type de question invalide. Types autorisés: {', '.join(valid_types)}")
        
        # Validation texte de la question
        if not DataValidator.validate_text_length(data["text"], 1, 500):
            validation_errors.append("Le texte de la question doit contenir entre 1 et 500 caractères")
        
        # Validation order_index
        if "order_index" in data:
            if not isinstance(data["order_index"], int) or data["order_index"] < 0:
                validation_errors.append("L'index d'ordre doit être un nombre entier positif")
        
        # Validation required
        if "required" in data and not isinstance(data["required"], bool):
            validation_errors.append("Le champ 'required' doit être un booléen")
        
        if validation_errors:
            return jsonify({"error": "Données invalides", "details": validation_errors}), 400

        # Vérifier que le formulaire existe (simplifié)
        try:
            form_model = Form(current_app.db)
            form = form_model.get_by_id(form_id)
            if not form:
                logger.error(f"Form {form_id} not found")
                return jsonify({"error": "Formulaire non trouvé"}), 404
        except Exception as e:
            logger.error(f"Error checking form existence: {e}")
            return jsonify({"error": f"Erreur vérification formulaire: {str(e)}"}), 500

        # Créer la question
        try:
            question_model = Question(current_app.db)
            question_id = question_model.create(
                form_id=form_id,
                type=data["type"],
                text=data["text"],
                options=data.get("options", []),
                required=data.get("required", False),
                validation=data.get("validation", {}),
                order_index=data.get("order_index", 0),
            )
        except Exception as e:
            logger.error(f"Error creating question: {e}")
            return jsonify({"error": f"Erreur création question: {str(e)}"}), 500

        logger.info(f"Question créée: {question_id}")

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

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur création question: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/questions/<question_id>", methods=["GET"])
@require_auth
def get_question(question_id):
    """Récupérer une question par ID"""
    try:
        question_model = Question(current_app.db)
        question = question_model.get_by_id(question_id)

        if not question:
            return jsonify({"error": "Question non trouvée"}), 404

        return jsonify({"success": True, "question": question})

    except Exception as e:
        logger.error(f"Erreur récupération question: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/questions/<question_id>", methods=["PUT"])
@require_auth
def update_question(question_id):
    """Mettre à jour une question"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Données requises"}), 400

        question_model = Question(current_app.db)

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
@require_auth
def delete_question(question_id):
    """Supprimer une question"""
    try:
        question_model = Question(current_app.db)

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
@require_auth
def list_questions(form_id):
    """Lister toutes les questions d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        question_model = Question(current_app.db)
        questions = question_model.get_by_form_id(form_id)

        return jsonify({"success": True, "questions": questions})

    except Exception as e:
        logger.error(f"Erreur liste questions: {e}")
        return jsonify({"error": str(e)}), 500


@questions_bp.route("/forms/<form_id>/questions/reorder", methods=["PUT"])
@require_auth
def reorder_questions(form_id):
    """Réorganiser les questions d'un formulaire"""
    try:
        data = request.get_json()

        if not data or "questions" not in data:
            return jsonify({"error": "Liste des questions requise"}), 400

        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Réorganiser
        question_model = Question(current_app.db)
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
@require_auth
def validate_question_response(question_id):
    """Valider une réponse à une question"""
    try:
        data = request.get_json()

        if not data or "response" not in data:
            return jsonify({"error": "Réponse requise"}), 400

        question_model = Question(current_app.db)
        validation_result = question_model.validate_response(
            question_id, data["response"]
        )

        return jsonify({"success": True, "validation": validation_result})

    except Exception as e:
        logger.error(f"Erreur validation réponse: {e}")
        return jsonify({"error": str(e)}), 500
