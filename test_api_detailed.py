#!/usr/bin/env python3
"""
Script de test détaillé de l'API FormForge en production
Utilise des headers navigateur pour éviter le blocage WAF
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_URL = "https://backend-skum.onrender.com"
TEST_EMAIL = f"test-{int(time.time())}@example.com"
TEST_PASSWORD = "Test123!@#Secure"
TEST_NAME = "Test User Automated"

# Session avec headers navigateur
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
})

# Résultats
results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'tests': []
}

def log_test(name, status, details=""):
    """Logger un test"""
    results['total'] += 1
    if status == 'PASS':
        results['passed'] += 1
        print(f"✅ {name}: PASS")
    else:
        results['failed'] += 1
        print(f"❌ {name}: FAIL - {details}")

    results['tests'].append({
        'name': name,
        'status': status,
        'details': details,
        'timestamp': datetime.now().isoformat()
    })

def test_health():
    """Test health check"""
    try:
        response = session.get(f"{API_URL}/api/health", timeout=20)
        if response.status_code == 200:
            data = response.json()
            log_test("Health Check", "PASS", f"Version: {data.get('version', 'N/A')}")
            return True
        else:
            log_test("Health Check", "FAIL", f"Status: {response.status_code}, Response: {response.text[:100]}")
            return False
    except Exception as e:
        log_test("Health Check", "FAIL", str(e))
        return False

def test_signup():
    """Test inscription"""
    try:
        response = session.post(
            f"{API_URL}/api/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME
            },
            timeout=20
        )

        if response.status_code == 201:
            data = response.json()
            token = data.get('authentication_token')
            if token:
                log_test("User Signup", "PASS", f"Token length: {len(token)}")
                return token
            else:
                log_test("User Signup", "FAIL", "No token in response")
                return None
        else:
            log_test("User Signup", "FAIL", f"Status: {response.status_code}, Response: {response.text[:200]}")
            return None
    except Exception as e:
        log_test("User Signup", "FAIL", str(e))
        return None

def test_signin():
    """Test connexion"""
    try:
        response = session.post(
            f"{API_URL}/api/auth/signin",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            },
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get('authentication_token')
            if token:
                log_test("User Signin", "PASS", f"Token received")
                return token
            else:
                log_test("User Signin", "FAIL", "No token in response")
                return None
        else:
            log_test("User Signin", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("User Signin", "FAIL", str(e))
        return None

def test_create_form(token):
    """Test création formulaire"""
    try:
        response = session.post(
            f"{API_URL}/api/forms",
            json={
                "title": f"Test Form {int(time.time())}",
                "description": "Formulaire de test automatisé",
                "settings": {"theme": "default"}
            },
            headers={"Authentication-Token": token},
            timeout=20
        )

        if response.status_code == 201:
            data = response.json()
            form_id = data.get('data', {}).get('form_id')
            if form_id:
                log_test("Create Form", "PASS", f"Form ID: {form_id[:20]}...")
                return form_id
            else:
                log_test("Create Form", "FAIL", "No form_id in response")
                return None
        else:
            log_test("Create Form", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("Create Form", "FAIL", str(e))
        return None

def test_list_forms(token):
    """Test liste formulaires"""
    try:
        response = session.get(
            f"{API_URL}/api/forms",
            headers={"Authentication-Token": token},
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            forms_count = len(data.get('forms', []))
            log_test("List Forms", "PASS", f"Found {forms_count} form(s)")
            return True
        else:
            log_test("List Forms", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("List Forms", "FAIL", str(e))
        return False

def test_create_question(token, form_id):
    """Test création question"""
    try:
        response = session.post(
            f"{API_URL}/api/forms/{form_id}/questions",
            json={
                "type": "text",
                "text": "Quelle est votre couleur préférée ?",
                "required": True,
                "order_index": 0
            },
            headers={"Authentication-Token": token},
            timeout=20
        )

        if response.status_code == 201:
            data = response.json()
            question_id = data.get('data', {}).get('question_id')
            log_test("Create Question", "PASS", f"Question created")
            return question_id
        else:
            log_test("Create Question", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("Create Question", "FAIL", str(e))
        return None

def test_publish_form(token, form_id):
    """Test publication formulaire"""
    try:
        response = session.post(
            f"{API_URL}/api/forms/{form_id}/publish",
            headers={"Authentication-Token": token},
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            public_token = data.get('data', {}).get('public_token')
            if public_token:
                log_test("Publish Form", "PASS", f"Public token: {public_token[:20]}...")
                return public_token
            else:
                log_test("Publish Form", "FAIL", "No public_token in response")
                return None
        else:
            log_test("Publish Form", "FAIL", f"Status: {response.status_code}")
            return None
    except Exception as e:
        log_test("Publish Form", "FAIL", str(e))
        return None

def test_get_public_form(public_token):
    """Test accès formulaire public"""
    try:
        response = session.get(
            f"{API_URL}/api/public/forms/{public_token}",
            timeout=20
        )

        if response.status_code == 200:
            data = response.json()
            form_title = data.get('data', {}).get('form', {}).get('title', 'N/A')
            log_test("Get Public Form", "PASS", f"Form accessible: {form_title}")
            return True
        else:
            log_test("Get Public Form", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Get Public Form", "FAIL", str(e))
        return False

def test_submit_response(public_token, form_id):
    """Test soumission réponse publique"""
    try:
        response = session.post(
            f"{API_URL}/api/public/forms/{public_token}/responses",
            json={
                "answers": {
                    "question_1": "Bleu"
                }
            },
            timeout=20
        )

        if response.status_code == 201:
            log_test("Submit Response", "PASS", "Response submitted")
            return True
        else:
            log_test("Submit Response", "FAIL", f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Submit Response", "FAIL", str(e))
        return False

def test_unauthorized_access():
    """Test accès non autorisé"""
    try:
        response = session.get(f"{API_URL}/api/forms", timeout=20)

        if response.status_code in [401, 403]:
            log_test("Security - Unauthorized Access", "PASS", "Protected endpoint correctly blocks unauthorized access")
            return True
        else:
            log_test("Security - Unauthorized Access", "FAIL", f"Endpoint should return 401/403, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Security - Unauthorized Access", "FAIL", str(e))
        return False

def main():
    """Fonction principale de test"""
    print("\n" + "="*60)
    print("TEST COMPLET API FORMFORGE - PRODUCTION")
    print(f"URL: {API_URL}")
    print(f"Date: {datetime.now().isoformat()}")
    print("="*60 + "\n")

    # Test 1: Health Check
    print("\n📍 Test 1: Health Check")
    if not test_health():
        print("\n⚠️  API inaccessible - WAF/Firewall actif")
        print("Les tests nécessitent un accès direct à l'API")
        return

    # Test 2: Security
    print("\n📍 Test 2: Security - Unauthorized Access")
    test_unauthorized_access()

    # Test 3: Signup
    print("\n📍 Test 3: User Signup")
    token = test_signup()
    if not token:
        print("\n⚠️  Impossible de continuer sans token")
        return

    # Test 4: Signin
    print("\n📍 Test 4: User Signin")
    token_signin = test_signin()
    if token_signin:
        token = token_signin  # Utiliser le nouveau token

    # Test 5: Create Form
    print("\n📍 Test 5: Create Form")
    form_id = test_create_form(token)
    if not form_id:
        print("\n⚠️  Impossible de continuer sans form_id")
        return

    # Test 6: List Forms
    print("\n📍 Test 6: List Forms")
    test_list_forms(token)

    # Test 7: Create Question
    print("\n📍 Test 7: Create Question")
    question_id = test_create_question(token, form_id)

    # Test 8: Publish Form
    print("\n📍 Test 8: Publish Form")
    public_token = test_publish_form(token, form_id)
    if not public_token:
        print("\n⚠️  Impossible de tester l'accès public sans token")
    else:
        # Test 9: Get Public Form
        print("\n📍 Test 9: Get Public Form (no auth)")
        test_get_public_form(public_token)

        # Test 10: Submit Response
        print("\n📍 Test 10: Submit Response (public)")
        test_submit_response(public_token, form_id)

    # Résultats
    print("\n" + "="*60)
    print("RÉSULTATS DES TESTS")
    print("="*60)
    print(f"Total tests: {results['total']}")
    print(f"✅ Tests réussis: {results['passed']}")
    print(f"❌ Tests échoués: {results['failed']}")

    if results['total'] > 0:
        success_rate = (results['passed'] / results['total']) * 100
        print(f"Taux de réussite: {success_rate:.1f}%")

    # Sauvegarder les résultats
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n📄 Résultats sauvegardés dans test_results.json")

    if results['failed'] == 0:
        print("\n✅ TOUS LES TESTS SONT PASSÉS ! L'API FONCTIONNE PARFAITEMENT !")
    else:
        print("\n⚠️  CERTAINS TESTS ONT ÉCHOUÉ. VÉRIFIER LES DÉTAILS CI-DESSUS.")

if __name__ == "__main__":
    main()
