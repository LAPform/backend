#!/usr/bin/env python3
"""
Test complet de l'API FormForge en production
Expert en développement d'API avec 15+ ans d'expérience
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
    BOLD = '\033[1m'
    END = '\033[0m'

class APITester:
    """Testeur API professionnel"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.form_id = None
        self.question_id = None
        self.response_id = None
        self.public_token = None
        self.test_results = []
        self.start_time = time.time()

    def log(self, message, level="INFO"):
        """Logger avec couleurs"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": Colors.BLUE,
            "SUCCESS": Colors.GREEN,
            "ERROR": Colors.RED,
            "WARNING": Colors.YELLOW
        }
        color = colors.get(level, Colors.BLUE)
        print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")

    def test_endpoint(self, name, method, endpoint, data=None, headers=None, expected_status=200, auth_required=True):
        """Tester un endpoint avec validation complète"""
        self.log(f"Testing: {name}", "INFO")

        url = f"{self.base_url}{endpoint}"

        # Préparer les headers
        if headers is None:
            headers = {"Content-Type": "application/json"}

        # Ajouter le token d'authentification si nécessaire
        if auth_required and self.token:
            headers["Authentication-Token"] = self.token
            headers["Authorization"] = f"Bearer {self.token}"

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
                response_data = {"raw": response.text}

            # Enregistrer le résultat
            result = {
                "name": name,
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "success": status_ok,
                "response_time": response.elapsed.total_seconds(),
                "response_data": response_data
            }

            self.test_results.append(result)

            if status_ok:
                self.log(f"✓ {name} - Status: {response.status_code} - Time: {response.elapsed.total_seconds():.2f}s", "SUCCESS")
            else:
                self.log(f"✗ {name} - Expected: {expected_status}, Got: {response.status_code}", "ERROR")
                self.log(f"Response: {json.dumps(response_data, indent=2)}", "ERROR")

            return response, response_data

        except requests.exceptions.Timeout:
            self.log(f"✗ {name} - TIMEOUT après {TIMEOUT}s", "ERROR")
            self.test_results.append({
                "name": name,
                "success": False,
                "error": "TIMEOUT"
            })
            return None, None
        except Exception as e:
            self.log(f"✗ {name} - Erreur: {str(e)}", "ERROR")
            self.test_results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
            return None, None

    def run_tests(self):
        """Exécuter tous les tests"""
        self.log("=" * 80, "INFO")
        self.log("DÉMARRAGE DES TESTS DE L'API FORMFORGE", "INFO")
        self.log(f"URL de base: {self.base_url}", "INFO")
        self.log("=" * 80, "INFO")

        # Test 1: Health Check
        self.log("\n### TEST 1: HEALTH CHECK ###", "INFO")
        self.test_endpoint(
            "Health Check",
            "GET",
            "/api/health",
            auth_required=False
        )

        # Test 2: Inscription
        self.log("\n### TEST 2: AUTHENTIFICATION ###", "INFO")
        timestamp = int(time.time())
        email = f"expert_test_{timestamp}@test.com"
        password = "Test123!@#"

        response, data = self.test_endpoint(
            "Inscription (signup)",
            "POST",
            "/api/auth/signup",
            data={
                "email": email,
                "password": password,
                "name": "Expert Tester"
            },
            expected_status=201,
            auth_required=False
        )

        if data and data.get("success"):
            self.token = data.get("authentication_token")
            self.user_id = data.get("user", {}).get("id")
            self.log(f"Token obtenu: {self.token[:20]}...", "SUCCESS")
            self.log(f"User ID: {self.user_id}", "SUCCESS")
        else:
            self.log("Échec de l'inscription, tentative de connexion...", "WARNING")

            # Tenter la connexion
            response, data = self.test_endpoint(
                "Connexion (signin)",
                "POST",
                "/api/auth/signin",
                data={
                    "email": email,
                    "password": password
                },
                expected_status=200,
                auth_required=False
            )

            if data and data.get("success"):
                self.token = data.get("authentication_token")
                self.user_id = data.get("user", {}).get("id")
                self.log(f"Token obtenu via connexion: {self.token[:20]}...", "SUCCESS")

        if not self.token:
            self.log("ERREUR CRITIQUE: Impossible d'obtenir un token d'authentification", "ERROR")
            return

        # Test 3: Vérifier l'utilisateur actuel
        self.test_endpoint(
            "Obtenir utilisateur actuel",
            "GET",
            "/api/auth/me"
        )

        # Test 4: Créer un formulaire
        self.log("\n### TEST 3: GESTION DES FORMULAIRES ###", "INFO")
        response, data = self.test_endpoint(
            "Créer un formulaire",
            "POST",
            "/api/forms",
            data={
                "title": "Formulaire de test expert",
                "description": "Test complet de l'API",
                "settings": {
                    "theme": "blue",
                    "public": True
                }
            },
            expected_status=201
        )

        if data and data.get("success"):
            self.form_id = data.get("data", {}).get("form_id")
            self.log(f"Formulaire créé: {self.form_id}", "SUCCESS")

        # Test 5: Lister les formulaires
        self.test_endpoint(
            "Lister les formulaires",
            "GET",
            "/api/forms"
        )

        # Test 6: Récupérer un formulaire
        if self.form_id:
            self.test_endpoint(
                "Récupérer un formulaire",
                "GET",
                f"/api/forms/{self.form_id}"
            )

        # Test 7: Mettre à jour un formulaire
        if self.form_id:
            self.test_endpoint(
                "Mettre à jour un formulaire",
                "PUT",
                f"/api/forms/{self.form_id}",
                data={
                    "title": "Formulaire de test expert (modifié)",
                    "description": "Description mise à jour"
                }
            )

        # Test 8: Créer des questions
        self.log("\n### TEST 4: GESTION DES QUESTIONS ###", "INFO")
        if self.form_id:
            # Question texte
            response, data = self.test_endpoint(
                "Créer une question texte",
                "POST",
                f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "text",
                    "text": "Quel est votre nom?",
                    "required": True,
                    "order_index": 0
                },
                expected_status=201
            )

            if data and data.get("success"):
                self.question_id = data.get("question_id")
                self.log(f"Question créée: {self.question_id}", "SUCCESS")

            # Question choix multiple
            self.test_endpoint(
                "Créer une question choix multiple",
                "POST",
                f"/api/forms/{self.form_id}/questions",
                data={
                    "type": "choice",
                    "text": "Quelle est votre couleur préférée?",
                    "options": ["Rouge", "Bleu", "Vert", "Jaune"],
                    "required": False,
                    "order_index": 1
                },
                expected_status=201
            )

            # Lister les questions
            self.test_endpoint(
                "Lister les questions",
                "GET",
                f"/api/forms/{self.form_id}/questions"
            )

        # Test 9: Publier le formulaire
        self.log("\n### TEST 5: PUBLICATION ###", "INFO")
        if self.form_id:
            response, data = self.test_endpoint(
                "Publier le formulaire",
                "POST",
                f"/api/forms/{self.form_id}/publish"
            )

            if data and data.get("success"):
                self.public_token = data.get("data", {}).get("public_token")
                self.log(f"Token public: {self.public_token}", "SUCCESS")

            # Obtenir le lien public
            response, data = self.test_endpoint(
                "Obtenir le lien public",
                "GET",
                f"/api/forms/{self.form_id}/public-link"
            )

            if data and data.get("success"):
                public_url = data.get("data", {}).get("public_url")
                self.log(f"URL publique: {public_url}", "SUCCESS")

        # Test 10: Accéder au formulaire public
        if self.public_token:
            self.test_endpoint(
                "Accéder au formulaire public",
                "GET",
                f"/api/public/forms/{self.public_token}",
                auth_required=False
            )

        # Test 11: Soumettre une réponse
        self.log("\n### TEST 6: RÉPONSES ###", "INFO")
        if self.form_id and self.question_id:
            response, data = self.test_endpoint(
                "Soumettre une réponse",
                "POST",
                f"/api/forms/{self.form_id}/responses",
                data={
                    "answers": {
                        self.question_id: "Test Response"
                    }
                },
                expected_status=201
            )

            if data and data.get("success"):
                self.response_id = data.get("response_id")
                self.log(f"Réponse créée: {self.response_id}", "SUCCESS")

        # Test 12: Récupérer les réponses
        if self.form_id:
            self.test_endpoint(
                "Récupérer les réponses",
                "GET",
                f"/api/forms/{self.form_id}/responses"
            )

        # Test 13: Analytics
        if self.form_id:
            self.test_endpoint(
                "Analytics du formulaire",
                "GET",
                f"/api/forms/{self.form_id}/analytics"
            )

        # Test 14: Export CSV
        self.log("\n### TEST 7: EXPORT ###", "INFO")
        if self.form_id:
            self.test_endpoint(
                "Export CSV",
                "GET",
                f"/api/forms/{self.form_id}/export/csv"
            )

            self.test_endpoint(
                "Export Excel",
                "GET",
                f"/api/forms/{self.form_id}/export/excel"
            )

        # Test 15: Statistiques du formulaire
        if self.form_id:
            self.test_endpoint(
                "Statistiques du formulaire",
                "GET",
                f"/api/forms/{self.form_id}/stats"
            )

        # Test 16: Nettoyage (optionnel)
        self.log("\n### TEST 8: NETTOYAGE ###", "INFO")
        if self.question_id:
            self.test_endpoint(
                "Supprimer une question",
                "DELETE",
                f"/api/questions/{self.question_id}"
            )

        # Génération du rapport
        self.generate_report()

    def generate_report(self):
        """Générer le rapport de tests"""
        self.log("\n" + "=" * 80, "INFO")
        self.log("RAPPORT DE TESTS", "INFO")
        self.log("=" * 80, "INFO")

        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.get("success"))
        failed_tests = total_tests - successful_tests

        total_time = time.time() - self.start_time

        self.log(f"\nTests exécutés: {total_tests}", "INFO")
        self.log(f"Tests réussis: {successful_tests} ({successful_tests/total_tests*100:.1f}%)", "SUCCESS")
        self.log(f"Tests échoués: {failed_tests} ({failed_tests/total_tests*100:.1f}%)", "ERROR" if failed_tests > 0 else "INFO")
        self.log(f"Temps total: {total_time:.2f}s", "INFO")

        if failed_tests > 0:
            self.log("\nTests échoués:", "ERROR")
            for result in self.test_results:
                if not result.get("success"):
                    self.log(f"  - {result.get('name')}: {result.get('error', 'Status code mismatch')}", "ERROR")

        # Calculer les temps de réponse
        response_times = [r.get("response_time", 0) for r in self.test_results if "response_time" in r]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            self.log(f"\nTemps de réponse:", "INFO")
            self.log(f"  - Moyen: {avg_response_time:.2f}s", "INFO")
            self.log(f"  - Max: {max_response_time:.2f}s", "INFO")
            self.log(f"  - Min: {min_response_time:.2f}s", "INFO")

        # Verdict final
        self.log("\n" + "=" * 80, "INFO")
        if failed_tests == 0:
            self.log("✓ VERDICT: TOUS LES TESTS RÉUSSIS", "SUCCESS")
            self.log("L'API est opérationnelle et fonctionnelle", "SUCCESS")
        elif failed_tests < total_tests * 0.2:  # Moins de 20% d'échecs
            self.log("⚠ VERDICT: MAJORITAIREMENT FONCTIONNEL", "WARNING")
            self.log(f"Quelques problèmes détectés ({failed_tests} tests échoués)", "WARNING")
        else:
            self.log("✗ VERDICT: PROBLÈMES CRITIQUES DÉTECTÉS", "ERROR")
            self.log(f"Plusieurs tests ont échoué ({failed_tests}/{total_tests})", "ERROR")

        self.log("=" * 80, "INFO")

        # Sauvegarder le rapport JSON
        report_file = f"test_report_{int(time.time())}.json"
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": successful_tests/total_tests*100,
                "total_time": total_time,
                "results": self.test_results
            }, f, indent=2)

        self.log(f"\nRapport détaillé sauvegardé: {report_file}", "INFO")

if __name__ == "__main__":
    tester = APITester(API_BASE_URL)
    tester.run_tests()
