# 🧪 GUIDE DE TEST API FORMFORGE - POWERSHELL

## URL de l'API
```powershell
$API_URL = "https://backend-skum.onrender.com"
```

---

## 📋 TESTS À EXÉCUTER (PowerShell)

### Test 1: Health Check ✅

```powershell
# Health Check
$response = Invoke-RestMethod -Uri "$API_URL/api/health" `
    -Method Get `
    -Headers @{
        "Accept" = "application/json"
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

Write-Host "✅ Health Check:" -ForegroundColor Green
$response | ConvertTo-Json -Depth 3
```

**Résultat attendu:**
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

```powershell
# Générer un email unique
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$email = "test-$timestamp@example.com"
$password = "Test123!@#Secure"

Write-Host "`n📝 Test Inscription..." -ForegroundColor Cyan
Write-Host "Email: $email"

# Inscription
$body = @{
    email = $email
    password = $password
    name = "Test User PowerShell"
} | ConvertTo-Json

$signupResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -Headers @{
        "Accept" = "application/json"
        "User-Agent" = "Mozilla/5.0"
    }

Write-Host "✅ Inscription réussie!" -ForegroundColor Green
$token = $signupResponse.user.authentication_token
Write-Host "Token: $($token.Substring(0,20))..." -ForegroundColor Yellow

# Sauvegarder pour les tests suivants
$script:AUTH_TOKEN = $token
$script:TEST_EMAIL = $email
$script:TEST_PASSWORD = $password
```

---

### Test 3: Connexion 🔐

```powershell
Write-Host "`n🔐 Test Connexion..." -ForegroundColor Cyan

$body = @{
    email = $script:TEST_EMAIL
    password = $script:TEST_PASSWORD
} | ConvertTo-Json

$signinResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/signin" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "✅ Connexion réussie!" -ForegroundColor Green
$script:AUTH_TOKEN = $signinResponse.user.authentication_token
Write-Host "Nouveau token: $($script:AUTH_TOKEN.Substring(0,20))..."
```

---

### Test 4: Sécurité - Accès non autorisé 🔒

```powershell
Write-Host "`n🔒 Test Sécurité - Accès non autorisé..." -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/forms" `
        -Method Get `
        -ErrorAction Stop
    Write-Host "❌ ÉCHEC: L'endpoint devrait bloquer l'accès!" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode -eq 403) {
        Write-Host "✅ SUCCÈS: Accès bloqué sans authentification" -ForegroundColor Green
    } else {
        Write-Host "❌ Code inattendu: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
}
```

---

### Test 5: Créer un formulaire 📋

```powershell
Write-Host "`n📋 Test Création formulaire..." -ForegroundColor Cyan

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$body = @{
    title = "Formulaire Test PowerShell $timestamp"
    description = "Créé depuis PowerShell"
    settings = @{
        theme = "default"
    }
} | ConvertTo-Json

$formResponse = Invoke-RestMethod -Uri "$API_URL/api/forms" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
        "Accept" = "application/json"
    }

Write-Host "✅ Formulaire créé!" -ForegroundColor Green
$script:FORM_ID = $formResponse.data.form_id
Write-Host "Form ID: $($script:FORM_ID.Substring(0,30))..."
```

---

### Test 6: Lister les formulaires 📚

```powershell
Write-Host "`n📚 Test Liste formulaires..." -ForegroundColor Cyan

$formsResponse = Invoke-RestMethod -Uri "$API_URL/api/forms" `
    -Method Get `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
        "Accept" = "application/json"
    }

Write-Host "✅ Formulaires récupérés: $($formsResponse.forms.Count)" -ForegroundColor Green
$formsResponse.forms | Select-Object id, title, created_at | Format-Table
```

---

### Test 7: Créer une question ❓

```powershell
Write-Host "`n❓ Test Création question..." -ForegroundColor Cyan

$body = @{
    type = "text"
    text = "Quelle est votre couleur préférée ?"
    required = $true
    order_index = 0
} | ConvertTo-Json

$questionResponse = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/questions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    }

Write-Host "✅ Question créée!" -ForegroundColor Green
$script:QUESTION_ID = $questionResponse.data.question_id
Write-Host "Question ID: $script:QUESTION_ID"
```

---

### Test 8: Publier le formulaire 🌐

```powershell
Write-Host "`n🌐 Test Publication formulaire..." -ForegroundColor Cyan

$publishResponse = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/publish" `
    -Method Post `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    }

Write-Host "✅ Formulaire publié!" -ForegroundColor Green
$script:PUBLIC_TOKEN = $publishResponse.data.public_token
Write-Host "Public Token: $($script:PUBLIC_TOKEN.Substring(0,20))..."
```

---

### Test 9: Accéder au formulaire public (sans auth) 🔓

```powershell
Write-Host "`n🔓 Test Accès formulaire public (sans auth)..." -ForegroundColor Cyan

$publicFormResponse = Invoke-RestMethod -Uri "$API_URL/api/public/forms/$($script:PUBLIC_TOKEN)" `
    -Method Get `
    -Headers @{
        "Accept" = "application/json"
    }

Write-Host "✅ Formulaire public accessible!" -ForegroundColor Green
Write-Host "Titre: $($publicFormResponse.data.form.title)"
Write-Host "Questions: $($publicFormResponse.data.form.questions.Count)"
```

---

### Test 10: Soumettre une réponse publique 📬

```powershell
Write-Host "`n📬 Test Soumission réponse publique..." -ForegroundColor Cyan

$body = @{
    answers = @{
        "question_1" = "Bleu"
    }
} | ConvertTo-Json

$responseSubmit = Invoke-RestMethod -Uri "$API_URL/api/public/forms/$($script:PUBLIC_TOKEN)/responses" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body

Write-Host "✅ Réponse soumise avec succès!" -ForegroundColor Green
```

---

### Test 11: Récupérer les réponses 📊

```powershell
Write-Host "`n📊 Test Récupération réponses..." -ForegroundColor Cyan

$responsesResponse = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/responses" `
    -Method Get `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    }

Write-Host "✅ Réponses récupérées: $($responsesResponse.responses.Count)" -ForegroundColor Green
```

---

### Test 12: Analytics 📈

```powershell
Write-Host "`n📈 Test Analytics..." -ForegroundColor Cyan

$analyticsResponse = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/analytics" `
    -Method Get `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    }

Write-Host "✅ Analytics récupérés!" -ForegroundColor Green
$analyticsResponse | ConvertTo-Json -Depth 3
```

---

### Test 13: Export CSV 📄

```powershell
Write-Host "`n📄 Test Export CSV..." -ForegroundColor Cyan

Invoke-WebRequest -Uri "$API_URL/api/forms/$($script:FORM_ID)/export/csv" `
    -Method Get `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    } `
    -OutFile "responses.csv"

Write-Host "✅ Export CSV téléchargé: responses.csv" -ForegroundColor Green
Get-Content responses.csv | Select-Object -First 5
```

---

### Test 14: Export Excel 📊

```powershell
Write-Host "`n📊 Test Export Excel..." -ForegroundColor Cyan

Invoke-WebRequest -Uri "$API_URL/api/forms/$($script:FORM_ID)/export/excel" `
    -Method Get `
    -Headers @{
        "Authentication-Token" = $script:AUTH_TOKEN
    } `
    -OutFile "responses.xlsx"

Write-Host "✅ Export Excel téléchargé: responses.xlsx" -ForegroundColor Green
```

---

## 🎯 COMMANDES RAPIDES

### Configuration initiale
```powershell
# Variables globales
$API_URL = "https://backend-skum.onrender.com"
$script:AUTH_TOKEN = $null
$script:FORM_ID = $null
$script:PUBLIC_TOKEN = $null
```

### Test rapide Health Check
```powershell
Invoke-RestMethod -Uri "$API_URL/api/health"
```

### Inscription rapide
```powershell
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

## 💡 ASTUCES POWERSHELL

### Afficher les réponses en JSON formaté
```powershell
$response | ConvertTo-Json -Depth 5
```

### Gérer les erreurs
```powershell
try {
    $response = Invoke-RestMethod -Uri $url -ErrorAction Stop
} catch {
    Write-Host "Erreur: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)"
}
```

### Mesurer le temps de réponse
```powershell
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$response = Invoke-RestMethod -Uri "$API_URL/api/health"
$stopwatch.Stop()
Write-Host "Temps de réponse: $($stopwatch.ElapsedMilliseconds)ms"
```

### Sauvegarder les résultats dans un fichier
```powershell
$response | ConvertTo-Json -Depth 5 | Out-File -FilePath "test_results.json"
```

---

## 🔧 CONFIGURATION PROXY (si nécessaire)

```powershell
# Utiliser le proxy système
$response = Invoke-RestMethod -Uri $url -Proxy "http://proxy:8080"

# Avec authentification proxy
$proxyCredential = Get-Credential
$response = Invoke-RestMethod -Uri $url -Proxy "http://proxy:8080" -ProxyCredential $proxyCredential

# Ignorer le proxy
$response = Invoke-RestMethod -Uri $url -NoProxy
```

---

## 🛠️ DÉPANNAGE

### Erreur SSL/TLS
```powershell
# Accepter tous les certificats (DEV UNIQUEMENT)
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
```

### Erreur 403 (WAF)
```powershell
# Ajouter des headers navigateur
$headers = @{
    "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    "Accept" = "application/json"
    "Accept-Language" = "fr-FR,fr;q=0.9"
}
$response = Invoke-RestMethod -Uri $url -Headers $headers
```

### Timeout
```powershell
# Augmenter le timeout (en secondes)
$response = Invoke-RestMethod -Uri $url -TimeoutSec 60
```

---

## 📊 TABLEAU RÉCAPITULATIF

| Commande PowerShell | Équivalent curl |
|---------------------|-----------------|
| `Invoke-RestMethod` | `curl` (retourne JSON) |
| `Invoke-WebRequest` | `curl -v` (plus détails) |
| `-Method Post` | `-X POST` |
| `-ContentType "application/json"` | `-H "Content-Type: application/json"` |
| `-Headers @{...}` | `-H "Header: Value"` |
| `-Body $json` | `-d '...'` |
| `-OutFile file.csv` | `-o file.csv` |

---

**Généré le:** 2025-11-05
**Version API:** 2.0.0
**PowerShell:** 5.1+
