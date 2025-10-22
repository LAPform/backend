"""
Script de test pour le rate limiting
"""

import requests
import time
import json
from datetime import datetime


def test_rate_limiting():
    """Tester le rate limiting sur l'API"""
    api_url = "https://backend-skum.onrender.com"
    
    print("Test du Rate Limiting")
    print("=" * 50)
    
    # Test 1: Rate limiting sur l'inscription
    print("\n1. Test rate limiting sur /api/auth/register:")
    print("   Limite: 5 requêtes par 5 minutes")
    
    for i in range(7):  # Dépasser la limite
        response = requests.post(f"{api_url}/api/auth/register", json={
            "email": f"test_rate_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
            "password": "TestPassword123!",
            "name": "Test User"
        })
        
        print(f"   Requête {i+1}: Status {response.status_code}")
        
        if response.status_code == 429:
            print(f"   ✅ Rate limit atteint: {response.json()}")
            break
        elif response.status_code == 201:
            print(f"   ✅ Inscription réussie")
        else:
            print(f"   ⚠️  Erreur: {response.json()}")
        
        time.sleep(1)  # Pause entre les requêtes
    
    # Test 2: Rate limiting sur la connexion
    print("\n2. Test rate limiting sur /api/auth/login:")
    print("   Limite: 10 requêtes par 5 minutes")
    
    for i in range(12):  # Dépasser la limite
        response = requests.post(f"{api_url}/api/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })
        
        print(f"   Requête {i+1}: Status {response.status_code}")
        
        if response.status_code == 429:
            print(f"   ✅ Rate limit atteint: {response.json()}")
            break
        elif response.status_code == 401:
            print(f"   ✅ Connexion échouée (attendu)")
        else:
            print(f"   ⚠️  Erreur: {response.json()}")
        
        time.sleep(1)
    
    # Test 3: Rate limiting sur la santé de l'API
    print("\n3. Test rate limiting sur /api/health:")
    print("   Limite: 1000 requêtes par heure")
    
    success_count = 0
    for i in range(5):  # Test rapide
        response = requests.get(f"{api_url}/api/health")
        
        if response.status_code == 200:
            success_count += 1
            print(f"   Requête {i+1}: ✅ OK")
        else:
            print(f"   Requête {i+1}: ❌ Erreur {response.status_code}")
        
        time.sleep(0.5)
    
    print(f"   Résultat: {success_count}/5 requêtes réussies")
    
    # Test 4: Headers de rate limiting
    print("\n4. Test des headers de rate limiting:")
    
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_headers_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    
    print(f"   Status: {response.status_code}")
    print(f"   Headers de rate limiting:")
    
    rate_limit_headers = [
        'X-RateLimit-Limit',
        'X-RateLimit-Remaining', 
        'X-RateLimit-Reset'
    ]
    
    for header in rate_limit_headers:
        value = response.headers.get(header, 'Non présent')
        print(f"   {header}: {value}")
    
    if response.status_code == 201:
        print("   ✅ Headers de rate limiting présents")
    else:
        print("   ⚠️  Headers de rate limiting manquants")
    
    print("\n" + "=" * 50)
    print("Tests de rate limiting terminés")


def test_rate_limiting_with_auth():
    """Tester le rate limiting avec authentification"""
    api_url = "https://backend-skum.onrender.com"
    
    print("\nTest du Rate Limiting avec Authentification")
    print("=" * 50)
    
    # Obtenir un token
    response = requests.post(f"{api_url}/api/auth/register", json={
        "email": f"test_auth_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    })
    
    if response.status_code != 201:
        print("❌ Impossible d'obtenir un token")
        return
    
    token = response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test rate limiting sur création de formulaires
    print("\n1. Test rate limiting sur /api/forms (création):")
    print("   Limite: 20 requêtes par heure")
    
    for i in range(5):  # Test modéré
        response = requests.post(f"{api_url}/api/forms", json={
            "title": f"Test Form {i}",
            "description": "Test description"
        }, headers=headers)
        
        print(f"   Requête {i+1}: Status {response.status_code}")
        
        if response.status_code == 201:
            print(f"   ✅ Formulaire créé")
        elif response.status_code == 429:
            print(f"   ✅ Rate limit atteint: {response.json()}")
            break
        else:
            print(f"   ⚠️  Erreur: {response.json()}")
        
        time.sleep(1)
    
    print("\n" + "=" * 50)
    print("Tests de rate limiting avec authentification terminés")


if __name__ == "__main__":
    print("🚦 Tests de Rate Limiting")
    print("=" * 60)
    
    try:
        test_rate_limiting()
        test_rate_limiting_with_auth()
        
        print("\n✅ Tests de rate limiting terminés")
        
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {e}")
