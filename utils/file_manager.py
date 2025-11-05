"""
Gestionnaire de fichiers pour FormForge
"""

import os
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Optional
import re


class FileManager:
    """Gestionnaire de fichiers uploadés"""

    # Types de fichiers autorisés (listes pour sérialisation JSON)
    ALLOWED_EXTENSIONS = {
        "images": ["png", "jpg", "jpeg", "gif", "bmp", "webp"],
        "documents": ["pdf", "doc", "docx", "txt", "rtf"],
        "spreadsheets": ["xls", "xlsx", "csv"],
        "presentations": ["ppt", "pptx"],
        "archives": ["zip", "rar", "7z", "tar", "gz"],
        "videos": ["mp4", "avi", "mov", "wmv", "flv"],
        "audio": ["mp3", "wav", "ogg", "aac"],
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

    # Magic numbers (signatures) pour validation des types de fichiers
    MAGIC_NUMBERS = {
        # Images
        b"\x89\x50\x4E\x47": "png",
        b"\xFF\xD8\xFF": "jpg",
        b"\x47\x49\x46\x38": "gif",
        b"\x42\x4D": "bmp",
        b"\x52\x49\x46\x46": "webp",  # Vérifié ensuite avec WEBP
        # Documents
        b"\x25\x50\x44\x46": "pdf",
        b"\xD0\xCF\x11\xE0": "doc",  # Aussi xls, ppt (MS Office)
        b"\x50\x4B\x03\x04": "docx",  # Aussi xlsx, pptx (ZIP-based)
        # Archives
        b"\x50\x4B\x03\x04": "zip",
        b"\x52\x61\x72\x21": "rar",
        b"\x37\x7A\xBC\xAF": "7z",
        b"\x1F\x8B": "gz",
        # Videos
        b"\x00\x00\x00\x18\x66\x74\x79\x70": "mp4",
        b"\x52\x49\x46\x46": "avi",  # Vérifié ensuite avec AVI
        # Audio
        b"\x49\x44\x33": "mp3",
        b"\x52\x49\x46\x46": "wav",  # Vérifié ensuite avec WAVE
        b"\x4F\x67\x67\x53": "ogg",
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
    def validate_file_signature(file, filename: str) -> tuple[bool, str]:
        """
        Valider la signature (magic number) d'un fichier

        Returns:
            tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Lire les premiers octets du fichier
            file.seek(0)
            header = file.read(32)  # Lire les 32 premiers octets
            file.seek(0)  # Retourner au début

            if len(header) < 4:
                return False, "Fichier trop petit ou vide"

            # Vérifier la correspondance avec les magic numbers
            detected_type = None
            for magic, file_type in FileManager.MAGIC_NUMBERS.items():
                if header.startswith(magic):
                    detected_type = file_type
                    # Pour RIFF files (webp, avi, wav), vérifier le sous-type
                    if magic == b"\x52\x49\x46\x46" and len(header) >= 12:
                        riff_type = header[8:12]
                        if riff_type == b"WEBP":
                            detected_type = "webp"
                        elif riff_type == b"AVI ":
                            detected_type = "avi"
                        elif riff_type == b"WAVE":
                            detected_type = "wav"
                    break

            if not detected_type:
                return False, "Type de fichier non reconnu par signature"

            # Vérifier que l'extension correspond au type détecté
            ext = filename.lower().split(".")[-1] if "." in filename else ""

            # Mapper les extensions alternatives
            ext_mapping = {
                "jpeg": "jpg",
                "tiff": "tif",
            }
            normalized_ext = ext_mapping.get(ext, ext)

            # Pour les fichiers Office, plusieurs extensions partagent la même signature
            if detected_type == "doc" and ext in ["doc", "xls", "ppt"]:
                return True, ""
            elif detected_type == "docx" and ext in ["docx", "xlsx", "pptx", "zip"]:
                return True, ""
            elif detected_type == normalized_ext or detected_type == ext:
                return True, ""
            else:
                return False, f"L'extension .{ext} ne correspond pas au type de fichier détecté ({detected_type})"

        except Exception as e:
            return False, f"Erreur validation signature: {str(e)}"

    @staticmethod
    def get_max_size(filename: str) -> int:
        """Obtenir la taille maximale pour un fichier"""
        category = FileManager.get_file_category(filename)
        return FileManager.MAX_SIZES.get(category, 5) * 1024 * 1024  # 5 MB par défaut

    @staticmethod
    def generate_filename(original_filename: str) -> str:
        """Générer un nom de fichier unique"""
        # Sécuriser le nom original (alternative à werkzeug)
        safe_name = re.sub(r"[^\w\-_\.]", "_", original_filename)
        name, ext = os.path.splitext(safe_name)

        # Générer un nom unique
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{timestamp}_{unique_id}_{name}{ext}"

    @staticmethod
    def get_upload_path(filename: str) -> str:
        """Obtenir le chemin de stockage pour un fichier"""
        # Valider que le nom de fichier ne contient pas de séquences de traversal
        if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
            raise ValueError("Invalid filename - path traversal detected")

        category = FileManager.get_file_category(filename)
        # Utiliser un dossier par défaut au lieu de current_app
        upload_folder = os.path.abspath("uploads")

        # Créer le dossier principal et le dossier de catégorie
        os.makedirs(upload_folder, exist_ok=True)
        category_folder = os.path.join(upload_folder, category)
        os.makedirs(category_folder, exist_ok=True)

        # Construire le chemin complet et le normaliser
        full_path = os.path.normpath(os.path.join(category_folder, filename))

        # SÉCURITÉ: Vérifier que le chemin final est bien dans le dossier uploads
        if not full_path.startswith(upload_folder):
            raise ValueError("Invalid file path - path traversal detected")

        return full_path

    @staticmethod
    def save_file(file, filename: str) -> Dict[str, str]:
        """Sauvegarder un fichier uploadé"""
        try:
            # Vérifier le type de fichier
            if not FileManager.is_allowed_file(filename):
                return {"success": False, "error": "Type de fichier non autorisé"}

            # SÉCURITÉ: Valider la signature du fichier (magic number)
            is_valid, error_msg = FileManager.validate_file_signature(file, filename)
            if not is_valid:
                return {"success": False, "error": f"Validation de signature échouée: {error_msg}"}

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
