# 🚀 Guide d'Intégration Frontend - FormForge API

## 📋 Informations Générales

**API Backend :** `https://backend-skum.onrender.com`  
**Version :** 2.0.0  
**Type :** REST API avec authentification SHA256  
**Documentation :** Ce guide complet  

---

## 🔐 Authentification

### **Système de Tokens SHA256**

L'API utilise un système de tokens SHA256 stateless avec rotation automatique.

#### **Endpoints d'Authentification**

```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Utilisateur créé avec succès",
  "user": {
    "id": "user_id",
    "email": "user@example.com"
  }
}
```

```http
POST /api/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Réponse :**
```json
{
  "success": true,
  "message": "Connexion réussie",
  "token": "sha256_token_here",
  "user": {
    "id": "user_id",
    "email": "user@example.com"
  }
}
```

#### **Utilisation du Token**

```javascript
// Stocker le token après connexion
const token = response.data.token;
localStorage.setItem('authToken', token);

// Utiliser le token dans toutes les requêtes authentifiées
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

#### **Vérification du Token**

```http
GET /api/auth/me
Authorization: Bearer sha256_token_here
```

**Réponse :**
```json
{
  "success": true,
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "created_at": "2025-10-26T..."
  }
}
```

---

## 📝 Gestion des Formulaires

### **Créer un Formulaire**

```http
POST /api/forms
Authorization: Bearer token
Content-Type: application/json

{
  "title": "Mon Formulaire",
  "description": "Description du formulaire",
  "settings": {
    "theme": "default",
    "allow_multiple_submissions": false
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "form": {
    "id": "form_id",
    "title": "Mon Formulaire",
    "description": "Description du formulaire",
    "created_by": "user_id",
    "created_at": "2025-10-26T...",
    "settings": {...}
  }
}
```

### **Lister les Formulaires**

```http
GET /api/forms
Authorization: Bearer token
```

**Réponse :**
```json
{
  "success": true,
  "forms": [
    {
      "id": "form_id",
      "title": "Mon Formulaire",
      "description": "Description",
      "created_at": "2025-10-26T...",
      "question_count": 5,
      "response_count": 12
    }
  ],
  "total": 1
}
```

### **Récupérer un Formulaire**

```http
GET /api/forms/{form_id}
Authorization: Bearer token
```

### **Modifier un Formulaire**

```http
PUT /api/forms/{form_id}
Authorization: Bearer token
Content-Type: application/json

{
  "title": "Nouveau Titre",
  "description": "Nouvelle description"
}
```

### **Supprimer un Formulaire**

```http
DELETE /api/forms/{form_id}
Authorization: Bearer token
```

---

## ❓ Gestion des Questions

### **Types de Questions Supportés**

```javascript
const questionTypes = [
  'text',           // Texte simple
  'textarea',       // Zone de texte
  'email',          // Email
  'phone',          // Téléphone
  'url',            // URL
  'date',           // Date
  'time',           // Heure
  'number',         // Nombre
  'choice',         // Choix unique
  'multiple_choice', // Choix multiples
  'checkbox',       // Cases à cocher
  'radio',          // Boutons radio
  'boolean',        // Oui/Non
  'scale'           // Échelle
];
```

### **Créer une Question**

```http
POST /api/forms/{form_id}/questions
Authorization: Bearer token
Content-Type: application/json

{
  "type": "text",
  "text": "Quel est votre nom ?",
  "required": true,
  "order_index": 1,
  "options": [] // Pour les questions à choix
}
```

**Réponse :**
```json
{
  "success": true,
  "question": {
    "id": "question_id",
    "form_id": "form_id",
    "type": "text",
    "text": "Quel est votre nom ?",
    "required": true,
    "order_index": 1,
    "options": [],
    "created_at": "2025-10-26T..."
  }
}
```

### **Questions à Choix Multiple**

```http
POST /api/forms/{form_id}/questions
Authorization: Bearer token
Content-Type: application/json

{
  "type": "multiple_choice",
  "text": "Quels sont vos centres d'intérêt ?",
  "required": true,
  "order_index": 2,
  "options": [
    "Sport",
    "Musique",
    "Cinéma",
    "Lecture"
  ]
}
```

### **Questions Booléennes**

```http
POST /api/forms/{form_id}/questions
Authorization: Bearer token
Content-Type: application/json

{
  "type": "boolean",
  "text": "Acceptez-vous les conditions ?",
  "required": true,
  "order_index": 3
}
```

### **Questions Scale**

```http
POST /api/forms/{form_id}/questions
Authorization: Bearer token
Content-Type: application/json

{
  "type": "scale",
  "text": "Notez votre satisfaction (1-10)",
  "required": true,
  "order_index": 4,
  "options": {
    "min": 1,
    "max": 10,
    "step": 1
  }
}
```

### **Lister les Questions**

```http
GET /api/forms/{form_id}/questions
Authorization: Bearer token
```

### **Modifier une Question**

```http
PUT /api/forms/{form_id}/questions/{question_id}
Authorization: Bearer token
Content-Type: application/json

{
  "text": "Question modifiée",
  "required": false
}
```

### **Supprimer une Question**

```http
DELETE /api/forms/{form_id}/questions/{question_id}
Authorization: Bearer token
```

---

## 📊 Gestion des Réponses

### **Soumettre une Réponse**

```http
POST /api/forms/{form_id}/responses
Content-Type: application/json

{
  "answers": {
    "question_id_1": "Réponse texte",
    "question_id_2": ["Option1", "Option2"],
    "question_id_3": true,
    "question_id_4": 8
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "response": {
    "id": "response_id",
    "form_id": "form_id",
    "answers": {...},
    "submitted_at": "2025-10-26T...",
    "ip_address": "192.168.1.1"
  }
}
```

### **Récupérer les Réponses**

```http
GET /api/forms/{form_id}/responses
Authorization: Bearer token
```

**Réponse :**
```json
{
  "success": true,
  "responses": [
    {
      "id": "response_id",
      "form_id": "form_id",
      "answers": {...},
      "submitted_at": "2025-10-26T...",
      "user_id": "user_id",
      "ip_address": "192.168.1.1"
    }
  ],
  "total": 1
}
```

### **Export Excel/CSV**

```http
GET /api/forms/{form_id}/export/excel
Authorization: Bearer token
```

**Réponse :**
```json
{
  "success": true,
  "excel_content": "csv_content_here",
  "filename": "form_form_id_responses.csv",
  "note": "Export Excel généré au format CSV pour compatibilité"
}
```

---

## 📁 Gestion des Fichiers

### **Upload de Fichier**

```http
POST /api/files/upload
Authorization: Bearer token
Content-Type: multipart/form-data

file: [fichier]
```

**Réponse :**
```json
{
  "success": true,
  "file": {
    "id": "file_id",
    "filename": "document.pdf",
    "size": 1024,
    "content_type": "application/pdf",
    "uploaded_at": "2025-10-26T..."
  }
}
```

### **Télécharger un Fichier**

```http
GET /api/files/{file_id}/download
Authorization: Bearer token
```

### **Types de Fichiers Autorisés**

```javascript
const allowedTypes = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
];
```

---

## 📈 Monitoring et Statistiques

### **Statistiques de Performance**

```http
GET /api/monitoring/performance
Authorization: Bearer token
```

**Réponse :**
```json
{
  "success": true,
  "data": {
    "database_stats": {...},
    "api_metrics": {...}
  },
  "system_stats": {
    "cpu_percent": "***", // Sanitisé pour utilisateurs non-admin
    "memory_percent": "***",
    "disk_usage": "***"
  },
  "user_role": "user",
  "timestamp": "2025-10-26T..."
}
```

### **Statut de Santé**

```http
GET /api/monitoring/health
Authorization: Bearer token
```

### **Dashboard de Monitoring**

```http
GET /api/monitoring/dashboard
Authorization: Bearer token
```

---

## 🚦 Rate Limiting

### **Limites Actuelles (Optimisées)**

| Endpoint             | Limite  | Fenêtre |
| -------------------- | ------- | ------- |
| **Authentification** |         |         |
| `auth_signup`        | 15 req  | 5 min   |
| `auth_signin`        | 25 req  | 5 min   |
| `auth_me`            | 60 req  | 5 min   |
| **Formulaires**      |         |         |
| `forms_create`       | 50 req  | 1 h     |
| `forms_get`          | 200 req | 1 h     |
| `forms_update`       | 60 req  | 1 h     |
| **Questions**        |         |         |
| `questions_create`   | 100 req | 1 h     |
| `questions_get`      | 300 req | 1 h     |
| **Réponses**         |         |         |
| `responses_submit`   | 120 req | 1 h     |
| `responses_get`      | 250 req | 1 h     |

### **Headers de Rate Limiting**

```javascript
// Vérifier les limites dans chaque réponse
const response = await fetch('/api/forms', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});

const limit = response.headers.get('X-RateLimit-Limit');
const remaining = response.headers.get('X-RateLimit-Remaining');
const reset = response.headers.get('X-RateLimit-Reset');

console.log(`Limite: ${limit}, Restant: ${remaining}, Reset: ${reset}`);
```

### **Gestion des Erreurs 429**

```javascript
const handleRateLimit = async (fn, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers.get('Retry-After');
        const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, i) * 1000;
        
        console.log(`Rate limit atteint. Attente de ${waitTime}ms...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      } else {
        throw error;
      }
    }
  }
  throw new Error('Nombre maximum de tentatives atteint');
};
```

---

## 🔒 Sécurité

### **Headers de Sécurité**

L'API applique automatiquement les headers de sécurité suivants :

```http
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Cache-Control: no-store, no-cache, must-revalidate, private
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

### **CORS Configuration**

```javascript
// Configuration CORS autorisée
const corsConfig = {
  origins: [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173'
  ],
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'Accept',
    'Origin'
  ],
  supportsCredentials: true
};
```

### **Isolation des Données**

- ✅ Chaque utilisateur ne peut accéder qu'à ses propres formulaires
- ✅ Les réponses sont isolées par formulaire
- ✅ Les fichiers sont associés aux utilisateurs

---

## 🛠️ Gestion d'Erreurs

### **Codes d'Erreur Courants**

| Code    | Signification    | Action                    |
| ------- | ---------------- | ------------------------- |
| **200** | Succès           | Continuer                 |
| **201** | Créé             | Continuer                 |
| **400** | Requête invalide | Vérifier les données      |
| **401** | Non autorisé     | Reconnecter l'utilisateur |
| **403** | Accès interdit   | Vérifier les permissions  |
| **404** | Non trouvé       | Vérifier l'URL            |
| **429** | Trop de requêtes | Attendre et réessayer     |
| **500** | Erreur serveur   | Contacter le support      |

### **Format des Erreurs**

```json
{
  "success": false,
  "error": "Type d'erreur",
  "message": "Description détaillée",
  "details": {
    "field": "validation_error"
  }
}
```

### **Gestion d'Erreurs JavaScript**

```javascript
const apiCall = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      
      switch (response.status) {
        case 401:
          // Token expiré, rediriger vers login
          localStorage.removeItem('authToken');
          window.location.href = '/login';
          break;
        case 429:
          // Rate limit, afficher message et attendre
          showRateLimitMessage();
          break;
        default:
          throw new Error(errorData.message || 'Erreur inconnue');
      }
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur API:', error);
    throw error;
  }
};
```

---

## 📚 Exemples d'Intégration

### **Exemple Complet : Créer un Formulaire avec Questions**

```javascript
class FormForgeAPI {
  constructor(baseURL = 'https://backend-skum.onrender.com') {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('authToken');
  }

  async createFormWithQuestions(formData, questions) {
    try {
      // 1. Créer le formulaire
      const form = await this.createForm(formData);
      
      // 2. Ajouter les questions
      const createdQuestions = [];
      for (let i = 0; i < questions.length; i++) {
        const question = await this.createQuestion(form.id, {
          ...questions[i],
          order_index: i + 1
        });
        createdQuestions.push(question);
      }
      
      return {
        form,
        questions: createdQuestions
      };
    } catch (error) {
      console.error('Erreur création formulaire:', error);
      throw error;
    }
  }

  async createForm(data) {
    const response = await fetch(`${this.baseURL}/api/forms`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Erreur création formulaire');
    return (await response.json()).form;
  }

  async createQuestion(formId, questionData) {
    const response = await fetch(`${this.baseURL}/api/forms/${formId}/questions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(questionData)
    });
    
    if (!response.ok) throw new Error('Erreur création question');
    return (await response.json()).question;
  }
}

// Utilisation
const api = new FormForgeAPI();

const formData = {
  title: 'Formulaire de Contact',
  description: 'Contactez-nous via ce formulaire'
};

const questions = [
  {
    type: 'text',
    text: 'Votre nom',
    required: true
  },
  {
    type: 'email',
    text: 'Votre email',
    required: true
  },
  {
    type: 'multiple_choice',
    text: 'Sujet',
    required: true,
    options: ['Support', 'Vente', 'Autre']
  },
  {
    type: 'textarea',
    text: 'Votre message',
    required: true
  }
];

api.createFormWithQuestions(formData, questions)
  .then(result => {
    console.log('Formulaire créé:', result);
  })
  .catch(error => {
    console.error('Erreur:', error);
  });
```

### **Exemple : Gestion des Réponses**

```javascript
class ResponseManager {
  constructor(formId) {
    this.formId = formId;
    this.baseURL = 'https://backend-skum.onrender.com';
  }

  async submitResponse(answers) {
    const response = await fetch(`${this.baseURL}/api/forms/${this.formId}/responses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ answers })
    });

    if (!response.ok) throw new Error('Erreur soumission');
    return await response.json();
  }

  async getResponses() {
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${this.baseURL}/api/forms/${this.formId}/responses`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Erreur récupération');
    return await response.json();
  }

  async exportToCSV() {
    const token = localStorage.getItem('authToken');
    const response = await fetch(`${this.baseURL}/api/forms/${this.formId}/export/excel`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error('Erreur export');
    
    const data = await response.json();
    
    // Créer et télécharger le fichier CSV
    const blob = new Blob([data.excel_content], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = data.filename;
    a.click();
    window.URL.revokeObjectURL(url);
  }
}
```

---

## 🎯 Bonnes Pratiques

### **1. Gestion des Tokens**

```javascript
// Vérifier la validité du token au démarrage
const checkAuth = async () => {
  const token = localStorage.getItem('authToken');
  if (!token) return false;
  
  try {
    const response = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.ok;
  } catch {
    localStorage.removeItem('authToken');
    return false;
  }
};
```

### **2. Gestion des États de Chargement**

```javascript
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);

const handleApiCall = async (apiFunction) => {
  setLoading(true);
  setError(null);
  
  try {
    const result = await apiFunction();
    return result;
  } catch (err) {
    setError(err.message);
    throw err;
  } finally {
    setLoading(false);
  }
};
```

### **3. Validation des Données**

```javascript
const validateFormData = (data) => {
  const errors = {};
  
  if (!data.title?.trim()) {
    errors.title = 'Le titre est requis';
  }
  
  if (!data.email || !/\S+@\S+\.\S+/.test(data.email)) {
    errors.email = 'Email invalide';
  }
  
  return Object.keys(errors).length === 0 ? null : errors;
};
```

### **4. Optimisation des Requêtes**

```javascript
// Utiliser des requêtes parallèles quand possible
const loadFormData = async (formId) => {
  const [form, questions, responses] = await Promise.all([
    api.getForm(formId),
    api.getQuestions(formId),
    api.getResponses(formId)
  ]);
  
  return { form, questions, responses };
};
```

---

## 📞 Support et Contact

### **En Cas de Problème**

1. **Vérifier les logs** dans la console du navigateur
2. **Tester les endpoints** avec Postman/Insomnia
3. **Vérifier les headers** de rate limiting
4. **Contacter le backend** avec les détails de l'erreur

### **Informations de Debug**

```javascript
// Activer le mode debug
const DEBUG = true;

const debugLog = (message, data) => {
  if (DEBUG) {
    console.log(`[FormForge API] ${message}`, data);
  }
};

// Utiliser dans les appels API
debugLog('Requête envoyée', { url, method, body });
```

---

## 🎉 Conclusion

Cette API FormForge est **entièrement fonctionnelle** et **optimisée** pour la production avec :

- ✅ **Authentification sécurisée** (SHA256)
- ✅ **Rate limiting équilibré** (UX/Sécurité)
- ✅ **Isolation des données** complète
- ✅ **Headers de sécurité** appliqués
- ✅ **Audit logging** intégré
- ✅ **Monitoring** disponible
- ✅ **Export de données** fonctionnel

**L'API est prête pour l'intégration frontend !** 🚀

---

*Document créé le 26 octobre 2025 - FormForge API Integration Guide*

