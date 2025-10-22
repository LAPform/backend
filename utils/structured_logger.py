"""
Système de logging structuré pour FormForge
"""

import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g, current_app
import uuid


class StructuredLogger:
    """Logger structuré pour FormForge"""
    
    def __init__(self, name: str = None):
        self.logger = logging.getLogger(name or __name__)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configurer le logger avec format structuré"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """Obtenir le contexte de la requête"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'request_id': getattr(g, 'request_id', None),
        }
        
        if request:
            context.update({
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent'),
                'content_type': request.content_type,
                'content_length': request.content_length,
            })
            
            # Ajouter les paramètres de requête
            if request.args:
                context['query_params'] = dict(request.args)
            
            # Ajouter les headers importants
            important_headers = ['Authorization', 'X-Forwarded-For', 'X-Real-IP']
            context['headers'] = {
                header: request.headers.get(header) 
                for header in important_headers 
                if request.headers.get(header)
            }
        
        return context
    
    def _create_log_entry(
        self, 
        level: str, 
        message: str, 
        extra_data: Dict[str, Any] = None,
        exception: Exception = None
    ) -> Dict[str, Any]:
        """Créer une entrée de log structurée"""
        log_entry = {
            'level': level,
            'message': message,
            'context': self._get_request_context(),
        }
        
        if extra_data:
            log_entry['data'] = extra_data
        
        if exception:
            log_entry['exception'] = {
                'type': type(exception).__name__,
                'message': str(exception),
                'traceback': traceback.format_exc()
            }
        
        return log_entry
    
    def info(self, message: str, **kwargs):
        """Logger un message d'information"""
        log_entry = self._create_log_entry('INFO', message, kwargs)
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
    
    def warning(self, message: str, **kwargs):
        """Logger un avertissement"""
        log_entry = self._create_log_entry('WARNING', message, kwargs)
        self.logger.warning(json.dumps(log_entry, ensure_ascii=False))
    
    def error(self, message: str, exception: Exception = None, **kwargs):
        """Logger une erreur"""
        log_entry = self._create_log_entry('ERROR', message, kwargs, exception)
        self.logger.error(json.dumps(log_entry, ensure_ascii=False))
    
    def debug(self, message: str, **kwargs):
        """Logger un message de debug"""
        log_entry = self._create_log_entry('DEBUG', message, kwargs)
        self.logger.debug(json.dumps(log_entry, ensure_ascii=False))
    
    def critical(self, message: str, exception: Exception = None, **kwargs):
        """Logger une erreur critique"""
        log_entry = self._create_log_entry('CRITICAL', message, kwargs, exception)
        self.logger.critical(json.dumps(log_entry, ensure_ascii=False))


class APILogger:
    """Logger spécialisé pour les opérations API"""
    
    def __init__(self):
        self.logger = StructuredLogger('formforge.api')
    
    def request_started(self, endpoint: str, method: str, user_id: str = None):
        """Logger le début d'une requête"""
        self.logger.info(
            "API Request Started",
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            action="request_start"
        )
    
    def request_completed(
        self, 
        endpoint: str, 
        method: str, 
        status_code: int, 
        duration_ms: float,
        user_id: str = None
    ):
        """Logger la fin d'une requête"""
        self.logger.info(
            "API Request Completed",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            user_id=user_id,
            action="request_complete"
        )
    
    def authentication_success(self, user_id: str, email: str, method: str):
        """Logger une authentification réussie"""
        self.logger.info(
            "Authentication Success",
            user_id=user_id,
            email=email,
            method=method,
            action="auth_success"
        )
    
    def authentication_failed(self, email: str, reason: str, ip_address: str):
        """Logger une authentification échouée"""
        self.logger.warning(
            "Authentication Failed",
            email=email,
            reason=reason,
            ip_address=ip_address,
            action="auth_failed"
        )
    
    def user_registered(self, user_id: str, email: str):
        """Logger l'inscription d'un utilisateur"""
        self.logger.info(
            "User Registered",
            user_id=user_id,
            email=email,
            action="user_registration"
        )
    
    def form_created(self, form_id: str, user_id: str, title: str):
        """Logger la création d'un formulaire"""
        self.logger.info(
            "Form Created",
            form_id=form_id,
            user_id=user_id,
            title=title,
            action="form_creation"
        )
    
    def form_accessed(self, form_id: str, user_id: str = None, public: bool = False):
        """Logger l'accès à un formulaire"""
        self.logger.info(
            "Form Accessed",
            form_id=form_id,
            user_id=user_id,
            public=public,
            action="form_access"
        )
    
    def question_created(self, question_id: str, form_id: str, user_id: str, question_type: str):
        """Logger la création d'une question"""
        self.logger.info(
            "Question Created",
            question_id=question_id,
            form_id=form_id,
            user_id=user_id,
            question_type=question_type,
            action="question_creation"
        )
    
    def response_submitted(self, response_id: str, form_id: str, user_id: str = None):
        """Logger la soumission d'une réponse"""
        self.logger.info(
            "Response Submitted",
            response_id=response_id,
            form_id=form_id,
            user_id=user_id,
            action="response_submission"
        )
    
    def file_uploaded(self, filename: str, user_id: str, file_size: int):
        """Logger l'upload d'un fichier"""
        self.logger.info(
            "File Uploaded",
            filename=filename,
            user_id=user_id,
            file_size=file_size,
            action="file_upload"
        )
    
    def rate_limit_exceeded(self, endpoint: str, ip_address: str, limit: int):
        """Logger le dépassement de rate limit"""
        self.logger.warning(
            "Rate Limit Exceeded",
            endpoint=endpoint,
            ip_address=ip_address,
            limit=limit,
            action="rate_limit_exceeded"
        )
    
    def database_operation(self, operation: str, table: str, duration_ms: float, success: bool):
        """Logger une opération de base de données"""
        self.logger.info(
            "Database Operation",
            operation=operation,
            table=table,
            duration_ms=duration_ms,
            success=success,
            action="database_operation"
        )
    
    def security_event(self, event_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Logger un événement de sécurité"""
        self.logger.warning(
            "Security Event",
            event_type=event_type,
            details=details,
            severity=severity,
            action="security_event"
        )
    
    def performance_metric(self, metric_name: str, value: float, unit: str = "ms"):
        """Logger une métrique de performance"""
        self.logger.info(
            "Performance Metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            action="performance_metric"
        )


class DatabaseLogger:
    """Logger spécialisé pour les opérations de base de données"""
    
    def __init__(self):
        self.logger = StructuredLogger('formforge.database')
    
    def connection_established(self, database_url: str):
        """Logger l'établissement d'une connexion"""
        self.logger.info(
            "Database Connection Established",
            database_url=database_url.split('@')[-1] if '@' in database_url else database_url,
            action="db_connection"
        )
    
    def query_executed(self, query_type: str, table: str, duration_ms: float, rows_affected: int = None):
        """Logger l'exécution d'une requête"""
        self.logger.info(
            "Database Query Executed",
            query_type=query_type,
            table=table,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            action="db_query"
        )
    
    def query_failed(self, query_type: str, table: str, error: str, exception: Exception = None):
        """Logger l'échec d'une requête"""
        self.logger.error(
            "Database Query Failed",
            query_type=query_type,
            table=table,
            error=error,
            action="db_query_failed",
            exception=exception
        )
    
    def transaction_started(self, transaction_id: str):
        """Logger le début d'une transaction"""
        self.logger.info(
            "Database Transaction Started",
            transaction_id=transaction_id,
            action="db_transaction_start"
        )
    
    def transaction_committed(self, transaction_id: str, duration_ms: float):
        """Logger la validation d'une transaction"""
        self.logger.info(
            "Database Transaction Committed",
            transaction_id=transaction_id,
            duration_ms=duration_ms,
            action="db_transaction_commit"
        )
    
    def transaction_rolled_back(self, transaction_id: str, reason: str):
        """Logger l'annulation d'une transaction"""
        self.logger.warning(
            "Database Transaction Rolled Back",
            transaction_id=transaction_id,
            reason=reason,
            action="db_transaction_rollback"
        )


# Instances globales
api_logger = APILogger()
db_logger = DatabaseLogger()
structured_logger = StructuredLogger('formforge')


def log_request_start():
    """Logger le début d'une requête (à appeler au début de chaque route)"""
    try:
        if request:
            g.request_id = str(uuid.uuid4())
            api_logger.request_started(
                endpoint=request.endpoint or request.path,
                method=request.method,
                user_id=getattr(g, 'user_id', None)
            )
    except RuntimeError:
        # Contexte Flask non disponible
        pass


def log_request_end(status_code: int, duration_ms: float):
    """Logger la fin d'une requête (à appeler à la fin de chaque route)"""
    try:
        if request:
            api_logger.request_completed(
                endpoint=request.endpoint or request.path,
                method=request.method,
                status_code=status_code,
                duration_ms=duration_ms,
                user_id=getattr(g, 'user_id', None)
            )
    except RuntimeError:
        # Contexte Flask non disponible
        pass
