"""
Routes de monitoring et métriques pour FormForge
"""

from flask import Blueprint, jsonify, current_app
from utils.auth import require_auth
from utils.rate_limiter import rate_limit
import logging

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/monitoring/performance", methods=["GET"])
@require_auth
@rate_limit("monitoring_performance")
def get_performance_stats():
    """Obtenir les statistiques de performance de la base de données"""
    try:
        # Obtenir les statistiques du DatabaseManager
        db_stats = current_app.db.get_performance_stats()
        
        # Ajouter des métriques système
        import psutil
        import os
        
        system_stats = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'process_memory': psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,  # MB
        }
        
        return jsonify({
            'success': True,
            'database_stats': db_stats,
            'system_stats': system_stats,
            'timestamp': current_app.db.query_stats.get('last_update', 'N/A')
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération statistiques: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur récupération statistiques',
            'details': str(e)
        }), 500


@monitoring_bp.route("/monitoring/health", methods=["GET"])
@rate_limit("monitoring_health")
def get_health_status():
    """Obtenir le statut de santé de l'API"""
    try:
        # Test de connexion base de données
        db_health = current_app.db.get_connection()
        db_health.close()
        
        # Test des tables principales
        tables_status = {}
        tables = ['forms', 'questions', 'users', 'responses']
        
        for table in tables:
            try:
                result = current_app.db.execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch=True)
                tables_status[table] = {
                    'status': 'healthy',
                    'count': result[0]['count'] if result else 0
                }
            except Exception as e:
                tables_status[table] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Vérifier les requêtes lentes
        db_stats = current_app.db.get_performance_stats()
        slow_queries_alert = db_stats['slow_query_rate'] > 0.1  # Plus de 10% de requêtes lentes
        
        health_status = {
            'overall': 'healthy' if not slow_queries_alert else 'degraded',
            'database': 'connected',
            'tables': tables_status,
            'performance': {
                'slow_queries_alert': slow_queries_alert,
                'slow_query_rate': db_stats['slow_query_rate'],
                'average_query_time': db_stats['average_time']
            }
        }
        
        return jsonify({
            'success': True,
            'health': health_status,
            'timestamp': current_app.db.query_stats.get('last_update', 'N/A')
        })
        
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return jsonify({
            'success': False,
            'health': {
                'overall': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }
        }), 500


@monitoring_bp.route("/monitoring/slow-queries", methods=["GET"])
@require_auth
@rate_limit("monitoring_slow_queries")
def get_slow_queries():
    """Obtenir les requêtes lentes détectées"""
    try:
        db_stats = current_app.db.get_performance_stats()
        
        return jsonify({
            'success': True,
            'slow_queries': {
                'count': db_stats['slow_queries'],
                'rate': db_stats['slow_query_rate'],
                'threshold': db_stats['slow_query_threshold'],
                'recommendations': _get_optimization_recommendations(db_stats)
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération requêtes lentes: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur récupération requêtes lentes',
            'details': str(e)
        }), 500


def _get_optimization_recommendations(stats):
    """Générer des recommandations d'optimisation basées sur les statistiques"""
    recommendations = []
    
    if stats['slow_query_rate'] > 0.2:
        recommendations.append("Taux de requêtes lentes élevé (>20%) - Vérifier les index")
    
    if stats['average_time'] > 0.5:
        recommendations.append("Temps moyen de requête élevé (>0.5s) - Optimiser les requêtes")
    
    if stats['slow_queries'] > 10:
        recommendations.append("Nombre élevé de requêtes lentes - Analyser les requêtes fréquentes")
    
    if not recommendations:
        recommendations.append("Performance acceptable - Aucune optimisation majeure nécessaire")
    
    return recommendations


@monitoring_bp.route("/monitoring/reset-stats", methods=["POST"])
@require_auth
@rate_limit("monitoring_reset")
def reset_performance_stats():
    """Réinitialiser les statistiques de performance"""
    try:
        # Réinitialiser les statistiques
        current_app.db.query_stats = {
            'total_queries': 0,
            'total_time': 0,
            'slow_queries': 0,
            'cache_hits': 0
        }
        
        logger.info("Statistiques de performance réinitialisées")
        
        return jsonify({
            'success': True,
            'message': 'Statistiques réinitialisées avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur réinitialisation statistiques: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur réinitialisation statistiques',
            'details': str(e)
        }), 500
