# 🧪 GUIDE DE TEST API FORMFORGE - PRODUCTION

## URL de l'API
```
https://backend-skum.onrender.com
```

## ⚠️ IMPORTANT
L'API est protégée par un WAF/Firewall qui bloque les accès automatisés.
**Ces tests doivent être exécutés depuis votre machine locale ou navigateur.**

---

## 📋 TESTS À EXÉCUTER

### Test 1: Health Check ✅

**Commande curl:**
```bash
curl -X GET "https://backend-skum.onrender.com/api/health" \
  -H "Accept: application/json" \
  -H "User-Agent: Mozilla/5.0"
```

**Résultat attendu:** HTTP 200
```json
{
  "status": "healthy",
  "message": "FormForge POC Backend with Flask-Security-Too is running",
  "version": "2.0.0",
  "security": "Flask-Security-Too"
}
```

---

### Test 2: Inscription utilisateur 📝

**Remplacer `{TIMESTAMP}` par le timestamp actuel** (ex: 1699012345)

```bash
curl -X POST "https://backend-skum.onrender.com/api/auth/signup" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test-{TIMESTAMP}@example.com",
    "password": "Test123!@#Secure",
    "name": "Test User"
  }'
```

**Résultat attendu:** HTTP 201
```json
{
  "success": true,
  "user": {
    "id": "...",
    "email": "test-XXX@example.com",
    "authentication_token": "64_caracteres_hex...",
    "roles": ["creator"]
  }
}
```

**⚠️ IMPORTANT:** Sauvegarder le `authentication_token` pour les tests suivants !

---

### Test 3: Connexion 🔐

**Utiliser l'email et mot de passe du test précédent:**

```bash
curl -X POST "https://backend-skum.onrender.com/api/auth/signin" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "email": "test-{TIMESTAMP}@example.com",
    "password": "Test123!@#Secure"
  }'
```

**Résultat attendu:** HTTP 200 avec token

---

### Test 4: Sécurité - Accès non autorisé 🔒

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms" \
  -H "Accept: application/json"
```

**Résultat attendu:** HTTP 401 ou 403 (accès bloqué sans authentification)

---

### Test 5: Créer un formulaire 📋

**Remplacer `{YOUR_TOKEN}` par le token obtenu lors de l'inscription/connexion:**

```bash
curl -X POST "https://backend-skum.onrender.com/api/forms" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "Authentication-Token: {YOUR_TOKEN}" \
  -d '{
    "title": "Mon formulaire de test",
    "description": "Test depuis curl",
    "settings": {"theme": "default"}
  }'
```

**Résultat attendu:** HTTP 201
```json
{
  "success": true,
  "message": "Formulaire créé avec succès",
  "data": {
    "form_id": "uuid-du-formulaire"
  }
}
```

**⚠️ Sauvegarder le `form_id` !**

---

### Test 6: Lister les formulaires 📚

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms" \
  -H "Accept: application/json" \
  -H "Authentication-Token: {YOUR_TOKEN}"
```

**Résultat attendu:** HTTP 200 avec liste de formulaires

---

### Test 7: Créer une question ❓

**Remplacer `{FORM_ID}` par le form_id obtenu précédemment:**

```bash
curl -X POST "https://backend-skum.onrender.com/api/forms/{FORM_ID}/questions" \
  -H "Content-Type: application/json" \
  -H "Authentication-Token: {YOUR_TOKEN}" \
  -d '{
    "type": "text",
    "text": "Quelle est votre couleur préférée ?",
    "required": true,
    "order_index": 0
  }'
```

**Résultat attendu:** HTTP 201 avec question_id

---

### Test 8: Publier le formulaire 🌐

```bash
curl -X POST "https://backend-skum.onrender.com/api/forms/{FORM_ID}/publish" \
  -H "Authentication-Token: {YOUR_TOKEN}"
```

**Résultat attendu:** HTTP 200
```json
{
  "success": true,
  "message": "Formulaire publié avec succès",
  "data": {
    "form_id": "...",
    "status": "published",
    "public_token": "token-public-32-caracteres"
  }
}
```

**⚠️ Sauvegarder le `public_token` !**

---

### Test 9: Accéder au formulaire public (sans auth) 🔓

**Remplacer `{PUBLIC_TOKEN}` par le token public obtenu:**

```bash
curl -X GET "https://backend-skum.onrender.com/api/public/forms/{PUBLIC_TOKEN}" \
  -H "Accept: application/json"
```

**Résultat attendu:** HTTP 200 avec le formulaire complet (sans authentification nécessaire)

---

### Test 10: Soumettre une réponse publique 📬

```bash
curl -X POST "https://backend-skum.onrender.com/api/public/forms/{PUBLIC_TOKEN}/responses" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "answers": {
      "question_1": "Bleu"
    }
  }'
```

**Résultat attendu:** HTTP 201 (réponse soumise avec succès)

---

### Test 11: Récupérer les réponses 📊

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms/{FORM_ID}/responses" \
  -H "Authentication-Token: {YOUR_TOKEN}"
```

**Résultat attendu:** HTTP 200 avec liste des réponses

---

### Test 12: Analytics 📈

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms/{FORM_ID}/analytics" \
  -H "Authentication-Token: {YOUR_TOKEN}"
```

**Résultat attendu:** HTTP 200 avec statistiques détaillées

---

### Test 13: Export CSV 📄

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms/{FORM_ID}/export/csv" \
  -H "Authentication-Token: {YOUR_TOKEN}" \
  -o responses.csv
```

**Résultat attendu:** Fichier CSV téléchargé

---

### Test 14: Export Excel 📊

```bash
curl -X GET "https://backend-skum.onrender.com/api/forms/{FORM_ID}/export/excel" \
  -H "Authentication-Token: {YOUR_TOKEN}" \
  -o responses.xlsx
```

**Résultat attendu:** Fichier Excel téléchargé

---

## 🔄 SCRIPT AUTOMATISÉ COMPLET

Voici un script bash qui exécute tous les tests automatiquement:

```bash
#!/bin/bash

API_URL="https://backend-skum.onrender.com"
EMAIL="test-$(date +%s)@example.com"
PASSWORD="Test123!@#Secure"

echo "🧪 Test 1: Health Check"
curl -s -X GET "$API_URL/api/health" | jq .

echo -e "\n🧪 Test 2: Inscription"
SIGNUP_RESPONSE=$(curl -s -X POST "$API_URL/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"name\":\"Test User\"}")
echo "$SIGNUP_RESPONSE" | jq .

TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.user.authentication_token')
echo "Token: $TOKEN"

echo -e "\n🧪 Test 3: Créer formulaire"
FORM_RESPONSE=$(curl -s -X POST "$API_URL/api/forms" \
  -H "Content-Type: application/json" \
  -H "Authentication-Token: $TOKEN" \
  -d '{"title":"Test Form","description":"Test"}')
echo "$FORM_RESPONSE" | jq .

FORM_ID=$(echo "$FORM_RESPONSE" | jq -r '.data.form_id')
echo "Form ID: $FORM_ID"

echo -e "\n🧪 Test 4: Créer question"
curl -s -X POST "$API_URL/api/forms/$FORM_ID/questions" \
  -H "Content-Type: application/json" \
  -H "Authentication-Token: $TOKEN" \
  -d '{"type":"text","text":"Question test?","required":true,"order_index":0}' | jq .

echo -e "\n🧪 Test 5: Publier formulaire"
PUBLISH_RESPONSE=$(curl -s -X POST "$API_URL/api/forms/$FORM_ID/publish" \
  -H "Authentication-Token: $TOKEN")
echo "$PUBLISH_RESPONSE" | jq .

PUBLIC_TOKEN=$(echo "$PUBLISH_RESPONSE" | jq -r '.data.public_token')
echo "Public Token: $PUBLIC_TOKEN"

echo -e "\n🧪 Test 6: Accès public (sans auth)"
curl -s -X GET "$API_URL/api/public/forms/$PUBLIC_TOKEN" | jq .

echo -e "\n✅ Tests terminés !"
```

**Pour exécuter:**
```bash
chmod +x test_script.sh
./test_script.sh
```

---

## 📱 TEST AVEC POSTMAN / THUNDER CLIENT

1. **Importer la collection Postman** (à créer dans l'interface)
2. **Ou utiliser Thunder Client** dans VS Code

### Variables d'environnement à configurer:
- `api_url`: `https://backend-skum.onrender.com`
- `auth_token`: (sera rempli automatiquement après signup)
- `form_id`: (sera rempli automatiquement après création)
- `public_token`: (sera rempli automatiquement après publication)

---

## 🌐 TEST AVEC LE FICHIER HTML

**Ouvrir le fichier `test_api_browser.html` dans votre navigateur:**

1. Double-cliquer sur le fichier HTML
2. Ou ouvrir avec Chrome/Firefox/Edge
3. Cliquer sur "▶️ Exécuter tous les tests"
4. Observer les résultats en temps réel

**Avantages:**
- Interface visuelle
- Tests automatisés
- Résumé des résultats
- Pas besoin de ligne de commande

---

## 📊 RÉSULTATS ATTENDUS

### ✅ Succès total

Si tous les tests passent:
- Health Check: ✅
- Inscription: ✅
- Connexion: ✅
- Création formulaire: ✅
- Création question: ✅
- Publication: ✅
- Accès public: ✅
- Soumission réponse: ✅
- Export: ✅

**Taux de réussite: 100%** = API fonctionnelle !

### ⚠️ Problèmes possibles

1. **HTTP 403**: WAF/Firewall bloque l'accès
   - **Solution**: Exécuter depuis navigateur ou votre machine locale

2. **HTTP 401**: Token manquant/expiré
   - **Solution**: Refaire l'inscription/connexion

3. **HTTP 500**: Erreur serveur
   - **Solution**: Vérifier les logs serveur

4. **Timeout**: Serveur lent ou inactif
   - **Solution**: Attendre quelques secondes (cold start Render)

---

## 📝 NOTES

- **Les tokens expirent après 1 heure**
- **Les emails de test doivent être uniques** (utiliser timestamp)
- **Le mot de passe doit respecter la complexité**: min 8 caractères, maj+min+chiffre+spécial
- **Le WAF peut bloquer les accès automatisés** (utiliser navigateur si besoin)

---

**Généré le:** 2025-11-05
**Version API:** 2.0.0
