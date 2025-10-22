"""
Script de développement pour FormForge POC
"""

import os
import sys
from app import create_app


def main():
    """Démarrer l'application en mode développement"""

    # Configuration pour le développement
    os.environ.setdefault("FLASK_ENV", "development")
    os.environ.setdefault("SECRET_KEY", "dev-secret-key")

    # Base de données SQLite pour le développement
    if not os.environ.get("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///formforge_dev.db"

    print("🗄️ Base de données: SQLite (compatible Render gratuit)")

    # Créer l'application
    app = create_app()

    # Configuration de développement
    app.config["DEBUG"] = True
    app.config["TESTING"] = False

    print("🚀 Démarrage de FormForge POC en mode développement")
    print(f"📊 Base de données: {os.environ.get('DATABASE_URL', 'SQLite local')}")
    print(f"🌐 URL: http://localhost:5000")
    print(f"📡 API Health: http://localhost:5000/api/health")
    print("=" * 50)

    # Démarrer l'application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)


if __name__ == "__main__":
    main()
