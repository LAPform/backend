# Documentation Swagger - Flask-RESTx

## ✅ Modifications apportées

### 1. **Infrastructure Flask-RESTx**

- ✅ Installation de Flask-RESTx avec configuration Swagger UI
- ✅ Création de modèles de documentation réutilisables (`utils/api_models.py`)
- ✅ Configuration de l'API dans `app.py` avec :
  - Swagger UI à `/api/docs/`
  - Authentification Bearer token documentée
  - Validation automatique des requêtes
  - Version 2.0.0 de l'API

### 2. **Namespaces refactorisés** ✅

Les routes suivantes ont été migrées vers Flask-RESTx avec documentation complète :

#### **Forms** (`routes/forms_ns.py`)
- ✅ 10 endpoints documentés
- ✅ POST `/api/forms` - Créer un formulaire
- ✅ GET `/api/forms` - Lister les formulaires
- ✅ GET `/api/forms/{id}` - Récupérer un formulaire
- ✅ PUT `/api/forms/{id}` - Modifier un formulaire
- ✅ DELETE `/api/forms/{id}` - Supprimer un formulaire
- ✅ GET `/api/forms/{id}/stats` - Statistiques
- ✅ POST `/api/forms/{id}/duplicate` - Dupliquer
- ✅ POST `/api/forms/{id}/publish` - Publier
- ✅ GET `/api/forms/{id}/public-link` - Lien public
- ✅ GET `/api/public/forms/{token}` - Accès public (blueprint séparé)

#### **Questions** (`routes/questions_ns.py`)
- ✅ 7 endpoints documentés
- ✅ POST `/api/questions/forms/{id}/questions` - Créer une question
- ✅ GET `/api/questions/forms/{id}/questions` - Lister les questions
- ✅ GET `/api/questions/{id}` - Récupérer une question
- ✅ PUT `/api/questions/{id}` - Modifier une question
- ✅ DELETE `/api/questions/{id}` - Supprimer une question
- ✅ PUT `/api/questions/forms/{id}/questions/reorder` - Réorganiser
- ✅ POST `/api/questions/{id}/validate` - Valider une réponse

#### **Responses** (`routes/responses_ns.py`)
- ✅ 9 endpoints documentés
- ✅ POST `/api/responses/forms/{id}/responses` - Soumettre une réponse
- ✅ GET `/api/responses/forms/{id}/responses` - Lister les réponses
- ✅ GET `/api/responses/{id}` - Récupérer une réponse
- ✅ GET `/api/responses/forms/{id}/analytics` - Analytics du formulaire
- ✅ GET `/api/responses/forms/{id}/questions/{q_id}/analytics` - Analytics question
- ✅ GET `/api/responses/forms/{id}/export/csv` - Export CSV
- ✅ GET `/api/responses/forms/{id}/export/excel` - Export Excel
- ✅ GET `/api/responses/forms/{id}/export/json` - Export JSON
- ✅ POST `/api/public/forms/{token}/responses` - Réponse publique (blueprint séparé)

### 3. **Modèles de documentation** (`utils/api_models.py`)

Tous les schémas Swagger sont définis avec types, validations et exemples :

- **Authentification** : Signup, Signin, ChangePassword, UserInfo
- **Formulaires** : FormCreate, FormUpdate, Form, FormStats
- **Questions** : QuestionCreate, QuestionUpdate, Question
- **Réponses** : ResponseCreate, Response, Analytics
- **Fichiers** : FileUploadResponse
- **Génériques** : Success, Error, Health, Pagination

### 4. **Routes publiques**

Les routes sans authentification ont été séparées en blueprints distincts :
- `public_forms_bp` - Accès public aux formulaires
- `public_responses_bp` - Soumission de réponses publiques

Ces blueprints sont enregistrés automatiquement par la fonction `register_namespaces()`.

---

## 🚀 Comment accéder à Swagger UI

### **URL de la documentation interactive**

```
http://localhost:5000/api/docs/
```

Ou en production :
```
https://backend-skum.onrender.com/api/docs/
```

### **Redirection automatique**

La route `/api/docs` redirige automatiquement vers `/api/docs/` (Swagger UI).

---

## 📖 Utilisation de Swagger UI

### 1. **Explorer les endpoints**

- Ouvrez `/api/docs/` dans votre navigateur
- Tous les endpoints sont organisés par namespace (forms, questions, responses)
- Cliquez sur un endpoint pour voir :
  - Description
  - Paramètres requis/optionnels
  - Schémas de requête/réponse
  - Codes de réponse HTTP

### 2. **Tester les endpoints**

1. Cliquez sur "Authorize" en haut à droite
2. Entrez votre token Bearer : `Bearer <votre_token>`
3. Cliquez sur "Authorize" puis "Close"
4. Sélectionnez un endpoint
5. Cliquez sur "Try it out"
6. Remplissez les paramètres
7. Cliquez sur "Execute"
8. Voir la réponse dans la section "Response"

### 3. **Authentification**

Deux types d'authentification sont supportés :

- **Bearer Token** (recommandé)
  ```
  Authorization: Bearer <token>
  ```

- **Authentication-Token** (Flask-Security)
  ```
  Authentication-Token: <token>
  ```

Pour obtenir un token :
1. POST `/api/auth/signup` - Créer un compte
2. POST `/api/auth/signin` - Se connecter
3. Utiliser le `token` retourné

---

## 🔧 Structure du code

```
backend/
├── app.py                          # Configuration Flask-RESTx
├── utils/
│   └── api_models.py               # Modèles Swagger réutilisables
├── routes/
│   ├── __init__.py                 # Enregistrement des namespaces
│   ├── forms_ns.py                 # Namespace Forms ✅
│   ├── questions_ns.py             # Namespace Questions ✅
│   ├── responses_ns.py             # Namespace Responses ✅
│   ├── forms.py                    # Ancien blueprint (compatibilité)
│   ├── questions.py                # Ancien blueprint (compatibilité)
│   ├── responses.py                # Ancien blueprint (compatibilité)
│   ├── security_auth.py            # À migrer
│   ├── files.py                    # À migrer
│   ├── monitoring.py               # À migrer
│   └── docs.py                     # Redirection vers Swagger
```

---

## ⚙️ Configuration

Dans `app.py`, l'API Flask-RESTx est configurée avec :

```python
api = Api(
    api_blueprint,
    version='2.0.0',
    title='FormForge API',
    description='API REST complète pour FormForge - Clone de Google Forms',
    doc='/docs/',  # Swagger UI
    authorizations={
        'Bearer': {...},
        'AuthToken': {...}
    },
    security='Bearer',
    validate=True,  # Validation automatique
    ordered=True,
)
```

---

## 📝 Prochaines étapes

### Routes restantes à migrer :

- ⏳ **Authentication** (`routes/security_auth.py`)
  - POST `/api/auth/signup`
  - POST `/api/auth/signin`
  - POST `/api/auth/logout`
  - GET `/api/auth/me`
  - POST `/api/auth/change-password`
  - GET `/api/auth/test`

- ⏳ **Files** (`routes/files.py`)
  - POST `/api/files/upload`
  - GET `/api/files/{file_id}`

- ⏳ **Monitoring** (`routes/monitoring.py`)
  - GET `/api/health`
  - GET `/api/monitoring/basic-test`
  - GET `/api/monitoring/performance`

### Améliorations futures :

1. **Modèles de réponse** : Ajouter `@api.marshal_with()` pour typer les réponses
2. **Validation avancée** : Utiliser `api.expect(validate=True)` partout
3. **Exemples** : Ajouter plus d'exemples de requêtes dans la doc
4. **Groupes de tags** : Organiser les endpoints par fonctionnalité
5. **Schémas imbriqués** : Améliorer les modèles pour mieux refléter la structure

---

## 🐛 Dépannage

### **Swagger UI ne s'affiche pas**

1. Vérifier que Flask-RESTx est installé : `pip install flask-restx`
2. Vérifier les logs au démarrage : "Flask-RESTx initialisé avec succès"
3. Accéder à `/api/docs/` (avec le slash final)

### **Endpoints manquants dans Swagger**

1. Vérifier que le namespace est bien enregistré dans `routes/__init__.py`
2. Vérifier que `register_namespaces()` est appelé dans `app.py`
3. Relancer l'application

### **Erreur 404 sur les routes**

- Les anciens blueprints (`/api/forms/*`) sont toujours actifs pour compatibilité
- Les namespaces utilisent les mêmes URLs mais avec validation Swagger
- Les deux systèmes coexistent temporairement

---

## ✨ Avantages de Flask-RESTx

1. **Documentation automatique** : Swagger UI généré automatiquement
2. **Validation des requêtes** : Les données sont validées avant d'atteindre le code
3. **Typage fort** : Les modèles définissent les schémas attendus
4. **Testabilité** : Swagger UI permet de tester directement les endpoints
5. **Maintenabilité** : Code plus organisé et documentation toujours à jour
6. **Standards** : Conforme à OpenAPI Specification 2.0

---

## 📚 Ressources

- [Flask-RESTx Documentation](https://flask-restx.readthedocs.io/)
- [Swagger UI](https://swagger.io/tools/swagger-ui/)
- [OpenAPI Specification](https://swagger.io/specification/v2/)

---

**Auteur** : Claude
**Date** : 2025-11-05
**Version** : 2.0.0
