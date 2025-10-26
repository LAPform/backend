"""
Middleware de sécurité pour FormForge
"""

import logging
from flask import request, current_app
from functools import wraps

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Middleware pour ajouter des headers de sécurité"""

    @staticmethod
    def add_security_headers(response):
        """Ajouter les headers de sécurité à toutes les réponses"""
        try:
            # Headers de sécurité essentiels
            security_headers = {
                # Protection contre le clickjacking
                'X-Frame-Options': 'DENY',
                
                # Protection contre le sniffing de type MIME
                'X-Content-Type-Options': 'nosniff',
                
                # Protection XSS (navigateurs modernes)
                'X-XSS-Protection': '1; mode=block',
                
                # Politique de référent
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                
                # Politique de permissions
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
                
                # Content Security Policy (CSP) basique
                'Content-Security-Policy': (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self'; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none';"
                ),
                
                # Cache Control pour les réponses sensibles
                'Cache-Control': 'no-store, no-cache, must-revalidate, private',
                'Pragma': 'no-cache',
                'Expires': '0',
                
                # Server header masqué
                'Server': 'FormForge-API',
                
                # HSTS (HTTP Strict Transport Security) - seulement en HTTPS
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            }
            
            # Ajouter les headers
            for header, value in security_headers.items():
                response.headers[header] = value
                
            logger.debug("Headers de sécurité ajoutés à la réponse")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des headers de sécurité: {e}")
            
        return response

    @staticmethod
    def log_security_events():
        """Logger les événements de sécurité suspects"""
        try:
            # Détecter les tentatives d'injection
            user_agent = request.headers.get('User-Agent', '')
            if any(pattern in user_agent.lower() for pattern in ['sqlmap', 'nikto', 'nmap', 'scanner']):
                logger.warning(f"🔒 SECURITY: Tentative de scan détectée - User-Agent: {user_agent}")
                
            # Détecter les requêtes suspectes
            if request.method == 'OPTIONS' and request.path.startswith('/api/'):
                origin = request.headers.get('Origin', '')
                if origin and not origin.startswith(('http://localhost', 'https://localhost')):
                    logger.warning(f"🔒 SECURITY: Requête CORS suspecte depuis: {origin}")
                    
        except Exception as e:
            logger.error(f"Erreur lors du logging de sécurité: {e}")


class CORSSecurityMiddleware:
    """Middleware pour sécuriser CORS"""
    
    @staticmethod
    def configure_cors(app):
        """Configurer CORS de manière sécurisée"""
        from flask_cors import CORS
        
        # Configuration CORS sécurisée
        cors_config = {
            'origins': [
                'http://localhost:3000',
                'http://localhost:5173',
                'http://127.0.0.1:3000',
                'http://127.0.0.1:5173',
                # Ajouter ici les domaines de production autorisés
            ],
            'methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': [
                'Content-Type',
                'Authorization',
                'X-Requested-With',
                'Accept',
                'Origin',
                'Access-Control-Request-Method',
                'Access-Control-Request-Headers'
            ],
            'expose_headers': [
                'Content-Type',
                'Authorization',
                'X-Total-Count'
            ],
            'supports_credentials': True,
            'max_age': 3600,  # Cache preflight pour 1 heure
        }
        
        # Appliquer la configuration CORS
        CORS(app, **cors_config)
        
        logger.info("Configuration CORS sécurisée appliquée")


def require_https(f):
    """Décorateur pour forcer HTTPS en production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.debug and not request.is_secure:
            logger.warning(f"🔒 SECURITY: Tentative d'accès HTTP en production: {request.url}")
            return {
                'error': 'HTTPS required',
                'message': 'Cette API nécessite une connexion sécurisée HTTPS'
            }, 400
        return f(*args, **kwargs)
    return decorated_function


def security_monitoring():
    """Monitoring des événements de sécurité"""
    try:
        # Logger les requêtes importantes
        if request.method in ['POST', 'PUT', 'DELETE']:
            logger.info(f"🔒 SECURITY: Opération {request.method} sur {request.path} depuis {request.remote_addr}")
            
        # Détecter les patterns suspects
        if request.path.startswith('/api/auth/'):
            logger.info(f"🔒 SECURITY: Tentative d'authentification depuis {request.remote_addr}")
            
    except Exception as e:
        logger.error(f"Erreur monitoring sécurité: {e}")


def setup_security_middleware(app):
    """Configurer tous les middlewares de sécurité"""
    try:
        # Ajouter les headers de sécurité à toutes les réponses
        app.after_request(SecurityHeadersMiddleware.add_security_headers)
        
        # Logger les événements de sécurité
        app.before_request(SecurityHeadersMiddleware.log_security_events)
        app.before_request(security_monitoring)
        
        # Configurer CORS de manière sécurisée
        CORSSecurityMiddleware.configure_cors(app)
        
        logger.info("🔒 Middlewares de sécurité configurés avec succès")
        
    except Exception as e:
        logger.error(f"Erreur configuration middlewares de sécurité: {e}")
        raise
