# ====================================================================
# DEBUG: Tester les headers d'authentification
# ====================================================================

$API_URL = "https://backend-skum.onrender.com"

Write-Host "`n[DEBUG] Test d'authentification avec headers" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Etape 1: Signup
Write-Host "`n[1] Signup..." -ForegroundColor Yellow
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$email = "debug-$timestamp@test.com"
$password = "Test123!@#Secure"

$signupBody = @{
    email = $email
    password = $password
    name = "Debug User"
} | ConvertTo-Json

try {
    $signupResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $signupBody `
        -ErrorAction Stop

    Write-Host "[OK] Signup reussi" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($signupResponse | ConvertTo-Json -Depth 5) -ForegroundColor Gray

    $token = $signupResponse.authentication_token
    if ($token) {
        Write-Host "`n[TOKEN TROUVE]" -ForegroundColor Green
        Write-Host "Token: $($token.Substring(0,30))..." -ForegroundColor Green
        Write-Host "Longueur: $($token.Length) caracteres" -ForegroundColor Gray
    } else {
        Write-Host "[ERREUR] Pas de token dans la reponse" -ForegroundColor Red
        exit 1
    }

} catch {
    Write-Host "[ERREUR] Signup echoue: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Etape 2: Test avec le token
Write-Host "`n[2] Test GET /api/forms avec le token..." -ForegroundColor Yellow

Write-Host "`n--- Headers envoyes ---" -ForegroundColor Cyan
Write-Host "Authentication-Token: $($token.Substring(0,30))..." -ForegroundColor Gray
Write-Host "Accept: application/json" -ForegroundColor Gray
Write-Host "User-Agent: Mozilla/5.0" -ForegroundColor Gray

try {
    $formsResponse = Invoke-RestMethod -Uri "$API_URL/api/forms" `
        -Method Get `
        -Headers @{
            "Authentication-Token" = $token
            "Accept" = "application/json"
            "User-Agent" = "Mozilla/5.0"
        } `
        -ErrorAction Stop

    Write-Host "`n[OK] Requete reussie !" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    Write-Host ($formsResponse | ConvertTo-Json -Depth 5) -ForegroundColor Gray

} catch {
    Write-Host "`n[ERREUR] Requete echouee" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "Status Description: $($_.Exception.Response.StatusDescription)" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        Write-Host "Message d'erreur:" -ForegroundColor Red
        Write-Host $_.ErrorDetails.Message -ForegroundColor Red
    }

    Write-Host "`n--- Debug: Verification du token ---" -ForegroundColor Yellow
    Write-Host "Type: $($token.GetType().Name)" -ForegroundColor Gray
    Write-Host "Contient des espaces: $($token.Contains(' '))" -ForegroundColor Gray
    Write-Host "Premiers caracteres: $($token.Substring(0, [Math]::Min(50, $token.Length)))" -ForegroundColor Gray
}

Write-Host "`n" -ForegroundColor Cyan
