#!/usr/bin/env python3
"""
Test de l'initialisation de la base de données de l'API
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_api_database():
    """Test de l'initialisation de la base de données"""
    print("Test de l'initialisation de la base de données")
    print("=" * 50)

    # 1. Vérifier l'état de l'API
    print("1. Vérification de l'état de l'API")
    try:
        health_response = requests.get(f"{api_url}/api/health", timeout=15)
        print(f"   Health Status: {health_response.status_code}")
        print(f"   Response: {health_response.text}")
    except Exception as e:
        print(f"   [ERROR] Health check failed: {e}")
        return

    # 2. Inscription (pour tester la base de données)
    print("\n2. Test d'inscription (base de données users)")
    email = f"db_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"   Email: {email}")

    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Database Test User",
    }

    try:
        response = requests.post(
            f"{api_url}/api/auth/register", json=register_data, timeout=15
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            print("   [OK] Inscription réussie - Table users fonctionne")
            token = response.json()["token"]
            print(f"   Token: {token[:20]}...")

            # 3. Créer un formulaire (table forms)
            print("\n3. Test de création de formulaire (table forms)")
            headers = {"Authorization": f"Bearer {token}"}
            form_data = {
                "title": "Database Test Form",
                "description": "Formulaire de test de base de données",
            }

            form_response = requests.post(
                f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
            )
            print(f"   Status: {form_response.status_code}")

            if form_response.status_code == 201:
                print("   [OK] Création formulaire réussie - Table forms fonctionne")
                form_id = form_response.json()["data"]["form_id"]
                print(f"   Form ID: {form_id}")

                # 4. Lister les questions (table questions)
                print("\n4. Test de liste des questions (table questions)")
                questions_response = requests.get(
                    f"{api_url}/api/forms/{form_id}/questions",
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {questions_response.status_code}")
                print(f"   Response: {questions_response.text}")

                if questions_response.status_code == 200:
                    print(
                        "   [OK] Liste questions réussie - Table questions accessible"
                    )
                else:
                    print("   [ERROR] Erreur liste questions")

                # 5. Créer une question (table questions)
                print("\n5. Test de création de question (table questions)")
                question_data = {"type": "text", "text": "Test question"}

                question_response = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response.status_code}")
                print(f"   Response: {question_response.text}")

                if question_response.status_code == 201:
                    print(
                        "   [OK] Création question réussie - Table questions fonctionne"
                    )
                else:
                    print("   [ERROR] Erreur création question")

            else:
                print(f"   [ERROR] Erreur création formulaire: {form_response.text}")
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_api_database()
