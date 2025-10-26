"""
Système d'authentification pour les administrateurs
Contrôle d'accès basé sur les rôles pour les métriques sensibles
"""

import logging
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)

# Liste des emails administrateurs (en production, utiliser une base de données)
ADMIN_EMAILS = [
    "admin@formforge.com",
    "test.fonctionnel@example.com",  # Pour les tests
    "admin.test@example.com",  # Nouvel admin pour les tests
    # Ajouter d'autres emails admin selon les besoins
]

def require_admin_role(f):
    """
    Décorateur pour restreindre l'accès aux administrateurs uniquement
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Récupérer le token d'authentification
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.warning("🔒 ADMIN: Tentative d'accès sans token")
                return jsonify({
                    "success": False,
                    "error": "Token d'authentification requis",
                    "code": "AUTH_TOKEN_REQUIRED"
                }), 401

            token = auth_header.split(' ')[1]
            
            # Valider le token et récupérer l'utilisateur
            from utils.security_auth import _validate_sha256_token
            user_id = _validate_sha256_token(token)
            
            if not user_id:
                logger.warning("🔒 ADMIN: Token invalide")
                return jsonify({
                    "success": False,
                    "error": "Token invalide",
                    "code": "INVALID_TOKEN"
                }), 401

            # Récupérer les informations utilisateur
            from models.security_models import SecurityUserDatastore
            datastore = SecurityUserDatastore(current_app.db)
            user = datastore.find_user(id=user_id)
            
            if not user:
                logger.warning(f"🔒 ADMIN: Utilisateur non trouvé pour ID: {user_id}")
                return jsonify({
                    "success": False,
                    "error": "Utilisateur non trouvé",
                    "code": "USER_NOT_FOUND"
                }), 404

            # Vérifier si l'utilisateur est administrateur
            if user.email not in ADMIN_EMAILS:
                logger.warning(f"🔒 ADMIN: Accès refusé pour {user.email} - Pas administrateur")
                return jsonify({
                    "success": False,
                    "error": "Accès refusé - Privilèges administrateur requis",
                    "code": "INSUFFICIENT_PRIVILEGES"
                }), 403

            logger.info(f"🔒 ADMIN: Accès autorisé pour {user.email}")
            
            # Ajouter l'utilisateur aux arguments de la fonction
            kwargs['authenticated_user_id'] = user_id
            kwargs['admin_user'] = user
            
            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"🔒 ADMIN: Erreur vérification admin: {e}")
            return jsonify({
                "success": False,
                "error": "Erreur de vérification des privilèges",
                "code": "ADMIN_CHECK_ERROR"
            }), 500

    return decorated_function


def require_monitoring_access(f):
    """
    Décorateur pour l'accès aux métriques de monitoring (niveau intermédiaire)
    Permet l'accès aux métriques de base mais pas aux métriques système sensibles
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Récupérer le token d'authentification
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.warning("🔒 MONITORING: Tentative d'accès sans token")
                return jsonify({
                    "success": False,
                    "error": "Token d'authentification requis",
                    "code": "AUTH_TOKEN_REQUIRED"
                }), 401

            token = auth_header.split(' ')[1]
            
            # Valider le token et récupérer l'utilisateur
            from utils.security_auth import _validate_sha256_token
            user_id = _validate_sha256_token(token)
            
            if not user_id:
                logger.warning("🔒 MONITORING: Token invalide")
                return jsonify({
                    "success": False,
                    "error": "Token invalide",
                    "code": "INVALID_TOKEN"
                }), 401

            # Récupérer les informations utilisateur
            from models.security_models import SecurityUserDatastore
            datastore = SecurityUserDatastore(current_app.db)
            user = datastore.find_user(id=user_id)
            
            if not user:
                logger.warning(f"🔒 MONITORING: Utilisateur non trouvé pour ID: {user_id}")
                return jsonify({
                    "success": False,
                    "error": "Utilisateur non trouvé",
                    "code": "USER_NOT_FOUND"
                }), 404

            logger.info(f"🔒 MONITORING: Accès autorisé pour {user.email}")
            
            # Ajouter l'utilisateur aux arguments de la fonction
            kwargs['authenticated_user_id'] = user_id
            kwargs['monitoring_user'] = user
            
            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"🔒 MONITORING: Erreur vérification monitoring: {e}")
            return jsonify({
                "success": False,
                "error": "Erreur de vérification des privilèges",
                "code": "MONITORING_CHECK_ERROR"
            }), 500

    return decorated_function


def sanitize_system_metrics(metrics):
    """
    Sanitiser les métriques système pour les utilisateurs non-admin
    Retire les informations sensibles
    """
    if not isinstance(metrics, dict):
        return metrics
    
    # Informations sensibles à masquer
    sensitive_keys = [
        'cpu_percent',
        'memory_percent', 
        'disk_percent',
        'process_memory',
        'process_cpu_percent',
        'memory_total_gb',
        'memory_used_gb',
        'disk_total_gb',
        'disk_used_gb',
        'pid',
        'platform'
    ]
    
    sanitized = {}
    for key, value in metrics.items():
        if key in sensitive_keys:
            # Masquer les valeurs sensibles
            sanitized[key] = "***"
        elif isinstance(value, dict):
            # Récursion pour les dictionnaires imbriqués
            sanitized[key] = sanitize_system_metrics(value)
        else:
            sanitized[key] = value
    
    return sanitized


def get_user_role(user_email):
    """
    Déterminer le rôle d'un utilisateur basé sur son email
    """
    if user_email in ADMIN_EMAILS:
        return "admin"
    else:
        return "user"
