"""
Routes API pour la gestion des fichiers (Flask-RESTx avec Swagger)
"""

from flask import request, send_file, current_app
from flask_restx import Namespace, Resource
from utils.file_manager import FileManager
from utils.security_auth import require_token_auth
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
import os
import logging

logger = logging.getLogger(__name__)

# Créer le namespace
api = Namespace('files', description='Upload et gestion des fichiers')

# Récupérer les modèles depuis la configuration
def get_models():
    """Récupère les modèles de documentation depuis la config de l'app"""
    return current_app.config.get('API_MODELS', {})


@api.route('/upload')
class FileUpload(Resource):
    """Upload de fichiers"""

    @api.doc('upload_file',
             description='Uploader un fichier avec validation de type et taille - Types autorisés: images, documents, vidéos',
             security='Bearer',
             consumes='multipart/form-data',
             params={'file': {'description': 'Fichier à uploader', 'type': 'file', 'required': True}})
    @api.response(201, 'Fichier uploadé', get_models().get('file_upload'))
    @api.response(400, 'Fichier invalide', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("files_upload")
    def post(self, authenticated_user_id=None):
        """Uploader un fichier"""
        try:
            if "file" not in request.files:
                return {"error": "Aucun fichier fourni"}, 400

            file = request.files["file"]
            if file.filename == "":
                return {"error": "Aucun fichier sélectionné"}, 400

            # Sauvegarder le fichier
            result = FileManager.save_file(file, file.filename)

            if not result["success"]:
                return {"error": result["error"]}, 400

            return {
                "success": True,
                "message": "Fichier uploadé avec succès",
                "file": {
                    "filename": result["filename"],
                    "original_filename": result["original_filename"],
                    "file_size": result["file_size"],
                    "category": result["category"],
                    "file_hash": result["file_hash"],
                },
            }, 201

        except Exception as e:
            logger.error(f"Erreur upload fichier: {e}")
            return {"error": str(e)}, 500


@api.route('/<string:filename>')
@api.param('filename', 'Le nom du fichier')
class FileResource(Resource):
    """Gestion d'un fichier spécifique"""

    @api.doc('download_file',
             description='Télécharger un fichier par son nom',
             security='Bearer',
             produces=['application/octet-stream'])
    @api.response(200, 'Fichier téléchargé')
    @api.response(404, 'Fichier non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("files_download")
    def get(self, filename, authenticated_user_id=None):
        """Télécharger un fichier"""
        try:
            file_info = FileManager.get_file_info(filename)
            if not file_info:
                return {"error": "Fichier non trouvé"}, 404

            return send_file(
                file_info["file_path"], as_attachment=True, download_name=filename
            )

        except Exception as e:
            logger.error(f"Erreur téléchargement fichier: {e}")
            return {"error": str(e)}, 500

    @api.doc('delete_file',
             description='Supprimer un fichier par son nom',
             security='Bearer')
    @api.response(200, 'Fichier supprimé', get_models().get('success'))
    @api.response(404, 'Fichier non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("files_delete")
    def delete(self, filename, authenticated_user_id=None):
        """Supprimer un fichier"""
        try:
            success = FileManager.delete_file(filename)
            if not success:
                return {"error": "Fichier non trouvé ou erreur suppression"}, 404

            return {"success": True, "message": "Fichier supprimé avec succès"}

        except Exception as e:
            logger.error(f"Erreur suppression fichier: {e}")
            return {"error": str(e)}, 500


@api.route('/<string:filename>/info')
@api.param('filename', 'Le nom du fichier')
class FileInfo(Resource):
    """Informations sur un fichier"""

    @api.doc('get_file_info',
             description='Obtenir les métadonnées d\'un fichier (taille, hash, dates)',
             security='Bearer')
    @api.response(200, 'Informations du fichier')
    @api.response(404, 'Fichier non trouvé', get_models().get('error'))
    def get(self, filename, authenticated_user_id=None):
        """Obtenir les informations d'un fichier"""
        try:
            file_info = FileManager.get_file_info(filename)
            if not file_info:
                return {"error": "Fichier non trouvé"}, 404

            return {
                "success": True,
                "file": {
                    "filename": file_info["filename"],
                    "file_size": file_info["file_size"],
                    "created_at": file_info["created_at"].isoformat(),
                    "modified_at": file_info["modified_at"].isoformat(),
                    "file_hash": file_info["file_hash"],
                },
            }

        except Exception as e:
            logger.error(f"Erreur info fichier: {e}")
            return {"error": str(e)}, 500


@api.route('/allowed-types')
class AllowedTypes(Resource):
    """Types de fichiers autorisés"""

    @api.doc('get_allowed_types',
             description='Obtenir la liste des types de fichiers autorisés et leurs tailles maximales',
             security='Bearer')
    @api.response(200, 'Types autorisés')
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def get(self, authenticated_user_id=None):
        """Obtenir les types de fichiers autorisés"""
        try:
            return {
                "success": True,
                "allowed_types": FileManager.ALLOWED_EXTENSIONS,
                "max_sizes": FileManager.MAX_SIZES,
            }

        except Exception as e:
            logger.error(f"Erreur types autorisés: {e}")
            return {"error": str(e)}, 500


@api.route('/validate')
class ValidateFile(Resource):
    """Validation de fichier avant upload"""

    @api.doc('validate_file',
             description='Valider qu\'un fichier peut être uploadé (type et taille) avant de l\'envoyer',
             security='Bearer')
    @api.response(200, 'Validation réussie')
    @api.response(400, 'Fichier invalide', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    def post(self, authenticated_user_id=None):
        """Valider un fichier avant upload"""
        try:
            data = request.get_json()
            filename = data.get("filename")
            file_size = data.get("file_size")

            if not filename:
                return {"error": "Nom de fichier requis"}, 400

            # Vérifier le type
            if not FileManager.is_allowed_file(filename):
                return {
                    "valid": False,
                    "error": "Type de fichier non autorisé",
                    "allowed_types": list(FileManager.ALLOWED_EXTENSIONS.keys()),
                }, 400

            # Vérifier la taille
            if file_size:
                max_size = FileManager.get_max_size(filename)
                if file_size > max_size:
                    return {
                        "valid": False,
                        "error": f"Fichier trop volumineux",
                        "max_size": max_size,
                        "max_size_mb": max_size // (1024 * 1024),
                    }, 400

            return {
                "valid": True,
                "message": "Fichier valide",
                "category": FileManager.get_file_category(filename),
                "max_size": FileManager.get_max_size(filename),
            }

        except Exception as e:
            logger.error(f"Erreur validation fichier: {e}")
            return {"error": str(e)}, 500
