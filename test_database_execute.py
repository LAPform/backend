#!/usr/bin/env python3
"""
Test de la méthode execute_query du DatabaseManager
"""

import sqlite3
import json
import uuid
import os
import sys

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager


def test_database_execute():
    """Test de la méthode execute_query"""
    print("Test de la méthode execute_query")
    print("=" * 40)

    # Initialiser le DatabaseManager
    print("1. Initialisation du DatabaseManager")
    try:
        db_manager = DatabaseManager()
        print(f"   Database URL: {db_manager.database_url}")
        print(f"   Database Path: {db_manager.db_path}")

        # Initialiser la base de données
        print("\n2. Initialisation de la base de données")
        db_manager.init_database()
        print("   [OK] Base de données initialisée")

        # Test d'insertion simple
        print("\n3. Test d'insertion simple")
        question_id = str(uuid.uuid4())
        form_id = "test-form-id"

        query = """
            INSERT INTO questions (id, form_id, type, text, options, required, validation, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = (
            question_id,
            form_id,
            "text",
            "Test question",
            json.dumps([]),
            False,
            json.dumps({}),
            0,
        )

        try:
            result = db_manager.execute_query(query, params)
            print(f"   [OK] Insertion réussie - Row count: {result}")
        except Exception as e:
            print(f"   [ERROR] Erreur insertion: {e}")
            import traceback

            traceback.print_exc()
            return

        # Vérifier l'insertion
        print("\n4. Vérification de l'insertion")
        try:
            select_query = "SELECT * FROM questions WHERE id = ?"
            results = db_manager.execute_query(select_query, (question_id,), fetch=True)
            if results and len(results) > 0:
                print("   [OK] Question trouvée en base")
                question_data = results[0]
                print(f"   ID: {question_data.get('id')}")
                print(f"   Form ID: {question_data.get('form_id')}")
                print(f"   Type: {question_data.get('type')}")
                print(f"   Text: {question_data.get('text')}")
                print(f"   Options: {question_data.get('options')}")
                print(f"   Required: {question_data.get('required')}")
                print(f"   Validation: {question_data.get('validation')}")
                print(f"   Order Index: {question_data.get('order_index')}")
            else:
                print("   [ERROR] Question non trouvée")
        except Exception as e:
            print(f"   [ERROR] Erreur vérification: {e}")
            import traceback

            traceback.print_exc()
            return

        # Nettoyer
        print("\n5. Nettoyage")
        try:
            delete_query = "DELETE FROM questions WHERE id = ?"
            db_manager.execute_query(delete_query, (question_id,))
            print("   [OK] Nettoyage effectué")
        except Exception as e:
            print(f"   [ERROR] Erreur nettoyage: {e}")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_database_execute()
