"""
Middleware global pour ajouter les headers de rate limiting à toutes les réponses
"""

import logging
from flask import request, current_app
from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


def setup_rate_limit_middleware(app):
    """Configurer le middleware global de rate limiting"""

    @app.after_request
    def add_rate_limit_headers(response):
        """Ajouter les headers de rate limiting à toutes les réponses"""
        try:
            # Déterminer le nom de la route basé sur l'endpoint
            endpoint = request.endpoint
            if not endpoint:
                return response

            # Mapper les endpoints aux noms de routes de rate limiting
            route_mapping = {
                "forms.create_form": "forms_create",
                "forms.get_form": "forms_get",
                "forms.update_form": "forms_update",
                "forms.delete_form": "forms_delete",
                "forms.list_forms": "forms_get",
                "forms.get_form_stats": "forms_stats",
                "questions.create_question": "questions_create",
                "questions.get_question": "questions_get",
                "questions.update_question": "questions_update",
                "questions.delete_question": "questions_delete",
                "questions.list_questions": "questions_get",
                "responses.submit_response": "responses_submit",
                "responses.get_responses": "responses_get",
                "security_auth.signup": "auth_signup",
                "security_auth.signin": "auth_signin",
                "security_auth.me": "auth_me",
                "monitoring.get_performance_stats": "monitoring_performance",
                "monitoring.get_health_status": "monitoring_health",
                "monitoring.get_system_metrics": "monitoring_system",
                "monitoring.get_dashboard_data": "monitoring_dashboard",
            }

            # Obtenir le nom de la route pour le rate limiting
            route_name = route_mapping.get(endpoint, "default")

            # Obtenir les headers de rate limiting
            headers = rate_limiter.get_rate_limit_headers(route_name)

            # Ajouter les headers à la réponse
            for key, value in headers.items():
                response.headers[key] = value

            logger.debug(f"Headers de rate limiting ajoutés pour {endpoint}: {headers}")

        except Exception as e:
            logger.error(f"Erreur ajout headers rate limiting: {e}")

        return response
