# 🚀 TESTS API FORMFORGE AVEC POWERSHELL

## 📁 Fichiers disponibles pour PowerShell

### 1. **test_api_production.ps1** ⭐ (RECOMMANDÉ)
Script automatisé complet qui exécute tous les tests.

### 2. **GUIDE_TEST_API_POWERSHELL.md**
Guide détaillé avec toutes les commandes PowerShell individuelles.

### 3. **test_api_browser.html**
Interface web pour tester depuis le navigateur (fonctionne sur Windows).

---

## ⚡ UTILISATION RAPIDE

### Option 1 : Script automatisé (le plus simple)

```powershell
# 1. Ouvrir PowerShell
# Faire un clic droit sur PowerShell → "Exécuter en tant qu'administrateur" (optionnel)

# 2. Se placer dans le dossier du projet
cd C:\chemin\vers\backend

# 3. Autoriser l'exécution de scripts (si nécessaire)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 4. Exécuter le script
.\test_api_production.ps1
```

**Résultat:** Tous les tests s'exécutent automatiquement avec affichage coloré !

---

### Option 2 : Commandes manuelles

Ouvrir le fichier **GUIDE_TEST_API_POWERSHELL.md** et copier/coller les commandes une par une.

**Exemple rapide:**

```powershell
# Configuration
$API_URL = "https://backend-skum.onrender.com"

# Test 1: Health Check
Invoke-RestMethod -Uri "$API_URL/api/health"

# Test 2: Inscription
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$body = @{
    email = "test-$timestamp@example.com"
    password = "Test123!@#Secure"
    name = "Test User"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

$token = $response.user.authentication_token
Write-Host "Token: $token"
```

---

### Option 3 : Interface web (navigateur)

```powershell
# Ouvrir le fichier HTML dans le navigateur
start test_api_browser.html
```

Puis cliquer sur "▶️ Exécuter tous les tests"

---

## 🔧 RÉSOLUTION DE PROBLÈMES

### Erreur "Impossible d'exécuter le script"

```powershell
# Solution 1: Autoriser pour cette session uniquement
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Solution 2: Autoriser pour l'utilisateur actuel
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Erreur SSL/TLS

```powershell
# Ajouter avant les commandes (DEV UNIQUEMENT)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
```

### Erreur 403 (WAF/Firewall)

Si vous obtenez une erreur 403, l'API est protégée par un firewall.

**Solutions:**
1. ✅ Utiliser le script PowerShell (ajoute des headers navigateur automatiquement)
2. ✅ Utiliser l'interface HTML (navigateur contourne le WAF)
3. Ajouter manuellement les headers:

```powershell
$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "Accept" = "application/json"
}
Invoke-RestMethod -Uri $url -Headers $headers
```

### Erreur de connexion / Timeout

```powershell
# Augmenter le timeout à 60 secondes
Invoke-RestMethod -Uri $url -TimeoutSec 60
```

---

## 📊 INTERPRÉTATION DES RÉSULTATS

### ✅ Test réussi (PASS)
```
✅ Health Check : PASS
   Détails: Version: 2.0.0, Temps: 234ms
```
→ Le test fonctionne correctement !

### ❌ Test échoué (FAIL)
```
❌ User Signup : FAIL
   Détails: Error: Email already exists
```
→ Vérifier le message d'erreur pour comprendre le problème

### Taux de réussite
```
Taux de réussite: 100%
```
- **100%** : ✅ API parfaitement fonctionnelle
- **80-99%** : ⚠️ Quelques problèmes mineurs
- **<80%** : ❌ Problèmes importants à corriger

---

## 📁 FICHIERS GÉNÉRÉS

Après exécution du script, vous trouverez:

- **test_results_powershell.json** : Résultats détaillés en JSON
- **responses.csv** : Export CSV des réponses (si Test 13 réussi)
- **responses.xlsx** : Export Excel des réponses (si Test 14 réussi)

---

## 🎯 TESTS INCLUS

Le script `test_api_production.ps1` exécute **10 tests complets** :

1. ✅ Health Check
2. ✅ Security - Accès non autorisé
3. ✅ User Signup (Inscription)
4. ✅ User Signin (Connexion)
5. ✅ Create Form
6. ✅ List Forms
7. ✅ Create Question
8. ✅ Publish Form
9. ✅ Get Public Form (sans auth)
10. ✅ Submit Response (public)

---

## 💡 ASTUCES

### Copier le token pour utilisation manuelle
```powershell
# Après inscription/connexion
$token | Set-Clipboard
Write-Host "Token copié dans le presse-papiers !"
```

### Afficher les résultats en JSON formaté
```powershell
$response | ConvertTo-Json -Depth 5
```

### Exécuter seulement certains tests
```powershell
# Éditer le fichier test_api_production.ps1
# Commenter (avec #) les sections de tests non désirées
```

### Déboguer une requête
```powershell
# Utiliser Invoke-WebRequest au lieu de Invoke-RestMethod pour plus de détails
$response = Invoke-WebRequest -Uri $url -Method Get
$response.StatusCode        # Code HTTP
$response.Headers           # Headers de réponse
$response.Content           # Contenu brut
```

---

## 📞 SUPPORT

### Problèmes fréquents

**Q: Le script ne s'exécute pas**
R: Vérifier la politique d'exécution PowerShell (voir section Résolution de problèmes)

**Q: Erreur 403 sur tous les tests**
R: L'API est protégée par un WAF. Utiliser l'interface HTML ou attendre que le WAF autorise votre IP

**Q: Tous les tests après Signup échouent**
R: Vérifier que le token est bien récupéré. Relancer le script.

**Q: Comment tester sur une autre URL?**
R: Modifier la variable `$API_URL` au début du script

---

## 🔗 LIENS UTILES

- **Documentation API complète** : README.md
- **Rapport de tests précédents** : RAPPORT_TESTS_API.md
- **Audit de sécurité** : AUDIT_SECURITE.md
- **Guide curl (Linux/Mac)** : GUIDE_TEST_API.md

---

## 📝 EXEMPLE DE SORTIE ATTENDUE

```
╔════════════════════════════════════════════════════════════╗
║          TEST COMPLET API FORMFORGE - PRODUCTION          ║
║                 backend-skum.onrender.com                 ║
╚════════════════════════════════════════════════════════════╝

ℹ️  Date: 2025-11-05 10:30:45
ℹ️  PowerShell Version: 7.4.0

========================================
TEST: 1. Health Check - /api/health
========================================
✅ Health Check : PASS
   Détails: Version: 2.0.0, Temps: 234ms

========================================
TEST: 2. Security - Accès non autorisé
========================================
✅ Security - Unauthorized Access : PASS
   Détails: Accès bloqué correctement (Status: 401)

[... autres tests ...]

╔════════════════════════════════════════════════════════════╗
║                    RÉSULTATS DES TESTS                    ║
╚════════════════════════════════════════════════════════════╝

Total tests:      10
Tests réussis:    10
Tests échoués:    0
Taux de réussite: 100%

📄 Résultats sauvegardés dans: test_results_powershell.json

✅ TOUS LES TESTS SONT PASSÉS ! L'API FONCTIONNE PARFAITEMENT !
```

---

**Créé le:** 2025-11-05
**PowerShell:** 5.1+ compatible
**Windows:** 10/11
