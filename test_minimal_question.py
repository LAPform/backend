#!/usr/bin/env python3
"""
Test minimal pour isoler le problème de création de question
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_minimal_question():
    """Test minimal de création de question"""
    print("Test minimal - Création de question")
    print("=" * 40)

    # 1. Inscription
    email = f"minimal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"1. Inscription: {email}")

    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Minimal Test User",
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
                "title": "Minimal Test Form",
                "description": "Formulaire de test minimal",
            }

            form_response = requests.post(
                f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
            )
            print(f"   Status: {form_response.status_code}")

            if form_response.status_code == 201:
                form_id = form_response.json()["data"]["form_id"]
                print(f"   Form ID: {form_id}")

                # 3. Test avec données ultra-minimales
                print("\n3. Création de question ultra-minimale")
                question_data = {"type": "text", "text": "Test"}

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

                    # 4. Test avec un autre type
                    print("\n4. Test avec type 'textarea'")
                    question_data_textarea = {
                        "type": "textarea",
                        "text": "Test textarea",
                    }

                    question_response_textarea = requests.post(
                        f"{api_url}/api/forms/{form_id}/questions",
                        json=question_data_textarea,
                        headers=headers,
                        timeout=15,
                    )
                    print(f"   Status: {question_response_textarea.status_code}")
                    print(f"   Response: {question_response_textarea.text}")

                    # 5. Test avec type 'email'
                    print("\n5. Test avec type 'email'")
                    question_data_email = {"type": "email", "text": "Test email"}

                    question_response_email = requests.post(
                        f"{api_url}/api/forms/{form_id}/questions",
                        json=question_data_email,
                        headers=headers,
                        timeout=15,
                    )
                    print(f"   Status: {question_response_email.status_code}")
                    print(f"   Response: {question_response_email.text}")

            else:
                print(f"   [ERROR] Erreur création formulaire: {form_response.text}")
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_minimal_question()
