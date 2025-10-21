"""
Gestionnaire de base de données PostgreSQL pour FormForge
"""

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
import os
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données PostgreSQL"""

    def __init__(self):
        self.database_url = os.environ.get(
            "DATABASE_URL", "postgresql://localhost/formforge_poc"
        )
        self.connection_pool = None
        self.init_connection_pool()

    def init_connection_pool(self):
        """Initialiser le pool de connexions"""
        try:
            self.connection_pool = SimpleConnectionPool(
                minconn=1, maxconn=20, dsn=self.database_url
            )
            logger.info("Pool de connexions PostgreSQL initialisé")
        except Exception as e:
            logger.error(f"Erreur initialisation pool: {e}")
            raise

    def get_connection(self):
        """Obtenir une connexion du pool"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Retourner une connexion au pool"""
        self.connection_pool.putconn(conn)

    def init_database(self):
        """Initialiser la base de données avec les tables"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Table forms
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS forms (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        title TEXT NOT NULL,
                        description TEXT,
                        settings JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Table questions
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS questions (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        form_id UUID REFERENCES forms(id) ON DELETE CASCADE,
                        type TEXT NOT NULL,
                        text TEXT NOT NULL,
                        options JSONB DEFAULT '[]',
                        required BOOLEAN DEFAULT FALSE,
                        validation JSONB DEFAULT '{}',
                        order_index INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Table responses
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS responses (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        form_id UUID REFERENCES forms(id) ON DELETE CASCADE,
                        answers JSONB NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        user_id TEXT,
                        ip_address INET
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
            self.return_connection(conn)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Exécuter une requête SQL"""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)

                if fetch:
                    if "SELECT" in query.upper():
                        return cursor.fetchall()
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
            self.return_connection(conn)

    def execute_transaction(self, queries: List[tuple]):
        """Exécuter plusieurs requêtes dans une transaction"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                for query, params in queries:
                    cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Erreur transaction: {e}")
            raise
        finally:
            self.return_connection(conn)

    def close_pool(self):
        """Fermer le pool de connexions"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Pool de connexions fermé")
