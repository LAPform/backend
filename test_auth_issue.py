import requests
import json

print("=== TEST PROBLÈME D'IDENTIFICATION ===\n")

try:
    session = requests.Session()

    # Test 1: Sans authentification
    print("--- Test 1: Sans authentification ---")
    r = requests.get(
        "https://backend-skum.onrender.com/api/forms",
        timeout=10,
    )
    print(f"Forms sans auth: {r.status_code}")
    print(f"Response: {r.text[:100]}...")

    # Test 2: Avec token invalide
    print("\n--- Test 2: Avec token invalide ---")
    headers_invalid = {"Authorization": "Bearer invalid_token"}
    r = requests.get(
        "https://backend-skum.onrender.com/api/forms",
        headers=headers_invalid,
        timeout=10,
    )
    print(f"Forms avec token invalide: {r.status_code}")
    print(f"Response: {r.text[:100]}...")

    # Test 3: Authentification normale
    print("\n--- Test 3: Authentification normale ---")
    signup_data = {
        "email": "auth_test@example.com",
        "password": "Test123!",
        "first_name": "Auth",
        "last_name": "Test",
    }

    # Signup
    r = session.post(
        "https://backend-skum.onrender.com/api/auth/signup",
        json=signup_data,
        timeout=10,
    )
    print(f"Signup: {r.status_code}")

    # Signin
    r = session.post(
        "https://backend-skum.onrender.com/api/auth/signin",
        json=signup_data,
        timeout=10,
    )
    print(f"Signin: {r.status_code}")

    if r.status_code == 200:
        token = r.json().get("token")
        print(f"Token reçu: {token[:20]}...")
        headers = {"Authorization": f"Bearer {token}"}

        # Test avec token valide
        r = session.get(
            "https://backend-skum.onrender.com/api/forms",
            headers=headers,
            timeout=10,
        )
        print(f"Forms avec token valide: {r.status_code}")

        # Test endpoint /me
        r = session.get(
            "https://backend-skum.onrender.com/api/auth/me",
            headers=headers,
            timeout=10,
        )
        print(f"Auth /me: {r.status_code}")
        print(f"Response: {r.text[:100]}...")

        # Créer un formulaire
        form_data = {"title": "Auth Test Form"}
        r = session.post(
            "https://backend-skum.onrender.com/api/forms",
            json=form_data,
            headers=headers,
            timeout=10,
        )
        print(f"Form Creation: {r.status_code}")

        if r.status_code == 201:
            form_id = r.json().get("data", {}).get("form_id")
            print(f"Form ID: {form_id}")

            # Test création de question avec token
            question_data = {"type": "text", "text": "Test question", "order_index": 0}

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data,
                headers=headers,
                timeout=10,
            )
            print(f"Question Creation: {r.status_code}")
            print(f"Response: {r.text[:200]}...")

            # Test sans token
            r = requests.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data,
                timeout=10,
            )
            print(f"Question Creation sans token: {r.status_code}")
            print(f"Response: {r.text[:200]}...")

        else:
            print(f"Form creation failed: {r.text}")
    else:
        print(f"Signin failed: {r.text}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    print(traceback.format_exc())
