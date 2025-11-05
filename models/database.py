"""
Gestionnaire de base de données SQLite pour FormForge
"""

import sqlite3
import os
import time
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données SQLite"""

    def __init__(self):
        # Configuration SQLite uniquement
        self.database_url = os.environ.get("DATABASE_URL", "sqlite:///formforge_poc.db")
        # S'assurer que c'est bien SQLite
        if not self.database_url.startswith("sqlite:///"):
            logger.warning(
                f"URL de base de données non-SQLite détectée: {self.database_url}"
            )
            logger.warning("Forçage vers SQLite pour la compatibilité Render gratuit")
            self.database_url = "sqlite:///formforge_poc.db"

        self.db_path = self.database_url.replace("sqlite:///", "")

        # Statistiques de performance
        self.query_stats = {
            "total_queries": 0,
            "total_time": 0,
            "slow_queries": 0,
            "cache_hits": 0,
        }
        self.slow_query_threshold = 1.0  # 1 seconde

    def get_connection(self):
        """Obtenir une connexion SQLite"""
        return sqlite3.connect(self.db_path)

    def return_connection(self, conn):
        """Fermer une connexion SQLite"""
        conn.close()

    def init_database(self):
        """Initialiser la base de données avec les tables"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Table forms
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS forms (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    settings TEXT DEFAULT '{}',
                    created_by TEXT,
                    status TEXT DEFAULT 'draft',
                    public_token TEXT UNIQUE,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Ajouter les colonnes status et public_token si elles n'existent pas (migration)
            try:
                cursor.execute("PRAGMA table_info(forms)")
                columns = [row[1] for row in cursor.fetchall()]
                if "status" not in columns:
                    cursor.execute(
                        "ALTER TABLE forms ADD COLUMN status TEXT DEFAULT 'draft'"
                    )
                if "public_token" not in columns:
                    cursor.execute("ALTER TABLE forms ADD COLUMN public_token TEXT")
                    # Créer un index unique pour public_token
                    cursor.execute(
                        "CREATE UNIQUE INDEX IF NOT EXISTS idx_forms_public_token ON forms(public_token)"
                    )
            except Exception as e_info:
                logger.warning(
                    f"Impossible d'ajouter status/public_token ou migration: {e_info}"
                )

            # Créer l'index unique pour public_token si la colonne existe déjà
            try:
                cursor.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_forms_public_token ON forms(public_token)"
                )
            except Exception:
                pass  # L'index existe peut-être déjà

            # Table questions
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    options TEXT DEFAULT '[]',
                    required INTEGER DEFAULT 0,
                    validation TEXT DEFAULT '{}',
                    order_index INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Table users
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login TEXT
                )
            """
            )

            # Assurer la présence des colonnes requises par Flask-Security-Too
            try:
                cursor.execute("PRAGMA table_info(users)")
                columns = [row[1] for row in cursor.fetchall()]

                # Colonne fs_uniquifier (requis par FST >= 4.0)
                if "fs_uniquifier" not in columns:
                    cursor.execute("ALTER TABLE users ADD COLUMN fs_uniquifier TEXT")
                    logger.info("Colonne fs_uniquifier ajoutée à la table users")

                # Colonnes pour la réinitialisation de mot de passe (SECURITY_RECOVERABLE)
                if "reset_password_token" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN reset_password_token TEXT"
                    )
                    logger.info("Colonne reset_password_token ajoutée à la table users")

                if "password_changed_at" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN password_changed_at TEXT"
                    )
                    logger.info("Colonne password_changed_at ajoutée à la table users")

                # Colonnes pour le tracking (SECURITY_TRACKABLE)
                if "current_login_at" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN current_login_at TEXT"
                    )
                    logger.info("Colonne current_login_at ajoutée à la table users")

                if "last_login_at" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN last_login_at TEXT"
                    )
                    logger.info("Colonne last_login_at ajoutée à la table users")

                if "current_login_ip" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN current_login_ip TEXT"
                    )
                    logger.info("Colonne current_login_ip ajoutée à la table users")

                if "last_login_ip" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN last_login_ip TEXT"
                    )
                    logger.info("Colonne last_login_ip ajoutée à la table users")

                if "login_count" not in columns:
                    cursor.execute(
                        "ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0"
                    )
                    logger.info("Colonne login_count ajoutée à la table users")

                # Créer un index unique pour garantir l'unicité de fs_uniquifier
                cursor.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_fs_uniquifier ON users(fs_uniquifier)"
                )

            except Exception as e_info:
                logger.warning(
                    f"Impossible d'ajouter/valider les colonnes FST ou index unique: {e_info}"
                )

            # Table responses
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    id TEXT PRIMARY KEY,
                    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
                    answers TEXT NOT NULL,
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    ip_address TEXT
                )
            """
            )

            # Table active_tokens supprimée - utilisation de Flask-Security-Too uniquement

            # Table roles (gestion des rôles)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT
                )
            """
            )

            # Table d'association user_roles
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_roles (
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    role_id TEXT REFERENCES roles(id) ON DELETE CASCADE,
                    PRIMARY KEY (user_id, role_id)
                )
            """
            )

            # Index pour améliorer les performances
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_questions_form_id 
                ON questions(form_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_responses_form_id 
                ON responses(form_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_responses_submitted_at 
                ON responses(submitted_at)
            """
            )

            # Index supplémentaires pour l'optimisation
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_forms_created_by 
                ON forms(created_by)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_forms_created_at 
                ON forms(created_at)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_questions_type 
                ON questions(type)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_questions_order 
                ON questions(form_id, order_index)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_created_at 
                ON users(created_at)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_responses_user_id
                ON responses(user_id)
            """
            )

            # Index composites pour optimiser les requêtes fréquentes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_forms_created_by_status
                ON forms(created_by, status)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_responses_form_user
                ON responses(form_id, user_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_users_email_lower
                ON users(LOWER(email))
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_forms_status
                ON forms(status)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_roles_user
                ON user_roles(user_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_user_roles_role
                ON user_roles(role_id)
            """
            )

            conn.commit()
            logger.info("Base de données initialisée avec succès - Indexes optimisés")

        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur initialisation base: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Exécuter une requête SQL avec gestion d'erreur robuste et monitoring"""
        start_time = time.time()
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Gérer le cas où params est None
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)

            if fetch:
                if "SELECT" in query.upper():
                    # Pour les requêtes SELECT, toujours retourner une liste
                    if cursor.description:
                        columns = [description[0] for description in cursor.description]
                        rows = cursor.fetchall()
                        result = [dict(zip(columns, row)) for row in rows]
                    else:
                        result = []
                else:
                    # Pour les autres requêtes, retourner le premier résultat
                    result = cursor.fetchone()
                    if result and cursor.description:
                        columns = [description[0] for description in cursor.description]
                        result = dict(zip(columns, result))
            else:
                result = cursor.rowcount

            # Commit en cas de succès
            conn.commit()
            execution_time = time.time() - start_time
            self._record_query_stats(query, execution_time)
            return result

        except Exception as e:
            logger.error(f"Erreur dans execute_query: {e}")
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Erreur lors du rollback: {rollback_error}")
            raise
        finally:
            if "cursor" in locals():
                cursor.close()
            # Pas de commit/rollback dans finally
            self.return_connection(conn)

    def _record_query_stats(self, query: str, execution_time: float):
        """Enregistrer les statistiques de performance"""
        self.query_stats["total_queries"] += 1
        self.query_stats["total_time"] += execution_time

        if execution_time > self.slow_query_threshold:
            self.query_stats["slow_queries"] += 1
            logger.warning(
                f"Requête lente détectée ({execution_time:.2f}s): {query[:100]}..."
            )

    def get_performance_stats(self):
        """Obtenir les statistiques de performance"""
        total_queries = self.query_stats["total_queries"]
        if total_queries > 0:
            avg_time = self.query_stats["total_time"] / total_queries
            slow_query_rate = self.query_stats["slow_queries"] / total_queries
        else:
            avg_time = 0
            slow_query_rate = 0

        return {
            "total_queries": total_queries,
            "total_time": self.query_stats["total_time"],
            "average_time": avg_time,
            "slow_queries": self.query_stats["slow_queries"],
            "slow_query_rate": slow_query_rate,
            "slow_query_threshold": self.slow_query_threshold,
        }

    def execute_transaction(self, queries: List[tuple]):
        """Exécuter plusieurs requêtes dans une transaction"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            for query, params in queries:
                cursor.execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur transaction: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)

    def close_pool(self):
        """Fermer le pool de connexions (non utilisé avec SQLite)"""
        pass
