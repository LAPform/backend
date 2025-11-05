"""
Routes API pour la gestion des réponses (Flask-RESTx avec Swagger)
"""

from flask import request, jsonify, current_app, Blueprint
from flask_restx import Namespace, Resource
from models.response import Response
from models.form import Form
from models.question import Question
from utils.exporters import CSVExporter
from utils.security_auth import require_token_auth
from utils.validators import DataValidator
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
import logging

logger = logging.getLogger(__name__)

# Créer le namespace
api = Namespace('responses', description='Opérations sur les réponses aux formulaires')

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


@api.route('/forms/<int:form_id>/responses')
@api.param('form_id', 'L\'identifiant du formulaire')
class FormResponseList(Resource):
    """Gestion des réponses à un formulaire"""

    @api.doc('submit_response',
             description='Soumettre une réponse à un formulaire (authentifié)',
             security='Bearer')
    @api.expect(get_models().get('response_create'), validate=True)
    @api.response(201, 'Réponse soumise', get_models().get('success'))
    @api.response(400, 'Erreur de validation', get_models().get('error'))
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("responses_submit")
    def post(self, form_id, authenticated_user_id=None):
        """Soumettre une réponse à un formulaire"""
        try:
            data = request.get_json()

            if not data or "answers" not in data:
                return {"error": "Réponses requises"}, 400

            # Validation basique des données
            if not isinstance(data["answers"], dict):
                return {"error": "Les réponses doivent être un objet JSON"}, 400

            # Validation user_id si fourni
            if "user_id" in data and not DataValidator.validate_text_length(
                str(data["user_id"]), 1, 100
            ):
                return {
                    "error": "L'ID utilisateur doit contenir entre 1 et 100 caractères"
                }, 400

            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Récupérer les questions du formulaire
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
                return {
                    "error": "Erreurs de validation",
                    "validation_errors": validation_errors,
                }, 400

            # Créer la réponse
            try:
                logger.info(f"Création réponse pour formulaire: {form_id}")
                logger.info(f"Réponses reçues: {data['answers']}")

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
                return {"error": f"Erreur création réponse: {str(e)}"}, 500

            logger.info(f"Réponse soumise: {response_id}")

            return {
                "success": True,
                "response_id": response_id,
                "message": "Réponse soumise avec succès",
            }, 201

        except Exception as e:
            logger.error(f"Erreur soumission réponse: {e}")
            return {"error": str(e)}, 500

    @api.doc('get_responses',
             description='Récupérer toutes les réponses d\'un formulaire',
             security='Bearer',
             params={
                 'limit': {'description': 'Nombre maximum de résultats', 'type': 'int', 'default': 100},
                 'offset': {'description': 'Décalage pour la pagination', 'type': 'int', 'default': 0}
             })
    @api.response(200, 'Succès', get_models().get('responses_list'))
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("responses_get")
    def get(self, form_id, authenticated_user_id=None):
        """Récupérer toutes les réponses d'un formulaire"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Paramètres de pagination
            limit = request.args.get("limit", 100, type=int)
            offset = request.args.get("offset", 0, type=int)

            response_model = Response(db)
            responses = response_model.get_by_form_id(form_id, limit, offset)

            return {
                "success": True,
                "responses": responses,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": len(responses),
                },
            }

        except Exception as e:
            logger.error(f"Erreur récupération réponses: {e}")
            return {"error": str(e)}, 500


@api.route('/<int:response_id>')
@api.param('response_id', 'L\'identifiant de la réponse')
class ResponseResource(Resource):
    """Gestion d'une réponse spécifique"""

    @api.doc('get_response',
             description='Récupérer une réponse par son ID',
             security='Bearer')
    @api.response(200, 'Succès', get_models().get('response'))
    @api.response(404, 'Réponse non trouvée', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("responses_get")
    def get(self, response_id, authenticated_user_id=None):
        """Récupérer une réponse par ID"""
        try:
            from models.database import DatabaseManager

            db = DatabaseManager()
            response_model = Response(db)
            response = response_model.get_by_id(response_id)

            if not response:
                return {"error": "Réponse non trouvée"}, 404

            return {"success": True, "response": response}

        except Exception as e:
            logger.error(f"Erreur récupération réponse: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/analytics')
@api.param('form_id', 'L\'identifiant du formulaire')
class FormAnalytics(Resource):
    """Analytics d'un formulaire"""

    @api.doc('get_form_analytics',
             description='Récupérer les statistiques et analytics d\'un formulaire',
             security='Bearer')
    @api.response(200, 'Succès', get_models().get('analytics'))
    @api.response(404, 'Formulaire non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, form_id, authenticated_user_id=None):
        """Récupérer les analytics d'un formulaire"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            response_model = Response(db)
            analytics = response_model.get_analytics(form_id)

            return {"success": True, "analytics": analytics}

        except Exception as e:
            logger.error(f"Erreur analytics formulaire: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/questions/<int:question_id>/analytics')
@api.param('form_id', 'L\'identifiant du formulaire')
@api.param('question_id', 'L\'identifiant de la question')
class QuestionAnalytics(Resource):
    """Analytics d'une question spécifique"""

    @api.doc('get_question_analytics',
             description='Récupérer les analytics pour une question spécifique',
             security='Bearer')
    @api.response(200, 'Succès', get_models().get('question_analytics'))
    @api.response(404, 'Formulaire ou question non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    def get(self, form_id, question_id, authenticated_user_id=None):
        """Récupérer les analytics d'une question"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            response_model = Response(db)
            analytics = response_model.get_question_analytics(form_id, question_id)

            return {"success": True, "analytics": analytics}

        except Exception as e:
            logger.error(f"Erreur analytics question: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/export/csv')
@api.param('form_id', 'L\'identifiant du formulaire')
class ExportCSV(Resource):
    """Export des réponses en CSV"""

    @api.doc('export_csv',
             description='Exporter les réponses d\'un formulaire au format CSV',
             security='Bearer',
             params={
                 'limit': {'description': 'Nombre maximum de réponses (max 1000)', 'type': 'int', 'default': 1000},
                 'offset': {'description': 'Décalage pour la pagination', 'type': 'int', 'default': 0}
             })
    @api.response(200, 'Export CSV généré', get_models().get('success'))
    @api.response(404, 'Formulaire non trouvé ou aucune réponse', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, form_id, authenticated_user_id=None):
        """Exporter les réponses en CSV"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Paramètres de pagination pour éviter les timeouts
            limit = request.args.get("limit", 1000, type=int)
            offset = request.args.get("offset", 0, type=int)

            # Limiter à 1000 réponses maximum pour éviter les timeouts
            if limit > 1000:
                limit = 1000

            response_model = Response(db)
            data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

            if not data_to_export:
                return {"error": "Aucune réponse à exporter"}, 404

            # Générer le CSV
            from utils.exporters import ExportManager

            export_result = ExportManager.export_responses(data_to_export, "csv")

            if not export_result["success"]:
                return {"error": export_result["error"]}, 500

            # Retourner le contenu CSV
            return {
                "success": True,
                "csv_content": export_result["content"],
                "filename": f"form_{form_id}_responses.csv",
            }

        except Exception as e:
            logger.error(f"Erreur export CSV: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/export/excel')
@api.param('form_id', 'L\'identifiant du formulaire')
class ExportExcel(Resource):
    """Export des réponses en Excel"""

    @api.doc('export_excel',
             description='Exporter les réponses d\'un formulaire au format Excel',
             security='Bearer',
             params={
                 'limit': {'description': 'Nombre maximum de réponses (max 1000)', 'type': 'int', 'default': 1000},
                 'offset': {'description': 'Décalage pour la pagination', 'type': 'int', 'default': 0}
             })
    @api.response(200, 'Export Excel généré', get_models().get('success'))
    @api.response(404, 'Formulaire non trouvé ou aucune réponse', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, form_id, authenticated_user_id=None):
        """Exporter les réponses en Excel"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Paramètres de pagination pour éviter les timeouts
            limit = request.args.get("limit", 1000, type=int)
            offset = request.args.get("offset", 0, type=int)

            # Limiter à 1000 réponses maximum pour éviter les timeouts
            if limit > 1000:
                limit = 1000

            response_model = Response(db)
            data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

            if not data_to_export:
                return {"error": "Aucune réponse à exporter"}, 404

            # Générer l'Excel
            from utils.exporters import ExportManager

            export_result = ExportManager.export_responses(data_to_export, "excel")

            if not export_result["success"]:
                return {"error": export_result["error"]}, 500

            # Retourner le contenu Excel
            return {
                "success": True,
                "excel_content": export_result["content"],
                "filename": f"form_{form_id}_responses.csv",
                "note": "Export Excel généré au format CSV pour compatibilité",
            }

        except Exception as e:
            logger.error(f"Erreur export Excel: {e}")
            return {"error": str(e)}, 500


@api.route('/forms/<int:form_id>/export/json')
@api.param('form_id', 'L\'identifiant du formulaire')
class ExportJSON(Resource):
    """Export des réponses en JSON"""

    @api.doc('export_json',
             description='Exporter les réponses d\'un formulaire au format JSON',
             security='Bearer',
             params={
                 'limit': {'description': 'Nombre maximum de réponses (max 1000)', 'type': 'int', 'default': 1000},
                 'offset': {'description': 'Décalage pour la pagination', 'type': 'int', 'default': 0}
             })
    @api.response(200, 'Export JSON généré', get_models().get('success'))
    @api.response(404, 'Formulaire non trouvé ou aucune réponse', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, form_id, authenticated_user_id=None):
        """Exporter les réponses en JSON"""
        try:
            # Vérifier que le formulaire existe
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form = form_model.get_by_id(form_id)
            if not form:
                return {"error": "Formulaire non trouvé"}, 404

            # Paramètres de pagination pour éviter les timeouts
            limit = request.args.get("limit", 1000, type=int)
            offset = request.args.get("offset", 0, type=int)

            # Limiter à 1000 réponses maximum pour éviter les timeouts
            if limit > 1000:
                limit = 1000

            response_model = Response(db)
            data_to_export = response_model.export_to_csv_data(form_id, limit, offset)

            if not data_to_export:
                return {"error": "Aucune réponse à exporter"}, 404

            # Générer le JSON
            from utils.exporters import ExportManager

            export_result = ExportManager.export_responses(data_to_export, "json")

            if not export_result["success"]:
                return {"error": export_result["error"]}, 500

            # Retourner le contenu JSON
            return {
                "success": True,
                "json_content": export_result["content"],
                "filename": f"form_{form_id}_responses.json",
            }

        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
            return {"error": str(e)}, 500


# Route publique pour soumettre une réponse sans authentification
# Cette route doit être enregistrée séparément dans app.py car elle a un préfixe différent
public_responses_bp = Blueprint("public_responses", __name__)

@public_responses_bp.route("/public/forms/<public_token>/responses", methods=["POST"])
@rate_limit("responses_submit_public")
def submit_public_response(public_token):
    """
    Soumettre une réponse à un formulaire publié via son token public (accès public, pas d'authentification requise)

    Cet endpoint permet aux répondants de soumettre leurs réponses sans authentification
    en utilisant le token public du formulaire.
    """
    try:
        data = request.get_json()

        if not data or "answers" not in data:
            return jsonify({"error": "Réponses requises"}), 400

        # Validation basique des données
        if not isinstance(data["answers"], dict):
            return jsonify({"error": "Les réponses doivent être un objet JSON"}), 400

        # Vérifier que le formulaire existe et est publié
        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)

        # Récupérer le formulaire par son token public
        form = form_model.get_by_public_token(public_token)

        if not form:
            return jsonify({"error": "Formulaire non trouvé ou non publié"}), 404

        form_id = form["id"]

        # Récupérer les questions du formulaire
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
            return jsonify({
                "error": "Erreurs de validation",
                "validation_errors": validation_errors,
            }), 400

        # Créer la réponse
        try:
            logger.info(f"Création réponse publique pour formulaire: {form_id}")
            logger.info(f"Réponses reçues: {data['answers']}")

            response_model = Response(db)
            user_id = data.get("user_id")  # Optionnel pour les réponses publiques
            ip_address = request.remote_addr

            logger.info(f"Paramètres: user_id={user_id}, ip_address={ip_address}")

            response_id = response_model.create(
                form_id=form_id,
                answers=data["answers"],
                user_id=user_id,
                ip_address=ip_address,
            )

            logger.info(f"Réponse créée avec succès: {response_id}")
        except Exception as e:
            logger.error(f"Error creating response: {e}")
            return jsonify({"error": f"Erreur création réponse: {str(e)}"}), 500

        logger.info(f"Réponse publique soumise: {response_id}")

        return jsonify({
            "success": True,
            "response_id": response_id,
            "message": "Réponse soumise avec succès",
        }), 201

    except Exception as e:
        logger.error(f"Erreur soumission réponse publique: {e}")
        return jsonify({"error": str(e)}), 500
