# ====================================================================
# TEST: Essayer differents formats de header pour le token
# ====================================================================

$API_URL = "https://backend-skum.onrender.com"

Write-Host "`n[DEBUG] Test de differents formats de header d'authentification" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan

# Signup pour obtenir un token
Write-Host "`n[1] Signup pour obtenir un token..." -ForegroundColor Yellow
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$email = "format-test-$timestamp@test.com"
$password = "Test123!@#Secure"

$signupBody = @{
    email = $email
    password = $password
    name = "Format Test User"
} | ConvertTo-Json

try {
    $signupResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $signupBody `
        -ErrorAction Stop

    $token = $signupResponse.authentication_token
    if (-not $token) {
        Write-Host "[ERREUR] Pas de token recu" -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Token recu: $($token.Substring(0,30))..." -ForegroundColor Green
    Write-Host "Longueur du token: $($token.Length) caracteres" -ForegroundColor Gray

} catch {
    Write-Host "[ERREUR] Signup echoue: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test differents formats de header
Write-Host "`n[2] Test de differents formats de header..." -ForegroundColor Yellow
Write-Host ""

$formats = @(
    @{Name = "Authentication-Token: <token>"; Headers = @{"Authentication-Token" = $token}},
    @{Name = "Authentication-Token: Bearer <token>"; Headers = @{"Authentication-Token" = "Bearer $token"}},
    @{Name = "Authorization: <token>"; Headers = @{"Authorization" = $token}},
    @{Name = "Authorization: Bearer <token>"; Headers = @{"Authorization" = "Bearer $token"}},
    @{Name = "Authorization: Token <token>"; Headers = @{"Authorization" = "Token $token"}},
    @{Name = "X-Auth-Token: <token>"; Headers = @{"X-Auth-Token" = $token}}
)

$successCount = 0

foreach ($format in $formats) {
    Write-Host "`n--- Test: $($format.Name) ---" -ForegroundColor Cyan

    try {
        $response = Invoke-RestMethod -Uri "$API_URL/api/forms" `
            -Method Get `
            -Headers $format.Headers `
            -ErrorAction Stop

        Write-Host "[SUCCESS] Format fonctionne !" -ForegroundColor Green
        Write-Host "Response: $($response | ConvertTo-Json -Depth 2)" -ForegroundColor Gray
        $successCount++

    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "[FAIL] Status: $statusCode - $($_.Exception.Response.StatusDescription)" -ForegroundColor Red
    }
}

Write-Host "`n" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "RESULTATS: $successCount/$($formats.Count) formats ont fonctionne" -ForegroundColor $(if ($successCount -gt 0) {"Green"} else {"Red"})
Write-Host "=" * 70 -ForegroundColor Cyan
