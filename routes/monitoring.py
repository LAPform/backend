"""
Routes de monitoring et métriques pour FormForge
"""

from flask import Blueprint, jsonify, current_app
from utils.security_auth import require_auth
from utils.admin_auth import require_admin_role, require_monitoring_access, sanitize_system_metrics, get_user_role
from utils.rate_limiter import rate_limit
from utils.metrics_collector import metrics_collector
import logging

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint("monitoring", __name__)


@monitoring_bp.route("/monitoring/basic-test", methods=["GET"])
def basic_test_monitoring():
    """Test basique sans décorateurs"""
    return jsonify(
        {"success": True, "message": "Test basique réussi", "timestamp": "2025-10-26"}
    )


@monitoring_bp.route("/monitoring/performance", methods=["GET"])
@require_monitoring_access
@rate_limit("monitoring_performance")
def get_performance_stats(authenticated_user_id=None, monitoring_user=None):
    """Obtenir les statistiques de performance de la base de données (accès monitoring)"""
    try:
        # Obtenir les statistiques du DatabaseManager
        db_manager = current_app.db
        logger.info(f"🔍 MONITORING: db_manager = {db_manager is not None}")
        if not db_manager:
            logger.error("🔍 MONITORING: Database manager non disponible")
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_stats = db_manager.get_performance_stats()

        # Ajouter des métriques système (sanitisées pour les non-admin)
        try:
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
            
            # Sanitiser les métriques selon le rôle de l'utilisateur
            user_role = get_user_role(monitoring_user.email)
            if user_role != "admin":
                system_stats = sanitize_system_metrics(system_stats)
                logger.info(f"🔒 MONITORING: Métriques sanitisées pour {monitoring_user.email} (rôle: {user_role})")
            
        except ImportError:
            system_stats = {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_usage": 0,
                "process_memory": 0,
                "note": "psutil non disponible",
            }

        return jsonify(
            {
                "success": True,
                "data": db_stats,
                "system_stats": system_stats,
                "user_role": get_user_role(monitoring_user.email),
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
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
def get_health_status(authenticated_user_id=None):
    """Obtenir le statut de santé de l'API"""
    try:
        # Test de connexion base de données
        db_manager = current_app.db
        if not db_manager:
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_health = db_manager.get_connection()
        db_health.close()

        # Test des tables principales
        tables_status = {}
        tables = ["forms", "questions", "users", "responses"]

        for table in tables:
            try:
                result = db_manager.execute_query(
                    f"SELECT COUNT(*) as count FROM {table}", fetch=True
                )
                tables_status[table] = {
                    "status": "healthy",
                    "count": result[0]["count"] if result else 0,
                }
            except Exception as e:
                tables_status[table] = {"status": "error", "error": str(e)}

        # Vérifier les requêtes lentes
        db_stats = db_manager.get_performance_stats()
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
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
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
@require_admin_role
@rate_limit("monitoring_system")
def get_system_metrics(authenticated_user_id=None, admin_user=None):
    """Obtenir les métriques système (CPU, mémoire, disque) - ADMIN UNIQUEMENT"""
    try:
        # Import conditionnel de psutil
        try:
            import psutil

            psutil_available = True
        except ImportError:
            psutil = None
            psutil_available = False
            logger.warning("psutil non disponible - métriques système limitées")

        import os

        if not psutil_available:
            return jsonify(
                {
                    "success": True,
                    "data": {
                        "error": "psutil non disponible",
                        "message": "Métriques système limitées - psutil non installé",
                        "basic_info": {"platform": os.name, "pid": os.getpid()},
                    },
                    "timestamp": "N/A",
                    "admin_access": True,
                }
            )

        # Métriques système (ADMIN UNIQUEMENT)
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
            "pid": os.getpid(),
            "platform": os.name,
        }

        # Obtenir le database manager pour le timestamp
        db_manager = current_app.db
        timestamp = (
            db_manager.query_stats.get("last_update", "N/A") if db_manager else "N/A"
        )

        logger.info(f"🔒 ADMIN: Métriques système accédées par {admin_user.email}")

        return (
            jsonify(
                {
                    "success": True,
                    "data": metrics,
                    "timestamp": timestamp,
                    "admin_access": True,
                    "accessed_by": admin_user.email,
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
def get_slow_queries(authenticated_user_id=None):
    """Obtenir les requêtes lentes détectées"""
    try:
        db_manager = current_app.db
        if not db_manager:
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_stats = db_manager.get_performance_stats()

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
def get_api_metrics(authenticated_user_id=None):
    """Obtenir les métriques API détaillées"""
    try:
        api_metrics = metrics_collector.get_api_metrics()

        # Obtenir le database manager pour le timestamp
        db_manager = current_app.db
        timestamp = (
            db_manager.query_stats.get("last_update", "N/A") if db_manager else "N/A"
        )

        return jsonify(
            {
                "success": True,
                "data": api_metrics,
                "timestamp": timestamp,
            }
        )

    except Exception as e:
        logger.error(f"Erreur récupération métriques API: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur récupération métriques API",
                    "details": str(e),
                }
            ),
            500,
        )


@monitoring_bp.route("/monitoring/health-detailed", methods=["GET"])
@require_auth
@rate_limit("monitoring_health_detailed")
def get_detailed_health(authenticated_user_id=None):
    """Obtenir un rapport de santé détaillé"""
    try:
        # Métriques système
        system_metrics = metrics_collector.get_system_metrics()

        # Métriques API
        api_metrics = metrics_collector.get_api_metrics()

        # Indicateurs de santé
        health_indicators = metrics_collector.get_health_indicators()

        # Métriques base de données
        db_manager = current_app.db
        if not db_manager:
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_stats = db_manager.get_performance_stats()

        return jsonify(
            {
                "success": True,
                "health": {
                    "overall_status": health_indicators["status"],
                    "alerts": health_indicators["alerts"],
                    "warnings": health_indicators["warnings"],
                    "system": system_metrics,
                    "api": api_metrics,
                    "database": db_stats,
                },
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
            }
        )

    except Exception as e:
        logger.error(f"Erreur rapport santé détaillé: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur rapport santé détaillé",
                    "details": str(e),
                }
            ),
            500,
        )


@monitoring_bp.route("/monitoring/dashboard", methods=["GET"])
@require_monitoring_access
@rate_limit("monitoring_dashboard")
def get_dashboard_data(authenticated_user_id=None, monitoring_user=None):
    """Obtenir les données pour le dashboard de monitoring (accès monitoring)"""
    try:
        # Collecter toutes les métriques
        system_metrics = metrics_collector.get_system_metrics()
        api_metrics = metrics_collector.get_api_metrics()
        health_indicators = metrics_collector.get_health_indicators()

        db_manager = current_app.db
        if not db_manager:
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_stats = db_manager.get_performance_stats()

        # Sanitiser les métriques système selon le rôle
        user_role = get_user_role(monitoring_user.email)
        if user_role != "admin":
            system_metrics = sanitize_system_metrics(system_metrics)
            logger.info(f"🔒 MONITORING: Dashboard sanitisé pour {monitoring_user.email} (rôle: {user_role})")

        # Créer un résumé pour le dashboard
        dashboard_data = {
            "status": {
                "overall": health_indicators["status"],
                "alerts_count": len(health_indicators["alerts"]),
                "warnings_count": len(health_indicators["warnings"]),
            },
            "performance": {
                "cpu_percent": system_metrics.get("cpu", {}).get("percent", 0),
                "memory_percent": system_metrics.get("memory", {}).get("percent", 0),
                "disk_percent": system_metrics.get("disk", {}).get("percent", 0),
                "avg_response_time": api_metrics.get("avg_response_time", 0),
                "requests_per_minute": api_metrics.get("requests_per_minute", 0),
                "error_rate": api_metrics.get("error_rate", 0),
            },
            "database": {
                "total_queries": db_stats.get("total_queries", 0),
                "slow_queries": db_stats.get("slow_queries", 0),
                "avg_query_time": db_stats.get("average_time", 0),
                "slow_query_rate": db_stats.get("slow_query_rate", 0),
            },
            "uptime": {
                "seconds": api_metrics.get("uptime_seconds", 0),
                "hours": api_metrics.get("uptime_hours", 0),
            },
            "user_role": user_role,
        }

        return jsonify(
            {
                "success": True,
                "dashboard": dashboard_data,
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
            }
        )

    except Exception as e:
        logger.error(f"Erreur données dashboard: {e}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Erreur données dashboard",
                    "details": str(e),
                }
            ),
            500,
        )


@monitoring_bp.route("/monitoring/reset-stats", methods=["POST"])
@require_admin_role
@rate_limit("monitoring_reset")
def reset_performance_stats(authenticated_user_id=None, admin_user=None):
    """Réinitialiser les statistiques de performance - ADMIN UNIQUEMENT"""
    try:
        # Réinitialiser les statistiques de base de données
        db_manager = current_app.db
        if not db_manager:
            return (
                jsonify({"success": False, "error": "Database manager non disponible"}),
                500,
            )

        db_manager.query_stats = {
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

        logger.info(f"🔒 ADMIN: Statistiques réinitialisées par {admin_user.email}")

        return jsonify(
            {
                "success": True, 
                "message": "Statistiques réinitialisées avec succès",
                "reset_by": admin_user.email,
                "admin_action": True
            }
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


@monitoring_bp.route("/monitoring/admin/users", methods=["GET"])
@require_admin_role
@rate_limit("admin_users")
def get_admin_users(authenticated_user_id=None, admin_user=None):
    """Obtenir la liste des utilisateurs administrateurs - ADMIN UNIQUEMENT"""
    try:
        from utils.admin_auth import ADMIN_EMAILS
        
        logger.info(f"🔒 ADMIN: Liste des admins consultée par {admin_user.email}")
        
        return jsonify({
            "success": True,
            "admin_emails": ADMIN_EMAILS,
            "total_admins": len(ADMIN_EMAILS),
            "accessed_by": admin_user.email,
            "admin_action": True
        })
        
    except Exception as e:
        logger.error(f"Erreur récupération liste admins: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur récupération liste administrateurs"
        }), 500


@monitoring_bp.route("/monitoring/admin/check-role", methods=["GET"])
@require_auth
@rate_limit("check_role")
def check_user_role(authenticated_user_id=None):
    """Vérifier le rôle de l'utilisateur actuel"""
    try:
        from models.security_models import SecurityUserDatastore
        from utils.admin_auth import get_user_role
        
        datastore = SecurityUserDatastore(current_app.db)
        user = datastore.find_user(id=authenticated_user_id)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Utilisateur non trouvé"
            }), 404
        
        user_role = get_user_role(user.email)
        
        return jsonify({
            "success": True,
            "user": {
                "email": user.email,
                "id": user.id,
                "name": getattr(user, "name", "")
            },
            "role": user_role,
            "is_admin": user_role == "admin"
        })
        
    except Exception as e:
        logger.error(f"Erreur vérification rôle: {e}")
        return jsonify({
            "success": False,
            "error": "Erreur vérification rôle"
        }), 500
