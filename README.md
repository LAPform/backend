# FormForge POC - Backend Flask

## 🎯 Description

Backend Flask pour le POC FormForge - Clone de Google Forms. Cette implémentation fournit une API REST complète pour la création, gestion et collecte de formulaires.

## 🚀 Fonctionnalités

### ✅ Implémentées
- **CRUD Formulaires** : Création, lecture, modification, suppression
- **Gestion Questions** : Types multiples (texte, choix, échelle, etc.)
- **Collecte Réponses** : Stockage et validation des réponses
- **Export Données** : CSV, Excel, JSON
- **Analytics** : Statistiques et analyses
- **API REST** : Endpoints complets

### 📋 Types de Questions Supportés
- Texte court
- Texte long (paragraphe)
- Choix multiple (radio)
- Cases à cocher
- Échelle linéaire
- Date/Heure
- Email
- Nombre
- Upload de fichiers

## 🏗️ Architecture

```
POC/
├── app.py                 # Application principale
├── config.py             # Configuration
├── requirements.txt      # Dépendances
├── Procfile             # Déploiement
├── render.yaml          # Configuration Render
├── models/              # Modèles de données
│   ├── database.py      # Gestionnaire PostgreSQL
│   ├── form.py          # Modèle Formulaire
│   ├── question.py      # Modèle Question
│   └── response.py      # Modèle Réponse
├── routes/              # Routes API
│   ├── forms.py         # CRUD formulaires
│   ├── questions.py     # Gestion questions
│   └── responses.py     # Gestion réponses
└── utils/               # Utilitaires
    ├── validators.py    # Validation données
    └── exporters.py     # Export CSV/Excel/JSON
```

## 🗄️ Base de Données

### Tables Principales
- **forms** : Métadonnées des formulaires
- **questions** : Questions avec types et validation
- **responses** : Réponses des utilisateurs
- **users** : Utilisateurs du système

### Schéma SQLite
```sql
-- Formulaires
CREATE TABLE forms (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    settings TEXT DEFAULT '{}',
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions
CREATE TABLE questions (
    id TEXT PRIMARY KEY,
    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    text TEXT NOT NULL,
    options TEXT DEFAULT '[]',
    required BOOLEAN DEFAULT FALSE,
    validation TEXT DEFAULT '{}',
    order_index INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Réponses
CREATE TABLE responses (
    id TEXT PRIMARY KEY,
    form_id TEXT REFERENCES forms(id) ON DELETE CASCADE,
    answers TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    ip_address TEXT
);

-- Utilisateurs
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

## 🚀 Installation et Démarrage

### 1. Installation Locale
```bash
# Cloner le projet
cd POC

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp env.example .env
# Modifier .env avec vos paramètres

# Démarrer l'application
python app.py
```

### 2. Déploiement Render
```bash
# Le fichier render.yaml est configuré pour un déploiement automatique
# Connecter votre repository GitHub à Render
# La base de données SQLite sera créée automatiquement
# Compatible avec le plan gratuit de Render
```

## 📡 API Endpoints

### Formulaires
```
POST   /api/forms              # Créer un formulaire
GET    /api/forms              # Lister les formulaires
GET    /api/forms/{id}         # Récupérer un formulaire
PUT    /api/forms/{id}         # Modifier un formulaire
DELETE /api/forms/{id}         # Supprimer un formulaire
GET    /api/forms/{id}/stats   # Statistiques d'un formulaire
POST   /api/forms/{id}/duplicate # Dupliquer un formulaire
```

### Questions
```
POST   /api/forms/{id}/questions     # Créer une question
GET    /api/forms/{id}/questions     # Lister les questions
GET    /api/questions/{id}           # Récupérer une question
PUT    /api/questions/{id}           # Modifier une question
DELETE /api/questions/{id}           # Supprimer une question
PUT    /api/forms/{id}/questions/reorder # Réorganiser les questions
POST   /api/questions/{id}/validate  # Valider une réponse
```

### Réponses
```
POST   /api/forms/{id}/responses     # Soumettre une réponse
GET    /api/forms/{id}/responses     # Récupérer les réponses
GET    /api/responses/{id}           # Récupérer une réponse
GET    /api/forms/{id}/analytics     # Analytics d'un formulaire
GET    /api/forms/{id}/export/csv    # Export CSV
GET    /api/forms/{id}/export/excel  # Export Excel
```

## 🔧 Configuration

### Variables d'Environnement
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
CORS_ORIGINS=http://localhost:3000
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216
```

### Base de Données
- **Développement** : SQLite local
- **Production** : SQLite (compatible Render gratuit)
- **Migration** : Automatique au démarrage

## 📊 Exemples d'Utilisation

### Créer un Formulaire
```bash
curl -X POST http://localhost:5000/api/forms \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Mon Formulaire",
    "description": "Description du formulaire",
    "settings": {"theme": "default"}
  }'
```

### Ajouter une Question
```bash
curl -X POST http://localhost:5000/api/forms/{form_id}/questions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "text",
    "text": "Votre nom",
    "required": true
  }'
```

### Soumettre une Réponse
```bash
curl -X POST http://localhost:5000/api/forms/{form_id}/responses \
  -H "Content-Type: application/json" \
  -d '{
    "answers": {
      "question_id": "votre_reponse"
    }
  }'
```

## 🧪 Tests

```bash
# Installer pytest
pip install pytest pytest-flask

# Exécuter les tests
pytest tests/
```

## 📈 Performance

- **Connexions DB** : Pool de connexions PostgreSQL
- **Cache** : Possible avec Redis (futur)
- **Export** : Optimisé pour gros volumes
- **Validation** : Côté serveur et client

## 🔒 Sécurité

- **Validation** : Toutes les entrées validées
- **CORS** : Configuré pour les domaines autorisés
- **SQL Injection** : Protection avec paramètres
- **XSS** : Échappement des données

## 🚀 Déploiement

### Render (Recommandé)
1. Connecter le repository GitHub
2. Render détecte automatiquement le `render.yaml`
3. La base PostgreSQL est créée automatiquement
4. L'application est déployée automatiquement

### Autres Plateformes
- **Heroku** : Compatible avec Procfile
- **Railway** : Configuration similaire
- **AWS** : Avec RDS PostgreSQL

## 📝 Logs et Monitoring

- **Logs** : Structurés avec timestamps
- **Erreurs** : Gestion centralisée
- **Métriques** : Endpoints de santé
- **Debug** : Mode développement

## 🔄 Évolutions Futures

- [ ] Authentification utilisateurs
- [ ] Cache Redis
- [ ] Webhooks
- [ ] Templates de formulaires
- [ ] Logique conditionnelle
- [ ] Intégrations tierces

## 📞 Support

Pour toute question ou problème :
1. Vérifier les logs de l'application
2. Tester les endpoints avec curl/Postman
3. Vérifier la configuration de la base de données

## 📄 Licence

Projet POC - Usage interne uniquement
