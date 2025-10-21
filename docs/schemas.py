"""
Schémas de validation pour l'API FormForge
"""

from flask_restx import fields, Model

# Schéma pour un formulaire
FormSchema = Model('Form', {
    'id': fields.String(required=True, description='ID unique du formulaire'),
    'title': fields.String(required=True, description='Titre du formulaire'),
    'description': fields.String(description='Description du formulaire'),
    'settings': fields.Raw(description='Paramètres du formulaire (JSON)'),
    'created_at': fields.DateTime(description='Date de création'),
    'updated_at': fields.DateTime(description='Date de dernière modification'),
    'questions': fields.List(fields.Nested('Question'), description='Questions du formulaire')
})

# Schéma pour créer un formulaire
FormCreateSchema = Model('FormCreate', {
    'title': fields.String(required=True, description='Titre du formulaire', example='Sondage de satisfaction'),
    'description': fields.String(description='Description du formulaire', example='Évaluez notre service'),
    'settings': fields.Raw(description='Paramètres du formulaire', example={'theme': 'blue', 'public': True})
})

# Schéma pour une question
QuestionSchema = Model('Question', {
    'id': fields.String(required=True, description='ID unique de la question'),
    'form_id': fields.String(required=True, description='ID du formulaire parent'),
    'type': fields.String(required=True, description='Type de question', 
                         enum=['text', 'textarea', 'multiple', 'checkbox', 'scale', 'date', 'time', 'file', 'email', 'number']),
    'text': fields.String(required=True, description='Texte de la question'),
    'options': fields.List(fields.String, description='Options pour les questions à choix'),
    'required': fields.Boolean(description='Question obligatoire'),
    'validation': fields.Raw(description='Règles de validation'),
    'order_index': fields.Integer(description='Ordre d\'affichage'),
    'created_at': fields.DateTime(description='Date de création')
})

# Schéma pour créer une question
QuestionCreateSchema = Model('QuestionCreate', {
    'type': fields.String(required=True, description='Type de question', 
                         enum=['text', 'textarea', 'multiple', 'checkbox', 'scale', 'date', 'time', 'file', 'email', 'number'],
                         example='text'),
    'text': fields.String(required=True, description='Texte de la question', 
                         example='Quel est votre nom ?'),
    'options': fields.List(fields.String, description='Options pour les questions à choix',
                          example=['Option 1', 'Option 2', 'Option 3']),
    'required': fields.Boolean(description='Question obligatoire', example=True),
    'validation': fields.Raw(description='Règles de validation', 
                            example={'min_length': 2, 'max_length': 50}),
    'order_index': fields.Integer(description='Ordre d\'affichage', example=0)
})

# Schéma pour une réponse
ResponseSchema = Model('Response', {
    'id': fields.String(required=True, description='ID unique de la réponse'),
    'form_id': fields.String(required=True, description='ID du formulaire'),
    'answers': fields.Raw(required=True, description='Réponses (JSON)'),
    'submitted_at': fields.DateTime(description='Date de soumission'),
    'user_id': fields.String(description='ID de l\'utilisateur'),
    'ip_address': fields.String(description='Adresse IP')
})

# Schéma pour soumettre une réponse
ResponseCreateSchema = Model('ResponseCreate', {
    'answers': fields.Raw(required=True, description='Réponses aux questions (JSON)',
                         example={'question_id_1': 'Ma réponse', 'question_id_2': ['Option 1', 'Option 2']}),
    'user_id': fields.String(description='ID de l\'utilisateur', example='user123')
})

# Schéma pour les statistiques
StatsSchema = Model('Stats', {
    'total_questions': fields.Integer(description='Nombre total de questions'),
    'total_responses': fields.Integer(description='Nombre total de réponses'),
    'form_id': fields.String(description='ID du formulaire')
})

# Schéma pour les analytics
AnalyticsSchema = Model('Analytics', {
    'total_responses': fields.Integer(description='Nombre total de réponses'),
    'daily_stats': fields.List(fields.Raw, description='Statistiques quotidiennes'),
    'hourly_stats': fields.List(fields.Raw, description='Statistiques horaires')
})

# Schéma de succès
SuccessSchema = Model('Success', {
    'success': fields.Boolean(description='Statut de succès', example=True),
    'message': fields.String(description='Message de confirmation', example='Opération réussie'),
    'data': fields.Raw(description='Données retournées')
})

# Schéma d'erreur
ErrorSchema = Model('Error', {
    'error': fields.String(description='Message d\'erreur', example='Erreur de validation'),
    'details': fields.Raw(description='Détails de l\'erreur')
})

# Schéma pour la pagination
PaginationSchema = Model('Pagination', {
    'limit': fields.Integer(description='Nombre d\'éléments par page'),
    'offset': fields.Integer(description='Décalage'),
    'total': fields.Integer(description='Nombre total d\'éléments')
})

# Schéma pour la santé de l'API
HealthSchema = Model('Health', {
    'status': fields.String(description='Statut de l\'API', example='healthy'),
    'message': fields.String(description='Message de statut', example='FormForge POC Backend is running'),
    'version': fields.String(description='Version de l\'API', example='1.0.0')
})
