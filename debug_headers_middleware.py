"""
Middleware de debug pour logger tous les headers de requêtes
"""
import logging

logger = logging.getLogger(__name__)


def log_all_requests(app):
    """Logger tous les headers de toutes les requêtes"""

    @app.before_request
    def log_request_headers():
        from flask import request

        logger.info("=" * 80)
        logger.info(f">>> DEBUG REQUEST: {request.method} {request.path}")
        logger.info(f">>> Headers:")
        for header, value in request.headers:
            # Masquer les tokens complets pour sécurité (montrer juste le début)
            if "token" in header.lower() or "authorization" in header.lower():
                display_value = value[:30] + "..." if len(value) > 30 else value
                logger.info(f">>>   {header}: {display_value}")
            else:
                logger.info(f">>>   {header}: {value}")
        logger.info("=" * 80)
