"""
Gestionnaire de base de données SQLite pour FormForge
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données SQLite"""

    def __init__(self):
        self.database_url = os.environ.get("DATABASE_URL", "sqlite:///formforge_poc.db")
        self.db_path = self.database_url.replace("sqlite:///", "")

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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Table questions
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
                    type TEXT NOT NULL,
                    text TEXT NOT NULL,
                    options TEXT DEFAULT '[]',
                    required BOOLEAN DEFAULT FALSE,
                    validation TEXT DEFAULT '{}',
                    order_index INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Table responses
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    id TEXT PRIMARY KEY,
                    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
                    answers TEXT NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    ip_address TEXT
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

            conn.commit()
            logger.info("Base de données initialisée avec succès")

        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur initialisation base: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Exécuter une requête SQL"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch:
                if "SELECT" in query.upper():
                    columns = [description[0] for description in cursor.description]
                    rows = cursor.fetchall()
                    return [dict(zip(columns, row)) for row in rows]
                else:
                    return cursor.fetchone()
            else:
                conn.commit()
                return cursor.rowcount

        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur requête: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(conn)

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
