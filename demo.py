"""
Script de démonstration FormForge POC
"""

import requests
import json
import time

API_BASE = "http://localhost:5000/api"


def demo_complete_workflow():
    """Démonstration complète du workflow FormForge"""

    print("🎯 Démonstration FormForge POC - Workflow Complet")
    print("=" * 60)

    # 1. Vérifier la santé de l'API
    print("1️⃣ Vérification de l'API...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ API accessible")
        else:
            print("❌ API non accessible")
            return
    except:
        print("❌ Impossible de se connecter à l'API")
        print("💡 Assurez-vous que le serveur est démarré avec: python run_dev.py")
        return

    # 2. Créer un formulaire
    print("\n2️⃣ Création d'un formulaire...")
    form_data = {
        "title": "Formulaire de Démonstration",
        "description": "Ce formulaire démontre les capacités de FormForge",
        "settings": {"theme": "modern", "allow_multiple_responses": True},
    }

    response = requests.post(f"{API_BASE}/forms", json=form_data)
    if response.status_code == 201:
        form_id = response.json()["form_id"]
        print(f"✅ Formulaire créé: {form_id}")
    else:
        print(f"❌ Erreur création formulaire: {response.text}")
        return

    # 3. Ajouter des questions
    print("\n3️⃣ Ajout de questions...")

    questions = [
        {
            "type": "text",
            "text": "Quel est votre nom complet ?",
            "required": True,
            "validation": {"min_length": 2, "max_length": 100},
        },
        {"type": "email", "text": "Votre adresse email", "required": True},
        {
            "type": "multiple",
            "text": "Quel est votre niveau d'expérience ?",
            "options": ["Débutant", "Intermédiaire", "Avancé", "Expert"],
            "required": True,
        },
        {
            "type": "checkbox",
            "text": "Quels sont vos centres d'intérêt ? (plusieurs choix possibles)",
            "options": ["Développement", "Design", "Marketing", "Ventes", "Support"],
            "required": False,
        },
        {
            "type": "scale",
            "text": "Évaluez votre satisfaction (1 = Très insatisfait, 5 = Très satisfait)",
            "options": ["1", "2", "3", "4", "5"],
            "required": True,
        },
        {
            "type": "textarea",
            "text": "Décrivez votre expérience avec FormForge",
            "required": False,
            "validation": {"max_length": 500},
        },
    ]

    question_ids = []
    for i, question in enumerate(questions):
        response = requests.post(
            f"{API_BASE}/forms/{form_id}/questions", json={**question, "order_index": i}
        )

        if response.status_code == 201:
            question_id = response.json()["question_id"]
            question_ids.append(question_id)
            print(f"✅ Question {i+1} créée: {question['text'][:50]}...")
        else:
            print(f"❌ Erreur création question {i+1}: {response.text}")

    # 4. Récupérer le formulaire complet
    print("\n4️⃣ Récupération du formulaire...")
    response = requests.get(f"{API_BASE}/forms/{form_id}")
    if response.status_code == 200:
        form = response.json()["form"]
        print(f"✅ Formulaire récupéré: {len(form.get('questions', []))} questions")
    else:
        print(f"❌ Erreur récupération formulaire: {response.text}")

    # 5. Simuler des réponses
    print("\n5️⃣ Simulation de réponses...")

    sample_responses = [
        {
            "answers": {
                question_ids[0]: "Jean Dupont",
                question_ids[1]: "jean.dupont@example.com",
                question_ids[2]: "Intermédiaire",
                question_ids[3]: ["Développement", "Design"],
                question_ids[4]: "4",
                question_ids[
                    5
                ]: "FormForge est un excellent outil pour créer des formulaires rapidement.",
            }
        },
        {
            "answers": {
                question_ids[0]: "Marie Martin",
                question_ids[1]: "marie.martin@example.com",
                question_ids[2]: "Avancé",
                question_ids[3]: ["Marketing", "Ventes"],
                question_ids[4]: "5",
                question_ids[5]: "Interface intuitive et fonctionnalités complètes.",
            }
        },
    ]

    for i, response_data in enumerate(sample_responses):
        response = requests.post(
            f"{API_BASE}/forms/{form_id}/responses", json=response_data
        )

        if response.status_code == 201:
            print(f"✅ Réponse {i+1} soumise avec succès")
        else:
            print(f"❌ Erreur soumission réponse {i+1}: {response.text}")

    # 6. Récupérer les statistiques
    print("\n6️⃣ Récupération des statistiques...")
    response = requests.get(f"{API_BASE}/forms/{form_id}/stats")
    if response.status_code == 200:
        stats = response.json()["stats"]
        print(
            f"✅ Statistiques: {stats['total_questions']} questions, {stats['total_responses']} réponses"
        )
    else:
        print(f"❌ Erreur récupération statistiques: {response.text}")

    # 7. Export CSV
    print("\n7️⃣ Export des données...")
    response = requests.get(f"{API_BASE}/forms/{form_id}/export/csv")
    if response.status_code == 200:
        csv_data = response.json()
        print(f"✅ Export CSV réussi: {csv_data['filename']}")
        print(f"📊 Contenu CSV (premiers 200 caractères):")
        print(csv_data["csv_content"][:200] + "...")
    else:
        print(f"❌ Erreur export CSV: {response.text}")

    # 8. Analytics
    print("\n8️⃣ Analytics avancées...")
    response = requests.get(f"{API_BASE}/forms/{form_id}/analytics")
    if response.status_code == 200:
        analytics = response.json()["analytics"]
        print(
            f"✅ Analytics récupérées: {analytics['total_responses']} réponses totales"
        )
    else:
        print(f"❌ Erreur analytics: {response.text}")

    print("\n" + "=" * 60)
    print("🎉 Démonstration terminée avec succès!")
    print(f"📋 Formulaire de démonstration: {form_id}")
    print(f"🔗 URL API: {API_BASE}/forms/{form_id}")
    print("💡 Vous pouvez maintenant tester l'API avec d'autres outils comme Postman")


if __name__ == "__main__":
    demo_complete_workflow()
