#!/usr/bin/env python3
"""
Test COMPLET de l'API FormForge - Fonctionnalité + Sécurité
Expert Cybersécurité & API - 15+ ans d'expérience

Tests:
1. Fonctionnalités complètes (tous les endpoints)
2. Sécurité (validation, rate limiting, tokens)
3. Performance (temps de réponse, stabilité)
4. Edge cases (erreurs, limites)
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Configuration
API_BASE_URL = "https://backend-skum.onrender.com"
TIMEOUT = 30

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ComprehensiveAPITester:
    """Testeur API complet avec focus sécurité et fonctionnalité"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.form_id = None
        self.question_ids = []
        self.public_token = None
        self.response_id = None

        # Résultats
        self.functional_tests = []
        self.security_tests = []
        self.performance_tests = []
        self.start_time = time.time()

    def log(self, message, level="INFO"):
        """Logger avec couleurs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW,
            "SECURITY": Colors.MAGENTA,
            "PERF": Colors.CYAN
        }
        color = colors.get(level, Colors.BLUE)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")

    def test(self, name, method, endpoint, data=None, headers=None,
             expected_status=200, auth=True, category="FUNCTIONAL") -> Tuple[bool, Dict]:
        """Test générique avec logging"""
        url = f"{self.base_url}{endpoint}"

        if headers is None:
            headers = {"Content-Type": "application/json"}

        if auth and self.token:
            headers["Authentication-Token"] = self.token

        try:
            start = time.time()

            if method == "GET":
                resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            elif method == "POST":
                resp = requests.post(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "PUT":
                resp = requests.put(url, json=data, headers=headers, timeout=TIMEOUT)
            elif method == "DELETE":
                resp = requests.delete(url, headers=headers, timeout=TIMEOUT)
            else:
                raise ValueError(f"Méthode non supportée: {method}")

            elapsed = time.time() - start

            success = resp.status_code == expected_status

            try:
                resp_data = resp.json()
            except:
                resp_data = {"raw": resp.text[:200]}

            result = {
                "name": name,
                "category": category,
                "method": method,
                "endpoint": endpoint,
                "status": resp.status_code,
                "expected": expected_status,
                "success": success,
                "time": elapsed,
                "data": resp_data
            }

            # Stocker dans la catégorie appropriée
            if category == "SECURITY":
                self.security_tests.append(result)
            elif category == "PERFORMANCE":
                self.performance_tests.append(result)
            else:
                self.functional_tests.append(result)

            if success:
                self.log(f"✓ {name} - {resp.status_code} - {elapsed:.2f}s", "SUCCESS")
            else:
                self.log(f"✗ {name} - Expected {expected_status}, got {resp.status_code}", "ERROR")

            return success, resp_data

        except requests.Timeout:
            self.log(f"✗ {name} - TIMEOUT", "ERROR")
            return False, {"error": "timeout"}
        except Exception as e:
            self.log(f"✗ {name} - {str(e)}", "ERROR")
            return False, {"error": str(e)}

    def run_functional_tests(self):
        """Tests fonctionnels complets"""
        self.log("\n" + "="*80, "INFO")
        self.log("PARTIE 1: TESTS FONCTIONNELS COMPLETS", "INFO")
        self.log("="*80, "INFO")

        # ========== AUTHENTIFICATION ==========
        self.log("\n### 1. AUTHENTIFICATION ###", "INFO")

        timestamp = int(time.time())
        email = f"fulltest_{timestamp}@test.com"
        password = "TestSecure123!@#"

        # Inscription
        success, data = self.test(
            "Inscription utilisateur",
            "POST", "/api/auth/signup",
            data={"email": email, "password": password, "name": "Full Tester"},
            expected_status=201,
            auth=False
        )

        if success and data.get("success"):
            self.token = data.get("authentication_token")
            self.user_id = data.get("user", {}).get("id")
            self.log(f"Token: {self.token[:30]}...", "INFO")

        # Me
        self.test("Obtenir utilisateur actuel", "GET", "/api/auth/me")

        # ========== FORMULAIRES ==========
        self.log("\n### 2. GESTION FORMULAIRES ###", "INFO")

        # Créer
        success, data = self.test(
            "Créer formulaire",
            "POST", "/api/forms",
            data={
                "title": "Formulaire Test Complet",
                "description": "Test exhaustif API",
                "settings": {"theme": "blue", "public": True}
            },
            expected_status=201
        )

        if success and data.get("success"):
            self.form_id = data.get("data", {}).get("form_id")
            self.log(f"Form ID: {self.form_id}", "INFO")

        # Lister
        self.test("Lister formulaires", "GET", "/api/forms")

        # Détails
        if self.form_id:
            self.test("Détails formulaire", "GET", f"/api/forms/{self.form_id}")

        # Modifier
        if self.form_id:
            self.test(
                "Modifier formulaire",
                "PUT", f"/api/forms/{self.form_id}",
                data={"title": "Formulaire Modifié", "description": "Description mise à jour"}
            )

        # Stats
        if self.form_id:
            self.test("Statistiques formulaire", "GET", f"/api/forms/{self.form_id}/stats")

        # ========== QUESTIONS ==========
        self.log("\n### 3. GESTION QUESTIONS ###", "INFO")

        if self.form_id:
            # Question text
            success, data = self.test(
                "Créer question TEXT",
                "POST", f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "text",
                    "text": "Quel est votre nom?",
                    "required": True,
                    "order_index": 0
                },
                expected_status=201
            )
            if success:
                self.question_ids.append(data.get("question_id"))

            # Question email
            success, data = self.test(
                "Créer question EMAIL",
                "POST", f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "email",
                    "text": "Votre email?",
                    "required": True,
                    "order_index": 1
                },
                expected_status=201
            )
            if success:
                self.question_ids.append(data.get("question_id"))

            # Question choice
            success, data = self.test(
                "Créer question CHOICE",
                "POST", f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "choice",
                    "text": "Votre couleur préférée?",
                    "options": ["Rouge", "Vert", "Bleu"],
                    "required": False,
                    "order_index": 2
                },
                expected_status=201
            )
            if success:
                self.question_ids.append(data.get("question_id"))

            # Lister questions
            self.test("Lister questions", "GET", f"/api/forms/{self.form_id}/questions")

        # ========== PUBLICATION ==========
        self.log("\n### 4. PUBLICATION ###", "INFO")

        if self.form_id:
            # Publier
            success, data = self.test(
                "Publier formulaire",
                "POST", f"/api/forms/{self.form_id}/publish"
            )
            if success:
                self.public_token = data.get("data", {}).get("public_token")
                self.log(f"Public Token: {self.public_token}", "INFO")

            # Lien public
            self.test("Obtenir lien public", "GET", f"/api/forms/{self.form_id}/public-link")

        # ========== ACCÈS PUBLIC ==========
        self.log("\n### 5. ACCÈS PUBLIC ###", "INFO")

        if self.public_token:
            self.test(
                "Accéder formulaire public",
                "GET", f"/api/public/forms/{self.public_token}",
                auth=False
            )

        # ========== RÉPONSES ==========
        self.log("\n### 6. RÉPONSES ###", "INFO")

        if self.form_id and len(self.question_ids) >= 2:
            # Réponse authentifiée
            success, data = self.test(
                "Soumettre réponse (authentifiée)",
                "POST", f"/api/forms/{self.form_id}/responses",
                data={
                    "answers": {
                        self.question_ids[0]: "John Doe",
                        self.question_ids[1]: "john@example.com"
                    }
                },
                expected_status=201
            )
            if success:
                self.response_id = data.get("response_id")

        if self.public_token and len(self.question_ids) >= 2:
            # Réponse publique
            self.test(
                "Soumettre réponse (publique)",
                "POST", f"/api/public/forms/{self.public_token}/responses",
                data={
                    "answers": {
                        self.question_ids[0]: "Jane Smith",
                        self.question_ids[1]: "jane@example.com"
                    }
                },
                expected_status=201,
                auth=False
            )

        # Lister réponses
        if self.form_id:
            self.test("Lister réponses", "GET", f"/api/forms/{self.form_id}/responses")

        # ========== ANALYTICS ==========
        self.log("\n### 7. ANALYTICS ###", "INFO")

        if self.form_id:
            self.test("Analytics formulaire", "GET", f"/api/forms/{self.form_id}/analytics")

        # ========== EXPORT ==========
        self.log("\n### 8. EXPORT ###", "INFO")

        if self.form_id:
            self.test("Export CSV", "GET", f"/api/forms/{self.form_id}/export/csv")
            self.test("Export Excel", "GET", f"/api/forms/{self.form_id}/export/excel")
            self.test("Export JSON", "GET", f"/api/forms/{self.form_id}/export/json")

    def run_security_tests(self):
        """Tests de sécurité avancés"""
        self.log("\n" + "="*80, "SECURITY")
        self.log("PARTIE 2: TESTS DE SÉCURITÉ AVANCÉS", "SECURITY")
        self.log("="*80, "SECURITY")

        # ========== VALIDATION MOTS DE PASSE ==========
        self.log("\n### 1. VALIDATION MOTS DE PASSE ###", "SECURITY")

        weak_passwords = [
            ("pass", "Trop court (4 caractères)"),
            ("password", "Mot de passe commun"),
            ("12345678", "Que des chiffres"),
            ("abcdefgh", "Que des lettres minuscules"),
            ("ABCDEFGH", "Que des lettres majuscules"),
            ("Password", "Pas de chiffre ni spécial"),
            ("Password1", "Pas de caractère spécial"),
            ("Short1!", "Trop court (7 caractères)"),
        ]

        for pwd, reason in weak_passwords:
            timestamp = int(time.time())
            self.test(
                f"Rejet: {reason}",
                "POST", "/api/auth/signup",
                data={
                    "email": f"weak_{timestamp}@test.com",
                    "password": pwd,
                    "name": "Test"
                },
                expected_status=400,
                auth=False,
                category="SECURITY"
            )

        # Mot de passe fort accepté
        self.test(
            "Acceptation mot de passe fort",
            "POST", "/api/auth/signup",
            data={
                "email": f"strong_{int(time.time())}@test.com",
                "password": "StrongP@ss123!",
                "name": "Strong User"
            },
            expected_status=201,
            auth=False,
            category="SECURITY"
        )

        # ========== TENTATIVES NON AUTORISÉES ==========
        self.log("\n### 2. ACCÈS NON AUTORISÉS ###", "SECURITY")

        # Sans token
        self.test(
            "Accès sans authentification",
            "GET", "/api/forms",
            expected_status=401,
            auth=False,
            category="SECURITY"
        )

        # Token invalide
        invalid_headers = {
            "Content-Type": "application/json",
            "Authentication-Token": "invalid_token_12345"
        }
        try:
            resp = requests.get(
                f"{self.base_url}/api/forms",
                headers=invalid_headers,
                timeout=TIMEOUT
            )
            success = resp.status_code == 401
            self.security_tests.append({
                "name": "Rejet token invalide",
                "success": success,
                "status": resp.status_code
            })
            if success:
                self.log("✓ Rejet token invalide - 401", "SUCCESS")
            else:
                self.log(f"✗ Rejet token invalide - {resp.status_code}", "ERROR")
        except Exception as e:
            self.log(f"✗ Erreur test token invalide: {e}", "ERROR")

        # ========== VALIDATION DONNÉES ==========
        self.log("\n### 3. VALIDATION DONNÉES ###", "SECURITY")

        if self.form_id:
            # Question sans type
            self.test(
                "Rejet question sans type",
                "POST", f"/api/forms/{self.form_id}/questions",
                data={"text": "Question?"},
                expected_status=400,
                category="SECURITY"
            )

            # Question type invalide
            self.test(
                "Rejet type question invalide",
                "POST", f"/api/forms/{self.form_id}/questions",
                data={"type": "invalid_type", "text": "Question?"},
                expected_status=400,
                category="SECURITY"
            )

        # ========== RATE LIMITING ==========
        self.log("\n### 4. RATE LIMITING ###", "SECURITY")

        # Test headers rate limiting
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=TIMEOUT)
            headers = resp.headers

            has_limit = "X-RateLimit-Limit" in headers
            has_remaining = "X-RateLimit-Remaining" in headers
            has_reset = "X-RateLimit-Reset" in headers

            if has_limit and has_remaining and has_reset:
                self.log(f"✓ Headers rate limiting présents", "SUCCESS")
                self.log(f"  Limit: {headers.get('X-RateLimit-Limit')}", "INFO")
                self.log(f"  Remaining: {headers.get('X-RateLimit-Remaining')}", "INFO")
                self.security_tests.append({
                    "name": "Headers rate limiting",
                    "success": True,
                    "headers": {
                        "limit": headers.get('X-RateLimit-Limit'),
                        "remaining": headers.get('X-RateLimit-Remaining')
                    }
                })
            else:
                self.log("⚠ Headers rate limiting manquants", "WARNING")
        except Exception as e:
            self.log(f"✗ Erreur test rate limiting: {e}", "ERROR")

        # ========== CORS ==========
        self.log("\n### 5. CONFIGURATION CORS ###", "SECURITY")

        try:
            resp = requests.options(
                f"{self.base_url}/api/health",
                headers={"Origin": "https://malicious-site.com"},
                timeout=TIMEOUT
            )

            cors_header = resp.headers.get("Access-Control-Allow-Origin")

            if cors_header and cors_header != "*":
                self.log(f"✓ CORS configuré (pas de wildcard): {cors_header}", "SUCCESS")
                self.security_tests.append({
                    "name": "CORS sécurisé",
                    "success": True
                })
            elif not cors_header:
                self.log("✓ CORS restrictif (pas de header)", "SUCCESS")
                self.security_tests.append({
                    "name": "CORS restrictif",
                    "success": True
                })
            elif cors_header == "*":
                self.log("✗ DANGEREUX: CORS wildcard *", "ERROR")
                self.security_tests.append({
                    "name": "CORS wildcard",
                    "success": False
                })
        except Exception as e:
            self.log(f"Erreur test CORS: {e}", "WARNING")

    def run_performance_tests(self):
        """Tests de performance"""
        self.log("\n" + "="*80, "PERF")
        self.log("PARTIE 3: TESTS DE PERFORMANCE", "PERF")
        self.log("="*80, "PERF")

        # ========== TEMPS DE RÉPONSE ==========
        self.log("\n### 1. TEMPS DE RÉPONSE ###", "PERF")

        endpoints = [
            ("Health Check", "GET", "/api/health", False),
            ("Liste formulaires", "GET", "/api/forms", True),
        ]

        for name, method, endpoint, auth in endpoints:
            times = []
            for i in range(5):
                start = time.time()
                try:
                    headers = {"Content-Type": "application/json"}
                    if auth and self.token:
                        headers["Authentication-Token"] = self.token

                    resp = requests.get(f"{self.base_url}{endpoint}", headers=headers, timeout=TIMEOUT)
                    elapsed = time.time() - start
                    times.append(elapsed)
                except:
                    pass

            if times:
                avg = sum(times) / len(times)
                self.log(f"{name}: {avg:.3f}s (moyenne sur {len(times)} requêtes)", "PERF")
                self.performance_tests.append({
                    "name": name,
                    "avg_time": avg,
                    "times": times
                })

        # ========== STABILITÉ ==========
        self.log("\n### 2. STABILITÉ (10 requêtes rapides) ###", "PERF")

        success_count = 0
        error_count = 0

        for i in range(10):
            try:
                resp = requests.get(f"{self.base_url}/api/health", timeout=TIMEOUT)
                if resp.status_code == 200:
                    success_count += 1
                else:
                    error_count += 1
            except:
                error_count += 1
            time.sleep(0.1)

        stability = (success_count / 10) * 100
        self.log(f"Stabilité: {stability}% ({success_count}/10 succès)", "PERF")
        self.performance_tests.append({
            "name": "Stabilité",
            "success_rate": stability,
            "successes": success_count,
            "errors": error_count
        })

    def generate_report(self):
        """Générer rapport final"""
        self.log("\n" + "="*80, "INFO")
        self.log("RAPPORT FINAL COMPLET", "INFO")
        self.log("="*80, "INFO")

        total_time = time.time() - self.start_time

        # Fonctionnel
        func_total = len(self.functional_tests)
        func_success = sum(1 for t in self.functional_tests if t.get("success"))

        # Sécurité
        sec_total = len(self.security_tests)
        sec_success = sum(1 for t in self.security_tests if t.get("success"))

        # Total
        total = func_total + sec_total
        success = func_success + sec_success

        self.log(f"\n📊 RÉSULTATS GLOBAUX", "INFO")
        self.log(f"Tests fonctionnels: {func_success}/{func_total} ({func_success/func_total*100:.1f}%)",
                "SUCCESS" if func_success == func_total else "WARNING")
        self.log(f"Tests sécurité: {sec_success}/{sec_total} ({sec_success/sec_total*100:.1f}%)",
                "SUCCESS" if sec_success == sec_total else "WARNING")
        self.log(f"TOTAL: {success}/{total} ({success/total*100:.1f}%)",
                "SUCCESS" if success == total else "WARNING")
        self.log(f"Temps total: {total_time:.2f}s", "INFO")

        # Performance
        if self.performance_tests:
            times = [t.get("avg_time", 0) for t in self.performance_tests if "avg_time" in t]
            if times:
                self.log(f"\n⚡ PERFORMANCE", "PERF")
                self.log(f"Temps moyen: {sum(times)/len(times):.3f}s", "PERF")

        # Verdict
        self.log("\n" + "="*80, "INFO")
        if success == total:
            self.log("✅ VERDICT: API COMPLÈTEMENT FONCTIONNELLE ET SÉCURISÉE", "SUCCESS")
        elif success / total >= 0.9:
            self.log("✅ VERDICT: API MAJORITAIREMENT FONCTIONNELLE", "SUCCESS")
        elif success / total >= 0.7:
            self.log("⚠️ VERDICT: API FONCTIONNELLE AVEC PROBLÈMES MINEURS", "WARNING")
        else:
            self.log("❌ VERDICT: PROBLÈMES IMPORTANTS DÉTECTÉS", "ERROR")
        self.log("="*80, "INFO")

        # Sauvegarder rapport
        report = {
            "timestamp": datetime.now().isoformat(),
            "url": self.base_url,
            "total_time": total_time,
            "functional": {
                "total": func_total,
                "success": func_success,
                "rate": func_success/func_total*100
            },
            "security": {
                "total": sec_total,
                "success": sec_success,
                "rate": sec_success/sec_total*100
            },
            "results": {
                "functional": self.functional_tests,
                "security": self.security_tests,
                "performance": self.performance_tests
            }
        }

        filename = f"test_report_complete_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        self.log(f"\nRapport sauvegardé: {filename}", "INFO")

if __name__ == "__main__":
    tester = ComprehensiveAPITester(API_BASE_URL)

    tester.run_functional_tests()
    tester.run_security_tests()
    tester.run_performance_tests()
    tester.generate_report()
