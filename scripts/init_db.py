"""
Script d'initialisation de la base de données
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import DatabaseManager


def init_database():
    """Initialiser la base de données"""
    print("🗄️ Initialisation de la base de données FormForge...")

    # Créer l'application
    app = create_app()

    with app.app_context():
        # Initialiser la base de données
        db_manager = DatabaseManager()
        db_manager.init_database()

        print("✅ Base de données initialisée avec succès!")
        print("📋 Tables créées:")
        print("   - forms")
        print("   - questions")
        print("   - responses")
        print("   - Index de performance")


if __name__ == "__main__":
    init_database()
