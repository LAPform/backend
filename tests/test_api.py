"""
Tests API pour FormForge POC
"""

import pytest
import json
from app import create_app
from models.database import DatabaseManager


@pytest.fixture
def app():
    """Créer une instance de l'application pour les tests"""
    app = create_app()
    app.config["TESTING"] = True
    app.config["DATABASE_URL"] = "sqlite:///:memory:"

    with app.app_context():
        # Initialiser la base de données de test
        app.db = DatabaseManager()
        app.db.init_database()
        yield app


@pytest.fixture
def client(app):
    """Client de test"""
    return app.test_client()


def test_health_endpoint(client):
    """Tester l'endpoint de santé"""
    response = client.get("/api/health")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["status"] == "healthy"


def test_create_form(client):
    """Tester la création d'un formulaire"""
    form_data = {
        "title": "Test Form",
        "description": "Test Description",
        "settings": {"theme": "default"},
    }

    response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )

    assert response.status_code == 201

    data = json.loads(response.data)
    assert data["success"] == True
    assert "form_id" in data


def test_get_form(client):
    """Tester la récupération d'un formulaire"""
    # Créer un formulaire
    form_data = {"title": "Test Form", "description": "Test Description"}

    create_response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )

    form_id = json.loads(create_response.data)["form_id"]

    # Récupérer le formulaire
    response = client.get(f"/api/forms/{form_id}")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"] == True
    assert data["form"]["title"] == "Test Form"


def test_create_question(client):
    """Tester la création d'une question"""
    # Créer un formulaire
    form_data = {"title": "Test Form"}
    create_response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )
    form_id = json.loads(create_response.data)["form_id"]

    # Créer une question
    question_data = {"type": "text", "text": "What is your name?", "required": True}

    response = client.post(
        f"/api/forms/{form_id}/questions",
        data=json.dumps(question_data),
        content_type="application/json",
    )

    assert response.status_code == 201

    data = json.loads(response.data)
    assert data["success"] == True
    assert "question_id" in data


def test_submit_response(client):
    """Tester la soumission d'une réponse"""
    # Créer un formulaire avec une question
    form_data = {"title": "Test Form"}
    create_response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )
    form_id = json.loads(create_response.data)["form_id"]

    # Créer une question
    question_data = {"type": "text", "text": "What is your name?", "required": True}
    question_response = client.post(
        f"/api/forms/{form_id}/questions",
        data=json.dumps(question_data),
        content_type="application/json",
    )
    question_id = json.loads(question_response.data)["question_id"]

    # Soumettre une réponse
    response_data = {"answers": {question_id: "John Doe"}}

    response = client.post(
        f"/api/forms/{form_id}/responses",
        data=json.dumps(response_data),
        content_type="application/json",
    )

    assert response.status_code == 201

    data = json.loads(response.data)
    assert data["success"] == True
    assert "response_id" in data


def test_export_csv(client):
    """Tester l'export CSV"""
    # Créer un formulaire avec une question et une réponse
    form_data = {"title": "Test Form"}
    create_response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )
    form_id = json.loads(create_response.data)["form_id"]

    # Créer une question
    question_data = {"type": "text", "text": "What is your name?", "required": True}
    question_response = client.post(
        f"/api/forms/{form_id}/questions",
        data=json.dumps(question_data),
        content_type="application/json",
    )
    question_id = json.loads(question_response.data)["question_id"]

    # Soumettre une réponse
    response_data = {"answers": {question_id: "John Doe"}}
    client.post(
        f"/api/forms/{form_id}/responses",
        data=json.dumps(response_data),
        content_type="application/json",
    )

    # Exporter en CSV
    response = client.get(f"/api/forms/{form_id}/export/csv")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert data["success"] == True
    assert "csv_content" in data


def test_form_not_found(client):
    """Tester la gestion des erreurs 404"""
    response = client.get("/api/forms/non-existent-id")
    assert response.status_code == 404

    data = json.loads(response.data)
    assert "error" in data


def test_invalid_question_type(client):
    """Tester la validation des types de questions"""
    # Créer un formulaire
    form_data = {"title": "Test Form"}
    create_response = client.post(
        "/api/forms", data=json.dumps(form_data), content_type="application/json"
    )
    form_id = json.loads(create_response.data)["form_id"]

    # Créer une question avec un type invalide
    question_data = {"type": "invalid_type", "text": "Test question"}

    response = client.post(
        f"/api/forms/{form_id}/questions",
        data=json.dumps(question_data),
        content_type="application/json",
    )

    assert response.status_code == 400

    data = json.loads(response.data)
    assert "error" in data
