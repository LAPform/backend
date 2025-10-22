"""
Système de gestion d'erreurs centralisé pour FormForge
"""

import traceback
import logging
from typing import Dict, Any, Optional
from flask import request, jsonify, current_app
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Gestionnaire centralisé des erreurs"""
    
    # Codes d'erreur personnalisés
    ERROR_CODES = {
        # Erreurs d'authentification (1000-1099)
        'AUTH_INVALID_CREDENTIALS': {'code': 1001, 'message': 'Identifiants invalides'},
        'AUTH_TOKEN_EXPIRED': {'code': 1002, 'message': 'Token expiré'},
        'AUTH_TOKEN_INVALID': {'code': 1003, 'message': 'Token invalide'},
        'AUTH_USER_NOT_FOUND': {'code': 1004, 'message': 'Utilisateur non trouvé'},
        'AUTH_EMAIL_ALREADY_EXISTS': {'code': 1005, 'message': 'Email déjà utilisé'},
        
        # Erreurs de validation (2000-2099)
        'VALIDATION_REQUIRED_FIELD': {'code': 2001, 'message': 'Champ requis manquant'},
        'VALIDATION_INVALID_FORMAT': {'code': 2002, 'message': 'Format invalide'},
        'VALIDATION_OUT_OF_RANGE': {'code': 2003, 'message': 'Valeur hors limites'},
        'VALIDATION_INVALID_TYPE': {'code': 2004, 'message': 'Type de données invalide'},
        'VALIDATION_TOO_LONG': {'code': 2005, 'message': 'Texte trop long'},
        'VALIDATION_TOO_SHORT': {'code': 2006, 'message': 'Texte trop court'},
        
        # Erreurs de ressources (3000-3099)
        'RESOURCE_NOT_FOUND': {'code': 3001, 'message': 'Ressource non trouvée'},
        'RESOURCE_ALREADY_EXISTS': {'code': 3002, 'message': 'Ressource déjà existante'},
        'RESOURCE_ACCESS_DENIED': {'code': 3003, 'message': 'Accès refusé'},
        'RESOURCE_CONFLICT': {'code': 3004, 'message': 'Conflit de ressources'},
        
        # Erreurs de base de données (4000-4099)
        'DB_CONNECTION_ERROR': {'code': 4001, 'message': 'Erreur de connexion à la base de données'},
        'DB_QUERY_ERROR': {'code': 4002, 'message': 'Erreur de requête base de données'},
        'DB_CONSTRAINT_ERROR': {'code': 4003, 'message': 'Contrainte de base de données violée'},
        'DB_TRANSACTION_ERROR': {'code': 4004, 'message': 'Erreur de transaction'},
        
        # Erreurs de fichiers (5000-5099)
        'FILE_NOT_FOUND': {'code': 5001, 'message': 'Fichier non trouvé'},
        'FILE_TOO_LARGE': {'code': 5002, 'message': 'Fichier trop volumineux'},
        'FILE_INVALID_TYPE': {'code': 5003, 'message': 'Type de fichier non autorisé'},
        'FILE_UPLOAD_ERROR': {'code': 5004, 'message': 'Erreur d\'upload de fichier'},
        
        # Erreurs de rate limiting (6000-6099)
        'RATE_LIMIT_EXCEEDED': {'code': 6001, 'message': 'Limite de requêtes dépassée'},
        
        # Erreurs système (9000-9099)
        'SYSTEM_ERROR': {'code': 9001, 'message': 'Erreur système interne'},
        'SYSTEM_MAINTENANCE': {'code': 9002, 'message': 'Système en maintenance'},
        'SYSTEM_OVERLOAD': {'code': 9003, 'message': 'Système surchargé'},
    }
    
    @staticmethod
    def get_error_info(error_code: str) -> Dict[str, Any]:
        """Obtenir les informations d'une erreur"""
        return ErrorHandler.ERROR_CODES.get(error_code, {
            'code': 9999,
            'message': 'Erreur inconnue'
        })
    
    @staticmethod
    def create_error_response(
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> tuple:
        """Créer une réponse d'erreur standardisée"""
        error_info = ErrorHandler.get_error_info(error_code)
        
        response_data = {
            'error': True,
            'error_code': error_code,
            'code': error_info['code'],
            'message': error_info['message'],
            'timestamp': datetime.utcnow().isoformat(),
            'path': request.path if request else None,
            'method': request.method if request else None,
        }
        
        if request_id:
            response_data['request_id'] = request_id
        
        if details:
            response_data['details'] = details
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def handle_validation_error(validation_errors: list) -> tuple:
        """Gérer les erreurs de validation"""
        return ErrorHandler.create_error_response(
            'VALIDATION_REQUIRED_FIELD',
            400,
            {'validation_errors': validation_errors}
        )
    
    @staticmethod
    def handle_not_found_error(resource_type: str = "Ressource") -> tuple:
        """Gérer les erreurs de ressource non trouvée"""
        return ErrorHandler.create_error_response(
            'RESOURCE_NOT_FOUND',
            404,
            {'resource_type': resource_type}
        )
    
    @staticmethod
    def handle_auth_error(error_type: str = 'AUTH_INVALID_CREDENTIALS') -> tuple:
        """Gérer les erreurs d'authentification"""
        return ErrorHandler.create_error_response(
            error_type,
            401 if 'TOKEN' not in error_type else 401,
            {'auth_error': True}
        )
    
    @staticmethod
    def handle_database_error(operation: str, original_error: Exception) -> tuple:
        """Gérer les erreurs de base de données"""
        request_id = str(uuid.uuid4())
        
        # Logger l'erreur complète
        logger.error(f"Database error in {operation}: {str(original_error)}", exc_info=True)
        
        return ErrorHandler.create_error_response(
            'DB_QUERY_ERROR',
            500,
            {
                'operation': operation,
                'request_id': request_id
            },
            request_id
        )
    
    @staticmethod
    def handle_file_error(error_type: str, filename: str = None) -> tuple:
        """Gérer les erreurs de fichiers"""
        details = {'filename': filename} if filename else None
        return ErrorHandler.create_error_response(
            error_type,
            400 if 'NOT_FOUND' in error_type else 500,
            details
        )
    
    @staticmethod
    def handle_rate_limit_error(limit: int, remaining: int, reset_time: float) -> tuple:
        """Gérer les erreurs de rate limiting"""
        return ErrorHandler.create_error_response(
            'RATE_LIMIT_EXCEEDED',
            429,
            {
                'limit': limit,
                'remaining': remaining,
                'reset_time': reset_time,
                'retry_after': int(reset_time - datetime.utcnow().timestamp())
            }
        )
    
    @staticmethod
    def handle_system_error(operation: str, original_error: Exception) -> tuple:
        """Gérer les erreurs système"""
        request_id = str(uuid.uuid4())
        
        # Logger l'erreur complète
        logger.error(f"System error in {operation}: {str(original_error)}", exc_info=True)
        
        return ErrorHandler.create_error_response(
            'SYSTEM_ERROR',
            500,
            {
                'operation': operation,
                'request_id': request_id
            },
            request_id
        )
    
    @staticmethod
    def log_error(error_code: str, details: Dict = None, exception: Exception = None):
        """Logger une erreur avec contexte"""
        log_data = {
            'error_code': error_code,
            'path': request.path if request else None,
            'method': request.method if request else None,
            'user_agent': request.headers.get('User-Agent') if request else None,
            'ip_address': request.remote_addr if request else None,
        }
        
        if details:
            log_data.update(details)
        
        if exception:
            log_data['exception'] = str(exception)
            log_data['traceback'] = traceback.format_exc()
        
        logger.error(f"API Error: {error_code}", extra=log_data)


# Instance globale du gestionnaire d'erreurs
error_handler = ErrorHandler()


def handle_api_error(error_code: str, status_code: int = 500, details: Dict = None):
    """Décorateur pour gérer les erreurs d'API"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                error_handler.log_error(error_code, details, e)
                return error_handler.create_error_response(error_code, status_code, details)
        return wrapper
    return decorator


def validate_request_data(required_fields: list, data: dict) -> tuple:
    """Valider les données de requête"""
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return error_handler.handle_validation_error([
            f"Champ requis manquant: {field}" for field in missing_fields
        ])
    
    return None, None


def ensure_resource_exists(resource, resource_type: str = "Ressource"):
    """Vérifier qu'une ressource existe"""
    if not resource:
        return error_handler.handle_not_found_error(resource_type)
    return None, None
