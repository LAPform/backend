#!/usr/bin/env python3
"""
Test de vérification du formulaire avant création de question
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_form_verification():
    """Test de vérification du formulaire"""
    print("Test de vérification du formulaire")
    print("=" * 40)

    # 1. Inscription
    email = f"form_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"1. Inscription: {email}")

    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Form Verification User",
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
                "title": "Form Verification Test",
                "description": "Formulaire de test de vérification",
            }

            form_response = requests.post(
                f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
            )
            print(f"   Status: {form_response.status_code}")

            if form_response.status_code == 201:
                form_id = form_response.json()["data"]["form_id"]
                print(f"   Form ID: {form_id}")

                # 3. Vérifier que le formulaire existe
                print("\n3. Vérification du formulaire")
                form_check_response = requests.get(
                    f"{api_url}/api/forms/{form_id}", headers=headers, timeout=15
                )
                print(f"   Status: {form_check_response.status_code}")
                print(f"   Response: {form_check_response.text}")

                if form_check_response.status_code == 200:
                    print("   [OK] Formulaire existe")

                    # 4. Créer une question
                    print("\n4. Création de question")
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
                        print("   [OK] Question créée avec succès!")
                    else:
                        print("   [ERROR] Erreur création question")
                else:
                    print("   [ERROR] Formulaire non trouvé")

            else:
                print(f"   [ERROR] Erreur création formulaire: {form_response.text}")
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_form_verification()
