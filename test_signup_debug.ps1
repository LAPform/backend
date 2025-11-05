# Script de debug pour tester l'inscription avec differentes variantes
$API_URL = "https://backend-skum.onrender.com"

Write-Host "=== DEBUG INSCRIPTION API ===" -ForegroundColor Yellow
Write-Host ""

# Test 1: Inscription basique
Write-Host "Test 1: Inscription avec donnees minimales" -ForegroundColor Cyan
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$body1 = @{
    email = "debug-$timestamp@test.com"
    password = "TestPass123!"
    name = "Debug User"
} | ConvertTo-Json

Write-Host "Body envoye:" -ForegroundColor Gray
Write-Host $body1

try {
    $response = Invoke-WebRequest -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body1 `
        -Headers @{
            "Accept" = "application/json"
            "User-Agent" = "Mozilla/5.0"
        }

    Write-Host "[OK] Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5

} catch {
    Write-Host "[FAIL] Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red

    # Tenter de lire le body de l'erreur
    try {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "Error Body:" -ForegroundColor Yellow
        Write-Host $errorBody
    } catch {
        Write-Host "Impossible de lire le body de l'erreur"
    }
}

Write-Host ""
Write-Host "=== FIN DEBUG ===" -ForegroundColor Yellow

# Test 2: Verifier l'endpoint register-json (alternative)
Write-Host ""
Write-Host "Test 2: Essayer endpoint /api/auth/register-json" -ForegroundColor Cyan

try {
    $timestamp2 = [int][double]::Parse((Get-Date -UFormat %s))
    $body2 = @{
        email = "debug2-$timestamp2@test.com"
        password = "TestPass123!"
    } | ConvertTo-Json

    $response2 = Invoke-WebRequest -Uri "$API_URL/api/auth/register-json" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body2 `
        -Headers @{
            "Accept" = "application/json"
        }

    Write-Host "[OK] Status: $($response2.StatusCode)" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Gray
    $response2.Content

} catch {
    Write-Host "[FAIL] Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}
