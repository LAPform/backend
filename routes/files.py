"""
Routes API pour la gestion des fichiers
"""

from flask import Blueprint, request, jsonify, current_app, send_file
from utils.file_manager import FileManager
from utils.security_auth import require_token_auth
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
import os
import logging

logger = logging.getLogger(__name__)

files_bp = Blueprint("files", __name__)


@files_bp.route("/files/upload", methods=["POST"])
@require_token_auth
@rate_limit("files_upload")
def upload_file(authenticated_user_id=None):
    """Uploader un fichier"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier fourni"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Aucun fichier sélectionné"}), 400

        # Sauvegarder le fichier
        result = FileManager.save_file(file, file.filename)

        if not result["success"]:
            return jsonify({"error": result["error"]}), 400

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Fichier uploadé avec succès",
                    "file": {
                        "filename": result["filename"],
                        "original_filename": result["original_filename"],
                        "file_size": result["file_size"],
                        "category": result["category"],
                        "file_hash": result["file_hash"],
                    },
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Erreur upload fichier: {e}")
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/<filename>", methods=["GET"])
@require_token_auth
@rate_limit("files_download")
def download_file(filename, authenticated_user_id=None):
    """Télécharger un fichier"""
    try:
        file_info = FileManager.get_file_info(filename)
        if not file_info:
            return jsonify({"error": "Fichier non trouvé"}), 404

        return send_file(
            file_info["file_path"], as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.error(f"Erreur téléchargement fichier: {e}")
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/<filename>/info", methods=["GET"])
def get_file_info(filename, authenticated_user_id=None):
    """Obtenir les informations d'un fichier"""
    try:
        file_info = FileManager.get_file_info(filename)
        if not file_info:
            return jsonify({"error": "Fichier non trouvé"}), 404

        return jsonify(
            {
                "success": True,
                "file": {
                    "filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "created_at": file_info["created_at"].isoformat(),
                    "modified_at": file_info["modified_at"].isoformat(),
                    "file_hash": file_info["file_hash"],
                },
            }
        )

    except Exception as e:
        logger.error(f"Erreur info fichier: {e}")
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/<filename>", methods=["DELETE"])
@require_token_auth
@rate_limit("files_delete")
def delete_file(filename, authenticated_user_id=None):
    """Supprimer un fichier"""
    try:
        success = FileManager.delete_file(filename)
        if not success:
            return jsonify({"error": "Fichier non trouvé ou erreur suppression"}), 404

        return jsonify({"success": True, "message": "Fichier supprimé avec succès"})

    except Exception as e:
        logger.error(f"Erreur suppression fichier: {e}")
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/allowed-types", methods=["GET"])
@require_token_auth
def get_allowed_types(authenticated_user_id=None):
    """Obtenir les types de fichiers autorisés"""
    try:
        return jsonify(
            {
                "success": True,
                "allowed_types": FileManager.ALLOWED_EXTENSIONS,
                "max_sizes": FileManager.MAX_SIZES,
            }
        )

    except Exception as e:
        logger.error(f"Erreur types autorisés: {e}")
        return jsonify({"error": str(e)}), 500


@files_bp.route("/files/validate", methods=["POST"])
@require_token_auth
def validate_file(authenticated_user_id=None):
    """Valider un fichier avant upload"""
    try:
        data = request.get_json()
        filename = data.get("filename")
        file_size = data.get("file_size")

        if not filename:
            return jsonify({"error": "Nom de fichier requis"}), 400

        # Vérifier le type
        if not FileManager.is_allowed_file(filename):
            return (
                jsonify(
                    {
                        "valid": False,
                        "error": "Type de fichier non autorisé",
                        "allowed_types": list(FileManager.ALLOWED_EXTENSIONS.keys()),
                    }
                ),
                400,
            )

        # Vérifier la taille
        if file_size:
            max_size = FileManager.get_max_size(filename)
            if file_size > max_size:
                return (
                    jsonify(
                        {
                            "valid": False,
                            "error": f"Fichier trop volumineux",
                            "max_size": max_size,
                            "max_size_mb": max_size // (1024 * 1024),
                        }
                    ),
                    400,
                )

        return jsonify(
            {
                "valid": True,
                "message": "Fichier valide",
                "category": FileManager.get_file_category(filename),
                "max_size": FileManager.get_max_size(filename),
            }
        )

    except Exception as e:
        logger.error(f"Erreur validation fichier: {e}")
        return jsonify({"error": str(e)}), 500
