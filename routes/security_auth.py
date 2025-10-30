"""
Routes d'authentification avec Flask-Security-Too
"""

from flask import Blueprint, request, jsonify, current_app
from flask_security import current_user, login_user, logout_user

from utils.security_auth import SecurityAuthManager, require_auth
from utils.rate_limiter import rate_limit
from utils.structured_logger import api_logger
from utils.security_validators import escape_html, create_safe_response
from utils.audit_logger import audit_auth, audit_logger
import logging

logger = logging.getLogger(__name__)

security_auth_bp = Blueprint("security_auth", __name__)


@security_auth_bp.route("/auth/test", methods=["GET"])
def test_auth():
    """Endpoint de test simple pour l'authentification"""
    return jsonify(
        {
            "success": True,
            "message": "Endpoint d'authentification accessible",
            "timestamp": "2024-01-15T10:30:00Z",
        }
    )


@security_auth_bp.route("/auth/test-register", methods=["POST"])
def test_register():
    """Endpoint de test d'inscription simplifié"""
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Test simple de validation
        if "@" not in email:
            return jsonify({"error": "Email invalide"}), 400

        if len(password) < 6:
            return jsonify({"error": "Mot de passe trop court"}), 400

        # Test de création d'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        # Vérifier si l'utilisateur existe
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"error": "Utilisateur déjà existant"}), 409

        # Créer l'utilisateur
        user = datastore.create_user(email=email, password=password, name=name)

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user": {"id": user.id, "email": user.email, "name": user.name},
                }
            ),
            201,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test inscription: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/test-login", methods=["POST"])
def test_login():
    """Endpoint de test de connexion simplifié"""
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]

        # Vérifier l'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        user = datastore.find_user(email=email)

        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 401

        # Vérifier le mot de passe
        if not datastore.verify_password(user, password):
            return jsonify({"error": "Mot de passe incorrect"}), 401

        # Connexion réussie
        return (
            jsonify(
                {
                    "success": True,
                    "message": "Connexion réussie",
                    "user": {"id": user.id, "email": user.email, "name": user.name},
                }
            ),
            200,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test connexion: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/signup", methods=["POST"])
@rate_limit("auth_signup")
@audit_auth("signup")
def signup():
    """Créer un nouveau compte utilisateur - Endpoint principal fonctionnel"""
    try:
        data = request.get_json()

        if not data or "email" not in data or "password" not in data:
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        name = data.get("name", "")

        # Test simple de validation
        if "@" not in email:
            return jsonify({"error": "Email invalide"}), 400

        if len(password) < 6:
            return jsonify({"error": "Mot de passe trop court"}), 400

        # Test de création d'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        # Vérifier si l'utilisateur existe
        existing_user = datastore.find_user(email=email)
        if existing_user:
            return jsonify({"error": "Utilisateur déjà existant"}), 409

        # Créer l'utilisateur
        user = datastore.create_user(email=email, password=password, name=name)

        # Créer une réponse sécurisée en échappant les données utilisateur
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(user.name),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Utilisateur créé avec succès",
                    "user": user_data,
                }
            ),
            201,
        )

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Erreur test inscription: {e}")
        return jsonify({"error": f"Erreur: {str(e)}"}), 500


@security_auth_bp.route("/auth/signin", methods=["POST"])
@rate_limit("auth_signin")
@audit_auth("signin")
def signin():
    """Connexion utilisateur - Version simplifiée sans Flask-Security-Too"""
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"🔍 LOGIN: Début processus de connexion")
        data = request.get_json()
        logger.info(f"🔍 LOGIN: Données reçues: {data}")

        if not data or "email" not in data or "password" not in data:
            logger.warning(f"🔍 LOGIN: Données manquantes - email ou password")
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        logger.info(
            f"🔍 LOGIN: Email: {email}, Password: {'*' * len(password) if password else 'None'}"
        )

        # Vérifier l'utilisateur
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        logger.info(f"🔍 LOGIN: SecurityUserDatastore initialisé")

        logger.info(f"🔍 LOGIN: Recherche utilisateur par email: {email}")
        user = datastore.find_user(email=email)
        logger.info(f"🔍 LOGIN: Utilisateur trouvé: {user is not None}")

        if not user:
            logger.warning(f"🔍 LOGIN: Utilisateur non trouvé pour email: {email}")
            return jsonify({"error": "Utilisateur non trouvé"}), 401

        # Vérifier le mot de passe
        logger.info(f"🔍 LOGIN: Vérification mot de passe pour user_id: {user.id}")
        password_valid = datastore.verify_password(user, password)
        logger.info(f"🔍 LOGIN: Mot de passe valide: {password_valid}")

        if not password_valid:
            logger.warning(f"🔍 LOGIN: Mot de passe incorrect pour user_id: {user.id}")
            return jsonify({"error": "Mot de passe incorrect"}), 401

        # Créer un token aléatoire sécurisé (64 hex) avec rotation
        import secrets
        import time
        from datetime import datetime, timedelta

        logger.info(f"🔍 LOGIN: Début génération token pour user_id: {user.id}")

        # Générer un token aléatoire de 32 octets (64 caractères hex)
        sha256_token = secrets.token_hex(32)
        logger.info(
            f"🔍 LOGIN: Token généré: {sha256_token[:10]}...{sha256_token[-10:]}"
        )

        # Calculer l'expiration (1 heure)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        logger.info(f"🔍 LOGIN: Expiration calculée: {expires_at.isoformat()}")

        # Stocker le token en base de données
        from models.database import DatabaseManager

        db = DatabaseManager()
        logger.info(f"🔍 LOGIN: DatabaseManager initialisé")

        # S'assurer que la table active_tokens existe
        try:
            db.execute_query("SELECT COUNT(*) FROM active_tokens LIMIT 1", fetch=True)
            logger.info(f"🔍 LOGIN: Table active_tokens existe")
        except Exception as table_error:
            # Table n'existe pas, la créer
            logger.info(
                f"🔍 LOGIN: Table active_tokens n'existe pas, création en cours"
            )
            logger.info(f"🔍 LOGIN: Erreur table: {table_error}")
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS active_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """
            )
            logger.info(f"🔍 LOGIN: Table active_tokens créée avec succès")

        # Supprimer les anciens tokens de l'utilisateur
        logger.info(f"🔍 LOGIN: Suppression anciens tokens pour user_id: {user.id}")
        deleted_count = db.execute_query(
            "DELETE FROM active_tokens WHERE user_id = ?", (user.id,)
        )
        logger.info(f"🔍 LOGIN: {deleted_count} anciens tokens supprimés")

        # Insérer le nouveau token
        logger.info(f"🔍 LOGIN: Insertion nouveau token en base")
        db.execute_query(
            """
            INSERT INTO active_tokens (token, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (sha256_token, user.id, expires_at.isoformat()),
        )
        logger.info(f"🔍 LOGIN: Token inséré avec succès en base")

        # Créer une réponse sécurisée en échappant les données utilisateur
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(user.name),
        }

        # Connexion réussie
        logger.info(f"🔍 LOGIN: Connexion réussie pour user_id: {user.id}")
        logger.info(
            f"🔍 LOGIN: Token retourné: {sha256_token[:10]}...{sha256_token[-10:]}"
        )

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Connexion réussie",
                    "user": user_data,
                    "token": sha256_token,
                }
            ),
            200,
        )

    except Exception as e:
        import traceback

        logger.error(f"🔍 LOGIN: Erreur connexion: {e}")
        logger.error(f"🔍 LOGIN: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur connexion: {str(e)}"}), 500


# Endpoints de compatibilité supprimés car non fonctionnels
# Flask-Security-Too intercepte automatiquement ces routes
# Utiliser uniquement /auth/signup et /auth/signin


@security_auth_bp.route("/auth/custom-logout", methods=["POST"])
def logout():
    """Déconnexion utilisateur - Route personnalisée pour éviter le conflit avec Flask-Security-Too"""
    try:
        from models.database import DatabaseManager

        # Récupérer le token depuis le header Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            # Supprimer le token de la base de données
            db = DatabaseManager()
            db.execute_query("DELETE FROM active_tokens WHERE token = ?", (token,))

        # Déconnexion simple
        logout_user()
        return jsonify({"success": True, "message": "Déconnexion réussie"}), 200
    except Exception as e:
        logger.error(f"Erreur déconnexion: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500


@security_auth_bp.route("/auth/test-token", methods=["GET"])
def test_token():
    """Tester la validité d'un token"""
    try:
        logger.info(f"🔍 TEST: Début test token")
        from utils.security_auth import require_auth
        from flask import request

        auth_header = request.headers.get("Authorization")
        logger.info(
            f"🔍 TEST: Header Authorization: {auth_header[:20] if auth_header else 'None'}..."
        )

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"🔍 TEST: Header Authorization manquant ou invalide")
            return jsonify({"error": "Token manquant"}), 401

        token = auth_header.split(" ")[1]
        logger.info(f"🔍 TEST: Token extrait: {token[:10]}...{token[-10:]}")

        # Valider le token
        from utils.security_auth import _validate_sha256_token

        logger.info(f"🔍 TEST: Début validation token")
        user_id = _validate_sha256_token(token)
        logger.info(f"🔍 TEST: Résultat validation: user_id = {user_id}")

        if user_id:
            logger.info(f"🔍 TEST: Token valide - user_id: {user_id}")
            return (
                jsonify(
                    {"success": True, "message": "Token valide", "user_id": user_id}
                ),
                200,
            )
        else:
            logger.warning(f"🔍 TEST: Token invalide ou expiré")
            return jsonify({"error": "Token invalide ou expiré"}), 401

    except Exception as e:
        logger.error(f"🔍 TEST: Erreur test token: {e}")
        import traceback

        logger.error(f"🔍 TEST: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur test token: {str(e)}"}), 500


@security_auth_bp.route("/auth/debug-tokens", methods=["GET"])
def debug_tokens():
    """Debug - Vérifier l'état des tokens en base"""
    try:
        logger.info(f"🔍 DEBUG: Début vérification tokens en base")
        from models.database import DatabaseManager

        db = DatabaseManager()

        # Vérifier si la table existe
        try:
            count_result = db.execute_query(
                "SELECT COUNT(*) as count FROM active_tokens", fetch=True
            )
            total_tokens = count_result[0]["count"] if count_result else 0
            logger.info(f"🔍 DEBUG: Nombre total de tokens: {total_tokens}")

            # Récupérer tous les tokens avec leurs infos
            all_tokens = db.execute_query(
                """
                SELECT token, user_id, created_at, expires_at 
                FROM active_tokens 
                ORDER BY created_at DESC
            """,
                fetch=True,
            )

            logger.info(f"🔍 DEBUG: Tokens en base: {all_tokens}")

            return (
                jsonify(
                    {
                        "success": True,
                        "total_tokens": total_tokens,
                        "tokens": all_tokens,
                    }
                ),
                200,
            )

        except Exception as table_error:
            logger.warning(f"🔍 DEBUG: Table active_tokens n'existe pas: {table_error}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Table active_tokens n'existe pas",
                        "details": str(table_error),
                    }
                ),
                404,
            )

    except Exception as e:
        logger.error(f"🔍 DEBUG: Erreur debug tokens: {e}")
        import traceback

        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur debug: {str(e)}"}), 500


@security_auth_bp.route("/auth/debug-connection", methods=["POST"])
def debug_connection():
    """Debug - Tester la connexion étape par étape"""
    try:
        logger.info(f"🔍 DEBUG CONNECTION: Début test connexion")

        # 1. Vérifier les données reçues
        data = request.get_json()
        logger.info(f"🔍 DEBUG CONNECTION: Données reçues: {data}")

        if not data:
            return jsonify({"error": "Aucune donnée JSON"}), 400

        email = data.get("email")
        password = data.get("password")
        logger.info(
            f"🔍 DEBUG CONNECTION: Email: {email}, Password: {'*' * len(password) if password else 'None'}"
        )

        # 2. Tester la connexion à la base
        from models.database import DatabaseManager

        db = DatabaseManager()
        logger.info(f"🔍 DEBUG CONNECTION: DatabaseManager créé")

        # 3. Tester la création de la table
        try:
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS active_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """
            )
            logger.info(f"🔍 DEBUG CONNECTION: Table active_tokens créée/vérifiée")
        except Exception as e:
            logger.error(f"🔍 DEBUG CONNECTION: Erreur création table: {e}")
            return jsonify({"error": f"Erreur table: {e}"}), 500

        # 4. Tester l'insertion d'un token de test
        test_token = "test_token_123456789"
        test_user_id = "test_user_123"
        test_expires = "2025-12-31T23:59:59"

        try:
            db.execute_query(
                """
                INSERT OR REPLACE INTO active_tokens (token, user_id, expires_at)
                VALUES (?, ?, ?)
            """,
                (test_token, test_user_id, test_expires),
            )
            logger.info(f"🔍 DEBUG CONNECTION: Token de test inséré")
        except Exception as e:
            logger.error(f"🔍 DEBUG CONNECTION: Erreur insertion: {e}")
            return jsonify({"error": f"Erreur insertion: {e}"}), 500

        # 5. Tester la récupération du token
        try:
            result = db.execute_query(
                "SELECT * FROM active_tokens WHERE token = ?", (test_token,), fetch=True
            )
            logger.info(f"🔍 DEBUG CONNECTION: Token récupéré: {result}")
        except Exception as e:
            logger.error(f"🔍 DEBUG CONNECTION: Erreur récupération: {e}")
            return jsonify({"error": f"Erreur récupération: {e}"}), 500

        # 6. Nettoyer le token de test
        try:
            db.execute_query("DELETE FROM active_tokens WHERE token = ?", (test_token,))
            logger.info(f"🔍 DEBUG CONNECTION: Token de test supprimé")
        except Exception as e:
            logger.warning(f"🔍 DEBUG CONNECTION: Erreur suppression: {e}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Test de connexion réussi",
                    "steps_completed": [
                        "Données reçues",
                        "DatabaseManager créé",
                        "Table active_tokens créée",
                        "Token de test inséré",
                        "Token de test récupéré",
                        "Token de test supprimé",
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"🔍 DEBUG CONNECTION: Erreur générale: {e}")
        import traceback

        logger.error(f"🔍 DEBUG CONNECTION: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur générale: {str(e)}"}), 500


@security_auth_bp.route("/auth/debug-signin", methods=["POST"])
def debug_signin():
    """Debug - Tester la connexion avec logs détaillés"""
    try:
        logger.info(f"🔍 DEBUG SIGNIN: Début test connexion détaillé")

        # 1. Vérifier les données reçues
        data = request.get_json()
        logger.info(f"🔍 DEBUG SIGNIN: Données reçues: {data}")

        if not data or "email" not in data or "password" not in data:
            logger.warning(f"🔍 DEBUG SIGNIN: Données manquantes")
            return jsonify({"error": "Email et mot de passe requis"}), 400

        email = data["email"].lower().strip()
        password = data["password"]
        logger.info(
            f"🔍 DEBUG SIGNIN: Email: {email}, Password: {'*' * len(password) if password else 'None'}"
        )

        # 2. Tester la recherche d'utilisateur
        from models.security_models import SecurityUserDatastore
        from models.database import DatabaseManager

        db = DatabaseManager()
        logger.info(f"🔍 DEBUG SIGNIN: DatabaseManager créé")

        datastore = SecurityUserDatastore(db)
        logger.info(f"🔍 DEBUG SIGNIN: SecurityUserDatastore créé")

        logger.info(f"🔍 DEBUG SIGNIN: Recherche utilisateur par email: {email}")
        user = datastore.find_user(email=email)
        logger.info(f"🔍 DEBUG SIGNIN: Utilisateur trouvé: {user is not None}")

        if not user:
            logger.warning(f"🔍 DEBUG SIGNIN: Utilisateur non trouvé")
            return jsonify({"error": "Utilisateur non trouvé"}), 401

        # 3. Tester la vérification du mot de passe
        logger.info(
            f"🔍 DEBUG SIGNIN: Vérification mot de passe pour user_id: {user.id}"
        )
        password_valid = datastore.verify_password(user, password)
        logger.info(f"🔍 DEBUG SIGNIN: Mot de passe valide: {password_valid}")

        if not password_valid:
            logger.warning(f"🔍 DEBUG SIGNIN: Mot de passe incorrect")
            return jsonify({"error": "Mot de passe incorrect"}), 401

        # 4. Tester la génération du token aléatoire sécurisé
        import secrets
        import time
        from datetime import datetime, timedelta

        logger.info(f"🔍 DEBUG SIGNIN: Début génération token pour user_id: {user.id}")

        sha256_token = secrets.token_hex(32)
        logger.info(
            f"🔍 DEBUG SIGNIN: Token généré: {sha256_token[:10]}...{sha256_token[-10:]}"
        )

        expires_at = datetime.utcnow() + timedelta(hours=1)
        logger.info(f"🔍 DEBUG SIGNIN: Expiration calculée: {expires_at.isoformat()}")

        # 5. Tester la création de la table
        try:
            db.execute_query("SELECT COUNT(*) FROM active_tokens LIMIT 1", fetch=True)
            logger.info(f"🔍 DEBUG SIGNIN: Table active_tokens existe")
        except Exception as table_error:
            logger.info(
                f"🔍 DEBUG SIGNIN: Table active_tokens n'existe pas, création en cours"
            )
            logger.info(f"🔍 DEBUG SIGNIN: Erreur table: {table_error}")
            db.execute_query(
                """
                CREATE TABLE IF NOT EXISTS active_tokens (
                    token TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """
            )
            logger.info(f"🔍 DEBUG SIGNIN: Table active_tokens créée avec succès")

        # 6. Tester l'insertion du token
        logger.info(
            f"🔍 DEBUG SIGNIN: Suppression anciens tokens pour user_id: {user.id}"
        )
        deleted_count = db.execute_query(
            "DELETE FROM active_tokens WHERE user_id = ?", (user.id,)
        )
        logger.info(f"🔍 DEBUG SIGNIN: {deleted_count} anciens tokens supprimés")

        logger.info(f"🔍 DEBUG SIGNIN: Insertion nouveau token en base")
        db.execute_query(
            """
            INSERT INTO active_tokens (token, user_id, expires_at)
            VALUES (?, ?, ?)
        """,
            (sha256_token, user.id, expires_at.isoformat()),
        )
        logger.info(f"🔍 DEBUG SIGNIN: Token inséré avec succès en base")

        # 7. Vérifier que le token est bien en base
        result = db.execute_query(
            "SELECT * FROM active_tokens WHERE token = ?", (sha256_token,), fetch=True
        )
        logger.info(f"🔍 DEBUG SIGNIN: Token vérifié en base: {result}")

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Test de connexion détaillé réussi",
                    "user_id": user.id,
                    "token": sha256_token,
                    "expires_at": expires_at.isoformat(),
                    "steps_completed": [
                        "Données reçues et validées",
                        "Utilisateur trouvé en base",
                        "Mot de passe vérifié",
                        "Token SHA256 généré",
                        "Table active_tokens créée/vérifiée",
                        "Anciens tokens supprimés",
                        "Nouveau token inséré",
                        "Token vérifié en base",
                    ],
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"🔍 DEBUG SIGNIN: Erreur générale: {e}")
        import traceback

        logger.error(f"🔍 DEBUG SIGNIN: Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Erreur générale: {str(e)}"}), 500


@security_auth_bp.route("/auth/me", methods=["GET"])
@require_auth
def get_current_user(authenticated_user_id=None):
    """Récupérer les informations de l'utilisateur actuel"""
    try:
        logger.info(f"🔍 AUTH ME: Début récupération utilisateur")
        logger.info(f"🔍 AUTH ME: authenticated_user_id: {authenticated_user_id}")

        if not authenticated_user_id:
            logger.warning(f"🔍 AUTH ME: Aucun utilisateur authentifié")
            return jsonify({"error": "Non authentifié"}), 401

        # Récupérer les informations utilisateur depuis la base
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)
        logger.info(f"🔍 AUTH ME: SecurityUserDatastore initialisé")

        user = datastore.find_user(id=authenticated_user_id)
        logger.info(f"🔍 AUTH ME: Utilisateur trouvé: {user is not None}")

        if not user:
            logger.warning(
                f"🔍 AUTH ME: Utilisateur non trouvé pour ID: {authenticated_user_id}"
            )
            return jsonify({"error": "Utilisateur non trouvé"}), 404

        # Créer une réponse sécurisée en échappant les données utilisateur
        user_data = {
            "id": user.id,
            "email": escape_html(user.email),
            "name": escape_html(getattr(user, "name", "")),
        }

        logger.info(f"🔍 AUTH ME: Données utilisateur récupérées avec succès")

        return jsonify(
            {
                "success": True,
                "user": user_data,
            }
        )

    except Exception as e:
        logger.error(f"🔍 AUTH ME: Erreur récupération utilisateur: {e}")
        import traceback

        logger.error(f"🔍 AUTH ME: Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Erreur interne du serveur"}), 500


@security_auth_bp.route("/auth/change-password", methods=["POST"])
def change_password():
    """Changer le mot de passe de l'utilisateur"""
    try:
        data = request.get_json()

        if not data or "current_password" not in data or "new_password" not in data:
            return (
                jsonify(
                    {"error": "Mot de passe actuel et nouveau mot de passe requis"}
                ),
                400,
            )

        current_password = data["current_password"]
        new_password = data["new_password"]

        # Validation simple du nouveau mot de passe
        if len(new_password) < 6:
            return (
                jsonify(
                    {
                        "error": "Le nouveau mot de passe doit contenir au moins 6 caractères"
                    }
                ),
                400,
            )

        # Vérifier le mot de passe actuel
        from models.security_models import SecurityUserDatastore

        datastore = SecurityUserDatastore(current_app.db)

        if not datastore.verify_password(current_user, current_password):
            return jsonify({"error": "Mot de passe actuel incorrect"}), 401

        # Mettre à jour le mot de passe
        from flask_security.utils import hash_password

        current_user.password_hash = hash_password(new_password)

        # Sauvegarder en base (à implémenter selon votre modèle)
        # datastore.update_user_password(current_user, new_password)

        return (
            jsonify({"success": True, "message": "Mot de passe modifié avec succès"}),
            200,
        )

    except Exception as e:
        logger.error(f"Erreur changement mot de passe: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500
