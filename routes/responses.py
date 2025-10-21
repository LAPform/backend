"""
Routes API pour la gestion des réponses
"""

from flask import Blueprint, request, jsonify, current_app
from models.response import Response
from models.form import Form
from models.question import Question
from utils.exporters import CSVExporter
import logging

logger = logging.getLogger(__name__)

responses_bp = Blueprint("responses", __name__)


@responses_bp.route("/forms/<form_id>/responses", methods=["POST"])
def submit_response(form_id):
    """Soumettre une réponse à un formulaire"""
    try:
        data = request.get_json()

        if not data or "answers" not in data:
            return jsonify({"error": "Réponses requises"}), 400

        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Récupérer les questions du formulaire
        question_model = Question(current_app.db)
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
        response_model = Response(current_app.db)
        user_id = data.get("user_id")
        ip_address = request.remote_addr

        response_id = response_model.create(
            form_id=form_id,
            answers=data["answers"],
            user_id=user_id,
            ip_address=ip_address,
        )

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
def get_responses(form_id):
    """Récupérer toutes les réponses d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Paramètres de pagination
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        response_model = Response(current_app.db)
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
def get_response(response_id):
    """Récupérer une réponse par ID"""
    try:
        response_model = Response(current_app.db)
        response = response_model.get_by_id(response_id)

        if not response:
            return jsonify({"error": "Réponse non trouvée"}), 404

        return jsonify({"success": True, "response": response})

    except Exception as e:
        logger.error(f"Erreur récupération réponse: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/analytics", methods=["GET"])
def get_form_analytics(form_id):
    """Récupérer les analytics d'un formulaire"""
    try:
        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        response_model = Response(current_app.db)
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
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        response_model = Response(current_app.db)
        analytics = response_model.get_question_analytics(form_id, question_id)

        return jsonify({"success": True, "analytics": analytics})

    except Exception as e:
        logger.error(f"Erreur analytics question: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/export/csv", methods=["GET"])
def export_responses_csv(form_id):
    """Exporter les réponses en CSV"""
    try:
        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        response_model = Response(current_app.db)
        csv_data = response_model.export_to_csv_data(form_id)

        if not csv_data:
            return jsonify({"error": "Aucune réponse à exporter"}), 404

        # Générer le CSV
        exporter = CSVExporter()
        csv_content = exporter.generate_csv(csv_data)

        return jsonify(
            {
                "success": True,
                "csv_content": csv_content,
                "filename": f"form_{form_id}_responses.csv",
            }
        )

    except Exception as e:
        logger.error(f"Erreur export CSV: {e}")
        return jsonify({"error": str(e)}), 500


@responses_bp.route("/forms/<form_id>/export/excel", methods=["GET"])
def export_responses_excel(form_id):
    """Exporter les réponses en Excel"""
    try:
        # Vérifier que le formulaire existe
        form_model = Form(current_app.db)
        form = form_model.get_by_id(form_id)
        if not form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        response_model = Response(current_app.db)
        csv_data = response_model.export_to_csv_data(form_id)

        if not csv_data:
            return jsonify({"error": "Aucune réponse à exporter"}), 404

        # Générer l'Excel
        exporter = CSVExporter()
        excel_content = exporter.generate_excel(csv_data)

        return jsonify(
            {
                "success": True,
                "excel_content": excel_content,
                "filename": f"form_{form_id}_responses.xlsx",
            }
        )

    except Exception as e:
        logger.error(f"Erreur export Excel: {e}")
        return jsonify({"error": str(e)}), 500
