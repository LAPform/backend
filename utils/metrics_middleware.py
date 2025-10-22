"""
Middleware pour collecter les métriques API automatiquement
"""

from flask import request, g
import time
import logging

logger = logging.getLogger(__name__)


class MetricsMiddleware:
    """Middleware pour collecter les métriques de requêtes"""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialiser le middleware avec l'application Flask"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Exécuté avant chaque requête"""
        g.start_time = time.time()
        g.request_id = f"{int(time.time() * 1000)}-{id(request)}"

    def after_request(self, response):
        """Exécuté après chaque requête"""
        try:
            if hasattr(g, 'start_time'):
                response_time = time.time() - g.start_time
                
                # Enregistrer les métriques
                from utils.metrics_collector import metrics_collector
                
                endpoint = request.endpoint or request.path
                method = request.method
                status_code = response.status_code
                
                metrics_collector.record_request(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    response_time=response_time
                )
                
                # Ajouter des headers de métriques
                response.headers['X-Response-Time'] = f"{response_time:.3f}s"
                response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
                
        except Exception as e:
            logger.error(f"Erreur collecte métriques middleware: {e}")
            
        return response
