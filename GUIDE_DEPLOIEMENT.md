# GUIDE DE DÉPLOIEMENT - FormForge API
## Configuration après corrections de sécurité

**Date**: 2025-10-31  
**Objectif**: S'assurer que l'API reste accessible après le push des corrections

---

## ✅ CONFIGURATION ACTUELLE (render.yaml)

Votre `render.yaml` est **déjà correctement configuré** :

```yaml
services:
  - type: web
    name: formforge-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
    plan: starter
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true  # ✅ Généré automatiquement par Render
      - key: DATABASE_URL
        value: sqlite:///formforge_prod.db
      - key: PYTHONPATH
        value: .
```

### ✅ Variables déjà configurées

1. **SECRET_KEY** : ✅ `generateValue: true` - Render génère automatiquement une clé sécurisée
2. **FLASK_ENV** : ✅ `production` - Activé
3. **DATABASE_URL** : ✅ Configuré

---

## ⚠️ CONFIGURATION RECOMMANDÉE (CORS)

### Problème potentiel

Si votre frontend est déployé sur un domaine différent de `localhost`, vous devez ajouter `CORS_ORIGINS` pour autoriser les requêtes.

### Solution 1 : Ajouter dans render.yaml (recommandé)

Modifier `render.yaml` pour ajouter `CORS_ORIGINS` :

```yaml
envVars:
  - key: FLASK_ENV
    value: production
  - key: SECRET_KEY
    generateValue: true
  - key: DATABASE_URL
    value: sqlite:///formforge_prod.db
  - key: PYTHONPATH
    value: .
  # Ajouter cette ligne si votre frontend est sur un autre domaine
  - key: CORS_ORIGINS
    value: https://votre-frontend.onrender.com,https://www.votre-domaine.com
```

**Important** : Remplacez les URLs par celles de votre frontend réel.

### Solution 2 : Configurer via l'interface Render

1. Aller sur https://dashboard.render.com
2. Sélectionner votre service `formforge-backend`
3. Aller dans **Environment** → **Environment Variables**
4. Ajouter :
   - **Key**: `CORS_ORIGINS`
   - **Value**: `https://votre-frontend.onrender.com,https://www.votre-domaine.com`

---

## 🔍 VÉRIFICATIONS APRÈS DÉPLOIEMENT

### 1. Vérifier que l'API démarre

Après le push, vérifiez les logs Render :

```bash
# Les logs doivent montrer :
# ✅ "🔒 Middlewares de sécurité configurés avec succès"
# ✅ "Base de données initialisée avec succès"
# ✅ Pas d'erreur "SECRET_KEY doit être défini"
```

Si vous voyez cette erreur :
```
ValueError: SECRET_KEY doit être défini en production
```

**Solution** : Vérifiez que `SECRET_KEY` avec `generateValue: true` est bien dans `render.yaml`

### 2. Tester l'accès à l'API

```bash
# Health check (doit retourner 200)
curl https://backend-skum.onrender.com/api/health

# Devrait retourner :
{
  "status": "healthy",
  "api": "FormForge",
  "version": "2.0.0"
}
```

### 3. Tester l'authentification

```bash
# Inscription (doit fonctionner avec mot de passe fort)
curl -X POST https://backend-skum.onrender.com/api/auth/register-json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!"
  }'

# Connexion (doit retourner un token)
curl -X POST https://backend-skum.onrender.com/api/auth/login-json \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!"
  }'
```

### 4. Vérifier que les endpoints debug sont bloqués

```bash
# Doit retourner 403 en production
curl https://backend-skum.onrender.com/api/debug/request

# Devrait retourner :
{
  "error": "Endpoint non disponible en production"
}
```

---

## 📋 CHECKLIST POST-DÉPLOIEMENT

### ✅ Avant le push

- [x] `render.yaml` contient `SECRET_KEY` avec `generateValue: true`
- [x] `render.yaml` contient `FLASK_ENV=production`
- [x] Code poussé sur la branche principale (ou branch connectée à Render)

### ✅ Après le push

- [ ] Render a bien déployé (vérifier les logs de build)
- [ ] Health check fonctionne : `GET /api/health`
- [ ] Inscription fonctionne avec mot de passe fort (8+ caractères)
- [ ] Connexion fonctionne et retourne un token
- [ ] Endpoints debug retournent 403
- [ ] Frontend peut se connecter (si CORS_ORIGINS configuré)

---

## 🚨 PROBLÈMES POTENTIELS ET SOLUTIONS

### Problème 1 : L'API ne démarre pas

**Erreur** : `ValueError: SECRET_KEY doit être défini en production`

**Solution** :
1. Vérifier que `render.yaml` contient bien `SECRET_KEY` avec `generateValue: true`
2. Si le problème persiste, aller dans Render → Environment → Ajouter manuellement `SECRET_KEY` avec une valeur générée

---

### Problème 2 : Erreur CORS depuis le frontend

**Erreur** : `Access to fetch at 'https://backend-skum.onrender.com' from origin 'https://votre-frontend.com' has been blocked by CORS policy`

**Solution** :
1. Ajouter `CORS_ORIGINS` dans `render.yaml` ou dans l'interface Render
2. Valeur : `https://votre-frontend.com` (sans slash final)
3. Pour plusieurs origines : `https://frontend1.com,https://frontend2.com`

---

### Problème 3 : Erreur "Mot de passe trop court"

**Erreur** : `Le mot de passe doit contenir au moins 8 caractères`

**Solution** : C'est normal ! La validation a été renforcée. Utiliser un mot de passe :
- Minimum 8 caractères
- Au moins 1 majuscule
- Au moins 1 minuscule
- Au moins 1 chiffre
- Au moins 1 caractère spécial

Exemple : `Password123!`

---

## 🔒 PROTECTIONS ACTIVÉES EN PRODUCTION

Après le déploiement avec `FLASK_ENV=production` :

1. ✅ **SECRET_KEY** : Obligatoire (généré automatiquement par Render)
2. ✅ **CORS** : Origines limitées (localhost par défaut, ou CORS_ORIGINS si défini)
3. ✅ **Endpoints debug** : Désactivés (retournent 403)
4. ✅ **Validation mot de passe** : Renforcée (8+ caractères avec complexité)
5. ✅ **DEBUG** : Désactivé (pas de stack traces exposés)

---

## 📝 RÉSUMÉ

### ✅ Votre API reste accessible normalement

**Points importants** :
1. ✅ **SECRET_KEY** : Déjà configuré dans `render.yaml` avec `generateValue: true`
2. ✅ **FLASK_ENV** : Déjà à `production`
3. ⚠️ **CORS_ORIGINS** : À ajouter si votre frontend est sur un autre domaine

**Accès à l'API** :
- ✅ Tous les endpoints fonctionnent normalement
- ✅ Authentification fonctionne (avec validation mot de passe renforcée)
- ✅ Endpoints debug bloqués (normal, protection active)
- ⚠️ CORS peut bloquer si frontend sur autre domaine (solution ci-dessus)

---

## 🧪 TEST APRÈS DÉPLOIEMENT

Utiliser le script de test :

```bash
# Tester l'API en production
BASE_URL=https://backend-skum.onrender.com python scripts/test_api_complet.py
```

Tous les tests doivent passer comme avant (22/22).

---

*Guide mis à jour après corrections de sécurité*

