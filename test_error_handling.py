"""
Script de test pour la gestion d'erreurs améliorée
"""

import requests
import json
from datetime import datetime


def test_error_handling():
    """Tester la gestion d'erreurs améliorée"""
    api_url = "https://backend-skum.onrender.com"
    
    print("Test de la Gestion d'Erreurs Amelioree")
    print("=" * 50)
    
    # Test 1: Erreurs de validation
    print("\n1. Test erreurs de validation:")
    
    # Email invalide
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "email-invalide",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    print(f"   Email invalide: Status {response.status_code}")
    if response.status_code == 400:
        error_data = response.json()
        print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
        print(f"   Message: {error_data.get('message', 'N/A')}")
        print(f"   Details: {error_data.get('details', 'N/A')}")
    
    # Mot de passe faible
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "test@example.com",
        "password": "123",
        "name": "Test User"
    })
    print(f"   Mot de passe faible: Status {response.status_code}")
    if response.status_code == 400:
        error_data = response.json()
        print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
        print(f"   Message: {error_data.get('message', 'N/A')}")
    
    # Test 2: Erreurs d'authentification
    print("\n2. Test erreurs d'authentification:")
    
    # Connexion avec mauvais identifiants
    response = requests.post(f"{api_url}/api/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "wrongpassword"
    })
    print(f"   Mauvais identifiants: Status {response.status_code}")
    if response.status_code == 401:
        error_data = response.json()
        print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
        print(f"   Message: {error_data.get('message', 'N/A')}")
    
    # Test 3: Erreurs de ressources
    print("\n3. Test erreurs de ressources:")
    
    # Formulaire inexistant
    response = requests.get(f"{api_url}/api/forms/nonexistent-form-id")
    print(f"   Formulaire inexistant: Status {response.status_code}")
    if response.status_code == 404:
        error_data = response.json()
        print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
        print(f"   Message: {error_data.get('message', 'N/A')}")
    
    # Test 4: Erreurs de validation de formulaire
    print("\n4. Test erreurs de validation de formulaire:")
    
    # Créer un utilisateur pour obtenir un token
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    
    if response.status_code == 201:
        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Créer un formulaire
        form_response = requests.post(f"{api_url}/api/forms", json={
            "title": "Test Form",
            "description": "Test description"
        }, headers=headers)
        
        if form_response.status_code == 201:
            form_id = form_response.json()["data"]["form_id"]
            
            # Créer une question avec type invalide
            response = requests.post(f"{api_url}/api/forms/{form_id}/questions", json={
                "type": "invalid_type",
                "text": "Test question"
            }, headers=headers)
            
            print(f"   Type de question invalide: Status {response.status_code}")
            if response.status_code == 400:
                error_data = response.json()
                print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
                print(f"   Message: {error_data.get('message', 'N/A')}")
                print(f"   Details: {error_data.get('details', 'N/A')}")
    
    # Test 5: Erreurs de rate limiting
    print("\n5. Test erreurs de rate limiting:")
    
    # Dépasser la limite d'inscription
    for i in range(7):
        response = requests.post(f"{api_url}/api/auth/register", json={
            "email": f"test_rate_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "password": "TestPassword123!",
            "name": "Test User"
        })
        
        if response.status_code == 429:
            print(f"   Rate limit atteint: Status {response.status_code}")
            error_data = response.json()
            print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
            print(f"   Message: {error_data.get('message', 'N/A')}")
            print(f"   Details: {error_data.get('details', 'N/A')}")
            break
        elif response.status_code == 201:
            print(f"   Requete {i+1}: OK")
    
    print("\n" + "=" * 50)
    print("Tests de gestion d'erreurs termines")


def test_error_response_structure():
    """Tester la structure des réponses d'erreur"""
    api_url = "https://backend-skum.onrender.com"
    
    print("\nTest de la Structure des Reponses d'Erreur")
    print("=" * 50)
    
    # Test avec une requête invalide
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "invalid-email",
        "password": "123"
    })
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 400:
        try:
            error_data = response.json()
            print(f"Response Body: {json.dumps(error_data, indent=2)}")
            
            # Vérifier la structure
            required_fields = ['error', 'error_code', 'code', 'message', 'timestamp']
            missing_fields = [field for field in required_fields if field not in error_data]
            
            if missing_fields:
                print(f"Champs manquants: {missing_fields}")
            else:
                print("Structure de réponse d'erreur valide")
                
        except json.JSONDecodeError:
            print("Erreur: Réponse non-JSON")
    else:
        print(f"Status inattendu: {response.status_code}")


if __name__ == "__main__":
    print("Test de la Gestion d'Erreurs FormForge")
    print("=" * 60)
    
    try:
        test_error_handling()
        test_error_response_structure()
        
        print("\nTests de gestion d'erreurs termines")
        
    except Exception as e:
        print(f"\nErreur lors des tests: {e}")
