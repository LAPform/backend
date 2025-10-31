"""
Script de test complet de l'API FormForge
Teste toutes les fonctionnalités principales
"""

import os
import json
import time
import urllib.request
import urllib.parse
import http.cookiejar


BASE_URL = os.environ.get("BASE_URL", "https://backend-skum.onrender.com")


def _url(path: str) -> str:
    return BASE_URL.rstrip("/") + path


class HttpClient:
    def __init__(self):
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.opener.addheaders = [
            ("Content-Type", "application/json"),
            ("Accept", "application/json"),
        ]
        self.token = None

    def post_json(
        self,
        path: str,
        data: dict,
        use_bearer: bool = False,
        use_query_token: bool = False,
    ):
        url = _url(path)
        if use_query_token and self.token:
            from urllib.parse import urlencode, urlparse, urlunparse

            parsed = urlparse(url)
            query_params = dict(urllib.parse.parse_qsl(parsed.query))
            query_params["token"] = self.token
            new_query = urlencode(query_params)
            url = urlunparse(parsed._replace(query=new_query))

        req = urllib.request.Request(url, method="POST")
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, body, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content)
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}

    def get_json(
        self, path: str, use_bearer: bool = False, use_query_token: bool = False
    ):
        url = _url(path)
        if use_query_token and self.token:
            from urllib.parse import urlencode, urlparse, urlunparse

            parsed = urlparse(url)
            query_params = dict(urllib.parse.parse_qsl(parsed.query))
            query_params["token"] = self.token
            new_query = urlencode(query_params)
            url = urlunparse(parsed._replace(query=new_query))

        req = urllib.request.Request(url, method="GET")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content)
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}

    def put_json(
        self,
        path: str,
        data: dict,
        use_bearer: bool = False,
        use_query_token: bool = False,
    ):
        url = _url(path)
        if use_query_token and self.token:
            from urllib.parse import urlencode, urlparse, urlunparse

            parsed = urlparse(url)
            query_params = dict(urllib.parse.parse_qsl(parsed.query))
            query_params["token"] = self.token
            new_query = urlencode(query_params)
            url = urlunparse(parsed._replace(query=new_query))

        req = urllib.request.Request(url, method="PUT")
        body = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, body, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content)
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}

    def delete_json(
        self, path: str, use_bearer: bool = False, use_query_token: bool = False
    ):
        url = _url(path)
        if use_query_token and self.token:
            from urllib.parse import urlencode, urlparse, urlunparse

            parsed = urlparse(url)
            query_params = dict(urllib.parse.parse_qsl(parsed.query))
            query_params["token"] = self.token
            new_query = urlencode(query_params)
            url = urlunparse(parsed._replace(query=new_query))

        req = urllib.request.Request(url, method="DELETE")
        if use_bearer and self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with self.opener.open(req, timeout=20) as resp:
                content = resp.read().decode("utf-8")
                try:
                    return resp.getcode(), json.loads(content) if content else {}
                except json.JSONDecodeError:
                    return resp.getcode(), {"raw": content}
        except Exception as e:
            return 0, {"error": str(e)}


def print_result(
    test_name: str, code: int, body: dict, success_codes: list = [200, 201]
):
    """Afficher le résultat d'un test"""
    status = "✅" if code in success_codes else "❌"
    print(f"{status} [{test_name}] HTTP {code}")
    if isinstance(body, dict):
        if "error" in body:
            print(f"   ⚠️  Erreur: {body.get('error', 'Unknown')}")
        elif "success" in body and not body.get("success"):
            print(f"   ⚠️  Success=False: {body.get('message', 'Unknown')}")
    return code in success_codes


def main():
    client = HttpClient()
    print(f"\n{'='*60}")
    print(f"TEST COMPLET DE L'API FormForge")
    print(f"URL: {BASE_URL}")
    print(f"{'='*60}\n")

    results = {"success": 0, "failed": 0}
    ts = int(time.time())
    test_email = f"test_complet_{ts}@example.com"
    test_password = "Password123!"

    # ========================================
    # 1. HEALTH CHECK
    # ========================================
    print("\n📋 SECTION 1: HEALTH CHECK")
    print("-" * 60)
    code, body = client.get_json("/api/health")
    if print_result("Health Check", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # ========================================
    # 2. AUTHENTIFICATION
    # ========================================
    print("\n📋 SECTION 2: AUTHENTIFICATION")
    print("-" * 60)

    # 2.1 Inscription
    code, body = client.post_json(
        "/api/auth/register-json", {"email": test_email, "password": test_password}
    )
    if print_result("Inscription", code, body, [200, 201, 409]):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 2.2 Connexion (login-json)
    code, body = client.post_json(
        "/api/auth/login-json", {"email": test_email, "password": test_password}
    )
    if print_result("Connexion (login-json)", code, body):
        results["success"] += 1
        if isinstance(body, dict) and "token" in body:
            client.token = body["token"]
            print(f"   ✓ Token récupéré: {client.token[:20]}...")
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 2.3 Connexion alternative (signin)
    code, body = client.post_json(
        "/api/auth/signin", {"email": test_email, "password": test_password}
    )
    if print_result("Connexion (signin)", code, body):
        results["success"] += 1
        if isinstance(body, dict) and "token" in body:
            client.token = body["token"]
    else:
        results["failed"] += 1
    time.sleep(0.5)

    if not client.token:
        print("\n❌ ÉCHEC: Impossible d'obtenir un token d'authentification")
        print("   Les tests suivants nécessitent une authentification.")
        return

    # ========================================
    # 3. GESTION DE FORMULAIRES
    # ========================================
    print("\n📋 SECTION 3: GESTION DE FORMULAIRES")
    print("-" * 60)

    # 3.1 Lister les formulaires (vide au départ)
    code, body = client.get_json("/api/forms", use_query_token=True)
    if print_result("Lister formulaires", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 3.2 Créer un formulaire
    form_data = {
        "title": f"Formulaire Test {ts}",
        "description": "Description du formulaire de test",
        "settings": {"theme": "blue"},
    }
    code, body = client.post_json("/api/forms", form_data, use_query_token=True)
    form_id = None
    if print_result("Créer formulaire", code, body):
        results["success"] += 1
        if isinstance(body, dict):
            form_id = (body.get("data") or {}).get("form_id") or body.get("form_id")
            if form_id:
                print(f"   ✓ Formulaire créé: {form_id}")
    else:
        results["failed"] += 1
    time.sleep(0.5)

    if not form_id:
        print("\n❌ ÉCHEC: Impossible de créer un formulaire")
        print("   Les tests suivants nécessitent un formulaire.")
        return

    # 3.3 Récupérer un formulaire
    code, body = client.get_json(f"/api/forms/{form_id}", use_query_token=True)
    if print_result("Récupérer formulaire", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 3.4 Mettre à jour un formulaire
    update_data = {
        "title": f"Formulaire Test {ts} - Modifié",
        "description": "Description modifiée",
        "settings": {"theme": "green"},
    }
    code, body = client.put_json(
        f"/api/forms/{form_id}", update_data, use_query_token=True
    )
    if print_result("Mettre à jour formulaire", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # ========================================
    # 4. GESTION DE QUESTIONS
    # ========================================
    print("\n📋 SECTION 4: GESTION DE QUESTIONS")
    print("-" * 60)

    # 4.1 Créer une question texte
    question1_data = {
        "type": "text",
        "text": "Quel est votre nom?",
        "required": True,
        "order_index": 0,
    }
    code, body = client.post_json(
        f"/api/forms/{form_id}/questions", question1_data, use_query_token=True
    )
    question1_id = None
    if print_result("Créer question (texte)", code, body):
        results["success"] += 1
        if isinstance(body, dict):
            question1_id = body.get("question_id") or body.get("data", {}).get(
                "question_id"
            )
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 4.2 Créer une question choix multiple
    question2_data = {
        "type": "multiple_choice",
        "text": "Quelle est votre couleur préférée?",
        "options": ["Rouge", "Vert", "Bleu"],
        "required": True,
        "order_index": 1,
    }
    code, body = client.post_json(
        f"/api/forms/{form_id}/questions", question2_data, use_query_token=True
    )
    question2_id = None
    if print_result("Créer question (choix multiple)", code, body):
        results["success"] += 1
        if isinstance(body, dict):
            question2_id = body.get("question_id") or body.get("data", {}).get(
                "question_id"
            )
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 4.3 Lister les questions
    code, body = client.get_json(
        f"/api/forms/{form_id}/questions", use_query_token=True
    )
    if print_result("Lister questions", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 4.4 Mettre à jour une question (si créée)
    if question1_id:
        update_question_data = {
            "text": "Quel est votre nom complet?",
            "required": True,
        }
        code, body = client.put_json(
            f"/api/questions/{question1_id}", update_question_data, use_query_token=True
        )
        if print_result("Mettre à jour question", code, body):
            results["success"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)

    # ========================================
    # 5. PUBLICATION DE FORMULAIRE
    # ========================================
    print("\n📋 SECTION 5: PUBLICATION DE FORMULAIRE")
    print("-" * 60)

    # 5.1 Publier le formulaire
    code, body = client.post_json(
        f"/api/forms/{form_id}/publish", {}, use_query_token=True
    )
    public_token = None
    if print_result("Publier formulaire", code, body):
        results["success"] += 1
        if isinstance(body, dict):
            public_token = body.get("data", {}).get("public_token") or body.get(
                "public_token"
            )
            if public_token:
                print(f"   ✓ Token public: {public_token[:20]}...")
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 5.2 Récupérer le lien public
    code, body = client.get_json(
        f"/api/forms/{form_id}/public-link", use_query_token=True
    )
    if print_result("Récupérer lien public", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 5.3 Accéder au formulaire public (sans authentification)
    if public_token:
        client_public = HttpClient()  # Client sans authentification
        code, body = client_public.get_json(f"/api/public/forms/{public_token}")
        if print_result("Accéder formulaire public", code, body):
            results["success"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)

    # ========================================
    # 6. GESTION DE RÉPONSES
    # ========================================
    print("\n📋 SECTION 6: GESTION DE RÉPONSES")
    print("-" * 60)

    # 6.1 Soumettre une réponse (authentifiée)
    if question1_id and question2_id:
        response_data = {
            "answers": {
                question1_id: "Jean Dupont",
                question2_id: "Bleu",
            }
        }
        code, body = client.post_json(
            f"/api/forms/{form_id}/responses", response_data, use_query_token=True
        )
        response_id = None
        if print_result("Soumettre réponse (authentifiée)", code, body):
            results["success"] += 1
            if isinstance(body, dict):
                response_id = body.get("response_id") or body.get("data", {}).get(
                    "response_id"
                )
        else:
            results["failed"] += 1
        time.sleep(0.5)

    # 6.2 Soumettre une réponse publique (si formulaire publié)
    if public_token and question1_id and question2_id:
        client_public = HttpClient()
        public_response_data = {
            "answers": {
                question1_id: "Marie Martin",
                question2_id: "Rouge",
            }
        }
        code, body = client_public.post_json(
            f"/api/public/forms/{public_token}/responses", public_response_data
        )
        if print_result("Soumettre réponse (publique)", code, body):
            results["success"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)

    # 6.3 Récupérer les réponses
    code, body = client.get_json(
        f"/api/forms/{form_id}/responses", use_query_token=True
    )
    if print_result("Récupérer réponses", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 6.4 Analytics
    code, body = client.get_json(
        f"/api/forms/{form_id}/analytics", use_query_token=True
    )
    if print_result("Analytics formulaire", code, body):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # ========================================
    # 7. EXPORT
    # ========================================
    print("\n📋 SECTION 7: EXPORT")
    print("-" * 60)

    # 7.1 Export CSV
    code, body = client.get_json(
        f"/api/forms/{form_id}/export/csv", use_query_token=True
    )
    if print_result("Export CSV", code, body, [200, 400, 404]):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # 7.2 Export Excel
    code, body = client.get_json(
        f"/api/forms/{form_id}/export/excel", use_query_token=True
    )
    if print_result("Export Excel", code, body, [200, 400, 404]):
        results["success"] += 1
    else:
        results["failed"] += 1
    time.sleep(0.5)

    # ========================================
    # 8. NETTOYAGE (OPTIONNEL)
    # ========================================
    print("\n📋 SECTION 8: NETTOYAGE")
    print("-" * 60)

    # 8.1 Supprimer une question (optionnel)
    if question2_id:
        code, body = client.delete_json(
            f"/api/questions/{question2_id}", use_query_token=True
        )
        if print_result("Supprimer question", code, body, [200, 204, 404]):
            results["success"] += 1
        else:
            results["failed"] += 1
        time.sleep(0.5)

    # ========================================
    # RÉSUMÉ
    # ========================================
    print("\n" + "=" * 60)
    print("RÉSUMÉ DES TESTS")
    print("=" * 60)
    total = results["success"] + results["failed"]
    success_rate = (results["success"] / total * 100) if total > 0 else 0
    print(f"✅ Réussis: {results['success']}/{total}")
    print(f"❌ Échoués: {results['failed']}/{total}")
    print(f"📊 Taux de réussite: {success_rate:.1f}%")
    print("=" * 60 + "\n")

    if success_rate >= 80:
        print("🎉 L'API fonctionne correctement!")
    elif success_rate >= 50:
        print("⚠️  L'API fonctionne partiellement. Vérifier les échecs.")
    else:
        print("❌ L'API a des problèmes majeurs. Révision nécessaire.")


if __name__ == "__main__":
    main()
