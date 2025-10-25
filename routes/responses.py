"""
Routes API pour la gestion des réponses
"""

from flask import Blueprint, request, jsonify, current_app
from models.response import Response
from models.form import Form
from models.question import Question

from utils.security_auth import require_auth
from utils.validators import DataValidator
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
import logging

logger = logging.getLogger(__name__)

responses_bp = Blueprint("responses", __name__)


@responses_bp.route("/forms/<form_id>/responses", methods=["POST"])
@require_auth
@rate_limit("responses_submit")
def submit_response(form_id):
    """Soumettre une réponse à un formulaire"""
    try:
        data = request.get_json()

        if not data or "answers" not in data:
            return jsonify({"error": "Réponses requises"}), 400

        # Validation basique des données
        if not isinstance(data["answers"], dict):
            return jsonify({"error": "Les réponses doivent être un objet JSON"}), 400

        # Validation user_id si fourni
        if "user_id" in data and not DataValidator.validate_text_length(
            str(data["user_id"]), 1, 100
        ):
            return (
                jsonify(
                    {
                        "error": "L'ID utilisateur doit contenir entre 1 et 100 caractères"
                    }
                ),
                400,
            )

        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Récupérer les questions du formulaire
        from models.database import DatabaseManager
        db = DatabaseManager()
        question_model = Question(db)
        questions = question_model.get_by_form_id(form_id)

        # Valider toutes les réponses
        validation_errors = []
        for question in questions:
            question_id = question["id"]
            answer = data["answers"].get(question_id)

            validation_result = question_model.validate_response(question_id, answer)
            if not validation_result["valid"]:
                validation_errors.append(
                    {
                        "question_id": question_id,
                        "question_text": question["text"],
                        "error": validation_result["error"],
                    }
                )

        if validation_errors:
            return (
                jsonify(
                    {
                        "error": "Erreurs de validation",
                        "validation_errors": validation_errors,
                    }
                ),
                400,
            )

        # Créer la réponse
        try:
            logger.info(f"Création réponse pour formulaire: {form_id}")
            logger.info(f"Réponses reçues: {data['answers']}")

            from models.database import DatabaseManager
            db = DatabaseManager()
            response_model = Response(db)
            user_id = data.get("user_id")
            ip_address = request.remote_addr

            logger.info(f"Paramètres: user_id={user_id}, ip_address={ip_address}")

            response_id = response_model.create(
                form_id=form_id,
                answers=data["answers"],
                user_id=user_id,
                ip_address=ip_address,
            )

            # Logger la soumission de réponse
            api_logger.response_submitted(response_id, form_id, user_id)

            logger.info(f"Réponse créée avec succès: {response_id}")
        except Exception as e:
            logger.error(f"Error creating response: {e}")
            return jsonify({"error": f"Erreur création réponse: {str(e)}"}), 500

        logger.info(f"Réponse soumise: {response_id}")

        return (
            jsonify(
                {
                    "success": True,
                    "response_id": response_id,
                    "message": "Réponse soumise avec succès",
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Erreur soumission réponse: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/responses", methods=["GET"])
@require_auth
@rate_limit("responses_get")
def get_responses(form_id):
    """Récupérer toutes les réponses d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Paramètres de pagination
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        responses = response_model.get_by_form_id(form_id, limit, offset)

        return jsonify(
            {
                "success": True,
                "responses": responses,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(responses),
                },
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération réponses: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/responses/<response_id>", methods=["GET"])
@require_auth
@rate_limit("responses_get")
def get_response(response_id):
    """Récupérer une réponse par ID"""
    try:
        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        response = response_model.get_by_id(response_id)

        if not response:
            return jsonify({"error": "Réponse non trouvée"}), 404

        return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Erreur récupération réponse: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/analytics", methods=["GET"])
@require_auth
def get_form_analytics(form_id):
    """Récupérer les analytics d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        analytics = response_model.get_analytics(form_id)

        return jsonify({"success": True, "analytics": analytics})

    except Exception as e:
        logger.error(f"Erreur analytics formulaire: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route(
    "/forms/<form_id>/questions/<question_id>/analytics", methods=["GET"]
)
def get_question_analytics(form_id, question_id):
    """Récupérer les analytics d'une question"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        analytics = response_model.get_question_analytics(form_id, question_id)

        return jsonify({"success": True, "analytics": analytics})

    except Exception as e:
        logger.error(f"Erreur analytics question: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/export/csv", methods=["GET"])
@require_auth
def export_responses_csv(form_id):
    """Exporter les réponses en CSV"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Paramètres de pagination pour éviter les timeouts
        limit = request.args.get("limit", 1000, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Limiter à 1000 réponses maximum pour éviter les timeouts
        if limit > 1000:
            limit = 1000

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

        if not data_to_export:
            return jsonify({"error": "Aucune réponse à exporter"}), 404

        # Générer le CSV
        from utils.exporters import ExportManager

        export_result = ExportManager.export_responses(data_to_export, "csv")

        if not export_result["success"]:
            return jsonify({"error": export_result["error"]}), 500

        # Retourner le contenu CSV
        return jsonify(
            {
                "success": True,
                "csv_content": export_result["content"],
                "filename": f"form_{form_id}_responses.csv",
            }
        )

    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/export/excel", methods=["GET"])
@require_auth
def export_responses_excel(form_id):
    """Exporter les réponses en Excel"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Paramètres de pagination pour éviter les timeouts
        limit = request.args.get("limit", 1000, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Limiter à 1000 réponses maximum pour éviter les timeouts
        if limit > 1000:
            limit = 1000

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

        if not data_to_export:
            return jsonify({"error": "Aucune réponse à exporter"}), 404

        # Générer l'Excel
        from utils.exporters import ExportManager

        export_result = ExportManager.export_responses(data_to_export, "excel")

        if not export_result["success"]:
            return jsonify({"error": export_result["error"]}), 500

        # Retourner le contenu Excel
        return jsonify(
            {
                "success": True,
                "excel_content": export_result["content"],
                "filename": f"form_{form_id}_responses.xlsx",
            }
        )

    except Exception as e:
        logger.error(f"Erreur export Excel: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/export/json", methods=["GET"])
@require_auth
def export_responses_json(form_id):
    """Exporter les réponses en JSON"""
    try:
        # Vérifier que le formulaire existe
        from models.database import DatabaseManager
        db = DatabaseManager()
        form_model = Form(db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Paramètres de pagination pour éviter les timeouts
        limit = request.args.get("limit", 1000, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Limiter à 1000 réponses maximum pour éviter les timeouts
        if limit > 1000:
            limit = 1000

        from models.database import DatabaseManager
        db = DatabaseManager()
        response_model = Response(db)
        data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

        if not data_to_export:
            return jsonify({"error": "Aucune réponse à exporter"}), 404

        # Générer le JSON
        from utils.exporters import ExportManager

        export_result = ExportManager.export_responses(data_to_export, "json")

        if not export_result["success"]:
            return jsonify({"error": export_result["error"]}), 500

        # Retourner le contenu JSON
        return jsonify(
            {
                "success": True,
                "json_content": export_result["content"],
                "filename": f"form_{form_id}_responses.json",
            }
        )

    except Exception as e:
        logger.error(f"Erreur export JSON: {e}")
        return jsonify({"error": str(e)}), 500
