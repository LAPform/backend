import requests
import json

print("=== TEST CONNEXION BASE DE DONNÉES ===\n")

try:
    session = requests.Session()
    
    # Auth
    signup_data = {
        "email": "db_connection@example.com",
        "password": "Test123!",
        "first_name": "DB",
        "last_name": "Connection",
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
        
        # Test 1: Vérifier si la base de données est initialisée
        print("\n--- Test 1: Vérification base de données ---")
        
        # Créer un formulaire (test de la table forms)
        form_data = {"title": "DB Connection Test Form"}
        r = session.post(
            "https://backend-skum.onrender.com/api/forms",
            json=form_data,
            headers=headers,
            timeout=10,
        )
        print(f"Form Creation (table forms): {r.status_code}")
        if r.status_code != 201:
            print(f"Error: {r.text}")
            print("❌ Problème avec la table 'forms'")
        else:
            print("✅ Table 'forms' fonctionne")
            form_id = r.json().get("data", {}).get("form_id")
            print(f"Form ID: {form_id}")
            
            # Test 2: Vérifier la table questions
            print("\n--- Test 2: Vérification table questions ---")
            
            # Test avec des données minimales
            question_data = {
                "type": "text",
                "text": "Test question",
                "order_index": 0
            }
            
            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=question_data,
                headers=headers,
                timeout=10,
            )
            print(f"Question Creation (table questions): {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")
                print("❌ Problème avec la table 'questions'")
            else:
                print("✅ Table 'questions' fonctionne")
            
            # Test 3: Vérifier la table users
            print("\n--- Test 3: Vérification table users ---")
            
            # Test endpoint /me (utilise la table users)
            r = session.get(
                "https://backend-skum.onrender.com/api/auth/me",
                headers=headers,
                timeout=10,
            )
            print(f"User Info (table users): {r.status_code}")
            if r.status_code != 200:
                print(f"Error: {r.text}")
                print("❌ Problème avec la table 'users'")
            else:
                print("✅ Table 'users' fonctionne")
            
            # Test 4: Vérifier la table responses
            print("\n--- Test 4: Vérification table responses ---")
            
            # Test soumission de réponse
            response_data = {
                "answers": [
                    {
                        "question_id": "test-question-id",
                        "value": "Test response"
                    }
                ]
            }
            
            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/responses",
                json=response_data,
                headers=headers,
                timeout=10,
            )
            print(f"Response Submission (table responses): {r.status_code}")
            if r.status_code != 201:
                print(f"Error: {r.text}")
                print("❌ Problème avec la table 'responses'")
            else:
                print("✅ Table 'responses' fonctionne")
            
            # Test 5: Vérifier les index et contraintes
            print("\n--- Test 5: Vérification contraintes ---")
            
            # Test avec form_id invalide
            r = session.post(
                "https://backend-skum.onrender.com/api/forms/invalid-form-id/questions",
                json=question_data,
                headers=headers,
                timeout=10,
            )
            print(f"Invalid Form ID: {r.status_code}")
            if r.status_code == 404:
                print("✅ Contrainte foreign key fonctionne")
            else:
                print(f"Error: {r.text}")
                print("❌ Problème avec les contraintes")
            
            # Test 6: Vérifier les types de données
            print("\n--- Test 6: Vérification types de données ---")
            
            # Test avec type invalide
            invalid_question_data = {
                "type": "invalid_type",
                "text": "Test question",
                "order_index": 0
            }
            
            r = session.post(
                f"https://backend-skum.onrender.com/api/forms/{form_id}/questions",
                json=invalid_question_data,
                headers=headers,
                timeout=10,
            )
            print(f"Invalid Type: {r.status_code}")
            if r.status_code == 400:
                print("✅ Validation des types fonctionne")
            else:
                print(f"Error: {r.text}")
                print("❌ Problème avec la validation des types")
            
        else:
            print(f"Form creation failed: {r.text}")
            print("❌ Problème avec la table 'forms'")
    else:
        print(f"Signin failed: {r.text}")
        print("❌ Problème avec la table 'users'")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    print(traceback.format_exc())

print("\n=== RÉSUMÉ ===")
print("✅ = Table fonctionne")
print("❌ = Problème avec la table")
print("🔍 = Autre erreur")
