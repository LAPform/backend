"""
Routes de documentation pour l'API FormForge
"""

from flask import Blueprint, jsonify, render_template_string
from docs.examples import *

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/docs/examples")
def get_examples():
    """Obtenir tous les exemples d'utilisation de l'API"""
    return jsonify(
        {
            "form_create": FORM_CREATE_EXAMPLE,
            "question_create": QUESTION_CREATE_EXAMPLE,
            "response_create": RESPONSE_CREATE_EXAMPLE,
            "form_response": FORM_RESPONSE_EXAMPLE,
            "stats_response": STATS_RESPONSE_EXAMPLE,
            "error_response": ERROR_RESPONSE_EXAMPLE,
            "success_response": SUCCESS_RESPONSE_EXAMPLE,
        }
    )


@docs_bp.route("/docs/guide")
def get_guide():
    """Guide d'utilisation de l'API"""
    return jsonify(
        {
            "title": "Guide d'utilisation FormForge API",
            "version": "1.0.0",
            "base_url": "/api",
            "authentication": "Authentification requise - Utiliser /api/auth/signup et /api/auth/signin",
            "content_type": "application/json",
            "endpoints": {
                "authentication": {
                    "POST /api/auth/signup": "Créer un compte utilisateur",
                    "POST /api/auth/signin": "Se connecter",
                    "POST /api/auth/logout": "Se déconnecter",
                    "GET /api/auth/me": "Informations utilisateur actuel",
                },
                "forms": {
                    "GET /api/forms": "Lister tous les formulaires (authentifié)",
                    "POST /api/forms": "Créer un nouveau formulaire (authentifié)",
                    "GET /api/forms/{id}": "Récupérer un formulaire (authentifié)",
                    "PUT /api/forms/{id}": "Modifier un formulaire (authentifié)",
                    "DELETE /api/forms/{id}": "Supprimer un formulaire (authentifié)",
                    "GET /api/forms/{id}/stats": "Statistiques d'un formulaire (authentifié)",
                },
                "questions": {
                    "POST /api/forms/{id}/questions": "Ajouter une question",
                    "GET /api/forms/{id}/questions": "Lister les questions",
                    "PUT /api/questions/{id}": "Modifier une question",
                    "DELETE /api/questions/{id}": "Supprimer une question",
                },
                "responses": {
                    "POST /api/forms/{id}/responses": "Soumettre une réponse",
                    "GET /api/forms/{id}/responses": "Voir les réponses",
                    "GET /api/forms/{id}/export/csv": "Exporter en CSV",
                    "GET /api/forms/{id}/export/excel": "Exporter en Excel",
                },
            },
            "question_types": [
                "text",
                "textarea",
                "multiple",
                "checkbox",
                "scale",
                "date",
                "time",
                "file",
                "email",
                "number",
            ],
            "examples": {
                "create_form": FORM_CREATE_EXAMPLE,
                "create_question": QUESTION_CREATE_EXAMPLE,
                "submit_response": RESPONSE_CREATE_EXAMPLE,
            },
        }
    )


# Template HTML pour la documentation
DOCS_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FormForge API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .method { font-weight: bold; color: #007bff; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <h1>FormForge API Documentation</h1>
    <p>API REST pour FormForge - Clone de Google Forms</p>
    
    <h2>Endpoints d'Authentification</h2>
    
    <div class="endpoint">
        <span class="method">POST</span> /api/auth/signup - Créer un compte utilisateur
    </div>
    
    <div class="endpoint">
        <span class="method">POST</span> /api/auth/signin - Se connecter
    </div>
    
    <div class="endpoint">
        <span class="method">POST</span> /api/auth/logout - Se déconnecter
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> /api/auth/me - Informations utilisateur actuel
    </div>
    
    <h2>Endpoints Principaux</h2>
    
    <div class="endpoint">
        <span class="method">GET</span> /api/health - Vérifier l'état de l'API
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> /api/forms - Lister tous les formulaires (authentifié)
    </div>
    
    <div class="endpoint">
        <span class="method">POST</span> /api/forms - Créer un nouveau formulaire (authentifié)
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> /api/forms/{id} - Récupérer un formulaire (authentifié)
    </div>
    
    <h2>Exemple d'Authentification</h2>
    <div class="code">
POST /api/auth/signup
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "Password123!",
    "name": "John Doe"
}
    </div>
    
    <div class="code">
POST /api/auth/signin
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "Password123!"
}
    </div>
    
    <h2>Exemple de Création de Formulaire (Authentifié)</h2>
    <div class="code">
POST /api/forms
Content-Type: application/json
Authorization: Bearer [token]

{
    "title": "Sondage de satisfaction",
    "description": "Évaluez notre service",
    "settings": {
        "theme": "blue",
        "public": true
    }
}
    </div>
    
    <h2>Types de Questions Supportés</h2>
    <ul>
        <li>text - Texte court</li>
        <li>textarea - Texte long</li>
        <li>multiple - Choix multiple (radio)</li>
        <li>checkbox - Cases à cocher</li>
        <li>scale - Échelle linéaire</li>
        <li>date - Date</li>
        <li>time - Heure</li>
        <li>file - Upload de fichier</li>
        <li>email - Email</li>
        <li>number - Nombre</li>
    </ul>
    
    <p><a href="/api/docs/">Documentation Swagger Interactive</a></p>
</body>
</html>
"""


@docs_bp.route("/docs")
def docs_html():
    """Documentation HTML simple"""
    return render_template_string(DOCS_HTML_TEMPLATE)


@docs_bp.route("/swagger.json")
def swagger_json():
    """Endpoint Swagger JSON simple"""
    return jsonify(
        {
            "swagger": "2.0",
            "info": {
                "title": "FormForge API",
                "version": "1.0.0",
                "description": "API REST pour FormForge - Clone de Google Forms",
            },
            "host": "backend-skum.onrender.com",
            "basePath": "/api",
            "schemes": ["https"],
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health Check",
                        "description": "Vérifier l'état de l'API",
                        "responses": {
                            "200": {
                                "description": "API is healthy",
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "string"},
                                        "message": {"type": "string"},
                                        "version": {"type": "string"},
                                    },
                                },
                            }
                        },
                    }
                },
                "/forms": {
                    "get": {
                        "summary": "List Forms",
                        "description": "Lister tous les formulaires",
                        "responses": {"200": {"description": "Liste des formulaires"}},
                    },
                    "post": {
                        "summary": "Create Form",
                        "description": "Créer un nouveau formulaire",
                        "parameters": [
                            {
                                "name": "body",
                                "in": "body",
                                "required": True,
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string"},
                                        "description": {"type": "string"},
                                        "settings": {"type": "object"},
                                    },
                                },
                            }
                        ],
                        "responses": {
                            "201": {"description": "Formulaire créé avec succès"}
                        },
                    },
                },
            },
        }
    )
