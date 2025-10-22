#!/usr/bin/env python3
"""
Test de débogage avancé pour la création de question
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_question_debug_advanced():
    """Test de débogage avancé"""
    print("Test de débogage avancé - Création de question")
    print("=" * 60)

    # 1. Inscription
    email = f"debug_advanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"1. Inscription: {email}")

    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Debug Advanced User",
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
                "title": "Debug Advanced Form",
                "description": "Formulaire de test de débogage avancé",
            }

            form_response = requests.post(
                f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
            )
            print(f"   Status: {form_response.status_code}")

            if form_response.status_code == 201:
                form_id = form_response.json()["data"]["form_id"]
                print(f"   Form ID: {form_id}")

                # 3. Test avec données ultra-minimales
                print("\n3. Test avec données ultra-minimales")
                question_data_minimal = {"type": "text", "text": "Test"}

                question_response_minimal = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data_minimal,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response_minimal.status_code}")
                print(f"   Response: {question_response_minimal.text}")

                # 4. Test avec données complètes
                print("\n4. Test avec données complètes")
                question_data_complete = {
                    "type": "text",
                    "text": "Question de test complète",
                    "required": False,
                    "order_index": 0,
                    "options": [],
                    "validation": {},
                }

                question_response_complete = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data_complete,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response_complete.status_code}")
                print(f"   Response: {question_response_complete.text}")

                # 5. Test avec différents types
                print("\n5. Test avec différents types")
                types_to_test = ["text", "textarea", "email", "number", "date"]

                for question_type in types_to_test:
                    print(f"\n   Test type: {question_type}")
                    question_data_type = {
                        "type": question_type,
                        "text": f"Question de type {question_type}",
                    }

                    question_response_type = requests.post(
                        f"{api_url}/api/forms/{form_id}/questions",
                        json=question_data_type,
                        headers=headers,
                        timeout=15,
                    )
                    print(f"   Status: {question_response_type.status_code}")
                    if question_response_type.status_code != 201:
                        print(f"   Response: {question_response_type.text}")
                        break  # Arrêter au premier échec
                    else:
                        print("   [OK] Question créée")

                # 6. Test de validation des données
                print("\n6. Test de validation des données")

                # Test avec type invalide
                print("   Test type invalide:")
                question_data_invalid_type = {
                    "type": "invalid_type",
                    "text": "Question avec type invalide",
                }

                question_response_invalid_type = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data_invalid_type,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response_invalid_type.status_code}")
                print(f"   Response: {question_response_invalid_type.text}")

                # Test avec texte vide
                print("\n   Test texte vide:")
                question_data_empty_text = {"type": "text", "text": ""}

                question_response_empty_text = requests.post(
                    f"{api_url}/api/forms/{form_id}/questions",
                    json=question_data_empty_text,
                    headers=headers,
                    timeout=15,
                )
                print(f"   Status: {question_response_empty_text.status_code}")
                print(f"   Response: {question_response_empty_text.text}")

            else:
                print(f"   [ERROR] Erreur création formulaire: {form_response.text}")
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_question_debug_advanced()
