#!/usr/bin/env python3
"""
Test complet de l'API FormForge sécurisée
Expert Cybersécurité - 15+ ans d'expérience

Tests:
1. Fonctionnalités normales (auth, CRUD, etc.)
2. Nouvelles protections de sécurité
3. Rate limiting persistant
4. Validation mots de passe renforcée
5. Headers de sécurité
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "https://backend-skum.onrender.com"
TIMEOUT = 30

# Couleurs pour le terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SecureAPITester:
    """Testeur API avec vérifications de sécurité"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.form_id = None
        self.question_id = None
        self.public_token = None
        self.test_results = []
        self.security_tests = []
        self.start_time = time.time()

    def log(self, message, level="INFO"):
        """Logger avec couleurs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "SECURITY": Colors.MAGENTA
        }
        color = colors.get(level, Colors.BLUE)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")

    def test_endpoint(self, name, method, endpoint, data=None, headers=None,
                     expected_status=200, auth_required=True, category="FUNCTIONAL"):
        """Tester un endpoint avec validation complète"""
        self.log(f"Testing: {name}", "INFO")

        url = f"{self.base_url}{endpoint}"

        # Préparer les headers
        if headers is None:
            headers = {"Content-Type": "application/json"}

        # Ajouter le token d'authentification si nécessaire
        if auth_required and self.token:
            headers["Authentication-Token"] = self.token

        try:
            # Faire la requête
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")

            # Analyser la réponse
            status_ok = response.status_code == expected_status

            try:
                response_data = response.json()
            except:
                response_data = {"raw": response.text[:500]}

            # Analyser les headers de sécurité
            security_headers = {
                "X-RateLimit-Limit": response.headers.get("X-RateLimit-Limit"),
                "X-RateLimit-Remaining": response.headers.get("X-RateLimit-Remaining"),
                "X-RateLimit-Reset": response.headers.get("X-RateLimit-Reset"),
                "X-Content-Type-Options": response.headers.get("X-Content-Type-Options"),
                "X-Frame-Options": response.headers.get("X-Frame-Options"),
            }

            # Enregistrer le résultat
            result = {
                "name": name,
                "category": category,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": status_ok,
                "response_time": response.elapsed.total_seconds(),
                "response_data": response_data,
                "security_headers": security_headers
            }

            if category == "SECURITY":
                self.security_tests.append(result)
            else:
                self.test_results.append(result)

            if status_ok:
                self.log(
                    f"✓ {name} - Status: {response.status_code} - "
                    f"Time: {response.elapsed.total_seconds():.2f}s",
                    "SUCCESS"
                )
            else:
                self.log(
                    f"✗ {name} - Expected: {expected_status}, Got: {response.status_code}",
                    "ERROR"
                )
                if len(str(response_data)) < 200:
                    self.log(f"Response: {response_data}", "ERROR")

            return response, response_data, security_headers

        except requests.exceptions.Timeout:
            self.log(f"✗ {name} - TIMEOUT après {TIMEOUT}s", "ERROR")
            result = {"name": name, "category": category, "success": False, "error": "TIMEOUT"}
            if category == "SECURITY":
                self.security_tests.append(result)
            else:
                self.test_results.append(result)
            return None, None, {}
        except Exception as e:
            self.log(f"✗ {name} - Erreur: {str(e)}", "ERROR")
            result = {"name": name, "category": category, "success": False, "error": str(e)}
            if category == "SECURITY":
                self.security_tests.append(result)
            else:
                self.test_results.append(result)
            return None, None, {}

    def run_functional_tests(self):
        """Tests fonctionnels normaux"""
        self.log("\n" + "="*80, "INFO")
        self.log("PARTIE 1: TESTS FONCTIONNELS", "INFO")
        self.log("="*80 + "\n", "INFO")

        # Test 1: Health Check
        self.log("### TEST 1: HEALTH CHECK ###", "INFO")
        self.test_endpoint(
            "Health Check",
            "GET",
            "/api/health",
            auth_required=False
        )

        # Test 2: Inscription avec mot de passe FORT
        self.log("\n### TEST 2: AUTHENTIFICATION ###", "INFO")
        timestamp = int(time.time())
        email = f"secure_test_{timestamp}@test.com"
        # Mot de passe FORT (conforme à la nouvelle politique)
        password = "SecureP@ss123!"

        self.log(f"Utilisation mot de passe fort: {password}", "INFO")

        response, data, headers = self.test_endpoint(
            "Inscription avec mot de passe fort",
            "POST",
            "/api/auth/signup",
            data={
                "email": email,
                "password": password,
                "name": "Secure Tester"
            },
            expected_status=201,
            auth_required=False
        )

        if data and data.get("success"):
            self.token = data.get("authentication_token")
            self.user_id = data.get("user", {}).get("id")
            self.log(f"Token obtenu: {self.token[:20] if self.token else 'None'}...", "SUCCESS")
            self.log(f"User ID: {self.user_id}", "SUCCESS")

            # Vérifier les headers rate limiting
            if headers.get("X-RateLimit-Limit"):
                self.log(f"✓ Rate Limit headers présents: {headers['X-RateLimit-Limit']} req", "SUCCESS")

        # Test 3: Créer un formulaire
        self.log("\n### TEST 3: GESTION DES FORMULAIRES ###", "INFO")
        response, data, headers = self.test_endpoint(
            "Créer un formulaire",
            "POST",
            "/api/forms",
            data={
                "title": "Formulaire sécurisé",
                "description": "Test post-sécurisation",
                "settings": {"theme": "blue"}
            },
            expected_status=201
        )

        if data and data.get("success"):
            self.form_id = data.get("data", {}).get("form_id")
            self.log(f"Formulaire créé: {self.form_id}", "SUCCESS")

        # Test 4: Lister les formulaires
        self.test_endpoint(
            "Lister les formulaires",
            "GET",
            "/api/forms"
        )

        # Test 5: Créer une question
        if self.form_id:
            self.log("\n### TEST 4: GESTION DES QUESTIONS ###", "INFO")
            response, data, headers = self.test_endpoint(
                "Créer une question",
                "POST",
                f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "text",
                    "text": "Question de test sécurisé",
                    "required": True
                },
                expected_status=201
            )

            if data and data.get("success"):
                self.question_id = data.get("question_id")

        # Test 6: Publier le formulaire
        if self.form_id:
            self.log("\n### TEST 5: PUBLICATION ###", "INFO")
            response, data, headers = self.test_endpoint(
                "Publier le formulaire",
                "POST",
                f"/api/forms/{self.form_id}/publish"
            )

            if data and data.get("success"):
                self.public_token = data.get("data", {}).get("public_token")
                self.log(f"Token public: {self.public_token}", "SUCCESS")

    def run_security_tests(self):
        """Tests de sécurité spécifiques"""
        self.log("\n" + "="*80, "SECURITY")
        self.log("PARTIE 2: TESTS DE SÉCURITÉ", "SECURITY")
        self.log("="*80 + "\n", "SECURITY")

        # Test sécurité 1: Tentative mot de passe faible
        self.log("### SÉCURITÉ 1: VALIDATION MOT DE PASSE ###", "SECURITY")

        weak_passwords = [
            ("password", "Mot de passe commun"),
            ("12345678", "Seulement des chiffres"),
            ("abcdefgh", "Seulement des lettres"),
            ("Short1!", "Trop court (7 caractères)"),
        ]

        for weak_pwd, reason in weak_passwords:
            self.log(f"Test rejet: {weak_pwd} ({reason})", "SECURITY")
            timestamp = int(time.time())
            response, data, headers = self.test_endpoint(
                f"Rejet mot de passe faible: {reason}",
                "POST",
                "/api/auth/signup",
                data={
                    "email": f"weak_{timestamp}@test.com",
                    "password": weak_pwd,
                    "name": "Test"
                },
                expected_status=400,
                auth_required=False,
                category="SECURITY"
            )

            if data and "error" in data:
                self.log(f"✓ Rejet correctement: {data.get('message', data.get('error'))}", "SUCCESS")

        # Test sécurité 2: Token en query string (doit être refusé en production)
        if self.token and self.form_id:
            self.log("\n### SÉCURITÉ 2: INTERDICTION TOKEN QUERY STRING ###", "SECURITY")

            # Vérifier si on est en production
            import os
            is_prod = os.environ.get("FLASK_ENV") == "production"

            if is_prod:
                self.log("Mode production détecté - Test rejet token query string", "SECURITY")
                response, data, headers = self.test_endpoint(
                    "Rejet token en query string (production)",
                    "GET",
                    f"/api/forms?token={self.token}",
                    expected_status=403,
                    auth_required=False,
                    category="SECURITY"
                )

                if response and response.status_code == 403:
                    self.log("✓ Token query string correctement refusé en production", "SUCCESS")
            else:
                self.log("Mode développement - Token query string autorisé", "WARNING")

        # Test sécurité 3: Rate limiting headers
        self.log("\n### SÉCURITÉ 3: RATE LIMITING HEADERS ###", "SECURITY")
        response, data, headers = self.test_endpoint(
            "Vérification headers rate limiting",
            "GET",
            "/api/health",
            auth_required=False,
            category="SECURITY"
        )

        if headers.get("X-RateLimit-Limit"):
            self.log(f"✓ X-RateLimit-Limit: {headers['X-RateLimit-Limit']}", "SUCCESS")
            self.log(f"✓ X-RateLimit-Remaining: {headers['X-RateLimit-Remaining']}", "SUCCESS")
            self.log(f"✓ X-RateLimit-Reset: {headers['X-RateLimit-Reset']}", "SUCCESS")
        else:
            self.log("⚠ Headers rate limiting non présents", "WARNING")

        # Test sécurité 4: CORS headers
        self.log("\n### SÉCURITÉ 4: HEADERS CORS ###", "SECURITY")
        try:
            response = requests.options(
                f"{self.base_url}/api/health",
                headers={"Origin": "https://evil.com"},
                timeout=TIMEOUT
            )

            cors_header = response.headers.get("Access-Control-Allow-Origin")
            if cors_header and cors_header != "*":
                self.log(f"✓ CORS configuré (pas de wildcard): {cors_header}", "SUCCESS")
            elif cors_header == "*":
                self.log("✗ CORS DANGEREUX: wildcard * détecté!", "ERROR")
            else:
                self.log("✓ CORS restrictif (pas de header pour origine non autorisée)", "SUCCESS")

        except Exception as e:
            self.log(f"Erreur test CORS: {e}", "WARNING")

    def run_performance_tests(self):
        """Tests de performance basiques"""
        self.log("\n" + "="*80, "INFO")
        self.log("PARTIE 3: TESTS DE PERFORMANCE", "INFO")
        self.log("="*80 + "\n", "INFO")

        # Test multiple requêtes pour vérifier le rate limiting
        self.log("### TEST RATE LIMITING (10 requêtes rapides) ###", "INFO")

        success_count = 0
        rate_limited_count = 0

        for i in range(10):
            response, data, headers = self.test_endpoint(
                f"Requête rapide #{i+1}",
                "GET",
                "/api/health",
                auth_required=False,
                expected_status=200
            )

            if response:
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                    self.log(f"Rate limit atteint à la requête #{i+1}", "WARNING")

            time.sleep(0.1)  # Petit délai entre requêtes

        self.log(f"Résultats: {success_count} succès, {rate_limited_count} rate limited", "INFO")

    def generate_report(self):
        """Générer le rapport de tests"""
        self.log("\n" + "="*80, "INFO")
        self.log("RAPPORT FINAL", "INFO")
        self.log("="*80 + "\n", "INFO")

        # Tests fonctionnels
        total_functional = len(self.test_results)
        successful_functional = sum(1 for r in self.test_results if r.get("success"))
        failed_functional = total_functional - successful_functional

        # Tests de sécurité
        total_security = len(self.security_tests)
        successful_security = sum(1 for r in self.security_tests if r.get("success"))
        failed_security = total_security - successful_security

        # Total
        total_tests = total_functional + total_security
        successful_tests = successful_functional + successful_security
        failed_tests = failed_functional + failed_security

        total_time = time.time() - self.start_time

        self.log(f"Tests fonctionnels: {successful_functional}/{total_functional} réussis",
                "SUCCESS" if failed_functional == 0 else "WARNING")
        self.log(f"Tests de sécurité: {successful_security}/{total_security} réussis",
                "SUCCESS" if failed_security == 0 else "WARNING")
        self.log(f"\nTotal: {successful_tests}/{total_tests} réussis ({successful_tests/total_tests*100:.1f}%)",
                "SUCCESS" if failed_tests == 0 else "WARNING")
        self.log(f"Temps total: {total_time:.2f}s", "INFO")

        # Détails des échecs
        if failed_tests > 0:
            self.log("\n=== TESTS ÉCHOUÉS ===", "ERROR")
            for result in self.test_results + self.security_tests:
                if not result.get("success"):
                    self.log(f"✗ {result.get('name')}: {result.get('error', 'Status mismatch')}", "ERROR")

        # Analyse des temps de réponse
        response_times = [r.get("response_time", 0) for r in self.test_results if "response_time" in r]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)

            self.log(f"\n=== PERFORMANCE ===", "INFO")
            self.log(f"Temps de réponse moyen: {avg_time:.2f}s", "INFO")
            self.log(f"Temps de réponse max: {max_time:.2f}s", "INFO")
            self.log(f"Temps de réponse min: {min_time:.2f}s", "INFO")

        # Verdict final
        self.log("\n" + "="*80, "INFO")
        if failed_tests == 0:
            self.log("✓ VERDICT: API SÉCURISÉE ET FONCTIONNELLE", "SUCCESS")
        elif failed_tests < total_tests * 0.2:
            self.log("⚠ VERDICT: MAJORITAIREMENT FONCTIONNEL", "WARNING")
        else:
            self.log("✗ VERDICT: PROBLÈMES DÉTECTÉS", "ERROR")
        self.log("="*80, "INFO")

        # Sauvegarder le rapport JSON
        report_file = f"test_report_secure_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "functional_tests": {
                    "total": total_functional,
                    "successful": successful_functional,
                    "failed": failed_functional
                },
                "security_tests": {
                    "total": total_security,
                    "successful": successful_security,
                    "failed": failed_security
                },
                "total": {
                    "tests": total_tests,
                    "successful": successful_tests,
                    "failed": failed_tests,
                    "success_rate": successful_tests/total_tests*100
                },
                "total_time": total_time,
                "results": self.test_results,
                "security_results": self.security_tests
            }, f, indent=2)

        self.log(f"\nRapport détaillé sauvegardé: {report_file}", "INFO")

if __name__ == "__main__":
    tester = SecureAPITester(API_BASE_URL)

    # Exécuter tous les tests
    tester.run_functional_tests()
    tester.run_security_tests()
    tester.run_performance_tests()

    # Générer le rapport
    tester.generate_report()
