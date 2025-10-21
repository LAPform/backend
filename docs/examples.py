"""
Exemples d'utilisation de l'API FormForge
"""

# Exemple de création de formulaire
FORM_CREATE_EXAMPLE = {
    "title": "Sondage de satisfaction client",
    "description": "Aidez-nous à améliorer notre service en répondant à ce questionnaire",
    "settings": {
        "theme": "blue",
        "public": True,
        "allow_anonymous": True,
        "collect_emails": False
    }
}

# Exemple de création de question
QUESTION_CREATE_EXAMPLE = {
    "type": "multiple",
    "text": "Comment avez-vous découvert notre service ?",
    "options": [
        "Réseaux sociaux",
        "Recommandation d'un ami",
        "Publicité en ligne",
        "Moteur de recherche",
        "Autre"
    ],
    "required": True,
    "validation": {
        "min_selections": 1,
        "max_selections": 1
    },
    "order_index": 0
}

# Exemple de soumission de réponse
RESPONSE_CREATE_EXAMPLE = {
    "answers": {
        "question_id_1": "Très satisfait",
        "question_id_2": ["Réseaux sociaux"],
        "question_id_3": "J'apprécie particulièrement la rapidité du service",
        "question_id_4": "9"
    },
    "user_id": "user_12345"
}

# Exemple de réponse API - Formulaire
FORM_RESPONSE_EXAMPLE = {
    "success": True,
    "form": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Sondage de satisfaction client",
        "description": "Aidez-nous à améliorer notre service",
        "settings": {
            "theme": "blue",
            "public": True
        },
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
        "questions": [
            {
                "id": "q1",
                "form_id": "550e8400-e29b-41d4-a716-446655440000",
                "type": "multiple",
                "text": "Comment avez-vous découvert notre service ?",
                "options": ["Réseaux sociaux", "Recommandation", "Publicité"],
                "required": True,
                "validation": {},
                "order_index": 0,
                "created_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
}

# Exemple de réponse API - Statistiques
STATS_RESPONSE_EXAMPLE = {
    "success": True,
    "stats": {
        "total_questions": 5,
        "total_responses": 42,
        "form_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    "analytics": {
        "total_responses": 42,
        "daily_stats": [
            {"date": "2024-01-15", "count": 12},
            {"date": "2024-01-16", "count": 18},
            {"date": "2024-01-17", "count": 12}
        ],
        "hourly_stats": [
            {"hour": 9, "count": 3},
            {"hour": 10, "count": 8},
            {"hour": 14, "count": 5}
        ]
    }
}

# Exemple d'erreur
ERROR_RESPONSE_EXAMPLE = {
    "error": "Validation failed",
    "details": {
        "title": "Title is required",
        "type": "Invalid question type"
    }
}

# Exemple de succès
SUCCESS_RESPONSE_EXAMPLE = {
    "success": True,
    "message": "Formulaire créé avec succès",
    "data": {
        "form_id": "550e8400-e29b-41d4-a716-446655440000"
    }
}
