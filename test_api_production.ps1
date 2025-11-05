# ====================================================================
# SCRIPT DE TEST COMPLET API FORMFORGE - PRODUCTION (PowerShell)
# URL: https://backend-skum.onrender.com
# ====================================================================

# Configuration
$API_URL = "https://backend-skum.onrender.com"
$script:Results = @{
    Total  = 0
    Passed = 0
    Failed = 0
    Tests  = @()
}

# Couleurs pour l'affichage
function Write-Success {
    param($Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Failure {
    param($Message)
    Write-Host "[FAIL] $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-TestHeader {
    param($Title)
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host "TEST: $Title" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
}

# Fonction pour logger les resultats
function Log-Test {
    param(
        [string]$Name,
        [string]$Status,
        [string]$Details = ""
    )

    $script:Results.Total++
    if ($Status -eq "PASS") {
        $script:Results.Passed++
        Write-Success "$Name : $Status"
    }
    else {
        $script:Results.Failed++
        Write-Failure "$Name : $Status"
    }

    if ($Details) {
        Write-Host "   Details: $Details" -ForegroundColor Gray
    }

    $script:Results.Tests += @{
        Name      = $Name
        Status    = $Status
        Details   = $Details
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }
}

# Banniere
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "     TEST COMPLET API FORMFORGE - PRODUCTION" -ForegroundColor Green
Write-Host "          backend-skum.onrender.com" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Info "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Info "PowerShell Version: $($PSVersionTable.PSVersion)"
Write-Host ""

# ====================================================================
# TEST 1: Health Check
# ====================================================================
Write-TestHeader "1. Health Check - /api/health"

try {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    $response = Invoke-RestMethod -Uri "$API_URL/api/health" `
        -Method Get `
        -Headers @{
        "Accept"     = "application/json"
        "User-Agent" = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    } `
        -ErrorAction Stop
    $stopwatch.Stop()

    Log-Test "Health Check" "PASS" "Version: $($response.version), Temps: $($stopwatch.ElapsedMilliseconds)ms"
    Write-Host ($response | ConvertTo-Json) -ForegroundColor Gray

}
catch {
    Log-Test "Health Check" "FAIL" "Status: $($_.Exception.Response.StatusCode), Error: $($_.Exception.Message)"
    Write-Info "L'API semble protegee par un WAF/Firewall. Continuons les tests..."
}

# ====================================================================
# TEST 2: Security - Unauthorized Access
# ====================================================================
Write-TestHeader "2. Security - Acces non autorise"

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/forms" `
        -Method Get `
        -Headers @{
        "Accept" = "application/json"
    } `
        -ErrorAction Stop

    Log-Test "Security - Unauthorized Access" "FAIL" "L'endpoint devrait bloquer l'acces sans authentification"

}
catch {
    $statusCode = [int]$_.Exception.Response.StatusCode
    if ($statusCode -eq 401 -or $statusCode -eq 403) {
        Log-Test "Security - Unauthorized Access" "PASS" "Acces bloque correctement (Status: $statusCode)"
    }
    else {
        Log-Test "Security - Unauthorized Access" "FAIL" "Status inattendu: $statusCode"
    }
}

# ====================================================================
# TEST 3: User Signup (Inscription)
# ====================================================================
Write-TestHeader "3. User Signup - POST /api/auth/signup"

$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$script:TEST_EMAIL = "test-$timestamp@example.com"
$script:TEST_PASSWORD = "Test123!@#Secure"
$script:TEST_NAME = "Test User PowerShell"

Write-Info "Creating user: $script:TEST_EMAIL"

$body = @{
    email    = $script:TEST_EMAIL
    password = $script:TEST_PASSWORD
    name     = $script:TEST_NAME
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -Headers @{
        "Accept"     = "application/json"
        "User-Agent" = "Mozilla/5.0"
    } `
        -ErrorAction Stop

    $script:AUTH_TOKEN = $response.authentication_token

    if ($script:AUTH_TOKEN) {
        Log-Test "User Signup" "PASS" "Email: $script:TEST_EMAIL, Token: $($script:AUTH_TOKEN.Substring(0,20))..."
    }
    else {
        Log-Test "User Signup" "FAIL" "No token in response"
    }

}
catch {
    $errorMessage = $_.Exception.Message
    if ($_.ErrorDetails.Message) {
        $errorMessage = $_.ErrorDetails.Message
    }
    Log-Test "User Signup" "FAIL" "Error: $errorMessage"
}

# ====================================================================
# TEST 4: User Signin (Connexion)
# ====================================================================
Write-TestHeader "4. User Signin - POST /api/auth/signin"

if ($script:TEST_EMAIL -and $script:TEST_PASSWORD) {
    Write-Info "Logging in with: $script:TEST_EMAIL"

    $body = @{
        email    = $script:TEST_EMAIL
        password = $script:TEST_PASSWORD
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/auth/signin" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop

        $newToken = $response.authentication_token

        if ($newToken) {
            $script:AUTH_TOKEN = $newToken
            Log-Test "User Signin" "PASS" "Token: $($newToken.Substring(0,20))..."
        }
        else {
            Log-Test "User Signin" "FAIL" "No token in response"
        }

    }
    catch {
        Log-Test "User Signin" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "User Signin" "FAIL" "No credentials available from signup"
}

# ====================================================================
# TEST 5: Create Form
# ====================================================================
Write-TestHeader "5. Create Form - POST /api/forms"

if ($script:AUTH_TOKEN) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $body = @{
        title       = "Test Form PowerShell $timestamp"
        description = "Formulaire de test cree depuis PowerShell"
        settings    = @{
            theme = "default"
        }
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/forms" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -Headers @{
            "Authentication-Token" = $script:AUTH_TOKEN
            "Accept"               = "application/json"
        } `
            -ErrorAction Stop

        $script:FORM_ID = $response.data.form_id

        if ($script:FORM_ID) {
            Log-Test "Create Form" "PASS" "Form ID: $($script:FORM_ID.Substring(0,30))..."
        }
        else {
            Log-Test "Create Form" "FAIL" "No form_id in response"
        }

    }
    catch {
        Log-Test "Create Form" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "Create Form" "FAIL" "No auth token available"
}

# ====================================================================
# TEST 6: List Forms
# ====================================================================
Write-TestHeader "6. List Forms - GET /api/forms"

if ($script:AUTH_TOKEN) {
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/forms" `
            -Method Get `
            -Headers @{
            "Authentication-Token" = $script:AUTH_TOKEN
            "Accept"               = "application/json"
        } `
            -ErrorAction Stop

        $formsCount = $response.forms.Count
        Log-Test "List Forms" "PASS" "Found $formsCount form(s)"

        if ($formsCount -gt 0) {
            Write-Host "   Derniers formulaires:" -ForegroundColor Gray
            $response.forms | Select-Object -First 3 | ForEach-Object {
                Write-Host "   - $($_.title)" -ForegroundColor Gray
            }
        }

    }
    catch {
        Log-Test "List Forms" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "List Forms" "FAIL" "No auth token available"
}

# ====================================================================
# TEST 7: Create Question
# ====================================================================
Write-TestHeader "7. Create Question - POST /api/forms/{id}/questions"

if ($script:AUTH_TOKEN -and $script:FORM_ID) {
    $body = @{
        type        = "text"
        text        = "Quelle est votre couleur preferee ?"
        required    = $true
        order_index = 0
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/questions" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -Headers @{
            "Authentication-Token" = $script:AUTH_TOKEN
        } `
            -ErrorAction Stop

        $script:QUESTION_ID = $response.question_id
        if ($script:QUESTION_ID) {
            Log-Test "Create Question" "PASS" "Question ID: $($script:QUESTION_ID.Substring(0,30))..."
        } else {
            Log-Test "Create Question" "FAIL" "No question_id in response"
        }

    }
    catch {
        Log-Test "Create Question" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "Create Question" "FAIL" "Missing auth token or form_id"
}

# ====================================================================
# TEST 8: Publish Form
# ====================================================================
Write-TestHeader "8. Publish Form - POST /api/forms/{id}/publish"

if ($script:AUTH_TOKEN -and $script:FORM_ID) {
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/forms/$($script:FORM_ID)/publish" `
            -Method Post `
            -Headers @{
            "Authentication-Token" = $script:AUTH_TOKEN
        } `
            -ErrorAction Stop

        $script:PUBLIC_TOKEN = $response.data.public_token
        Log-Test "Publish Form" "PASS" "Public Token: $($script:PUBLIC_TOKEN.Substring(0,20))..."

    }
    catch {
        Log-Test "Publish Form" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "Publish Form" "FAIL" "Missing auth token or form_id"
}

# ====================================================================
# TEST 9: Get Public Form (no auth)
# ====================================================================
Write-TestHeader "9. Get Public Form - GET /api/public/forms/{token}"

if ($script:PUBLIC_TOKEN) {
    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/public/forms/$($script:PUBLIC_TOKEN)" `
            -Method Get `
            -Headers @{
            "Accept" = "application/json"
        } `
            -ErrorAction Stop

        $formTitle = $response.data.form.title
        $questionsCount = $response.data.form.questions.Count
        Log-Test "Get Public Form" "PASS" "Title: $formTitle, Questions: $questionsCount"

    }
    catch {
        Log-Test "Get Public Form" "FAIL" "Error: $($_.Exception.Message)"
    }
}
else {
    Log-Test "Get Public Form" "FAIL" "No public token available"
}

# ====================================================================
# TEST 10: Submit Response (public)
# ====================================================================
Write-TestHeader "10. Submit Response - POST /api/public/forms/{token}/responses"

if ($script:PUBLIC_TOKEN -and $script:QUESTION_ID) {
    # Utiliser le vrai question_id comme cle
    $answersDict = @{}
    $answersDict[$script:QUESTION_ID] = "Bleu"

    $body = @{
        answers = $answersDict
    } | ConvertTo-Json

    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/public/forms/$($script:PUBLIC_TOKEN)/responses" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body `
            -ErrorAction Stop

        Log-Test "Submit Response" "PASS" "Response submitted successfully"

    }
    catch {
        Log-Test "Submit Response" "FAIL" "Error: $($_.Exception.Message)"
    }
} else {
    if (-not $script:PUBLIC_TOKEN) {
        Log-Test "Submit Response" "FAIL" "No public token available"
    } elseif (-not $script:QUESTION_ID) {
        Log-Test "Submit Response" "FAIL" "No question_id available"
    }
}

# ====================================================================
# RESULTATS FINAUX
# ====================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "                RESULTATS DES TESTS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Total tests:      " -NoNewline
Write-Host $script:Results.Total -ForegroundColor Blue

Write-Host "Tests reussis:    " -NoNewline
Write-Host $script:Results.Passed -ForegroundColor Green

Write-Host "Tests echoues:    " -NoNewline
Write-Host $script:Results.Failed -ForegroundColor Red

if ($script:Results.Total -gt 0) {
    $successRate = [math]::Round(($script:Results.Passed / $script:Results.Total) * 100, 1)
    Write-Host "Taux de reussite: " -NoNewline
    Write-Host "$successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 50) { "Yellow" } else { "Red" })
}

# Sauvegarder les resultats
$resultsJson = $script:Results | ConvertTo-Json -Depth 5
$resultsJson | Out-File -FilePath "test_results_powershell.json" -Encoding UTF8
Write-Host "`n[SAVE] Resultats sauvegardes dans: test_results_powershell.json" -ForegroundColor Cyan

# Message final
Write-Host ""
if ($script:Results.Failed -eq 0) {
    Write-Host "SUCCESS: TOUS LES TESTS SONT PASSES ! L'API FONCTIONNE PARFAITEMENT !" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "WARNING: CERTAINS TESTS ONT ECHOUE. VERIFIER LES LOGS CI-DESSUS." -ForegroundColor Yellow
    exit 1
}
