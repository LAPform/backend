#!/usr/bin/env python3
"""
Test rapide des corrections critiques
"""

import requests
import json

API_URL = "https://backend-skum.onrender.com"

def test_auth_me_endpoint():
    """Tester /api/auth/me avec token custom"""
    print("\n" + "="*60)
    print("TEST 1: Token authentication pour /api/auth/me")
    print("="*60)

    # Créer un compte
    signup_resp = requests.post(
        f"{API_URL}/api/auth/signup",
        json={
            "email": f"test_fixes_{int(__import__('time').time())}@test.com",
            "password": "SecureP@ss123!",
            "name": "Test Fixes"
        },
        timeout=30
    )

    print(f"Signup: {signup_resp.status_code}")

    if signup_resp.status_code != 201:
        print(f"❌ Signup failed: {signup_resp.text}")
        return False

    data = signup_resp.json()
    token = data.get("authentication_token")
    user_id = data.get("user", {}).get("id")

    print(f"✓ Token received: {token[:20]}...")
    print(f"✓ User ID: {user_id}")

    # Tester /api/auth/me avec le token
    me_resp = requests.get(
        f"{API_URL}/api/auth/me",
        headers={"Authentication-Token": token},
        timeout=30
    )

    print(f"\n/api/auth/me: {me_resp.status_code}")

    if me_resp.status_code == 200:
        me_data = me_resp.json()
        if me_data.get("success") and me_data.get("user", {}).get("id") == user_id:
            print(f"✅ SUCCESS: /api/auth/me fonctionne avec token custom!")
            print(f"   User: {me_data.get('user', {}).get('email')}")
            return True
        else:
            print(f"❌ FAIL: Response incorrecte: {me_data}")
            return False
    else:
        print(f"❌ FAIL: Status {me_resp.status_code}")
        print(f"   Response: {me_resp.text}")
        return False


def test_response_validation():
    """Tester validation réponses améliorée"""
    print("\n" + "="*60)
    print("TEST 2: Validation réponses (questions optionnelles)")
    print("="*60)

    # Créer un compte
    signup_resp = requests.post(
        f"{API_URL}/api/auth/signup",
        json={
            "email": f"test_val_{int(__import__('time').time())}@test.com",
            "password": "SecureP@ss123!",
            "name": "Test Validation"
        },
        timeout=30
    )

    if signup_resp.status_code != 201:
        print(f"❌ Signup failed")
        return False

    token = signup_resp.json().get("authentication_token")
    print(f"✓ Token received")

    # Créer un formulaire
    form_resp = requests.post(
        f"{API_URL}/api/forms",
        json={
            "title": "Test Validation Form",
            "description": "Test"
        },
        headers={"Authentication-Token": token},
        timeout=30
    )

    if form_resp.status_code != 201:
        print(f"❌ Form creation failed: {form_resp.status_code}")
        return False

    form_id = form_resp.json().get("data", {}).get("form_id")
    print(f"✓ Form created: {form_id}")

    # Créer 2 questions: 1 requise, 1 optionnelle
    q1_resp = requests.post(
        f"{API_URL}/api/forms/{form_id}/questions",
        json={
            "type": "text",
            "text": "Nom (requis)",
            "required": True
        },
        headers={"Authentication-Token": token},
        timeout=30
    )

    if q1_resp.status_code != 201:
        print(f"❌ Question 1 creation failed")
        return False

    q1_id = q1_resp.json().get("question_id")
    print(f"✓ Question 1 created (required)")

    q2_resp = requests.post(
        f"{API_URL}/api/forms/{form_id}/questions",
        json={
            "type": "email",
            "text": "Email (optionnel)",
            "required": False
        },
        headers={"Authentication-Token": token},
        timeout=30
    )

    if q2_resp.status_code != 201:
        print(f"❌ Question 2 creation failed")
        return False

    q2_id = q2_resp.json().get("question_id")
    print(f"✓ Question 2 created (optional)")

    # Publier le formulaire
    pub_resp = requests.post(
        f"{API_URL}/api/forms/{form_id}/publish",
        headers={"Authentication-Token": token},
        timeout=30
    )

    if pub_resp.status_code != 200:
        print(f"❌ Publish failed")
        return False

    public_token = pub_resp.json().get("data", {}).get("public_token")
    print(f"✓ Form published: {public_token}")

    # Soumettre réponse avec SEULEMENT la question requise (pas l'optionnelle)
    submit_resp = requests.post(
        f"{API_URL}/api/public/forms/{public_token}/responses",
        json={
            "answers": {
                q1_id: "John Doe"
                # q2_id intentionnellement omis (optionnel)
            }
        },
        timeout=30
    )

    print(f"\nSubmit response: {submit_resp.status_code}")

    if submit_resp.status_code == 201:
        print(f"✅ SUCCESS: Validation accepte question optionnelle vide!")
        return True
    else:
        print(f"❌ FAIL: Status {submit_resp.status_code}")
        print(f"   Response: {submit_resp.json()}")
        return False


if __name__ == "__main__":
    print("\n🧪 TEST DES CORRECTIONS CRITIQUES")
    print("="*60)

    results = []

    try:
        results.append(("Token /api/auth/me", test_auth_me_endpoint()))
    except Exception as e:
        print(f"❌ Test 1 error: {e}")
        results.append(("Token /api/auth/me", False))

    try:
        results.append(("Validation réponses", test_response_validation()))
    except Exception as e:
        print(f"❌ Test 2 error: {e}")
        results.append(("Validation réponses", False))

    print("\n" + "="*60)
    print("RÉSULTATS")
    print("="*60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} ({passed*100//total}%)")

    if passed == total:
        print("\n🎉 TOUTES LES CORRECTIONS FONCTIONNENT!")
    else:
        print("\n⚠️ Certaines corrections nécessitent une révision")
