"""
Middleware de logging pour Flask
"""

import time
import uuid
import os
from flask import request, g, current_app


class LoggingMiddleware:
    """Middleware pour logger automatiquement les requêtes"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialiser le middleware avec l'application Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)
    
    def before_request(self):
        """Exécuté avant chaque requête"""
        g.start_time = time.time()
        g.request_id = str(uuid.uuid4())
        
        # Importer ici pour éviter les problèmes de contexte
        from utils.structured_logger import api_logger
        
        # Logger le début de la requête
        api_logger.request_started(
            endpoint=request.endpoint or request.path,
            method=request.method,
            user_id=getattr(g, 'user_id', None)
        )
        
        # Logger les détails de la requête
        api_logger.logger.info(
            "Request Details",
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            content_type=request.content_type,
            content_length=request.content_length,
            action="request_details"
        )
    
    def after_request(self, response):
        """Exécuté après chaque requête"""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Importer ici pour éviter les problèmes de contexte
            from utils.structured_logger import api_logger
            
            # Logger la fin de la requête
            api_logger.request_completed(
                endpoint=request.endpoint or request.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user_id=getattr(g, 'user_id', None)
            )
            
            # Logger les métriques de performance
            api_logger.performance_metric(
                metric_name="request_duration",
                value=duration_ms,
                unit="ms"
            )
            
            # Logger les détails de la réponse
            api_logger.logger.info(
                "Response Details",
                status_code=response.status_code,
                content_length=response.content_length,
                content_type=response.content_type,
                duration_ms=duration_ms,
                action="response_details"
            )
        
        return response
    
    def teardown_request(self, exception):
        """Exécuté en cas d'exception"""
        if exception:
            # Importer ici pour éviter les problèmes de contexte
            from utils.structured_logger import api_logger
            
            api_logger.logger.error(
                "Request Exception",
                exception=str(exception),
                exception_type=type(exception).__name__,
                action="request_exception"
            )


def setup_logging_config(app):
    """Configurer le logging pour l'application"""
    import logging
    import os
    
    # Configuration du niveau de log
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Configuration du format de log
    if not app.logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        app.logger.addHandler(handler)
    
    # Logger la configuration
    app.logger.info(f"Logging configured with level: {log_level}")


def log_application_startup(app):
    """Logger le démarrage de l'application"""
    from utils.structured_logger import api_logger
    api_logger.logger.info(
        "Application Started",
        app_name=app.name,
        debug=app.debug,
        environment=os.environ.get('FLASK_ENV', 'production'),
        action="app_startup"
    )


def log_application_shutdown(app):
    """Logger l'arrêt de l'application"""
    from utils.structured_logger import api_logger
    api_logger.logger.info(
        "Application Shutdown",
        app_name=app.name,
        action="app_shutdown"
    )
