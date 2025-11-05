# COUVERTURE FONCTIONNALITÉS API - FormForge Backend

**Expert API & Architecture - 15+ ans d'expérience**
**Date**: 2025-11-05
**Version**: 2.1.0 (Security Hardened)

---

## FONCTIONNALITÉS API DISPONIBLES

### 🔐 AUTHENTIFICATION & GESTION UTILISATEURS

#### Inscription / Connexion
- ✅ **POST /api/auth/signup** - Créer un compte
  - Email + mot de passe fort (validation renforcée)
  - Génération token automatique
  - Rate limiting: 15 req/5min

- ✅ **POST /api/auth/signin** - Se connecter
  - Email + mot de passe
  - Retour token d'authentification
  - Rate limiting: 15 req/5min

#### Gestion de session
- ✅ **GET /api/auth/me** - Informations utilisateur actuel
- ✅ **POST /api/auth/logout** - Déconnexion
- ✅ **POST /api/auth/change-password** - Changer mot de passe
  - Validation ancienne + nouvelle
  - Révocation tokens optionnelle

---

### 📋 GESTION DES FORMULAIRES

#### CRUD Formulaires
- ✅ **POST /api/forms** - Créer un formulaire
  ```json
  {
    "title": "Titre",
    "description": "Description",
    "settings": {"theme": "blue", "public": true}
  }
  ```
  - Rate limiting: 30 req/h
  - Génération ID unique (UUID v4)

- ✅ **GET /api/forms** - Lister mes formulaires
  - Pagination: limit, offset
  - Filtrage par utilisateur automatique
  - Rate limiting: 150 req/h

- ✅ **GET /api/forms/{id}** - Détails d'un formulaire
  - Vérification propriété
  - Inclut toutes les questions
  - Rate limiting: 150 req/h

- ✅ **PUT /api/forms/{id}** - Modifier un formulaire
  - Titre, description, settings
  - Vérification propriété
  - Rate limiting: 40 req/h

- ✅ **DELETE /api/forms/{id}** - Supprimer un formulaire
  - Suppression cascade (questions, réponses)
  - Vérification propriété
  - Rate limiting: 15 req/h

#### Fonctionnalités avancées
- ✅ **POST /api/forms/{id}/duplicate** - Dupliquer un formulaire
  - Clone avec toutes les questions
  - Titre "(Copie)" ajouté

- ✅ **GET /api/forms/{id}/stats** - Statistiques d'un formulaire
  - Nombre de réponses
  - Taux de complétion
  - Dernière réponse

---

### ❓ GESTION DES QUESTIONS

#### CRUD Questions
- ✅ **POST /api/forms/{id}/questions** - Créer une question
  ```json
  {
    "type": "text|choice|multiple_choice|email|phone|url|date|number|scale",
    "text": "Question?",
    "options": ["Option 1", "Option 2"],  // Si type choice
    "required": true,
    "validation": {},
    "order_index": 0
  }
  ```
  - 16 types de questions supportés
  - Rate limiting: 80 req/h

- ✅ **GET /api/forms/{id}/questions** - Lister questions d'un formulaire
  - Triées par order_index
  - Rate limiting: 200 req/h

- ✅ **GET /api/questions/{id}** - Détails d'une question
- ✅ **PUT /api/questions/{id}** - Modifier une question
- ✅ **DELETE /api/questions/{id}** - Supprimer une question

#### Fonctionnalités avancées
- ✅ **PUT /api/forms/{id}/questions/reorder** - Réorganiser les questions
  ```json
  {
    "questions": [
      {"id": "q1", "order_index": 0},
      {"id": "q2", "order_index": 1}
    ]
  }
  ```

- ✅ **POST /api/questions/{id}/validate** - Valider une réponse
  - Validation selon type de question
  - Validation règles personnalisées

---

### 🌐 PUBLICATION & PARTAGE

#### Publication publique
- ✅ **POST /api/forms/{id}/publish** - Publier un formulaire
  - Génère token public unique
  - Change statut à "published"
  - Rate limiting: 20 req/h

- ✅ **GET /api/forms/{id}/public-link** - Obtenir lien public
  - Génère token si pas déjà publié
  - Retourne URL complète

#### Accès public (SANS authentification)
- ✅ **GET /api/public/forms/{token}** - Accéder au formulaire public
  - Pas d'authentification requise
  - Retourne formulaire avec questions
  - Rate limiting: 200 req/h

---

### 📝 GESTION DES RÉPONSES

#### Soumettre des réponses
- ✅ **POST /api/forms/{id}/responses** - Soumettre réponse (authentifié)
  ```json
  {
    "answers": {
      "question_id_1": "Réponse 1",
      "question_id_2": ["Option A", "Option B"]
    },
    "user_id": "optional"
  }
  ```
  - Validation automatique selon type question
  - Enregistrement IP
  - Rate limiting: 100 req/h

- ✅ **POST /api/public/forms/{token}/responses** - Soumettre réponse publique
  - Pas d'authentification requise
  - Validation identique
  - Rate limiting: 150 req/h

#### Consulter les réponses
- ✅ **GET /api/forms/{id}/responses** - Lister toutes les réponses
  - Pagination: limit, offset
  - Seulement propriétaire du formulaire
  - Rate limiting: 200 req/h

- ✅ **GET /api/responses/{id}** - Détails d'une réponse
  - Format complet avec questions

---

### 📊 ANALYTICS & STATISTIQUES

#### Analytics formulaires
- ✅ **GET /api/forms/{id}/analytics** - Analytics d'un formulaire
  - Nombre total de réponses
  - Taux de complétion
  - Distribution des réponses
  - Évolution temporelle

#### Analytics questions
- ✅ **GET /api/forms/{id}/questions/{qid}/analytics** - Analytics d'une question
  - Distribution des réponses
  - Réponses les plus fréquentes
  - Statistiques selon type

---

### 📤 EXPORT DE DONNÉES

#### Export des réponses
- ✅ **GET /api/forms/{id}/export/csv** - Export CSV
  - Format tabulaire
  - En-têtes = questions
  - Lignes = réponses
  - Limit: 1000 réponses max

- ✅ **GET /api/forms/{id}/export/excel** - Export Excel
  - Format CSV (compatible Excel)
  - Même structure que CSV
  - Limit: 1000 réponses max

- ✅ **GET /api/forms/{id}/export/json** - Export JSON
  - Format complet
  - Structure hiérarchique
  - Limit: 1000 réponses max

---

### 📁 GESTION DES FICHIERS

#### Upload / Download
- ✅ **POST /api/files/upload** - Upload fichier
  - Max 16MB
  - Types: images, documents, etc.
  - Stockage: static/uploads/
  - Rate limiting: 20 req/h

- ✅ **GET /api/files/{id}** - Télécharger fichier
  - Vérification propriété
  - Rate limiting: 100 req/h

- ✅ **DELETE /api/files/{id}** - Supprimer fichier
  - Vérification propriété

---

### 📊 MONITORING (Admin uniquement)

#### Métriques système
- ✅ **GET /api/monitoring/performance** - Métriques performance
  - Temps de réponse
  - Requêtes par seconde
  - Erreurs

- ✅ **GET /api/monitoring/health-detailed** - Health check détaillé
  - Status DB
  - Status services
  - Métriques système

- ✅ **GET /api/monitoring/system** - Informations système
  - CPU, RAM, Disk
  - Processus actifs

- ✅ **GET /api/monitoring/dashboard** - Dashboard monitoring
  - Vue d'ensemble
  - Métriques clés

---

## TYPES DE QUESTIONS SUPPORTÉS

### Types de base
1. ✅ **text** - Texte court
2. ✅ **textarea** - Texte long
3. ✅ **email** - Email (validation)
4. ✅ **phone** - Téléphone (validation)
5. ✅ **url** - URL (validation)
6. ✅ **date** - Date
7. ✅ **time** - Heure
8. ✅ **number** - Nombre

### Types choix
9. ✅ **choice** - Choix unique (radio)
10. ✅ **multiple_choice** - Choix multiple (checkbox)
11. ✅ **multiple_choices** - Alias de multiple_choice
12. ✅ **checkbox** - Alias de multiple_choice
13. ✅ **radio** - Alias de choice

### Types avancés
14. ✅ **boolean** - Oui/Non
15. ✅ **scale** - Échelle (1-5, 1-10, etc.)

### Validation supportée
- ✅ Requis / Optionnel
- ✅ Longueur min/max
- ✅ Format (email, phone, url)
- ✅ Plage de valeurs (number, scale)
- ✅ Règles personnalisées (JSON)

---

## SÉCURITÉ & RATE LIMITING

### Authentification
- ✅ Token Bearer (header)
- ✅ Token custom (Authentication-Token header)
- ✅ Session cookies
- ⚠️ Token query string (interdit en production)

### Rate Limiting (Persistant SQLite)
| Route | Limite |
|-------|--------|
| Auth signup/signin | 15 req/5min |
| Forms create | 30 req/h |
| Forms get | 150 req/h |
| Questions create | 80 req/h |
| Responses submit | 100 req/h |
| Export | 1000 réponses max |

### Protections
- ✅ Validation mot de passe forte
- ✅ Révocation tokens (blacklist)
- ✅ Protection XSS (échappement HTML)
- ✅ CORS restrictif
- ✅ Headers de sécurité

---

## USER FLOWS TYPIQUES SUPPORTÉS

### Flow 1: Création de formulaire
1. ✅ Inscription/Connexion → `/api/auth/signup` ou `/api/auth/signin`
2. ✅ Créer formulaire → `/api/forms` POST
3. ✅ Ajouter questions → `/api/forms/{id}/questions` POST (x N)
4. ✅ Réorganiser questions → `/api/forms/{id}/questions/reorder` PUT
5. ✅ Publier formulaire → `/api/forms/{id}/publish` POST
6. ✅ Obtenir lien public → `/api/forms/{id}/public-link` GET

### Flow 2: Réponse à un formulaire
1. ✅ Accéder formulaire public → `/api/public/forms/{token}` GET
2. ✅ Voir questions → Inclus dans réponse ci-dessus
3. ✅ Soumettre réponses → `/api/public/forms/{token}/responses` POST
4. ✅ Confirmation → Status 201

### Flow 3: Consultation des résultats
1. ✅ Connexion → `/api/auth/signin`
2. ✅ Lister formulaires → `/api/forms` GET
3. ✅ Voir détails → `/api/forms/{id}` GET
4. ✅ Voir réponses → `/api/forms/{id}/responses` GET
5. ✅ Voir analytics → `/api/forms/{id}/analytics` GET
6. ✅ Export CSV/Excel → `/api/forms/{id}/export/csv` GET

### Flow 4: Gestion des formulaires
1. ✅ Lister formulaires → `/api/forms` GET
2. ✅ Modifier formulaire → `/api/forms/{id}` PUT
3. ✅ Dupliquer formulaire → `/api/forms/{id}/duplicate` POST
4. ✅ Supprimer formulaire → `/api/forms/{id}` DELETE

---

## FONCTIONNALITÉS MANQUANTES POTENTIELLES

### À vérifier avec user flows Whimsical:
- ❓ Templates de formulaires pré-définis
- ❓ Logique conditionnelle (questions conditionnelles)
- ❓ Webhooks (notifications externes)
- ❓ Intégrations (Google Sheets, Zapier, etc.)
- ❓ Collaboration multi-utilisateurs
- ❓ Branding personnalisé (logo, couleurs)
- ❓ Notifications email répondants
- ❓ Limites de réponses par formulaire
- ❓ Expiration de formulaires
- ❓ Modes de formulaire (quiz, sondage, etc.)

---

## PROCHAINES ÉTAPES

1. **Obtenir les 4 user flows depuis Whimsical**
2. **Analyser chaque étape de chaque flow**
3. **Mapper endpoints API nécessaires**
4. **Identifier gaps éventuels**
5. **Implémenter fonctionnalités manquantes si nécessaire**

---

*Document généré par Expert API - 15+ ans d'expérience*
*Prêt pour analyse détaillée des user flows*
