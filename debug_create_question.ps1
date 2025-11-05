# Script de debug pour Create Question
$API_URL = "https://backend-skum.onrender.com"

Write-Host "`n=== DEBUG CREATE QUESTION ===" -ForegroundColor Cyan

# 1. Signup
Write-Host "`n[1] Signup..." -ForegroundColor Yellow
$timestamp = [int][double]::Parse((Get-Date -UFormat %s))
$email = "debug-q-$timestamp@test.com"
$password = "Test123!@#Secure"

$signupBody = @{
    email = $email
    password = $password
    name = "Debug Question User"
} | ConvertTo-Json

$signupResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/signup" `
    -Method Post `
    -ContentType "application/json" `
    -Body $signupBody

$token = $signupResponse.authentication_token
Write-Host "[OK] Token: $($token.Substring(0,20))..." -ForegroundColor Green

# 2. Create Form
Write-Host "`n[2] Create Form..." -ForegroundColor Yellow
$formBody = @{
    title = "Debug Form"
    description = "Test"
} | ConvertTo-Json

$formResponse = Invoke-RestMethod -Uri "$API_URL/api/forms" `
    -Method Post `
    -ContentType "application/json" `
    -Body $formBody `
    -Headers @{"Authentication-Token" = $token}

$formId = $formResponse.data.form_id
Write-Host "[OK] Form ID: $formId" -ForegroundColor Green

# 3. Create Question avec DEBUG
Write-Host "`n[3] Create Question (DEBUG)..." -ForegroundColor Yellow
$questionBody = @{
    type = "text"
    text = "Question de test"
    required = $true
    order_index = 0
} | ConvertTo-Json

Write-Host "URL: $API_URL/api/forms/$formId/questions" -ForegroundColor Gray
Write-Host "Body: $questionBody" -ForegroundColor Gray

$questionResponse = Invoke-RestMethod -Uri "$API_URL/api/forms/$formId/questions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $questionBody `
    -Headers @{"Authentication-Token" = $token}

Write-Host "`n--- REPONSE COMPLETE ---" -ForegroundColor Cyan
Write-Host ($questionResponse | ConvertTo-Json -Depth 5) -ForegroundColor White

Write-Host "`n--- ANALYSE ---" -ForegroundColor Cyan
Write-Host "Type de response: $($questionResponse.GetType().Name)" -ForegroundColor Gray
Write-Host "Proprietes disponibles:" -ForegroundColor Gray
$questionResponse.PSObject.Properties | ForEach-Object {
    Write-Host "  - $($_.Name) = $($_.Value)" -ForegroundColor Gray
}

Write-Host "`n--- EXTRACTION ---" -ForegroundColor Cyan
$qid1 = $questionResponse.question_id
$qid2 = $questionResponse.data.question_id
$qid3 = $questionResponse.data

Write-Host "questionResponse.question_id = $qid1" -ForegroundColor $(if ($qid1) {"Green"} else {"Red"})
Write-Host "questionResponse.data.question_id = $qid2" -ForegroundColor $(if ($qid2) {"Green"} else {"Red"})
Write-Host "questionResponse.data = $qid3" -ForegroundColor Gray

Write-Host "`n"