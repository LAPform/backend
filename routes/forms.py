"""
Routes API pour la gestion des formulaires
"""

from flask import Blueprint, request, jsonify, current_app
from models.form import Form
from models.question import Question
from models.response import Response
from utils.security_auth import require_auth
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

forms_bp = Blueprint("forms", __name__)


@forms_bp.route("/forms", methods=["POST"])
@require_auth
@rate_limit("forms_create")
def create_form(authenticated_user_id=None, **kwargs):
    """
    Créer un nouveau formulaire

    Exemple de requête:
    ```json
    {
        "title": "Sondage de satisfaction",
        "description": "Évaluez notre service",
        "settings": {
            "theme": "blue",
            "public": true
        }
    }
    ```
    """
    try:
        # Gestion robuste du parsing JSON avec gestion d'erreur d'encodage
        try:
            data = request.get_json()
        except Exception as json_error:
            logger.error(f"Erreur parsing JSON: {json_error}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Erreur de format JSON",
                        "message": "Le JSON envoyé contient des caractères invalides",
                    }
                ),
                400,
            )

        if not data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Données manquantes",
                        "message": "Aucune donnée JSON fournie",
                    }
                ),
                400,
            )

        # Debug: Logger les données reçues
        logger.info(f"Données reçues pour création formulaire: {data}")

        # Nettoyer les données pour éviter les problèmes d'encodage
        if isinstance(data, dict):
            # Nettoyer les chaînes de caractères
            for key, value in data.items():
                if isinstance(value, str):
                    # Nettoyer les caractères problématiques
                    data[key] = value.encode("utf-8", errors="ignore").decode("utf-8")

        # Validation des données requises
        validation_error, status_code = validate_request_data(["title"], data)
        if validation_error:
            return validation_error

        title = data["title"]
        description = data.get("description", "")
        settings = data.get("settings", {})

        # Validation stricte des données
        validation_errors = []

        # Validation titre
        if not DataValidator.validate_text_length(title, 1, 200):
            validation_errors.append("Le titre doit contenir entre 1 et 200 caractères")

        # Validation description (optionnelle)
        if description and not DataValidator.validate_text_length(description, 0, 1000):
            validation_errors.append(
                "La description doit contenir moins de 1000 caractères"
            )

        # Validation settings
        if settings and not isinstance(settings, dict):
            validation_errors.append("Les paramètres doivent être un objet JSON")

        if validation_errors:
            return error_handler.handle_validation_error(validation_errors)

        # Récupérer l'utilisateur authentifié depuis les kwargs ou la session
        from flask import session

        user_id = authenticated_user_id or kwargs.get("authenticated_user_id") or session.get(
            "user_id", "unknown_user"
        )

        # Debug: Logger l'utilisateur et les données
        logger.info(f"Utilisateur authentifié: {user_id}")
        logger.info(f"Titre: {title}, Description: {description}, Settings: {settings}")

        # Créer le formulaire
        try:
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            form_id = form_model.create(title, description, settings, user_id)

            # Logger la création du formulaire
            api_logger.form_created(form_id, user_id, title)

        except Exception as e:
            logger.error(f"Erreur lors de la création du formulaire: {str(e)}")
            logger.error(f"Type d'erreur: {type(e).__name__}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return error_handler.handle_database_error("form_creation", e)

        logger.info(f"Formulaire créé: {form_id}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Formulaire créé avec succès",
                    "data": {"form_id": form_id},
                }
            ),
            201,
        )

    except Exception as e:
        return error_handler.handle_system_error("form_creation", e)


@forms_bp.route("/forms/<form_id>", methods=["GET"])
@require_auth
@rate_limit("forms_get")
def get_form(form_id, authenticated_user_id=None, **kwargs):
    """
    Récupérer un formulaire par ID (seulement si l'utilisateur en est propriétaire)

    Retourne le formulaire complet avec toutes ses questions.
    """
    try:
        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        try:
            from models.database import DatabaseManager

            db = DatabaseManager()
            form_model = Form(db)
            # Vérifier la propriété du formulaire
            form = form_model.get_by_id_and_user(form_id, authenticated_user_id)
        except Exception as e:
            logger.error(f"Error retrieving form: {e}")
            return jsonify({"error": f"Erreur récupération formulaire: {str(e)}"}), 500

        if not form:
            return jsonify({"error": "Formulaire non trouvé ou accès non autorisé"}), 404

        # Récupérer les questions du formulaire
        try:
            form_with_questions = form_model.get_with_questions(form_id)
            if form_with_questions:
                return jsonify({"success": True, "form": form_with_questions})
            else:
                return jsonify({"success": True, "form": form})
        except Exception as e:
            logger.error(f"Error retrieving questions: {e}")
            return jsonify({"success": True, "form": form})

    except Exception as e:
        logger.error(f"Erreur récupération formulaire: {e}")
        return jsonify({"error": str(e)}), 500


@forms_bp.route("/forms/<form_id>", methods=["PUT"])
@require_auth
@rate_limit("forms_update")
def update_form(form_id, authenticated_user_id=None, **kwargs):
    """Mettre à jour un formulaire (seulement si l'utilisateur en est propriétaire)"""
    try:
        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        data = request.get_json()

        if not data:
            return jsonify({"error": "Données requises"}), 400

        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)

        # Vérifier que le formulaire existe ET que l'utilisateur en est propriétaire
        if not form_model.is_owner(form_id, authenticated_user_id):
            return jsonify({"error": "Formulaire non trouvé ou accès non autorisé"}), 404

        # Mettre à jour
        success = form_model.update(
            form_id,
            title=data.get("title"),
            description=data.get("description"),
            settings=data.get("settings"),
        )

        if not success:
            return jsonify({"error": "Erreur lors de la mise à jour"}), 500

        logger.info(f"Formulaire mis à jour: {form_id} par utilisateur: {authenticated_user_id}")

        return jsonify(
            {"success": True, "message": "Formulaire mis à jour avec succès"}
        )

    except Exception as e:
        logger.error(f"Erreur mise à jour formulaire: {e}")
        return jsonify({"error": str(e)}), 500


@forms_bp.route("/forms/<form_id>", methods=["DELETE"])
@require_auth
@rate_limit("forms_delete")
def delete_form(form_id, authenticated_user_id=None, **kwargs):
    """Supprimer un formulaire (seulement si l'utilisateur en est propriétaire)"""
    try:
        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)

        # Vérifier que le formulaire existe ET que l'utilisateur en est propriétaire
        if not form_model.is_owner(form_id, authenticated_user_id):
            return jsonify({"error": "Formulaire non trouvé ou accès non autorisé"}), 404

        # Supprimer
        success = form_model.delete(form_id)

        if not success:
            return jsonify({"error": "Erreur lors de la suppression"}), 500

        logger.info(f"Formulaire supprimé: {form_id} par utilisateur: {authenticated_user_id}")

        return jsonify({"success": True, "message": "Formulaire supprimé avec succès"})

    except Exception as e:
        logger.error(f"Erreur suppression formulaire: {e}")
        return jsonify({"error": str(e)}), 500


@forms_bp.route("/forms", methods=["GET"])
@require_auth
@rate_limit("forms_get")
def list_forms(authenticated_user_id=None, **kwargs):
    """Lister tous les formulaires de l'utilisateur authentifié"""
    try:
        # Paramètres de pagination
        limit = request.args.get("limit", 100, type=int)
        offset = request.args.get("offset", 0, type=int)

        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        # Filtrer les formulaires par utilisateur
        forms = form_model.get_all(limit, offset, user_id=authenticated_user_id)

        return jsonify(
            {
                "success": True,
                "forms": forms,
                "pagination": {"limit": limit, "offset": offset, "total": len(forms)},
            }
        )

    except Exception as e:
        logger.error(f"Erreur liste formulaires: {e}")
        return jsonify({"error": str(e)}), 500


@forms_bp.route("/forms/<form_id>/stats", methods=["GET"])
@require_auth
def get_form_stats(form_id, authenticated_user_id=None, **kwargs):
    """Récupérer les statistiques d'un formulaire (seulement si l'utilisateur en est propriétaire)"""
    try:
        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        response_model = Response(db)

        # Vérifier que le formulaire existe ET que l'utilisateur en est propriétaire
        if not form_model.is_owner(form_id, authenticated_user_id):
            return jsonify({"error": "Formulaire non trouvé ou accès non autorisé"}), 404

        # Récupérer les statistiques
        stats = form_model.get_stats(form_id)
        analytics = response_model.get_analytics(form_id)

        return jsonify({"success": True, "stats": stats, "analytics": analytics})

    except Exception as e:
        logger.error(f"Erreur statistiques formulaire: {e}")
        return jsonify({"error": str(e)}), 500


@forms_bp.route("/forms/<form_id>/duplicate", methods=["POST"])
@require_auth
def duplicate_form(form_id, authenticated_user_id=None, **kwargs):
    """Dupliquer un formulaire (seulement si l'utilisateur en est propriétaire)"""
    try:
        # Vérifier que l'utilisateur est authentifié
        if not authenticated_user_id:
            return jsonify({"error": "Utilisateur non authentifié"}), 401

        from models.database import DatabaseManager

        db = DatabaseManager()
        form_model = Form(db)
        question_model = Question(db)

        # Vérifier que le formulaire existe ET que l'utilisateur en est propriétaire
        if not form_model.is_owner(form_id, authenticated_user_id):
            return jsonify({"error": "Formulaire non trouvé ou accès non autorisé"}), 404

        # Récupérer le formulaire original
        original_form = form_model.get_with_questions(form_id)
        if not original_form:
            return jsonify({"error": "Formulaire non trouvé"}), 404

        # Créer le nouveau formulaire avec le même utilisateur
        new_title = f"{original_form['title']} (Copie)"
        new_description = original_form.get("description", "")
        new_settings = original_form.get("settings", {})

        new_form_id = form_model.create(new_title, new_description, new_settings, authenticated_user_id)

        # Dupliquer les questions
        for question in original_form.get("questions", []):
            question_model.create(
                form_id=new_form_id,
                type=question["type"],
                text=question["text"],
                options=question.get("options", []),
                required=question.get("required", False),
                validation=question.get("validation", {}),
                order_index=question.get("order_index", 0),
            )

        logger.info(f"Formulaire dupliqué: {form_id} -> {new_form_id} par utilisateur: {authenticated_user_id}")

        return jsonify(
            {
                "success": True,
                "new_form_id": new_form_id,
                "message": "Formulaire dupliqué avec succès",
            }
        )

    except Exception as e:
        logger.error(f"Erreur duplication formulaire: {e}")
        return jsonify({"error": str(e)}), 500
