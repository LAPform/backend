"""
Routes de monitoring et métriques pour FormForge (Flask-RESTx avec Swagger)
"""

from flask import current_app
from flask_restx import Namespace, Resource
from utils.security_auth import require_token_auth
from utils.admin_auth import require_admin_role, require_monitoring_access, sanitize_system_metrics, get_user_role
from utils.rate_limiter import rate_limit
from utils.metrics_collector import metrics_collector
from utils.audit_logger import audit_logger
import logging

logger = logging.getLogger(__name__)

# Créer le namespace
api = Namespace('monitoring', description='Monitoring, métriques et santé de l\'API')

# Récupérer les modèles depuis la configuration
def get_models():
    """Récupère les modèles de documentation"""
    # Utiliser les modèles stockés dans le namespace (évite l'accès à current_app pendant l'import)
    if hasattr(api, '_models'):
        return api._models
    # Fallback pour le développement local
    try:
        return current_app.config.get('API_MODELS', {})
    except RuntimeError:
        return {}


@api.route('/basic-test')
class BasicTest(Resource):
    """Test basique du système de monitoring"""

    @api.doc('basic_test',
             description='Test basique sans authentification pour vérifier que le monitoring est opérationnel')
    @api.response(200, 'Test réussi')
    def get(self):
        """Test basique sans décorateurs"""
        return {
            "success": True,
            "message": "Test basique réussi",
            "timestamp": "2025-10-26"
        }


@api.route('/performance')
class Performance(Resource):
    """Statistiques de performance de la base de données"""

    @api.doc('get_performance',
             description='Obtenir les statistiques de performance de la base de données - Accès monitoring requis',
             security='Bearer')
    @api.response(200, 'Statistiques de performance')
    @api.response(500, 'Erreur serveur', get_models().get('error'))
    @api.response(401, 'Accès monitoring requis', get_models().get('error'))
    @require_monitoring_access
    @rate_limit("monitoring_performance")
    def get(self, authenticated_user_id=None, monitoring_user=None):
        """Obtenir les statistiques de performance de la base de données"""
        try:
            db_manager = current_app.db
            logger.info(f"🔍 MONITORING: db_manager = {db_manager is not None}")
            if not db_manager:
                logger.error("🔍 MONITORING: Database manager non disponible")
                return {"success": False, "error": "Database manager non disponible"}, 500

            db_stats = db_manager.get_performance_stats()

            # Ajouter des métriques système (sanitisées pour les non-admin)
            try:
                import psutil
                import os

                system_stats = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "process_memory": psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024,  # MB
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

            return {
                "success": True,
                "data": db_stats,
                "system_stats": system_stats,
                "user_role": get_user_role(monitoring_user.email),
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
            }

        except Exception as e:
            logger.error(f"Erreur récupération statistiques: {e}")
            return {
                "success": False,
                "error": "Erreur récupération statistiques",
                "details": str(e),
            }, 500


@api.route('/health')
class Health(Resource):
    """Statut de santé de l'API"""

    @api.doc('get_health',
             description='Obtenir le statut de santé de l\'API (base de données, tables, performance)',
             security='Bearer')
    @api.response(200, 'Statut de santé')
    @api.response(500, 'API non opérationnelle', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("monitoring_health")
    def get(self, authenticated_user_id=None):
        """Obtenir le statut de santé de l'API"""
        try:
            # Test de connexion base de données
            db_manager = current_app.db
            if not db_manager:
                return {"success": False, "error": "Database manager non disponible"}, 500

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
            slow_queries_alert = db_stats["slow_query_rate"] > 0.1  # Plus de 10%

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

            return {
                "success": True,
                "health": health_status,
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
            }

        except Exception as e:
            logger.error(f"Erreur health check: {e}")
            return {
                "success": False,
                "health": {
                    "overall": "unhealthy",
                    "database": "disconnected",
                    "error": str(e),
                },
            }, 500


@api.route('/system')
class SystemMetrics(Resource):
    """Métriques système (CPU, mémoire, disque) - Admin uniquement"""

    @api.doc('get_system_metrics',
             description='Obtenir les métriques système complètes - ADMIN UNIQUEMENT',
             security='Bearer')
    @api.response(200, 'Métriques système')
    @api.response(403, 'Accès admin requis', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_admin_role
    @rate_limit("monitoring_system")
    def get(self, authenticated_user_id=None, admin_user=None):
        """Obtenir les métriques système - ADMIN UNIQUEMENT"""
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
                return {
                    "success": True,
                    "data": {
                        "error": "psutil non disponible",
                        "message": "Métriques système limitées - psutil non installé",
                        "basic_info": {"platform": os.name, "pid": os.getpid()},
                    },
                    "timestamp": "N/A",
                    "admin_access": True,
                }

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
            timestamp = db_manager.query_stats.get("last_update", "N/A") if db_manager else "N/A"

            logger.info(f"🔒 ADMIN: Métriques système accédées par {admin_user.email}")

            # Log d'audit pour l'accès aux métriques système
            audit_logger.log_admin_action(
                action="access_system_metrics",
                resource="system_metrics",
                details={
                    "admin_email": admin_user.email,
                    "metrics_accessed": list(metrics.keys())
                }
            )

            return {
                "success": True,
                "data": metrics,
                "timestamp": timestamp,
                "admin_access": True,
                "accessed_by": admin_user.email,
            }

        except Exception as e:
            logger.error(f"Erreur récupération métriques système: {e}")
            return {"success": False, "error": "Erreur interne du serveur"}, 500


@api.route('/slow-queries')
class SlowQueries(Resource):
    """Requêtes lentes détectées"""

    @api.doc('get_slow_queries',
             description='Obtenir les requêtes lentes et recommandations d\'optimisation',
             security='Bearer')
    @api.response(200, 'Requêtes lentes')
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("monitoring_slow_queries")
    def get(self, authenticated_user_id=None):
        """Obtenir les requêtes lentes détectées"""
        try:
            db_manager = current_app.db
            if not db_manager:
                return {"success": False, "error": "Database manager non disponible"}, 500

            db_stats = db_manager.get_performance_stats()

            return {
                "success": True,
                "slow_queries": {
                    "count": db_stats["slow_queries"],
                    "rate": db_stats["slow_query_rate"],
                    "threshold": db_stats["slow_query_threshold"],
                    "recommendations": _get_optimization_recommendations(db_stats),
                },
            }

        except Exception as e:
            logger.error(f"Erreur récupération requêtes lentes: {e}")
            return {
                "success": False,
                "error": "Erreur récupération requêtes lentes",
                "details": str(e),
            }, 500


@api.route('/api-metrics')
class APIMetrics(Resource):
    """Métriques API détaillées"""

    @api.doc('get_api_metrics',
             description='Obtenir les métriques API (requêtes, temps de réponse, erreurs)',
             security='Bearer')
    @api.response(200, 'Métriques API')
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("monitoring_api_metrics")
    def get(self, authenticated_user_id=None):
        """Obtenir les métriques API détaillées"""
        try:
            api_metrics = metrics_collector.get_api_metrics()

            # Obtenir le database manager pour le timestamp
            db_manager = current_app.db
            timestamp = db_manager.query_stats.get("last_update", "N/A") if db_manager else "N/A"

            return {
                "success": True,
                "data": api_metrics,
                "timestamp": timestamp,
            }

        except Exception as e:
            logger.error(f"Erreur récupération métriques API: {e}")
            return {
                "success": False,
                "error": "Erreur récupération métriques API",
                "details": str(e),
            }, 500


@api.route('/health-detailed')
class DetailedHealth(Resource):
    """Rapport de santé détaillé"""

    @api.doc('get_detailed_health',
             description='Obtenir un rapport de santé complet (système, API, base de données)',
             security='Bearer')
    @api.response(200, 'Rapport de santé détaillé')
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("monitoring_health_detailed")
    def get(self, authenticated_user_id=None):
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
                return {"success": False, "error": "Database manager non disponible"}, 500

            db_stats = db_manager.get_performance_stats()

            return {
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

        except Exception as e:
            logger.error(f"Erreur rapport santé détaillé: {e}")
            return {
                "success": False,
                "error": "Erreur rapport santé détaillé",
                "details": str(e),
            }, 500


@api.route('/dashboard')
class Dashboard(Resource):
    """Données pour le dashboard de monitoring"""

    @api.doc('get_dashboard',
             description='Obtenir les données consolidées pour le dashboard - Accès monitoring requis',
             security='Bearer')
    @api.response(200, 'Données dashboard')
    @api.response(401, 'Accès monitoring requis', get_models().get('error'))
    @require_monitoring_access
    @rate_limit("monitoring_dashboard")
    def get(self, authenticated_user_id=None, monitoring_user=None):
        """Obtenir les données pour le dashboard de monitoring"""
        try:
            # Collecter toutes les métriques
            system_metrics = metrics_collector.get_system_metrics()
            api_metrics = metrics_collector.get_api_metrics()
            health_indicators = metrics_collector.get_health_indicators()

            db_manager = current_app.db
            if not db_manager:
                return {"success": False, "error": "Database manager non disponible"}, 500

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

            return {
                "success": True,
                "dashboard": dashboard_data,
                "timestamp": db_manager.query_stats.get("last_update", "N/A"),
            }

        except Exception as e:
            logger.error(f"Erreur données dashboard: {e}")
            return {
                "success": False,
                "error": "Erreur données dashboard",
                "details": str(e),
            }, 500


@api.route('/reset-stats')
class ResetStats(Resource):
    """Réinitialisation des statistiques - Admin uniquement"""

    @api.doc('reset_stats',
             description='Réinitialiser toutes les statistiques de performance - ADMIN UNIQUEMENT',
             security='Bearer')
    @api.response(200, 'Statistiques réinitialisées')
    @api.response(403, 'Accès admin requis', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_admin_role
    @rate_limit("monitoring_reset")
    def post(self, authenticated_user_id=None, admin_user=None):
        """Réinitialiser les statistiques de performance - ADMIN UNIQUEMENT"""
        try:
            # Réinitialiser les statistiques de base de données
            db_manager = current_app.db
            if not db_manager:
                return {"success": False, "error": "Database manager non disponible"}, 500

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

            # Log d'audit pour la réinitialisation des statistiques
            audit_logger.log_admin_action(
                action="reset_statistics",
                resource="performance_stats",
                details={
                    "admin_email": admin_user.email,
                    "reset_components": ["database_stats", "api_metrics"]
                }
            )

            return {
                "success": True,
                "message": "Statistiques réinitialisées avec succès",
                "reset_by": admin_user.email,
                "admin_action": True
            }

        except Exception as e:
            logger.error(f"Erreur réinitialisation statistiques: {e}")
            return {
                "success": False,
                "error": "Erreur réinitialisation statistiques",
                "details": str(e),
            }, 500


@api.route('/admin/users')
class AdminUsers(Resource):
    """Liste des administrateurs - Admin uniquement"""

    @api.doc('get_admin_users',
             description='Obtenir la liste de tous les administrateurs du système - ADMIN UNIQUEMENT',
             security='Bearer')
    @api.response(200, 'Liste des administrateurs')
    @api.response(403, 'Accès admin requis', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_admin_role
    @rate_limit("admin_users")
    def get(self, authenticated_user_id=None, admin_user=None):
        """Obtenir la liste des utilisateurs administrateurs - ADMIN UNIQUEMENT"""
        try:
            from utils.admin_auth import ADMIN_EMAILS

            logger.info(f"🔒 ADMIN: Liste des admins consultée par {admin_user.email}")

            return {
                "success": True,
                "admin_emails": ADMIN_EMAILS,
                "total_admins": len(ADMIN_EMAILS),
                "accessed_by": admin_user.email,
                "admin_action": True
            }

        except Exception as e:
            logger.error(f"Erreur récupération liste admins: {e}")
            return {
                "success": False,
                "error": "Erreur récupération liste administrateurs"
            }, 500


@api.route('/admin/check-role')
class CheckRole(Resource):
    """Vérification du rôle utilisateur"""

    @api.doc('check_role',
             description='Vérifier le rôle de l\'utilisateur actuel (user, admin, etc.)',
             security='Bearer')
    @api.response(200, 'Rôle utilisateur')
    @api.response(404, 'Utilisateur non trouvé', get_models().get('error'))
    @api.response(401, 'Non authentifié', get_models().get('error'))
    @require_token_auth
    @rate_limit("check_role")
    def get(self, authenticated_user_id=None):
        """Vérifier le rôle de l'utilisateur actuel"""
        try:
            from models.security_models import SecurityUserDatastore
            from utils.admin_auth import get_user_role

            datastore = SecurityUserDatastore(current_app.db)
            user = datastore.find_user(id=authenticated_user_id)

            if not user:
                return {
                    "success": False,
                    "error": "Utilisateur non trouvé"
                }, 404

            user_role = get_user_role(user.email)

            return {
                "success": True,
                "user": {
                    "email": user.email,
                    "id": user.id,
                    "name": getattr(user, "name", "")
                },
                "role": user_role,
                "is_admin": user_role == "admin"
            }

        except Exception as e:
            logger.error(f"Erreur vérification rôle: {e}")
            return {
                "success": False,
                "error": "Erreur vérification rôle"
            }, 500


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
