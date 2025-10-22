"""
Collecteur de métriques avancées pour FormForge
"""

import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collecteur de métriques système et API"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.endpoint_stats = {}
        self.daily_stats = {}
        
    def record_request(self, endpoint: str, method: str, status_code: int, response_time: float):
        """Enregistrer une requête API"""
        self.request_count += 1
        
        if status_code >= 400:
            self.error_count += 1
            
        self.response_times.append(response_time)
        
        # Statistiques par endpoint
        key = f"{method} {endpoint}"
        if key not in self.endpoint_stats:
            self.endpoint_stats[key] = {
                "count": 0,
                "total_time": 0,
                "errors": 0,
                "avg_time": 0
            }
            
        stats = self.endpoint_stats[key]
        stats["count"] += 1
        stats["total_time"] += response_time
        if status_code >= 400:
            stats["errors"] += 1
        stats["avg_time"] = stats["total_time"] / stats["count"]
        
        # Garder seulement les 1000 dernières réponses pour la mémoire
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def get_api_metrics(self) -> Dict[str, Any]:
        """Obtenir les métriques API"""
        uptime = time.time() - self.start_time
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        # Calculer les percentiles
        sorted_times = sorted(self.response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)] if sorted_times else 0
        p95 = sorted_times[int(len(sorted_times) * 0.95)] if sorted_times else 0
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if sorted_times else 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": round(self.error_count / max(self.request_count, 1) * 100, 2),
            "avg_response_time": round(avg_response_time, 3),
            "response_time_p50": round(p50, 3),
            "response_time_p95": round(p95, 3),
            "response_time_p99": round(p99, 3),
            "requests_per_minute": round(self.request_count / (uptime / 60), 2),
            "endpoint_stats": self.endpoint_stats
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Obtenir les métriques système détaillées"""
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Mémoire
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disque
            disk = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            # Réseau
            network = psutil.net_io_counters()
            
            # Processus
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": round(cpu_freq.current, 2) if cpu_freq else None,
                    "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "percent": memory.percent,
                    "swap_total_gb": round(swap.total / (1024**3), 2),
                    "swap_used_gb": round(swap.used / (1024**3), 2),
                    "swap_percent": swap.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent,
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0
                },
                "network": {
                    "bytes_sent": network.bytes_sent if network else 0,
                    "bytes_recv": network.bytes_recv if network else 0,
                    "packets_sent": network.packets_sent if network else 0,
                    "packets_recv": network.packets_recv if network else 0
                },
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "cpu_percent": process_cpu,
                    "threads": process.num_threads(),
                    "connections": len(process.connections())
                }
            }
        except Exception as e:
            logger.error(f"Erreur collecte métriques système: {e}")
            return {"error": str(e)}
    
    def get_health_indicators(self) -> Dict[str, Any]:
        """Obtenir les indicateurs de santé"""
        system_metrics = self.get_system_metrics()
        api_metrics = self.get_api_metrics()
        
        indicators = {
            "status": "healthy",
            "alerts": [],
            "warnings": []
        }
        
        # Vérifications système
        if system_metrics.get("cpu", {}).get("percent", 0) > 80:
            indicators["alerts"].append("CPU usage élevé (>80%)")
            indicators["status"] = "degraded"
            
        if system_metrics.get("memory", {}).get("percent", 0) > 85:
            indicators["alerts"].append("Mémoire usage élevé (>85%)")
            indicators["status"] = "degraded"
            
        if system_metrics.get("disk", {}).get("percent", 0) > 90:
            indicators["alerts"].append("Espace disque faible (>90%)")
            indicators["status"] = "critical"
            
        # Vérifications API
        if api_metrics.get("error_rate", 0) > 10:
            indicators["alerts"].append(f"Taux d'erreur élevé ({api_metrics['error_rate']}%)")
            indicators["status"] = "degraded"
            
        if api_metrics.get("avg_response_time", 0) > 2:
            indicators["warnings"].append(f"Temps de réponse élevé ({api_metrics['avg_response_time']}s)")
            
        if api_metrics.get("response_time_p95", 0) > 5:
            indicators["warnings"].append(f"P95 temps de réponse élevé ({api_metrics['response_time_p95']}s)")
        
        return indicators


# Instance globale
metrics_collector = MetricsCollector()
