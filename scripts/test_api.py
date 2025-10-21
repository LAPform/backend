"""
Script de test de l'API FormForge
"""

import requests
import json
import sys

API_BASE = "http://localhost:5000/api"


def test_health():
    """Tester l'endpoint de santé"""
    print("🔍 Test de l'endpoint de santé...")

    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Santé: {data['status']}")
            return True
        else:
            print(f"❌ Erreur santé: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return False


def test_create_form():
    """Tester la création d'un formulaire"""
    print("🔍 Test de création de formulaire...")

    form_data = {
        "title": "Test Form API",
        "description": "Formulaire de test via API",
        "settings": {"theme": "default"},
    }

    try:
        response = requests.post(
            f"{API_BASE}/forms",
            json=form_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Formulaire créé: {data['form_id']}")
            return data["form_id"]
        else:
            print(f"❌ Erreur création: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_create_question(form_id):
    """Tester la création d'une question"""
    print("🔍 Test de création de question...")

    question_data = {"type": "text", "text": "Quel est votre nom ?", "required": True}

    try:
        response = requests.post(
            f"{API_BASE}/forms/{form_id}/questions",
            json=question_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Question créée: {data['question_id']}")
            return data["question_id"]
        else:
            print(
                f"❌ Erreur création question: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


def test_submit_response(form_id, question_id):
    """Tester la soumission d'une réponse"""
    print("🔍 Test de soumission de réponse...")

    response_data = {"answers": {question_id: "John Doe"}}

    try:
        response = requests.post(
            f"{API_BASE}/forms/{form_id}/responses",
            json=response_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Réponse soumise: {data['response_id']}")
            return True
        else:
            print(f"❌ Erreur soumission: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_export_csv(form_id):
    """Tester l'export CSV"""
    print("🔍 Test d'export CSV...")

    try:
        response = requests.get(f"{API_BASE}/forms/{form_id}/export/csv")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Export CSV réussi: {data['filename']}")
            return True
        else:
            print(f"❌ Erreur export: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécuter tous les tests"""
    print("🧪 Tests de l'API FormForge POC")
    print("=" * 50)

    # Test 1: Santé
    if not test_health():
        print("❌ L'API n'est pas accessible. Vérifiez que le serveur est démarré.")
        sys.exit(1)

    # Test 2: Création de formulaire
    form_id = test_create_form()
    if not form_id:
        print("❌ Impossible de créer un formulaire")
        sys.exit(1)

    # Test 3: Création de question
    question_id = test_create_question(form_id)
    if not question_id:
        print("❌ Impossible de créer une question")
        sys.exit(1)

    # Test 4: Soumission de réponse
    if not test_submit_response(form_id, question_id):
        print("❌ Impossible de soumettre une réponse")
        sys.exit(1)

    # Test 5: Export CSV
    if not test_export_csv(form_id):
        print("❌ Impossible d'exporter en CSV")
        sys.exit(1)

    print("=" * 50)
    print("🎉 Tous les tests sont passés avec succès!")
    print(f"📋 Formulaire de test créé: {form_id}")
    print(f"🔗 URL du formulaire: {API_BASE}/forms/{form_id}")


if __name__ == "__main__":
    main()
