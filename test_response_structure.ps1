# Script pour afficher la reponse complete de signup
$API_URL = "https://backend-skum.onrender.com"

Write-Host "=== TEST SIGNUP - AFFICHAGE COMPLET ===" -ForegroundColor Yellow

$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$body = @{
    email = "debug-$timestamp@test.com"
    password = "TestPass123!"
    name = "Debug User"
} | ConvertTo-Json

Write-Host "`nBody envoye:" -ForegroundColor Cyan
Write-Host $body

try {
    $response = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -Headers @{
            "Accept" = "application/json"
            "User-Agent" = "Mozilla/5.0"
        }

    Write-Host "`n[OK] Inscription reussie !" -ForegroundColor Green
    Write-Host "`n=== STRUCTURE COMPLETE DE LA REPONSE ===" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10

    Write-Host "`n=== RECHERCHE DU TOKEN ===" -ForegroundColor Yellow

    # Tester differentes structures
    if ($response.user.authentication_token) {
        Write-Host "[TROUVE] response.user.authentication_token = $($response.user.authentication_token.Substring(0,20))..." -ForegroundColor Green
    } elseif ($response.authentication_token) {
        Write-Host "[TROUVE] response.authentication_token = $($response.authentication_token.Substring(0,20))..." -ForegroundColor Green
    } elseif ($response.data.authentication_token) {
        Write-Host "[TROUVE] response.data.authentication_token = $($response.data.authentication_token.Substring(0,20))..." -ForegroundColor Green
    } elseif ($response.user.auth_token) {
        Write-Host "[TROUVE] response.user.auth_token = $($response.user.auth_token.Substring(0,20))..." -ForegroundColor Green
    } elseif ($response.token) {
        Write-Host "[TROUVE] response.token = $($response.token.Substring(0,20))..." -ForegroundColor Green
    } else {
        Write-Host "[NON TROUVE] Token introuvable dans la structure" -ForegroundColor Red
        Write-Host "Proprietes disponibles dans response:" -ForegroundColor Yellow
        $response | Get-Member -MemberType NoteProperty | Select-Object Name

        if ($response.user) {
            Write-Host "Proprietes disponibles dans response.user:" -ForegroundColor Yellow
            $response.user | Get-Member -MemberType NoteProperty | Select-Object Name
        }
    }

} catch {
    Write-Host "`n[FAIL] Erreur: $($_.Exception.Message)" -ForegroundColor Red
}
