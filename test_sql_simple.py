import requests
import json

print("=== TEST REQUÊTE SQL SIMPLE ===\n")

try:
    session = requests.Session()

    # Auth
    signup_data = {
        "email": "sql_test@example.com",
        "password": "Test123!",
        "first_name": "SQL",
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
        headers = {"Authorization": f"Bearer {token}"}

        # Créer un formulaire
        form_data = {"title": "SQL Test Form"}
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

            # Test 1: Requête SQL simple - INSERT direct
            print("\n--- Test 1: INSERT SQL simple ---")
            question_data = {
                "type": "text",
                "text": "Simple SQL test",
                "order_index": 0,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data,
                headers=headers,
                timeout=10,
            )
            print(f"Simple INSERT: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 2: Requête SQL avec tous les champs
            print("\n--- Test 2: INSERT SQL complet ---")
            question_data2 = {
                "type": "text",
                "text": "Complete SQL test",
                "options": [],
                "required": False,
                "validation": {},
                "order_index": 1,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data2,
                headers=headers,
                timeout=10,
            )
            print(f"Complete INSERT: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 3: Requête SQL avec JSON
            print("\n--- Test 3: INSERT SQL avec JSON ---")
            question_data3 = {
                "type": "choice",
                "text": "JSON SQL test",
                "options": ["Option 1", "Option 2"],
                "validation": {"min": 1},
                "required": True,
                "order_index": 2,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data3,
                headers=headers,
                timeout=10,
            )
            print(f"JSON INSERT: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 4: Requête SELECT simple
            print("\n--- Test 4: SELECT SQL simple ---")
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                headers=headers,
                timeout=10,
            )
            print(f"Simple SELECT: {r.status_code}")
            if r.status_code != 200:
                print(f"Error: {r.text}")

            # Test 5: Test avec des données qui pourraient causer des problèmes
            print("\n--- Test 5: Données problématiques ---")
            question_data5 = {
                "type": "text",
                "text": "Test with special chars: éàçù€£¥",
                "order_index": 3,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data5,
                headers=headers,
                timeout=10,
            )
            print(f"Special Chars INSERT: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 6: Test avec des données NULL/None
            print("\n--- Test 6: Données NULL/None ---")
            question_data6 = {
                "type": "text",
                "text": "NULL test",
                "options": None,
                "validation": None,
                "required": None,
                "order_index": 4,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data6,
                headers=headers,
                timeout=10,
            )
            print(f"NULL INSERT: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

        else:
            print(f"Form creation failed: {r.text}")
    else:
        print(f"Signin failed: {r.text}")

except Exception as e:
    print(f"Error: {e}")
    import traceback

    print(traceback.format_exc())

print("\n=== RÉSUMÉ ===")
print("✅ = Fonctionne (200/201)")
print("❌ = Erreur 500")
print("🔍 = Autre erreur")
