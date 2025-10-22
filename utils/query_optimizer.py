"""
Système d'optimisation des requêtes pour FormForge
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Optimiseur de requêtes avec cache et indexation"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.query_cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 seconde
        
    def create_optimized_indexes(self):
        """Créer des index optimisés pour les requêtes fréquentes"""
        indexes = [
            # Index pour les formulaires
            "CREATE INDEX IF NOT EXISTS idx_forms_created_by ON forms(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_forms_created_at ON forms(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_forms_updated_at ON forms(updated_at)",
            
            # Index pour les questions
            "CREATE INDEX IF NOT EXISTS idx_questions_form_id ON questions(form_id)",
            "CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(type)",
            "CREATE INDEX IF NOT EXISTS idx_questions_order ON questions(form_id, order_index)",
            "CREATE INDEX IF NOT EXISTS idx_questions_required ON questions(required)",
            
            # Index pour les utilisateurs
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)",
            
            # Index pour les réponses
            "CREATE INDEX IF NOT EXISTS idx_responses_form_id ON responses(form_id)",
            "CREATE INDEX IF NOT EXISTS idx_responses_user_id ON responses(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_responses_submitted_at ON responses(submitted_at)",
            "CREATE INDEX IF NOT EXISTS idx_responses_ip_address ON responses(ip_address)",
            
            # Index composites pour les requêtes complexes
            "CREATE INDEX IF NOT EXISTS idx_forms_with_questions ON forms(id, created_at)",
            "CREATE INDEX IF NOT EXISTS idx_questions_with_form ON questions(form_id, type, order_index)",
            "CREATE INDEX IF NOT EXISTS idx_responses_with_form ON responses(form_id, submitted_at)",
        ]
        
        for index_query in indexes:
            try:
                self.db.execute_query(index_query)
                logger.info(f"Index créé: {index_query}")
            except Exception as e:
                logger.error(f"Erreur création index: {e}")
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Récupérer un résultat du cache"""
        if cache_key in self.query_cache:
            cached_data, timestamp = self.query_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
            else:
                # Cache expiré
                del self.query_cache[cache_key]
        return None
    
    def set_cached_result(self, cache_key: str, result: Any):
        """Mettre en cache un résultat"""
        self.query_cache[cache_key] = (result, time.time())
    
    def generate_cache_key(self, query: str, params: Tuple = None) -> str:
        """Générer une clé de cache"""
        return f"{query}:{params if params else 'no_params'}"
    
    def execute_optimized_query(self, query: str, params: Tuple = None, fetch: bool = False, use_cache: bool = True) -> Any:
        """Exécuter une requête optimisée avec cache"""
        start_time = time.time()
        
        # Générer la clé de cache pour les requêtes SELECT
        cache_key = None
        if fetch and use_cache and query.strip().upper().startswith('SELECT'):
            cache_key = self.generate_cache_key(query, params)
            cached_result = self.get_cached_result(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit pour: {query[:50]}...")
                return cached_result
        
        # Exécuter la requête
        try:
            result = self.db.execute_query(query, params, fetch)
            
            # Mettre en cache les résultats SELECT
            if fetch and use_cache and cache_key:
                self.set_cached_result(cache_key, result)
            
            # Enregistrer les statistiques
            execution_time = time.time() - start_time
            self._record_query_stats(query, execution_time)
            
            # Logger les requêtes lentes
            if execution_time > self.slow_query_threshold:
                logger.warning(f"Requête lente détectée ({execution_time:.2f}s): {query[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur requête optimisée: {e}")
            raise
    
    def _record_query_stats(self, query: str, execution_time: float):
        """Enregistrer les statistiques de requête"""
        query_type = query.strip().upper().split()[0]
        if query_type not in self.query_stats:
            self.query_stats[query_type] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'max_time': 0,
                'min_time': float('inf')
            }
        
        stats = self.query_stats[query_type]
        stats['count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['min_time'] = min(stats['min_time'], execution_time)
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Obtenir les statistiques des requêtes"""
        return {
            'query_stats': self.query_stats,
            'cache_size': len(self.query_cache),
            'cache_hit_rate': self._calculate_cache_hit_rate()
        }
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculer le taux de hit du cache"""
        # Simplification - en production, on utiliserait des compteurs
        return 0.0
    
    def clear_cache(self):
        """Vider le cache"""
        self.query_cache.clear()
        logger.info("Cache vidé")
    
    def optimize_slow_queries(self):
        """Analyser et optimiser les requêtes lentes"""
        slow_queries = []
        for query_type, stats in self.query_stats.items():
            if stats['avg_time'] > self.slow_query_threshold:
                slow_queries.append({
                    'type': query_type,
                    'avg_time': stats['avg_time'],
                    'count': stats['count']
                })
        
        if slow_queries:
            logger.warning(f"Requêtes lentes détectées: {slow_queries}")
            return slow_queries
        return []


def query_performance_monitor(func):
    """Décorateur pour monitorer les performances des requêtes"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Plus d'1 seconde
                logger.warning(f"Requête lente dans {func.__name__}: {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Erreur dans {func.__name__} après {execution_time:.2f}s: {e}")
            raise
    
    return wrapper


class QueryBuilder:
    """Constructeur de requêtes optimisées"""
    
    @staticmethod
    def build_optimized_select(table: str, columns: List[str] = None, 
                             where_clause: str = None, order_by: str = None, 
                             limit: int = None) -> str:
        """Construire une requête SELECT optimisée"""
        if columns is None:
            columns = ["*"]
        
        query = f"SELECT {', '.join(columns)} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return query
    
    @staticmethod
    def build_optimized_join(primary_table: str, join_table: str, 
                            join_condition: str, columns: List[str] = None) -> str:
        """Construire une requête JOIN optimisée"""
        if columns is None:
            columns = ["*"]
        
        query = f"""
            SELECT {', '.join(columns)} 
            FROM {primary_table} 
            JOIN {join_table} ON {join_condition}
        """
        
        return query.strip()


# Instance globale de l'optimiseur
query_optimizer = None

def initialize_query_optimizer(db_manager):
    """Initialiser l'optimiseur de requêtes"""
    global query_optimizer
    query_optimizer = QueryOptimizer(db_manager)
    query_optimizer.create_optimized_indexes()
    return query_optimizer

def get_query_optimizer():
    """Obtenir l'instance de l'optimiseur"""
    return query_optimizer
