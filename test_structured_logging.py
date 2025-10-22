"""
Script de test pour le logging structuré
"""

import requests
import json
import time
from datetime import datetime


def test_structured_logging():
    """Tester le logging structuré de l'API"""
    api_url = "https://backend-skum.onrender.com"

    print("Test du Logging Structuré FormForge")
    print("=" * 50)

    # Test 1: Inscription avec logging
    print("\n1. Test inscription avec logging:")

    email = f"test_logging_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    response = requests.post(
        f"{api_url}/api/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
            "name": "Test Logging User",
        },
    )

    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print("   [OK] Inscription reussie - Logs generes")
        token = response.json()["token"]
        user_id = response.json()["user"]["id"]

        # Test 2: Création de formulaire avec logging
        print("\n2. Test création formulaire avec logging:")

        headers = {"Authorization": f"Bearer {token}"}
        form_response = requests.post(
            f"{api_url}/api/forms",
            json={
                "title": "Test Logging Form",
                "description": "Formulaire de test pour le logging",
            },
            headers=headers,
        )

        print(f"   Status: {form_response.status_code}")
        if form_response.status_code == 201:
            print("   [OK] Formulaire cree - Logs generes")
            form_id = form_response.json()["data"]["form_id"]

            # Test 3: Création de question avec logging
            print("\n3. Test création question avec logging:")

            question_response = requests.post(
                f"{api_url}/api/forms/{form_id}/questions",
                json={
                    "type": "text",
                    "text": "Question de test pour le logging",
                    "required": True,
                },
                headers=headers,
            )

            print(f"   Status: {question_response.status_code}")
            if question_response.status_code == 201:
                print("   [OK] Question creee - Logs generes")

                # Test 4: Soumission de réponse avec logging
                print("\n4. Test soumission réponse avec logging:")

                response_data = requests.post(
                    f"{api_url}/api/forms/{form_id}/responses",
                    json={
                        "answers": {"1": "Réponse de test pour le logging"},
                        "user_id": "test_user_logging",
                    },
                )

                print(f"   Status: {response_data.status_code}")
                if response_data.status_code == 201:
                    print("   [OK] Reponse soumise - Logs generes")
                else:
                    print(f"   [ERROR] Erreur soumission: {response_data.text}")
            else:
                print(f"   [ERROR] Erreur creation question: {question_response.text}")
        else:
            print(f"   [ERROR] Erreur creation formulaire: {form_response.text}")
    else:
        print(f"   [ERROR] Erreur inscription: {response.text}")

    # Test 5: Test de rate limiting avec logging
    print("\n5. Test rate limiting avec logging:")

    for i in range(3):
        try:
            response = requests.post(
                f"{api_url}/api/auth/register",
                json={
                    "email": f"rate_test_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                    "password": "TestPassword123!",
                    "name": "Rate Test User",
                },
            )
            print(f"   Requête {i+1}: Status {response.status_code}")
        except Exception as e:
            print(f"   Requête {i+1}: Erreur {e}")

    # Test 6: Test d'erreurs avec logging
    print("\n6. Test erreurs avec logging:")

    # Email invalide
    response = requests.post(
        f"{api_url}/api/auth/register",
        json={
            "email": "email-invalide",
            "password": "TestPassword123!",
            "name": "Test User",
        },
    )
    print(f"   Email invalide: Status {response.status_code}")

    # Mot de passe faible
    response = requests.post(
        f"{api_url}/api/auth/register",
        json={"email": "test@example.com", "password": "123", "name": "Test User"},
    )
    print(f"   Mot de passe faible: Status {response.status_code}")

    print("\n" + "=" * 50)
    print("Tests de logging structuré terminés")
    print("\n[INFO] Verifiez les logs Render pour voir les logs structures JSON")


def test_logging_performance():
    """Tester les métriques de performance"""
    api_url = "https://backend-skum.onrender.com"

    print("\nTest des Métriques de Performance")
    print("=" * 40)

    # Test de performance des requêtes
    endpoints = ["/api/health", "/api/auth/register", "/api/forms"]

    for endpoint in endpoints:
        start_time = time.time()

        if endpoint == "/api/health":
            response = requests.get(f"{api_url}{endpoint}")
        elif endpoint == "/api/auth/register":
            response = requests.post(
                f"{api_url}{endpoint}",
                json={
                    "email": f"perf_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                    "password": "TestPassword123!",
                    "name": "Performance Test",
                },
            )
        else:
            response = requests.get(f"{api_url}{endpoint}")

        duration = (time.time() - start_time) * 1000

        print(f"   {endpoint}: {response.status_code} - {duration:.2f}ms")

    print("\n[INFO] Metriques de performance enregistrees dans les logs")


if __name__ == "__main__":
    print("Test du Logging Structuré FormForge")
    print("=" * 60)

    try:
        test_structured_logging()
        test_logging_performance()

        print("\n[OK] Tests de logging structure termines")
        print("\n[INFO] Consultez les logs Render pour voir les logs JSON structures")

    except Exception as e:
        print(f"\n[ERROR] Erreur lors des tests: {e}")
