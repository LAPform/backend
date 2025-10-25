import requests
import json

print("=== TEST MODÈLE QUESTION ===\n")

try:
    session = requests.Session()

    # Auth
    signup_data = {
        "email": "model_test@example.com",
        "password": "Test123!",
        "first_name": "Model",
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
        form_data = {"title": "Model Test Form"}
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

            # Test 1: Question avec données minimales
            print("\n--- Test 1: Données minimales ---")
            question_data1 = {"type": "text", "text": "Test"}

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data1,
                headers=headers,
                timeout=10,
            )
            print(f"Minimal Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 2: Question avec tous les champs
            print("\n--- Test 2: Tous les champs ---")
            question_data2 = {
                "type": "text",
                "text": "Complete test question",
                "options": [],
                "required": False,
                "validation": {},
                "order_index": 0,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data2,
                headers=headers,
                timeout=10,
            )
            print(f"Complete Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 3: Question avec options
            print("\n--- Test 3: Question avec options ---")
            question_data3 = {
                "type": "choice",
                "text": "Choose an option",
                "options": ["Option 1", "Option 2"],
                "required": True,
                "order_index": 1,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data3,
                headers=headers,
                timeout=10,
            )
            print(f"Choice Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 4: Question avec validation
            print("\n--- Test 4: Question avec validation ---")
            question_data4 = {
                "type": "number",
                "text": "Enter a number",
                "validation": {"min": 1, "max": 100},
                "required": True,
                "order_index": 2,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data4,
                headers=headers,
                timeout=10,
            )
            print(f"Number Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 5: Question avec caractères spéciaux
            print("\n--- Test 5: Caractères spéciaux ---")
            question_data5 = {
                "type": "text",
                "text": "Question avec caractères spéciaux: éàçù€£¥",
                "order_index": 3,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data5,
                headers=headers,
                timeout=10,
            )
            print(f"Special Chars Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 6: Question avec JSON complexe
            print("\n--- Test 6: JSON complexe ---")
            question_data6 = {
                "type": "multiple_choices",
                "text": "Select multiple options",
                "options": ["Option A", "Option B", "Option C"],
                "validation": {
                    "min_selections": 1,
                    "max_selections": 3,
                    "required_options": ["Option A"],
                },
                "required": True,
                "order_index": 4,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data6,
                headers=headers,
                timeout=10,
            )
            print(f"Complex JSON Question: {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")

            # Test 7: Récupération des questions
            print("\n--- Test 7: Récupération des questions ---")
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                headers=headers,
                timeout=10,
            )
            print(f"Get Questions: {r.status_code}")
            if r.status_code != 200:
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
