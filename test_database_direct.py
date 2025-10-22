#!/usr/bin/env python3
"""
Test direct de la base de données pour isoler le problème
"""

import sqlite3
import json
import uuid
import os


def test_database_direct():
    """Test direct de la base de données"""
    print("Test direct de la base de données")
    print("=" * 40)

    # Connexion à la base de données
    db_path = "formforge_poc.db"
    print(f"1. Connexion à la base: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("   [OK] Connexion réussie")

        # Vérifier la structure de la table questions
        print("\n2. Vérification de la structure de la table questions")
        cursor.execute("PRAGMA table_info(questions)")
        columns = cursor.fetchall()
        print(f"   Colonnes: {[col[1] for col in columns]}")

        # Vérifier les contraintes
        print("\n3. Vérification des contraintes")
        cursor.execute("PRAGMA foreign_key_list(questions)")
        fk_constraints = cursor.fetchall()
        print(f"   Contraintes FK: {fk_constraints}")

        # Test d'insertion directe
        print("\n4. Test d'insertion directe")
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
            "Test question directe",
            json.dumps([]),
            False,
            json.dumps({}),
            0,
        )

        cursor.execute(query, params)
        conn.commit()
        print("   [OK] Insertion réussie")

        # Vérifier l'insertion
        print("\n5. Vérification de l'insertion")
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        result = cursor.fetchone()
        if result:
            print("   [OK] Question trouvée en base")
            print(f"   ID: {result[0]}")
            print(f"   Form ID: {result[1]}")
            print(f"   Type: {result[2]}")
            print(f"   Text: {result[3]}")
        else:
            print("   [ERROR] Question non trouvée")

        # Nettoyer
        cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        print("\n6. Nettoyage effectué")

    except Exception as e:
        print(f"   [ERROR] Exception: {e}")
        import traceback

        traceback.print_exc()
    finally:
        if "conn" in locals():
            conn.close()
            print("   Connexion fermée")


if __name__ == "__main__":
    test_database_direct()
