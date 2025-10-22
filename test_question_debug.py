#!/usr/bin/env python3
"""
Test de débogage pour la création de question
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_question_creation_debug():
    """Test de débogage pour la création de question"""
    print("Test de débogage - Création de question")
    print("=" * 50)

    # 1. Inscription
    email = f"debug_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"1. Inscription avec email: {email}")

    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Debug Test User",
    }

    try:
        response = requests.post(
            f"{api_url}/api/auth/register", json=register_data, timeout=15
        )
        print(f"   Status: {response.status_code}")

        if response.status_code == 201:
            token = response.json()["token"]
            print(f"   Token: {token[:20]}...")

            # 2. Créer un formulaire
            print("\n2. Création de formulaire")
            headers = {"Authorization": f"Bearer {token}"}
            form_data = {
                "title": "Debug Test Form",
                "description": "Formulaire de test de débogage",
            }

            form_response = requests.post(
                f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
            )
            print(f"   Status: {form_response.status_code}")

            if form_response.status_code == 201:
                form_id = form_response.json()["data"]["form_id"]
                print(f"   Form ID: {form_id}")

                # 3. Créer une question simple
                print("\n3. Création de question simple")
                question_data = {
                    "type": "text",
                    "text": "Question de test simple",
                    "required": True,
                }

                question_response = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response.status_code}")
                print(f"   Response: {question_response.text}")

                if question_response.status_code == 201:
                    print("   [OK] Question créée avec succès!")
                else:
                    print("   [ERROR] Erreur création question")
                    print(f"   Détails: {question_response.text}")
            else:
                print(f"   [ERROR] Erreur création formulaire: {form_response.text}")
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_question_creation_debug()
