import requests
import json

print("=== TEST COMPLET DE TOUS LES ENDPOINTS ===\n")

try:
    session = requests.Session()

    # Auth
    signup_data = {
        "email": "complete@example.com",
        "password": "Test123!",
        "first_name": "Complete",
        "last_name": "Test",
    }

    # Signup
    r = session.post(
        "https://backend-skum.onrender.com/api/auth/signup",
        json=signup_data,
        timeout=10,
    )
    print(f"1. Signup: {r.status_code}")

    # Signin
    r = session.post(
        "https://backend-skum.onrender.com/api/auth/signin",
        json=signup_data,
        timeout=10,
    )
    print(f"2. Signin: {r.status_code}")

    if r.status_code == 200:
        token = r.json().get("token")
        headers = {"Authorization": f"Bearer {token}"}

        # Créer un formulaire
        form_data = {"title": "Complete Test Form", "description": "Test Description"}
        r = session.post(
            "https://backend-skum.onrender.com/api/forms",
            json=form_data,
            headers=headers,
            timeout=10,
        )
        print(f"3. Form Creation: {r.status_code}")

        if r.status_code == 201:
            form_id = r.json().get("data", {}).get("form_id")
            print(f"   Form ID: {form_id}")

            # Test récupération du formulaire
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}",
                headers=headers,
                timeout=10,
            )
            print(f"4. Get Form: {r.status_code}")

            # Test liste des formulaires
            r = session.get(
                "https://backend-skum.onrender.com/api/forms",
                headers=headers,
                timeout=10,
            )
            print(f"5. List Forms: {r.status_code}")

            # Test statistiques
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/stats",
                headers=headers,
                timeout=10,
            )
            print(f"6. Form Stats: {r.status_code}")

            # Test création de question (le problème)
            question_data = {
                "type": "text",
                "text": "Test question",
                "required": False,
                "order_index": 0,
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data,
                headers=headers,
                timeout=10,
            )
            print(f"7. Question Creation: {r.status_code}")
            if r.status_code != 201:
                print(f"   Error: {r.text[:100]}...")

            # Test récupération des questions
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                headers=headers,
                timeout=10,
            )
            print(f"8. Get Questions: {r.status_code}")

            # Test soumission de réponse
            response_data = {
                "answers": [
                    {"question_id": "test-question-id", "value": "Test response"}
                ]
            }

            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/responses",
                json=response_data,
                headers=headers,
                timeout=10,
            )
            print(f"9. Submit Response: {r.status_code}")
            if r.status_code != 201:
                print(f"   Error: {r.text[:100]}...")

            # Test récupération des réponses
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/responses",
                headers=headers,
                timeout=10,
            )
            print(f"10. Get Responses: {r.status_code}")

            # Test export CSV
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/export/csv",
                headers=headers,
                timeout=10,
            )
            print(f"11. CSV Export: {r.status_code}")
            if r.status_code != 200:
                print(f"   Error: {r.text[:100]}...")

            # Test export Excel
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/export/excel",
                headers=headers,
                timeout=10,
            )
            print(f"12. Excel Export: {r.status_code}")
            if r.status_code != 200:
                print(f"   Error: {r.text[:100]}...")

            # Test export JSON
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/export/json",
                headers=headers,
                timeout=10,
            )
            print(f"13. JSON Export: {r.status_code}")
            if r.status_code != 200:
                print(f"   Error: {r.text[:100]}...")

            # Test analytics
            r = session.get(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/analytics",
                headers=headers,
                timeout=10,
            )
            print(f"14. Analytics: {r.status_code}")
            if r.status_code != 200:
                print(f"   Error: {r.text[:100]}...")

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
