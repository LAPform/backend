#!/usr/bin/env python3
"""
Test de la gestion des erreurs pour isoler le problème
"""

import requests
import json
from datetime import datetime

api_url = "https://backend-skum.onrender.com"


def test_error_handling():
    """Test de la gestion des erreurs"""
    print("Test de la gestion des erreurs")
    print("=" * 40)

    # 1. Test avec des données invalides pour déclencher des erreurs
    print("1. Test avec des données invalides")

    # Test avec type invalide
    print("\n   Test type invalide:")
    try:
        response = requests.post(
            f"{api_url}/api/forms/invalid-form-id/questions",
            json={"type": "invalid_type", "text": "Test"},
            timeout=15,
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # Test avec formulaire inexistant
    print("\n   Test formulaire inexistant:")
    try:
        response = requests.post(
            f"{api_url}/api/forms/00000000-0000-0000-0000-000000000000/questions",
            json={"type": "text", "text": "Test"},
            headers={"Authorization": "Bearer invalid-token"},
            timeout=15,
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # Test avec données manquantes
    print("\n   Test données manquantes:")
    try:
        response = requests.post(
            f"{api_url}/api/forms/00000000-0000-0000-0000-000000000000/questions",
            json={"type": "text"},  # Manque 'text'
            headers={"Authorization": "Bearer invalid-token"},
            timeout=15,
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

    # 2. Test avec un token valide mais formulaire inexistant
    print("\n2. Test avec token valide mais formulaire inexistant")

    # Inscription pour obtenir un token valide
    email = f"error_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"   Inscription: {email}")

    try:
        register_response = requests.post(
            f"{api_url}/api/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "name": "Error Test User",
            },
            timeout=15,
        )

        if register_response.status_code == 201:
            token = register_response.json()["token"]
            print(f"   Token: {token[:20]}...")

            # Test avec formulaire inexistant
            print("\n   Test avec formulaire inexistant:")
            response = requests.post(
                f"{api_url}/api/forms/00000000-0000-0000-0000-000000000000/questions",
                json={"type": "text", "text": "Test"},
                headers={"Authorization": f"Bearer {token}"},
                timeout=15,
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text}")

        else:
            print(f"   [ERROR] Erreur inscription: {register_response.text}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")


if __name__ == "__main__":
    test_error_handling()
