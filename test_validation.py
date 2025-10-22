"""
Script de test pour les validations de données
"""

import requests
import json
from datetime import datetime


def test_validation_auth():
    """Tester les validations d'authentification"""
    api_url = "https://backend-skum.onrender.com"
    
    print("🧪 Test des Validations d'Authentification")
    print("=" * 50)
    
    # Test 1: Email invalide
    print("\n1. Test email invalide:")
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "email-invalide",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Mot de passe faible
    print("\n2. Test mot de passe faible:")
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "test@example.com",
        "password": "123",
        "name": "Test User"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Nom trop long
    print("\n3. Test nom trop long:")
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPassword123!",
        "name": "A" * 200  # Nom trop long
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 4: Données valides
    print("\n4. Test données valides:")
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_validation_forms():
    """Tester les validations de formulaires"""
    api_url = "https://backend-skum.onrender.com"
    
    print("\n🧪 Test des Validations de Formulaires")
    print("=" * 50)
    
    # Obtenir un token d'abord
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    
    if response.status_code != 201:
        print("❌ Impossible d'obtenir un token")
        return
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Titre trop long
    print("\n1. Test titre trop long:")
    response = requests.post(f"{api_url}/api/forms", json={
        "title": "A" * 300,  # Titre trop long
        "description": "Test description"
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Description trop longue
    print("\n2. Test description trop longue:")
    response = requests.post(f"{api_url}/api/forms", json={
        "title": "Test Form",
        "description": "A" * 2000  # Description trop longue
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Données valides
    print("\n3. Test données valides:")
    response = requests.post(f"{api_url}/api/forms", json={
        "title": "Test Form",
        "description": "Test description",
        "settings": {"theme": "blue", "public": True}
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_validation_questions():
    """Tester les validations de questions"""
    api_url = "https://backend-skum.onrender.com"
    
    print("\n🧪 Test des Validations de Questions")
    print("=" * 50)
    
    # Obtenir un token et créer un formulaire
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    
    if response.status_code != 201:
        print("❌ Impossible d'obtenir un token")
        return
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Créer un formulaire
    response = requests.post(f"{api_url}/api/forms", json={
        "title": "Test Form",
        "description": "Test description"
    }, headers=headers)
    
    if response.status_code != 201:
        print("❌ Impossible de créer un formulaire")
        return
    
    form_id = response.json()["data"]["form_id"]
    
    # Test 1: Type de question invalide
    print("\n1. Test type de question invalide:")
    response = requests.post(f"{api_url}/api/forms/{form_id}/questions", json={
        "type": "invalid_type",
        "text": "Test question",
        "required": True
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Texte trop long
    print("\n2. Test texte trop long:")
    response = requests.post(f"{api_url}/api/forms/{form_id}/questions", json={
        "type": "text",
        "text": "A" * 600,  # Texte trop long
        "required": True
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 3: Données valides
    print("\n3. Test données valides:")
    response = requests.post(f"{api_url}/api/forms/{form_id}/questions", json={
        "type": "text",
        "text": "Quel est votre nom ?",
        "required": True,
        "order_index": 0
    }, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == "__main__":
    print("🔒 Tests de Validation des Données")
    print("=" * 60)
    
    try:
        test_validation_auth()
        test_validation_forms()
        test_validation_questions()
        
        print("\n✅ Tests de validation terminés")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
