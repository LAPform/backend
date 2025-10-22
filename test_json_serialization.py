#!/usr/bin/env python3
"""
Test de la sérialisation JSON pour isoler le problème
"""

import json
import uuid


def test_json_serialization():
    """Test de la sérialisation JSON"""
    print("Test de la sérialisation JSON")
    print("=" * 40)

    # Test des données qui sont sérialisées dans la méthode create
    question_id = str(uuid.uuid4())
    form_id = "test-form-id"
    question_type = "text"
    text = "Test question"
    options = []
    required = False
    validation = {}
    order_index = 0

    print(f"1. Données de test:")
    print(f"   question_id: {question_id}")
    print(f"   form_id: {form_id}")
    print(f"   type: {question_type}")
    print(f"   text: {text}")
    print(f"   options: {options}")
    print(f"   required: {required}")
    print(f"   validation: {validation}")
    print(f"   order_index: {order_index}")

    # Test de sérialisation JSON
    print("\n2. Test de sérialisation JSON:")
    try:
        options_json = json.dumps(options)
        print(f"   options JSON: {options_json}")

        validation_json = json.dumps(validation)
        print(f"   validation JSON: {validation_json}")

        print("   [OK] Sérialisation JSON réussie")
    except Exception as e:
        print(f"   [ERROR] Erreur sérialisation JSON: {e}")
        return

    # Test de désérialisation JSON
    print("\n3. Test de désérialisation JSON:")
    try:
        options_deserialized = json.loads(options_json)
        print(f"   options désérialisées: {options_deserialized}")

        validation_deserialized = json.loads(validation_json)
        print(f"   validation désérialisée: {validation_deserialized}")

        print("   [OK] Désérialisation JSON réussie")
    except Exception as e:
        print(f"   [ERROR] Erreur désérialisation JSON: {e}")
        return

    # Test avec des données plus complexes
    print("\n4. Test avec des données plus complexes:")
    complex_options = ["Option 1", "Option 2", "Option 3"]
    complex_validation = {
        "min_length": 5,
        "max_length": 100,
        "pattern": "^[a-zA-Z0-9]+$",
    }

    try:
        complex_options_json = json.dumps(complex_options)
        print(f"   options complexes JSON: {complex_options_json}")

        complex_validation_json = json.dumps(complex_validation)
        print(f"   validation complexe JSON: {complex_validation_json}")

        print("   [OK] Sérialisation complexe réussie")
    except Exception as e:
        print(f"   [ERROR] Erreur sérialisation complexe: {e}")
        return

    print("\n5. Test de la requête SQL simulée:")
    query = """
        INSERT INTO questions (id, form_id, type, text, options, required, validation, order_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    params = (
        question_id,
        form_id,
        question_type,
        text,
        options_json,
        required,
        validation_json,
        order_index,
    )

    print(f"   Query: {query.strip()}")
    print(f"   Params: {params}")
    print("   [OK] Requête SQL simulée correcte")


if __name__ == "__main__":
    test_json_serialization()
