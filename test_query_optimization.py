#!/usr/bin/env python3
"""
Test d'optimisation des requêtes pour FormForge
"""

import requests
import json
import time
from datetime import datetime

api_url = "https://backend-skum.onrender.com"

def test_query_optimization():
    """Test d'optimisation des requêtes"""
    print("Test d'optimisation des requêtes FormForge")
    print("=" * 50)
    
    # 1. Inscription pour obtenir un token
    email = f"optimization_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
    print(f"1. Inscription: {email}")
    
    register_data = {
        "email": email,
        "password": "TestPassword123!",
        "name": "Optimization Test User",
    }
    
    try:
        response = requests.post(
            f"{api_url}/api/auth/register", json=register_data, timeout=15
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            token = response.json()["token"]
            print(f"   Token: {token[:20]}...")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Test de création de formulaires multiples
            print("\n2. Test création de formulaires multiples")
            form_ids = []
            start_time = time.time()
            
            for i in range(5):
                form_data = {
                    "title": f"Test Form {i+1}",
                    "description": f"Formulaire de test d'optimisation {i+1}",
                }
                
                form_response = requests.post(
                    f"{api_url}/api/forms", json=form_data, headers=headers, timeout=15
                )
                
                if form_response.status_code == 201:
                    form_id = form_response.json()["data"]["form_id"]
                    form_ids.append(form_id)
                    print(f"   Form {i+1}: {form_id[:8]}...")
                else:
                    print(f"   [ERROR] Form {i+1}: {form_response.text}")
            
            forms_creation_time = time.time() - start_time
            print(f"   Temps création 5 formulaires: {forms_creation_time:.2f}s")
            
            # 3. Test de création de questions multiples
            print("\n3. Test création de questions multiples")
            if form_ids:
                form_id = form_ids[0]
                start_time = time.time()
                
                for i in range(10):
                    question_data = {
                        "type": "text",
                        "text": f"Question de test {i+1}",
                        "order_index": i
                    }
                    
                    question_response = requests.post(
                        f"{api_url}/api/forms/{form_id}/questions",
                        json=question_data,
                        headers=headers,
                        timeout=15,
                    )
                    
                    if question_response.status_code == 201:
                        print(f"   Question {i+1}: OK")
                    else:
                        print(f"   [ERROR] Question {i+1}: {question_response.text}")
                
                questions_creation_time = time.time() - start_time
                print(f"   Temps création 10 questions: {questions_creation_time:.2f}s")
            
            # 4. Test de récupération de formulaires avec questions
            print("\n4. Test récupération formulaires avec questions")
            start_time = time.time()
            
            for form_id in form_ids:
                form_response = requests.get(
                    f"{api_url}/api/forms/{form_id}", headers=headers, timeout=15
                )
                
                if form_response.status_code == 200:
                    form_data = form_response.json()["form"]
                    questions_count = len(form_data.get("questions", []))
                    print(f"   Form {form_id[:8]}...: {questions_count} questions")
                else:
                    print(f"   [ERROR] Form {form_id[:8]}...: {form_response.text}")
            
            forms_retrieval_time = time.time() - start_time
            print(f"   Temps récupération formulaires: {forms_retrieval_time:.2f}s")
            
            # 5. Test des statistiques de performance
            print("\n5. Test statistiques de performance")
            try:
                perf_response = requests.get(
                    f"{api_url}/api/monitoring/performance", headers=headers, timeout=15
                )
                print(f"   Status: {perf_response.status_code}")
                
                if perf_response.status_code == 200:
                    perf_data = perf_response.json()
                    db_stats = perf_data.get("database_stats", {})
                    print(f"   Requêtes totales: {db_stats.get('total_queries', 0)}")
                    print(f"   Temps moyen: {db_stats.get('average_time', 0):.3f}s")
                    print(f"   Requêtes lentes: {db_stats.get('slow_queries', 0)}")
                    print(f"   Taux requêtes lentes: {db_stats.get('slow_query_rate', 0):.1%}")
                else:
                    print(f"   [ERROR] Performance stats: {perf_response.text}")
            except Exception as e:
                print(f"   [ERROR] Performance stats: {e}")
            
            # 6. Test health check
            print("\n6. Test health check")
            try:
                health_response = requests.get(
                    f"{api_url}/api/monitoring/health", timeout=15
                )
                print(f"   Status: {health_response.status_code}")
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    health_status = health_data.get("health", {})
                    print(f"   Statut global: {health_status.get('overall', 'unknown')}")
                    print(f"   Base de données: {health_status.get('database', 'unknown')}")
                else:
                    print(f"   [ERROR] Health check: {health_response.text}")
            except Exception as e:
                print(f"   [ERROR] Health check: {e}")
            
            # 7. Test de soumission de réponses
            print("\n7. Test soumission de réponses")
            if form_ids:
                form_id = form_ids[0]
                start_time = time.time()
                
                for i in range(5):
                    response_data = {
                        "answers": {f"question_{j}": f"Réponse {i+1}-{j}" for j in range(10)},
                        "user_id": f"test_user_{i}"
                    }
                    
                    submit_response = requests.post(
                        f"{api_url}/api/forms/{form_id}/responses",
                        json=response_data,
                        timeout=15,
                    )
                    
                    if submit_response.status_code == 201:
                        print(f"   Réponse {i+1}: OK")
                    else:
                        print(f"   [ERROR] Réponse {i+1}: {submit_response.text}")
                
                responses_submission_time = time.time() - start_time
                print(f"   Temps soumission 5 réponses: {responses_submission_time:.2f}s")
            
            print("\n" + "=" * 50)
            print("Test d'optimisation terminé")
            print("Vérifiez les logs Render pour voir les métriques de performance")
            
        else:
            print(f"   [ERROR] Erreur inscription: {response.text}")
            
    except Exception as e:
        print(f"   [ERROR] Exception: {e}")

if __name__ == "__main__":
    test_query_optimization()
