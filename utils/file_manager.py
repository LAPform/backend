"""
Gestionnaire de fichiers pour FormForge
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Optional
from werkzeug.utils import secure_filename
from flask import current_app


class FileManager:
    """Gestionnaire de fichiers uploadés"""

    # Types de fichiers autorisés
    ALLOWED_EXTENSIONS = {
        "images": {"png", "jpg", "jpeg", "gif", "bmp", "webp"},
        "documents": {"pdf", "doc", "docx", "txt", "rtf"},
        "spreadsheets": {"xls", "xlsx", "csv"},
        "presentations": {"ppt", "pptx"},
        "archives": {"zip", "rar", "7z", "tar", "gz"},
        "videos": {"mp4", "avi", "mov", "wmv", "flv"},
        "audio": {"mp3", "wav", "ogg", "aac"},
    }

    # Taille maximale par type (en MB)
    MAX_SIZES = {
        "images": 10,  # 10 MB
        "documents": 25,  # 25 MB
        "spreadsheets": 25,
        "presentations": 25,
        "archives": 50,  # 50 MB
        "videos": 100,  # 100 MB
        "audio": 50,  # 50 MB
    }

    @staticmethod
    def get_file_category(filename: str) -> str:
        """Déterminer la catégorie d'un fichier"""
        ext = filename.lower().split(".")[-1] if "." in filename else ""

        for category, extensions in FileManager.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return category
        return "other"

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Vérifier si le fichier est autorisé"""
        category = FileManager.get_file_category(filename)
        return category != "other"

    @staticmethod
    def get_max_size(filename: str) -> int:
        """Obtenir la taille maximale pour un fichier"""
        category = FileManager.get_file_category(filename)
        return FileManager.MAX_SIZES.get(category, 5) * 1024 * 1024  # 5 MB par défaut

    @staticmethod
    def generate_filename(original_filename: str) -> str:
        """Générer un nom de fichier unique"""
        # Sécuriser le nom original
        safe_name = secure_filename(original_filename)
        name, ext = os.path.splitext(safe_name)

        # Générer un nom unique
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{timestamp}_{unique_id}_{name}{ext}"

    @staticmethod
    def get_upload_path(filename: str) -> str:
        """Obtenir le chemin de stockage pour un fichier"""
        category = FileManager.get_file_category(filename)
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")

        # Créer le dossier de catégorie
        category_folder = os.path.join(upload_folder, category)
        os.makedirs(category_folder, exist_ok=True)

        return os.path.join(category_folder, filename)

    @staticmethod
    def save_file(file, filename: str) -> Dict[str, str]:
        """Sauvegarder un fichier uploadé"""
        try:
            # Vérifier le type de fichier
            if not FileManager.is_allowed_file(filename):
                return {"success": False, "error": "Type de fichier non autorisé"}

            # Vérifier la taille
            file.seek(0, 2)  # Aller à la fin
            file_size = file.tell()
            file.seek(0)  # Retourner au début

            max_size = FileManager.get_max_size(filename)
            if file_size > max_size:
                return {
                    "success": False,
                    "error": f"Fichier trop volumineux. Maximum: {max_size // (1024*1024)} MB",
                }

            # Générer un nom unique
            unique_filename = FileManager.generate_filename(filename)
            file_path = FileManager.get_upload_path(unique_filename)

            # Sauvegarder le fichier
            file.save(file_path)

            # Calculer le hash pour l'intégrité
            file_hash = FileManager.calculate_file_hash(file_path)

            return {
                "success": True,
                "filename": unique_filename,
                "original_filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "file_hash": file_hash,
                "category": FileManager.get_file_category(filename),
            }

        except Exception as e:
            return {"success": False, "error": f"Erreur sauvegarde: {str(e)}"}

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculer le hash SHA256 d'un fichier"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @staticmethod
    def delete_file(filename: str) -> bool:
        """Supprimer un fichier"""
        try:
            file_path = FileManager.get_upload_path(filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_file_info(filename: str) -> Optional[Dict]:
        """Obtenir les informations d'un fichier"""
        try:
            file_path = FileManager.get_upload_path(filename)
            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)
            return {
                "filename": filename,
                "file_path": file_path,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "file_hash": FileManager.calculate_file_hash(file_path),
            }
        except Exception:
            return None
