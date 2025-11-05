# Test minimal de tous les endpoints publics
$API_URL = "https://backend-skum.onrender.com"

Write-Host "=== TEST ENDPOINTS PUBLICS ===" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health
Write-Host "1. GET /api/health" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$API_URL/api/health"
    Write-Host "   [OK] $($r.status) - Version $($r.version)" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: Security headers
Write-Host "2. GET /api/security/headers" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$API_URL/api/security/headers"
    Write-Host "   [OK] Headers de securite actifs" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] $($_.Exception.Message)" -ForegroundColor Red
}

# Test 3: Documentation
Write-Host "3. GET /api/docs" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$API_URL/api/docs"
    Write-Host "   [OK] Documentation accessible" -ForegroundColor Green
} catch {
    Write-Host "   [INFO] Endpoint non disponible ou protege" -ForegroundColor Yellow
}

# Test 4: Monitoring health
Write-Host "4. GET /api/monitoring/health" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "$API_URL/api/monitoring/health"
    Write-Host "   [OK] Monitoring actif" -ForegroundColor Green
} catch {
    Write-Host "   [INFO] Endpoint protege ou non disponible" -ForegroundColor Yellow
}

# Test 5: Auth endpoints
Write-Host "5. POST /api/auth/signup (avec body)" -ForegroundColor Cyan
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$body = @{
    email = "test-$timestamp@example.com"
    password = "Test123!@#"
    name = "Test"
} | ConvertTo-Json

try {
    $r = Invoke-WebRequest -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -ErrorAction Stop

    Write-Host "   [OK] Status $($r.StatusCode)" -ForegroundColor Green

} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   [FAIL] Status $statusCode" -ForegroundColor Red

    # Essayer de lire le corps de l'erreur
    if ($_.Exception.Response) {
        try {
            $result = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($result)
            $responseBody = $reader.ReadToEnd()
            Write-Host "   Error details: $responseBody" -ForegroundColor Yellow
        } catch {}
    }
}

# Test 6: Alternative register-json
Write-Host "6. POST /api/auth/register-json" -ForegroundColor Cyan
$timestamp2 = [int][double]::Parse((Get-Date -UFormat %s))
$body2 = @{
    email = "test2-$timestamp2@example.com"
    password = "Test123!@#"
} | ConvertTo-Json

try {
    $r = Invoke-RestMethod -Uri "$API_URL/api/auth/register-json" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body2

    Write-Host "   [OK] Inscription reussie via register-json" -ForegroundColor Green

} catch {
    Write-Host "   [FAIL] Status $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== FIN TEST ===" -ForegroundColor Yellow
