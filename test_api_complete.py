"""
Script de test complet pour l'API FormForge déployée
À utiliser avec l'URL de votre API Render
"""

import requests
import json
import sys
from datetime import datetime


class FormForgeAPITester:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url.rstrip("/")
        self.token = None
        self.user_id = None
        self.form_id = None
        self.question_id = None
        self.response_id = None

    def log_test(self, test_name, status, details=""):
        """Logger les résultats des tests"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = (
            "✅" if status == "SUCCESS" else "❌" if status == "ERROR" else "⚠️"
        )
        print(f"[{timestamp}] {status_icon} {test_name}: {status}")
        if details:
            print(f"    {details}")

    def test_health(self):
        """Test 1: Vérifier la santé de l'API"""
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health", "SUCCESS", f"Status: {data.get('status', 'unknown')}"
                )
                return True
            else:
                self.log_test(
                    "API Health", "ERROR", f"Status code: {response.status_code}"
                )
                return False
        except Exception as e:
            self.log_test("API Health", "ERROR", f"Exception: {str(e)}")
            return False

    def test_auth_register(self):
        """Test 2: Inscription d'un utilisateur"""
        try:
            user_data = {
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "name": "Test User",
            }
            response = requests.post(
                f"{self.api_base_url}/api/auth/register", json=user_data, timeout=10
            )

            if response.status_code == 201:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test(
                    "User Registration", "SUCCESS", f"User ID: {self.user_id}"
                )
                return True
            else:
                self.log_test(
                    "User Registration",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("User Registration", "ERROR", f"Exception: {str(e)}")
            return False

    def test_auth_login(self):
        """Test 3: Connexion utilisateur"""
        try:
            login_data = {
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
            }
            response = requests.post(
                f"{self.api_base_url}/api/auth/login", json=login_data, timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("token")
                self.user_id = data.get("user", {}).get("id")
                self.log_test("User Login", "SUCCESS", f"User ID: {self.user_id}")
                return True
            else:
                self.log_test(
                    "User Login",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("User Login", "ERROR", f"Exception: {str(e)}")
            return False

    def get_auth_headers(self):
        """Obtenir les headers d'authentification"""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def test_forms_create(self):
        """Test 4: Création d'un formulaire"""
        try:
            form_data = {
                "title": f"Test Form {datetime.now().strftime('%H:%M:%S')}",
                "description": "Formulaire de test pour l'API",
                "settings": {"theme": "blue", "public": True},
            }
            response = requests.post(
                f"{self.api_base_url}/api/forms",
                json=form_data,
                headers=self.get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                self.form_id = data.get("data", {}).get("form_id")
                self.log_test("Form Creation", "SUCCESS", f"Form ID: {self.form_id}")
                return True
            else:
                self.log_test(
                    "Form Creation",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Form Creation", "ERROR", f"Exception: {str(e)}")
            return False

    def test_forms_get(self):
        """Test 5: Récupération d'un formulaire"""
        if not self.form_id:
            self.log_test("Form Get", "ERROR", "No form ID available")
            return False

        try:
            response = requests.get(
                f"{self.api_base_url}/api/forms/{self.form_id}",
                headers=self.get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                form = data.get("form", {})
                self.log_test(
                    "Form Get", "SUCCESS", f"Title: {form.get('title', 'Unknown')}"
                )
                return True
            else:
                self.log_test(
                    "Form Get",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Form Get", "ERROR", f"Exception: {str(e)}")
            return False

    def test_questions_create(self):
        """Test 6: Création d'une question"""
        if not self.form_id:
            self.log_test("Question Creation", "ERROR", "No form ID available")
            return False

        try:
            question_data = {
                "type": "text",
                "text": "Quel est votre nom ?",
                "required": True,
                "order_index": 0,
            }
            response = requests.post(
                f"{self.api_base_url}/api/forms/{self.form_id}/questions",
                json=question_data,
                headers=self.get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                self.question_id = data.get("question_id")
                self.log_test(
                    "Question Creation", "SUCCESS", f"Question ID: {self.question_id}"
                )
                return True
            else:
                self.log_test(
                    "Question Creation",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Question Creation", "ERROR", f"Exception: {str(e)}")
            return False

    def test_responses_submit(self):
        """Test 7: Soumission d'une réponse (route publique)"""
        if not self.form_id or not self.question_id:
            self.log_test("Response Submit", "ERROR", "Missing form or question ID")
            return False

        try:
            response_data = {
                "answers": {self.question_id: "John Doe"},
                "user_id": "anonymous_user",
            }
            response = requests.post(
                f"{self.api_base_url}/api/forms/{self.form_id}/responses",
                json=response_data,
                timeout=10,
            )

            if response.status_code == 201:
                data = response.json()
                self.response_id = data.get("response_id")
                self.log_test(
                    "Response Submit", "SUCCESS", f"Response ID: {self.response_id}"
                )
                return True
            else:
                self.log_test(
                    "Response Submit",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Response Submit", "ERROR", f"Exception: {str(e)}")
            return False

    def test_responses_get(self):
        """Test 8: Récupération des réponses (route protégée)"""
        if not self.form_id:
            self.log_test("Responses Get", "ERROR", "No form ID available")
            return False

        try:
            response = requests.get(
                f"{self.api_base_url}/api/forms/{self.form_id}/responses",
                headers=self.get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                responses = data.get("responses", [])
                self.log_test(
                    "Responses Get", "SUCCESS", f"Found {len(responses)} responses"
                )
                return True
            else:
                self.log_test(
                    "Responses Get",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Responses Get", "ERROR", f"Exception: {str(e)}")
            return False

    def test_analytics(self):
        """Test 9: Analytics du formulaire"""
        if not self.form_id:
            self.log_test("Analytics", "ERROR", "No form ID available")
            return False

        try:
            response = requests.get(
                f"{self.api_base_url}/api/forms/{self.form_id}/analytics",
                headers=self.get_auth_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                analytics = data.get("analytics", {})
                total_responses = analytics.get("total_responses", 0)
                self.log_test(
                    "Analytics", "SUCCESS", f"Total responses: {total_responses}"
                )
                return True
            else:
                self.log_test(
                    "Analytics",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Analytics", "ERROR", f"Exception: {str(e)}")
            return False

    def test_export_csv(self):
        """Test 10: Export CSV"""
        if not self.form_id:
            self.log_test("Export CSV", "ERROR", "No form ID available")
            return False

        try:
            response = requests.get(
                f"{self.api_base_url}/api/forms/{self.form_id}/export/csv",
                headers=self.get_auth_headers(),
                timeout=15,
            )

            if response.status_code == 200:
                data = response.json()
                csv_content = data.get("csv_content", "")
                self.log_test(
                    "Export CSV",
                    "SUCCESS",
                    f"CSV length: {len(csv_content)} characters",
                )
                return True
            else:
                self.log_test(
                    "Export CSV",
                    "ERROR",
                    f"Status: {response.status_code}, Response: {response.text}",
                )
                return False
        except Exception as e:
            self.log_test("Export CSV", "ERROR", f"Exception: {str(e)}")
            return False

    def test_protected_routes_without_auth(self):
        """Test 11: Vérifier que les routes protégées retournent 401 sans token"""
        protected_routes = [
            ("POST", "/api/forms", {"title": "Test"}),
            ("PUT", "/api/forms/test-id", {"title": "Test"}),
            ("DELETE", "/api/forms/test-id", None),
            ("GET", "/api/forms", None),
            ("GET", "/api/forms/test-id/responses", None),
            ("GET", "/api/forms/test-id/analytics", None),
        ]

        success_count = 0
        for method, endpoint, data in protected_routes:
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)
                elif method == "POST":
                    response = requests.post(
                        f"{self.api_base_url}{endpoint}", json=data, timeout=5
                    )
                elif method == "PUT":
                    response = requests.put(
                        f"{self.api_base_url}{endpoint}", json=data, timeout=5
                    )
                elif method == "DELETE":
                    response = requests.delete(
                        f"{self.api_base_url}{endpoint}", timeout=5
                    )

                if response.status_code == 401:
                    success_count += 1
                    self.log_test(
                        f"Protected Route {method} {endpoint}",
                        "SUCCESS",
                        "Returns 401 as expected",
                    )
                else:
                    self.log_test(
                        f"Protected Route {method} {endpoint}",
                        "ERROR",
                        f"Returns {response.status_code}, should be 401",
                    )
            except Exception as e:
                self.log_test(
                    f"Protected Route {method} {endpoint}",
                    "ERROR",
                    f"Exception: {str(e)}",
                )

        self.log_test(
            "Protected Routes Test",
            "SUCCESS" if success_count == len(protected_routes) else "WARNING",
            f"{success_count}/{len(protected_routes)} routes correctly protected",
        )
        return success_count == len(protected_routes)

    def test_public_routes(self):
        """Test 12: Vérifier que les routes publiques fonctionnent"""
        public_routes = [
            ("GET", "/api/health", None),
        ]

        success_count = 0
        for method, endpoint, data in public_routes:
            try:
                if method == "GET":
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=5)

                if response.status_code != 401:
                    success_count += 1
                    self.log_test(
                        f"Public Route {method} {endpoint}",
                        "SUCCESS",
                        f"Returns {response.status_code} (not 401)",
                    )
                else:
                    self.log_test(
                        f"Public Route {method} {endpoint}",
                        "ERROR",
                        "Returns 401, should be public",
                    )
            except Exception as e:
                self.log_test(
                    f"Public Route {method} {endpoint}", "ERROR", f"Exception: {str(e)}"
                )

        self.log_test(
            "Public Routes Test",
            "SUCCESS" if success_count == len(public_routes) else "WARNING",
            f"{success_count}/{len(public_routes)} routes correctly public",
        )
        return success_count == len(public_routes)

    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🧪 Tests Complets de l'API FormForge")
        print("=" * 60)
        print(f"API URL: {self.api_base_url}")
        print("=" * 60)

        tests = [
            ("API Health", self.test_health),
            ("User Registration", self.test_auth_register),
            ("Form Creation", self.test_forms_create),
            ("Form Get", self.test_forms_get),
            ("Question Creation", self.test_questions_create),
            ("Response Submit", self.test_responses_submit),
            ("Responses Get", self.test_responses_get),
            ("Analytics", self.test_analytics),
            ("Export CSV", self.test_export_csv),
            ("Protected Routes", self.test_protected_routes_without_auth),
            ("Public Routes", self.test_public_routes),
        ]

        success_count = 0
        total_count = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    success_count += 1
            except Exception as e:
                self.log_test(test_name, "ERROR", f"Unexpected exception: {str(e)}")

        print("\n" + "=" * 60)
        print(f"📊 Résultats: {success_count}/{total_count} tests réussis")

        if success_count == total_count:
            print("🎉 TOUS LES TESTS SONT PASSÉS!")
            print("✅ L'API FormForge fonctionne correctement")
            print("✅ L'authentification est correctement configurée")
            print("✅ Toutes les routes sont sécurisées")
        else:
            print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
            print("🔍 Vérifiez les détails ci-dessus pour identifier les problèmes")

        return success_count == total_count


def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python test_api_complete.py <API_URL>")
        print(
            "Example: python test_api_complete.py https://formforge-backend.onrender.com"
        )
        sys.exit(1)

    api_url = sys.argv[1]
    tester = FormForgeAPITester(api_url)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
