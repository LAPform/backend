"""
Routes API pour FormForge
"""

from .forms import forms_bp
from .questions import questions_bp
from .responses import responses_bp

__all__ = ["forms_bp", "questions_bp", "responses_bp", "register_namespaces"]


def register_namespaces(api):
    """
    Enregistre tous les namespaces Flask-RESTx dans l'API principale

    Args:
        api: Instance de flask_restx.Api
    """
    # Importer tous les namespaces
    from routes.forms_ns import api as forms_ns, public_forms_bp
    from routes.questions_ns import api as questions_ns
    from routes.responses_ns import api as responses_ns, public_responses_bp
    from routes.auth_ns import api as auth_ns
    from routes.files_ns import api as files_ns
    from routes.monitoring_ns import api as monitoring_ns

    # Enregistrer les namespaces avec leurs préfixes
    api.add_namespace(forms_ns, path='/forms')
    api.add_namespace(questions_ns, path='/questions')
    api.add_namespace(responses_ns, path='/responses')
    api.add_namespace(auth_ns, path='/auth')
    api.add_namespace(files_ns, path='/files')
    api.add_namespace(monitoring_ns, path='/monitoring')

    # Retourner les blueprints supplémentaires à enregistrer (routes publiques)
    return {
        'public_forms': public_forms_bp,
        'public_responses': public_responses_bp
    }
