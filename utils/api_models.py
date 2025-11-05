"""
Modèles de documentation Flask-RESTx pour Swagger
Définit tous les schémas réutilisables pour l'API
"""

from flask_restx import fields


def register_models(api):
    """
    Enregistre tous les modèles de documentation dans l'API Flask-RESTx

    Args:
        api: Instance de flask_restx.Api
    """

    # ============================================================================
    # MODÈLES D'AUTHENTIFICATION
    # ============================================================================

    signup_model = api.model('Signup', {
        'email': fields.String(required=True, description='Email de l\'utilisateur', example='user@example.com'),
        'password': fields.String(required=True, description='Mot de passe (min 8 chars, maj, min, chiffre, spécial)', example='Password123!'),
        'name': fields.String(description='Nom complet de l\'utilisateur', example='John Doe'),
    })

    signin_model = api.model('Signin', {
        'email': fields.String(required=True, description='Email de l\'utilisateur', example='user@example.com'),
        'password': fields.String(required=True, description='Mot de passe', example='Password123!'),
    })

    change_password_model = api.model('ChangePassword', {
        'old_password': fields.String(required=True, description='Ancien mot de passe'),
        'new_password': fields.String(required=True, description='Nouveau mot de passe'),
    })

    auth_response_model = api.model('AuthResponse', {
        'user': fields.Raw(description='Informations utilisateur'),
        'token': fields.String(description='Token d\'authentification'),
        'message': fields.String(description='Message de confirmation'),
    })

    user_info_model = api.model('UserInfo', {
        'id': fields.Integer(description='ID de l\'utilisateur'),
        'email': fields.String(description='Email de l\'utilisateur'),
        'name': fields.String(description='Nom de l\'utilisateur'),
        'created_at': fields.String(description='Date de création du compte'),
        'roles': fields.List(fields.String, description='Rôles de l\'utilisateur'),
    })

    # ============================================================================
    # MODÈLES DE FORMULAIRES
    # ============================================================================

    form_settings_model = api.model('FormSettings', {
        'theme': fields.String(description='Thème du formulaire', example='blue'),
        'public': fields.Boolean(description='Formulaire public ou privé', example=True),
        'allow_multiple_responses': fields.Boolean(description='Autoriser plusieurs réponses', example=False),
        'require_login': fields.Boolean(description='Authentification requise', example=False),
        'show_progress': fields.Boolean(description='Afficher la progression', example=True),
        'collect_email': fields.Boolean(description='Collecter l\'email', example=True),
    })

    form_create_model = api.model('FormCreate', {
        'title': fields.String(required=True, description='Titre du formulaire', example='Sondage de satisfaction'),
        'description': fields.String(description='Description du formulaire', example='Évaluez notre service'),
        'settings': fields.Nested(form_settings_model, description='Paramètres du formulaire'),
    })

    form_update_model = api.model('FormUpdate', {
        'title': fields.String(description='Titre du formulaire'),
        'description': fields.String(description='Description du formulaire'),
        'settings': fields.Nested(form_settings_model, description='Paramètres du formulaire'),
        'status': fields.String(description='Statut du formulaire', enum=['draft', 'published', 'closed']),
    })

    form_response_model = api.model('Form', {
        'id': fields.Integer(description='ID du formulaire'),
        'title': fields.String(description='Titre du formulaire'),
        'description': fields.String(description='Description du formulaire'),
        'settings': fields.Raw(description='Paramètres du formulaire'),
        'status': fields.String(description='Statut du formulaire'),
        'created_by': fields.Integer(description='ID du créateur'),
        'created_at': fields.String(description='Date de création'),
        'updated_at': fields.String(description='Date de modification'),
        'public_token': fields.String(description='Token public pour partage'),
        'questions': fields.List(fields.Raw, description='Liste des questions'),
    })

    form_list_response_model = api.model('FormList', {
        'forms': fields.List(fields.Nested(form_response_model), description='Liste des formulaires'),
        'total': fields.Integer(description='Nombre total de formulaires'),
        'page': fields.Integer(description='Page actuelle'),
        'per_page': fields.Integer(description='Éléments par page'),
    })

    form_stats_model = api.model('FormStats', {
        'form_id': fields.Integer(description='ID du formulaire'),
        'total_responses': fields.Integer(description='Nombre total de réponses'),
        'total_questions': fields.Integer(description='Nombre total de questions'),
        'completion_rate': fields.Float(description='Taux de completion'),
        'last_response_at': fields.String(description='Date de dernière réponse'),
    })

    # ============================================================================
    # MODÈLES DE QUESTIONS
    # ============================================================================

    question_validation_model = api.model('QuestionValidation', {
        'min_length': fields.Integer(description='Longueur minimale'),
        'max_length': fields.Integer(description='Longueur maximale'),
        'pattern': fields.String(description='Pattern regex'),
        'min_value': fields.Float(description='Valeur minimale'),
        'max_value': fields.Float(description='Valeur maximale'),
        'required_format': fields.String(description='Format requis'),
    })

    question_create_model = api.model('QuestionCreate', {
        'type': fields.String(required=True, description='Type de question',
                            enum=['text', 'textarea', 'multiple', 'checkbox', 'scale', 'date', 'time', 'file', 'email', 'number', 'phone', 'url', 'rating', 'dropdown', 'matrix']),
        'text': fields.String(required=True, description='Texte de la question', example='Quelle est votre satisfaction ?'),
        'description': fields.String(description='Description/aide pour la question'),
        'required': fields.Boolean(description='Question obligatoire', example=True),
        'order_index': fields.Integer(description='Position de la question'),
        'options': fields.Raw(description='Options pour questions à choix multiples', example=['Très satisfait', 'Satisfait', 'Insatisfait']),
        'validation': fields.Nested(question_validation_model, description='Règles de validation'),
    })

    question_update_model = api.model('QuestionUpdate', {
        'type': fields.String(description='Type de question'),
        'text': fields.String(description='Texte de la question'),
        'description': fields.String(description='Description de la question'),
        'required': fields.Boolean(description='Question obligatoire'),
        'order_index': fields.Integer(description='Position de la question'),
        'options': fields.Raw(description='Options pour questions à choix multiples'),
        'validation': fields.Nested(question_validation_model, description='Règles de validation'),
    })

    question_response_model = api.model('Question', {
        'id': fields.Integer(description='ID de la question'),
        'form_id': fields.Integer(description='ID du formulaire parent'),
        'type': fields.String(description='Type de question'),
        'text': fields.String(description='Texte de la question'),
        'description': fields.String(description='Description de la question'),
        'required': fields.Boolean(description='Question obligatoire'),
        'order_index': fields.Integer(description='Position de la question'),
        'options': fields.Raw(description='Options disponibles'),
        'validation': fields.Raw(description='Règles de validation'),
        'created_at': fields.String(description='Date de création'),
    })

    questions_reorder_model = api.model('QuestionsReorder', {
        'question_orders': fields.Raw(required=True, description='Map question_id -> order_index',
                                     example={'1': 0, '2': 1, '3': 2}),
    })

    # ============================================================================
    # MODÈLES DE RÉPONSES
    # ============================================================================

    response_create_model = api.model('ResponseCreate', {
        'answers': fields.Raw(required=True, description='Réponses aux questions (map question_id -> answer)',
                            example={'1': 'Très satisfait', '2': 'Excellent service'}),
        'respondent_email': fields.String(description='Email du répondant (optionnel)'),
    })

    response_model = api.model('Response', {
        'id': fields.Integer(description='ID de la réponse'),
        'form_id': fields.Integer(description='ID du formulaire'),
        'answers': fields.Raw(description='Réponses fournies'),
        'submitted_at': fields.String(description='Date de soumission'),
        'user_id': fields.Integer(description='ID de l\'utilisateur (si authentifié)'),
        'ip_address': fields.String(description='Adresse IP du répondant'),
    })

    responses_list_model = api.model('ResponsesList', {
        'responses': fields.List(fields.Nested(response_model), description='Liste des réponses'),
        'total': fields.Integer(description='Nombre total de réponses'),
    })

    analytics_model = api.model('Analytics', {
        'form_id': fields.Integer(description='ID du formulaire'),
        'total_responses': fields.Integer(description='Nombre total de réponses'),
        'questions_analytics': fields.Raw(description='Statistiques par question'),
        'completion_time_avg': fields.Float(description='Temps moyen de complétion (secondes)'),
        'response_trend': fields.Raw(description='Tendance des réponses par jour'),
    })

    question_analytics_model = api.model('QuestionAnalytics', {
        'question_id': fields.Integer(description='ID de la question'),
        'question_text': fields.String(description='Texte de la question'),
        'total_answers': fields.Integer(description='Nombre total de réponses'),
        'answer_distribution': fields.Raw(description='Distribution des réponses'),
        'most_common': fields.String(description='Réponse la plus fréquente'),
    })

    # ============================================================================
    # MODÈLES DE FICHIERS
    # ============================================================================

    file_upload_response_model = api.model('FileUploadResponse', {
        'file_id': fields.String(description='ID unique du fichier'),
        'filename': fields.String(description='Nom du fichier'),
        'size': fields.Integer(description='Taille en octets'),
        'mime_type': fields.String(description='Type MIME du fichier'),
        'url': fields.String(description='URL de téléchargement'),
        'uploaded_at': fields.String(description='Date d\'upload'),
    })

    # ============================================================================
    # MODÈLES GÉNÉRIQUES
    # ============================================================================

    success_model = api.model('Success', {
        'success': fields.Boolean(description='Succès de l\'opération', example=True),
        'message': fields.String(description='Message de confirmation', example='Opération réussie'),
        'data': fields.Raw(description='Données supplémentaires'),
    })

    error_model = api.model('Error', {
        'success': fields.Boolean(description='Succès de l\'opération', example=False),
        'error': fields.String(description='Message d\'erreur'),
        'error_code': fields.Integer(description='Code d\'erreur'),
        'details': fields.Raw(description='Détails supplémentaires'),
    })

    health_model = api.model('Health', {
        'status': fields.String(description='Statut de l\'API', example='healthy'),
        'message': fields.String(description='Message de santé'),
        'version': fields.String(description='Version de l\'API'),
        'security': fields.String(description='Système de sécurité utilisé'),
    })

    pagination_model = api.model('Pagination', {
        'page': fields.Integer(description='Page actuelle', example=1),
        'per_page': fields.Integer(description='Éléments par page', example=100),
        'total': fields.Integer(description='Nombre total d\'éléments', example=250),
        'pages': fields.Integer(description='Nombre total de pages', example=3),
    })

    # Retourner un dictionnaire avec tous les modèles pour référence
    return {
        # Auth
        'signup': signup_model,
        'signin': signin_model,
        'change_password': change_password_model,
        'auth_response': auth_response_model,
        'user_info': user_info_model,

        # Forms
        'form_settings': form_settings_model,
        'form_create': form_create_model,
        'form_update': form_update_model,
        'form': form_response_model,
        'form_list': form_list_response_model,
        'form_stats': form_stats_model,

        # Questions
        'question_validation': question_validation_model,
        'question_create': question_create_model,
        'question_update': question_update_model,
        'question': question_response_model,
        'questions_reorder': questions_reorder_model,

        # Responses
        'response_create': response_create_model,
        'response': response_model,
        'responses_list': responses_list_model,
        'analytics': analytics_model,
        'question_analytics': question_analytics_model,

        # Files
        'file_upload': file_upload_response_model,

        # Generic
        'success': success_model,
        'error': error_model,
        'health': health_model,
        'pagination': pagination_model,
    }
