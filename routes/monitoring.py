"""
Routes de monitoring et métriques pour FormForge
"""

from flask import Blueprint, jsonify, current_app
from utils.security_auth import require_auth
from utils.rate_limiter import rate_limit
from utils.metrics_collector import metrics_collector
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
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
            "process_memory": psutil.Process(os.getpid()).memory_info().rss
            / 1024
            / 1024,  # MB
        }

        return jsonify(
            {
                "success": True,
                "data": db_stats,
                "system_stats": system_stats,
                "timestamp": current_app.db.query_stats.get("last_update", "N/A"),
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération statistiques: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur récupération statistiques",
                    "details": str(e),
                }
            ),
            500,
        )


@monitoring_bp.route("/monitoring/health", methods=["GET"])
@require_auth
@rate_limit("monitoring_health")
def get_health_status():
    """Obtenir le statut de santé de l'API"""
    try:
        # Test de connexion base de données
        db_health = current_app.db.get_connection()
        db_health.close()

        # Test des tables principales
        tables_status = {}
        tables = ["forms", "questions", "users", "responses"]

        for table in tables:
            try:
                result = current_app.db.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}", fetch=True
                )
                tables_status[table] = {
                    "status": "healthy",
                    "count": result[0]["count"] if result else 0,
                }
            except Exception as e:
                tables_status[table] = {"status": "error", "error": str(e)}

        # Vérifier les requêtes lentes
        db_stats = current_app.db.get_performance_stats()
        slow_queries_alert = (
            db_stats["slow_query_rate"] > 0.1
        )  # Plus de 10% de requêtes lentes

        health_status = {
            "overall": "healthy" if not slow_queries_alert else "degraded",
            "database": "connected",
            "tables": tables_status,
            "performance": {
                "slow_queries_alert": slow_queries_alert,
                "slow_query_rate": db_stats["slow_query_rate"],
                "average_query_time": db_stats["average_time"],
            },
        }

        return jsonify(
            {
                "success": True,
                "health": health_status,
                "timestamp": current_app.db.query_stats.get("last_update", "N/A"),
            }
        )

    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "health": {
                        "overall": "unhealthy",
                        "database": "disconnected",
                        "error": str(e),
                    },
                }
            ),
            500,
        )


@monitoring_bp.route("/monitoring/system", methods=["GET"])
@require_auth
@rate_limit("monitoring_system")
def get_system_metrics():
    """Obtenir les métriques système (CPU, mémoire, disque)"""
    try:
        import psutil
        import os

        # Métriques système
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage("/")

        # Métriques du processus
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info().rss / 1024 / 1024  # MB

        metrics = {
            "cpu_percent": cpu_percent,
            "memory_total_gb": round(memory_info.total / (1024**3), 2),
            "memory_used_gb": round(memory_info.used / (1024**3), 2),
            "memory_percent": memory_info.percent,
            "disk_total_gb": round(disk_usage.total / (1024**3), 2),
            "disk_used_gb": round(disk_usage.used / (1024**3), 2),
            "disk_percent": disk_usage.percent,
            "process_memory_mb": round(process_memory, 2),
            "process_cpu_percent": process.cpu_percent(),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "data": metrics,
                    "timestamp": current_app.db.query_stats.get("last_update", "N/A"),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Erreur récupération métriques système: {e}")
        return jsonify({"success": False, "error": "Erreur interne du serveur"}), 500


@monitoring_bp.route("/monitoring/slow-queries", methods=["GET"])
@require_auth
@rate_limit("monitoring_slow_queries")
def get_slow_queries():
    """Obtenir les requêtes lentes détectées"""
    try:
        db_stats = current_app.db.get_performance_stats()

        return jsonify(
            {
                "success": True,
                "slow_queries": {
                    "count": db_stats["slow_queries"],
                    "rate": db_stats["slow_query_rate"],
                    "threshold": db_stats["slow_query_threshold"],
                    "recommendations": _get_optimization_recommendations(db_stats),
                },
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération requêtes lentes: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur récupération requêtes lentes",
                    "details": str(e),
                }
            ),
            500,
        )


def _get_optimization_recommendations(stats):
    """Générer des recommandations d'optimisation basées sur les statistiques"""
    recommendations = []

    if stats["slow_query_rate"] > 0.2:
        recommendations.append(
            "Taux de requêtes lentes élevé (>20%) - Vérifier les index"
        )

    if stats["average_time"] > 0.5:
        recommendations.append(
            "Temps moyen de requête élevé (>0.5s) - Optimiser les requêtes"
        )

    if stats["slow_queries"] > 10:
        recommendations.append(
            "Nombre élevé de requêtes lentes - Analyser les requêtes fréquentes"
        )

    if not recommendations:
        recommendations.append(
            "Performance acceptable - Aucune optimisation majeure nécessaire"
        )

    return recommendations


@monitoring_bp.route("/monitoring/api-metrics", methods=["GET"])
@require_auth
@rate_limit("monitoring_api_metrics")
def get_api_metrics():
    """Obtenir les métriques API détaillées"""
    try:
        api_metrics = metrics_collector.get_api_metrics()
        
        return jsonify({
            "success": True,
            "data": api_metrics,
            "timestamp": current_app.db.query_stats.get("last_update", "N/A")
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération métriques API: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur récupération métriques API",
            "details": str(e)
        }), 500


@monitoring_bp.route("/monitoring/health-detailed", methods=["GET"])
@require_auth
@rate_limit("monitoring_health_detailed")
def get_detailed_health():
    """Obtenir un rapport de santé détaillé"""
    try:
        # Métriques système
        system_metrics = metrics_collector.get_system_metrics()
        
        # Métriques API
        api_metrics = metrics_collector.get_api_metrics()
        
        # Indicateurs de santé
        health_indicators = metrics_collector.get_health_indicators()
        
        # Métriques base de données
        db_stats = current_app.db.get_performance_stats()
        
        return jsonify({
            "success": True,
            "health": {
                "overall_status": health_indicators["status"],
                "alerts": health_indicators["alerts"],
                "warnings": health_indicators["warnings"],
                "system": system_metrics,
                "api": api_metrics,
                "database": db_stats
            },
            "timestamp": current_app.db.query_stats.get("last_update", "N/A")
        })
        
    except Exception as e:
        logger.error(f"Erreur rapport santé détaillé: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur rapport santé détaillé",
            "details": str(e)
        }), 500


@monitoring_bp.route("/monitoring/dashboard", methods=["GET"])
@require_auth
@rate_limit("monitoring_dashboard")
def get_dashboard_data():
    """Obtenir les données pour le dashboard de monitoring"""
    try:
        # Collecter toutes les métriques
        system_metrics = metrics_collector.get_system_metrics()
        api_metrics = metrics_collector.get_api_metrics()
        health_indicators = metrics_collector.get_health_indicators()
        db_stats = current_app.db.get_performance_stats()
        
        # Créer un résumé pour le dashboard
        dashboard_data = {
            "status": {
                "overall": health_indicators["status"],
                "alerts_count": len(health_indicators["alerts"]),
                "warnings_count": len(health_indicators["warnings"])
            },
            "performance": {
                "cpu_percent": system_metrics.get("cpu", {}).get("percent", 0),
                "memory_percent": system_metrics.get("memory", {}).get("percent", 0),
                "disk_percent": system_metrics.get("disk", {}).get("percent", 0),
                "avg_response_time": api_metrics.get("avg_response_time", 0),
                "requests_per_minute": api_metrics.get("requests_per_minute", 0),
                "error_rate": api_metrics.get("error_rate", 0)
            },
            "database": {
                "total_queries": db_stats.get("total_queries", 0),
                "slow_queries": db_stats.get("slow_queries", 0),
                "avg_query_time": db_stats.get("average_time", 0),
                "slow_query_rate": db_stats.get("slow_query_rate", 0)
            },
            "uptime": {
                "seconds": api_metrics.get("uptime_seconds", 0),
                "hours": api_metrics.get("uptime_hours", 0)
            }
        }
        
        return jsonify({
            "success": True,
            "dashboard": dashboard_data,
            "timestamp": current_app.db.query_stats.get("last_update", "N/A")
        })
        
    except Exception as e:
        logger.error(f"Erreur données dashboard: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur données dashboard",
            "details": str(e)
        }), 500


@monitoring_bp.route("/monitoring/reset-stats", methods=["POST"])
@require_auth
@rate_limit("monitoring_reset")
def reset_performance_stats():
    """Réinitialiser les statistiques de performance"""
    try:
        # Réinitialiser les statistiques de base de données
        current_app.db.query_stats = {
            "total_queries": 0,
            "total_time": 0,
            "slow_queries": 0,
            "cache_hits": 0,
        }
        
        # Réinitialiser les métriques API
        metrics_collector.request_count = 0
        metrics_collector.error_count = 0
        metrics_collector.response_times = []
        metrics_collector.endpoint_stats = {}

        logger.info("Statistiques de performance réinitialisées")

        return jsonify(
            {"success": True, "message": "Statistiques réinitialisées avec succès"}
        )

    except Exception as e:
        logger.error(f"Erreur réinitialisation statistiques: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur réinitialisation statistiques",
                    "details": str(e),
                }
            ),
            500,
        )
