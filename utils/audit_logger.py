"""
Système de logs d'audit pour FormForge
Enregistre toutes les actions sensibles pour la conformité et la sécurité
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, current_app, g
from functools import wraps

logger = logging.getLogger(__name__)

class AuditLogger:
    """Gestionnaire de logs d'audit"""
    
    def __init__(self):
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
        
        # Créer un handler pour les logs d'audit si pas déjà créé
        if not self.audit_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s'
            )
            handler.setFormatter(formatter)
            self.audit_logger.addHandler(handler)
    
    def _get_client_info(self) -> Dict[str, Any]:
        """Récupérer les informations du client"""
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        return {
            "ip_address": client_ip,
            "user_agent": request.headers.get("User-Agent", "Unknown"),
            "origin": request.headers.get("Origin", "Unknown"),
            "referer": request.headers.get("Referer", "Unknown"),
        }
    
    def _get_user_info(self) -> Dict[str, Any]:
        """Récupérer les informations de l'utilisateur authentifié"""
        user_info = {
            "user_id": None,
            "user_email": None,
            "user_role": None,
            "authenticated": False
        }
        
        # Essayer de récupérer l'utilisateur depuis le contexte Flask
        if hasattr(g, 'authenticated_user_id') and g.authenticated_user_id:
            user_info["user_id"] = g.authenticated_user_id
            user_info["authenticated"] = True
            
            # Récupérer les détails de l'utilisateur
            try:
                from models.security_models import SecurityUserDatastore
                from utils.admin_auth import get_user_role
                
                datastore = SecurityUserDatastore(current_app.db)
                user = datastore.find_user(id=g.authenticated_user_id)
                
                if user:
                    user_info["user_email"] = user.email
                    user_info["user_role"] = get_user_role(user.email)
                    
            except Exception as e:
                logger.warning(f"Erreur récupération détails utilisateur: {e}")
        
        return user_info
    
    def log_action(self, 
                   action: str, 
                   resource: str, 
                   resource_id: Optional[str] = None,
                   details: Optional[Dict[str, Any]] = None,
                   success: bool = True,
                   error_message: Optional[str] = None):
        """Enregistrer une action d'audit"""
        
        try:
            client_info = self._get_client_info()
            user_info = self._get_user_info()
            
            audit_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "resource": resource,
                "resource_id": resource_id,
                "success": success,
                "error_message": error_message,
                "details": details or {},
                "client": client_info,
                "user": user_info,
                "request": {
                    "method": request.method,
                    "url": request.url,
                    "endpoint": request.endpoint,
                    "content_type": request.content_type,
                    "content_length": request.content_length,
                }
            }
            
            # Log au niveau approprié
            if success:
                self.audit_logger.info(json.dumps(audit_data, ensure_ascii=False))
            else:
                self.audit_logger.warning(json.dumps(audit_data, ensure_ascii=False))
                
        except Exception as e:
            logger.error(f"Erreur enregistrement audit: {e}")
    
    def log_authentication(self, action: str, email: str, success: bool, details: Optional[Dict] = None):
        """Logger les actions d'authentification"""
        self.log_action(
            action=f"AUTH_{action.upper()}",
            resource="authentication",
            details={
                "email": email,
                "success": success,
                **(details or {})
            },
            success=success
        )
    
    def log_data_access(self, action: str, resource: str, resource_id: str, details: Optional[Dict] = None):
        """Logger les accès aux données"""
        self.log_action(
            action=f"DATA_{action.upper()}",
            resource=resource,
            resource_id=resource_id,
            details=details,
            success=True
        )
    
    def log_security_event(self, event_type: str, details: Optional[Dict] = None, severity: str = "medium"):
        """Logger les événements de sécurité"""
        self.log_action(
            action=f"SECURITY_{event_type.upper()}",
            resource="security",
            details={
                "severity": severity,
                **(details or {})
            },
            success=False  # Les événements de sécurité sont généralement des échecs
        )
    
    def log_admin_action(self, action: str, resource: str, resource_id: Optional[str] = None, details: Optional[Dict] = None):
        """Logger les actions d'administration"""
        self.log_action(
            action=f"ADMIN_{action.upper()}",
            resource=resource,
            resource_id=resource_id,
            details=details,
            success=True
        )

# Instance globale
audit_logger = AuditLogger()

def audit_log(action: str, resource: str, resource_id: Optional[str] = None, details: Optional[Dict] = None):
    """Décorateur pour logger automatiquement les actions"""
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                # Exécuter la fonction
                result = f(*args, **kwargs)
                
                # Logger l'action
                audit_logger.log_action(
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    details={
                        **(details or {}),
                        "execution_time": round(time.time() - start_time, 3)
                    },
                    success=True
                )
                
                return result
                
            except Exception as e:
                success = False
                error_message = str(e)
                
                # Logger l'erreur
                audit_logger.log_action(
                    action=action,
                    resource=resource,
                    resource_id=resource_id,
                    details={
                        **(details or {}),
                        "execution_time": round(time.time() - start_time, 3)
                    },
                    success=False,
                    error_message=error_message
                )
                
                raise
        
        return decorated_function
    return decorator

def audit_auth(action: str):
    """Décorateur spécialisé pour l'authentification"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            logger.debug(f"AUDIT_AUTH DECORATOR: {action} - START")
            start_time = time.time()

            try:
                logger.debug(f"AUDIT_AUTH: Calling function {f.__name__}")
                result = f(*args, **kwargs)
                logger.debug(f"AUDIT_AUTH: Function {f.__name__} returned successfully")

                # Extraire l'email depuis la requête
                email = "unknown"
                if request.is_json:
                    email = request.json.get("email", "unknown")

                audit_logger.log_authentication(
                    action=action,
                    email=email,
                    success=True,
                    details={
                        "execution_time": round(time.time() - start_time, 3)
                    }
                )

                return result

            except Exception as e:
                logger.debug(f"AUDIT_AUTH: EXCEPTION CAUGHT: {type(e).__name__}: {e}")
                # Extraire l'email depuis la requête
                email = "unknown"
                if request.is_json:
                    email = request.json.get("email", "unknown")

                logger.debug(f"AUDIT_AUTH: Logging authentication failure for {email}")
                audit_logger.log_authentication(
                    action=action,
                    email=email,
                    success=False,
                    details={
                        "error": str(e),
                        "execution_time": round(time.time() - start_time, 3)
                    }
                )

                logger.debug("AUDIT_AUTH: Re-raising exception")
                raise
        
        return decorated_function
    return decorator

def audit_data_access(action: str, resource: str):
    """Décorateur spécialisé pour l'accès aux données"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extraire l'ID de la ressource depuis les arguments
            resource_id = None
            if args:
                resource_id = str(args[0]) if args[0] else None
            
            audit_logger.log_data_access(
                action=action,
                resource=resource,
                resource_id=resource_id
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
