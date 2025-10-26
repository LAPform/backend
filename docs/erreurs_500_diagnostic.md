# 🔍 Guide de Diagnostic des Erreurs 500 - FormForge API

## 📋 Vue d'Ensemble

Ce document liste les causes courantes d'erreurs 500 (Internal Server Error) rencontrées dans l'API FormForge et leurs solutions.

## 🚨 Erreurs 500 Rencontrées et Résolues

### 1️⃣ **Erreur : `NameError: name 'request' is not defined`**

**Symptômes :**
```
NameError: name 'request' is not defined
File "/opt/render/project/src/app.py", line 51, in log_request_info
    logger.info(f"🔍 REQUEST: {request.method} {request.url}")
```

**Cause :**
- Variable `request` utilisée sans import explicite dans le scope de la fonction
- Problème d'import Flask dans les middlewares

**Solution :**
```python
# ❌ Incorrect
@app.before_request
def log_request_info():
    logger.info(f"🔍 REQUEST: {request.method} {request.url}")

# ✅ Correct
@app.before_request
def log_request_info():
    from flask import request
    logger.info(f"🔍 REQUEST: {request.method} {request.url}")
```

**Fichiers concernés :** `app.py` (middlewares)

---

### 2️⃣ **Erreur : `UnboundLocalError: cannot access local variable 'logger'`**

**Symptômes :**
```
UnboundLocalError: cannot access local variable 'logger' where it is not associated with a value
File "/opt/render/project/src/routes/security_auth.py", line 191, in signin
    logger.info(f"🔍 LOGIN: Début processus de connexion")
```

**Cause :**
- Conflit entre variable `logger` globale et locale
- Redéfinition de `logger` dans le bloc `except` créant un conflit

**Solution :**
```python
# ❌ Incorrect
def signin():
    try:
        logger.info(f"🔍 LOGIN: Début processus de connexion")  # logger non défini localement
        # ... code ...
    except Exception as e:
        logger = logging.getLogger(__name__)  # Redéfinition locale
        logger.error(f"Erreur: {e}")

# ✅ Correct
def signin():
    try:
        import logging
        logger = logging.getLogger(__name__)  # Définition locale explicite
        logger.info(f"🔍 LOGIN: Début processus de connexion")
        # ... code ...
    except Exception as e:
        logger.error(f"Erreur: {e}")  # Utilise le logger défini dans try
```

**Fichiers concernés :** `routes/security_auth.py`

---

### 3️⃣ **Erreur : Import `psutil` non disponible**

**Symptômes :**
```
ImportError: No module named 'psutil'
File "/opt/render/project/src/routes/monitoring.py", line 26, in get_performance_stats
    import psutil
```

**Cause :**
- Librairie `psutil` non installée ou non disponible sur l'environnement de déploiement
- Import non géré avec try/catch

**Solution :**
```python
# ❌ Incorrect
import psutil
import os

system_stats = {
    "cpu_percent": psutil.cpu_percent(interval=1),
    "memory_percent": psutil.virtual_memory().percent,
}

# ✅ Correct
try:
    import psutil
    import os
    
    system_stats = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
    }
except ImportError:
    system_stats = {
        "cpu_percent": 0,
        "memory_percent": 0,
        "note": "psutil non disponible"
    }
```

**Fichiers concernés :** `routes/monitoring.py`

---

### 4️⃣ **Erreur : Dossier d'upload inexistant**

**Symptômes :**
```
FileNotFoundError: [Errno 2] No such file or directory: 'static/uploads/images'
File "/opt/render/project/src/utils/file_manager.py", line 82, in get_upload_path
    os.makedirs(category_folder, exist_ok=True)
```

**Cause :**
- Dossier parent `static/uploads` n'existe pas
- `os.makedirs()` ne crée que le dossier spécifié, pas les parents

**Solution :**
```python
# ❌ Incorrect
upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
category_folder = os.path.join(upload_folder, category)
os.makedirs(category_folder, exist_ok=True)  # Échoue si upload_folder n'existe pas

# ✅ Correct
upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
os.makedirs(upload_folder, exist_ok=True)  # Créer le dossier parent d'abord
category_folder = os.path.join(upload_folder, category)
os.makedirs(category_folder, exist_ok=True)  # Puis le dossier de catégorie
```

**Fichiers concernés :** `utils/file_manager.py`

---

## 🔧 Méthodes de Diagnostic

### 1️⃣ **Vérification des Logs Render**

**Commandes utiles :**
```bash
# Vérifier les logs en temps réel
# Dans l'interface Render : Logs > Live Logs

# Patterns à rechercher :
- "NameError"
- "UnboundLocalError" 
- "ImportError"
- "FileNotFoundError"
- "ModuleNotFoundError"
```

### 2️⃣ **Tests d'Endpoints**

**Tests systématiques :**
```powershell
# Test de santé
Invoke-WebRequest -Uri "https://backend-skum.onrender.com/api/health" -Method GET

# Test d'authentification
$body = '{"email": "test@example.com", "password": "test123"}'
Invoke-WebRequest -Uri "https://backend-skum.onrender.com/api/auth/signin" -Method POST -Body $body -ContentType "application/json"

# Test d'endpoints protégés
$headers = @{"Authorization" = "Bearer [token]"}
Invoke-WebRequest -Uri "https://backend-skum.onrender.com/api/[endpoint]" -Method GET -Headers $headers
```

### 3️⃣ **Vérification des Dépendances**

**Fichier :** `requirements.txt`
```bash
# Vérifier que toutes les dépendances sont listées
psutil==5.9.0
Flask==3.0.0
# etc...
```

---

## 🛠️ Solutions Préventives

### 1️⃣ **Gestion des Imports**

**Règle :** Toujours gérer les imports optionnels avec try/catch
```python
try:
    import module_optionnel
    # Utiliser le module
except ImportError:
    # Fallback ou valeurs par défaut
    pass
```

### 2️⃣ **Gestion des Variables**

**Règle :** Définir explicitement les variables dans chaque scope
```python
def fonction():
    import logging
    logger = logging.getLogger(__name__)  # Définition explicite
    # ... reste du code
```

### 3️⃣ **Gestion des Dossiers**

**Règle :** Créer les dossiers parents avant les sous-dossiers
```python
os.makedirs(parent_folder, exist_ok=True)
os.makedirs(child_folder, exist_ok=True)
```

### 4️⃣ **Tests de Déploiement**

**Checklist :**
- [ ] Tous les endpoints retournent 200/401/404 (pas de 500)
- [ ] Authentification fonctionne
- [ ] Création de ressources fonctionne
- [ ] Logs sans erreurs critiques

---

## 📊 Patterns d'Erreurs 500 Courants

| Pattern | Cause | Solution |
|---------|-------|----------|
| `NameError: name 'X' is not defined` | Import manquant dans le scope | Ajouter `from module import X` |
| `UnboundLocalError` | Conflit variable globale/locale | Définir explicitement la variable |
| `ImportError: No module named 'X'` | Dépendance manquante | Gérer avec try/catch |
| `FileNotFoundError` | Dossier inexistant | Créer les dossiers parents |
| `AttributeError: 'NoneType'` | Objet non initialisé | Vérifier l'initialisation |

---

## 🚀 Actions Correctives Rapides

### 1️⃣ **En cas d'erreur 500 :**

1. **Vérifier les logs Render** pour l'erreur exacte
2. **Identifier le pattern** dans cette liste
3. **Appliquer la solution** correspondante
4. **Tester l'endpoint** après correction
5. **Déployer** avec `git push origin main`

### 2️⃣ **Tests de Validation :**

```powershell
# Test rapide de tous les endpoints principaux
$endpoints = @(
    "/api/health",
    "/api/auth/test", 
    "/api/docs/examples",
    "/api/docs/guide"
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri "https://backend-skum.onrender.com$endpoint" -Method GET
        Write-Host "✅ $endpoint : $($response.StatusCode)"
    } catch {
        Write-Host "❌ $endpoint : $($_.Exception.Response.StatusCode)"
    }
}
```

---

## 📝 Notes Importantes

- **Render Free Tier** : Limitations sur les dépendances système
- **SQLite** : Base de données utilisée (pas de PostgreSQL)
- **Python 3.13** : Version utilisée (compatibilité à vérifier)
- **Flask-Security-Too** : Extension d'authentification principale

---

**Dernière mise à jour :** 25 Octobre 2025  
**Version API :** 2.0.0  
**Environnement :** Production (Render)
