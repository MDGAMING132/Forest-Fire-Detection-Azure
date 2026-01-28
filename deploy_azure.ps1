# Azure Deployment - Quick Start Script
# Run this from PowerShell to deploy to Azure

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "forest-fire-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "eastus",
    
    [Parameter(Mandatory=$false)]
    [string]$PlanName = "forest-fire-plan",
    
    [Parameter(Mandatory=$false)]
    [string]$Sku = "B1"
)

Write-Host "🔥 Forest Fire Detection - Azure Deployment" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# Check if Azure CLI is installed
Write-Host "Checking Azure CLI..." -ForegroundColor Yellow
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI not found. Please install from: https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Azure CLI found" -ForegroundColor Green

# Login to Azure
Write-Host "`nLogging in to Azure..." -ForegroundColor Yellow
az login
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Azure login failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Logged in to Azure" -ForegroundColor Green

# Create resource group
Write-Host "`nCreating resource group '$ResourceGroup'..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Resource group creation failed (may already exist)" -ForegroundColor Yellow
} else {
    Write-Host "✅ Resource group created" -ForegroundColor Green
}

# Create App Service Plan
Write-Host "`nCreating App Service Plan '$PlanName'..." -ForegroundColor Yellow
az appservice plan create `
    --name $PlanName `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku $Sku `
    --is-linux
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ App Service Plan creation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ App Service Plan created" -ForegroundColor Green

# Create Web App
Write-Host "`nCreating Web App '$AppName'..." -ForegroundColor Yellow
az webapp create `
    --resource-group $ResourceGroup `
    --plan $PlanName `
    --name $AppName `
    --runtime "PYTHON:3.11"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Web App creation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Web App created" -ForegroundColor Green

# Configure application settings
Write-Host "`nConfiguring application settings..." -ForegroundColor Yellow
$FirmsKey = Read-Host "Enter your FIRMS API key (or press Enter to skip)"
$WeatherKey = Read-Host "Enter your OpenWeather API key (or press Enter to skip)"

$settings = @(
    "PORT=8000",
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true",
    "ENABLE_FIRMS_WMS=true",
    "FIRMS_DAYS_DEFAULT=1",
    "FIRMS_WMS_URL=https://firms.modaps.eosdis.nasa.gov/wms/",
    "SENTINEL_WMS_URL=https://tiles.maps.eox.at/wms"
)

if ($FirmsKey) {
    $settings += "FIRMS_MAP_KEY=$FirmsKey"
}

if ($WeatherKey) {
    $settings += "OPENWEATHER_KEY=$WeatherKey"
}

az webapp config appsettings set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --settings $settings
Write-Host "✅ Application settings configured" -ForegroundColor Green

# Set startup command
Write-Host "`nConfiguring startup command..." -ForegroundColor Yellow
az webapp config set `
    --resource-group $ResourceGroup `
    --name $AppName `
    --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 backend.app:app"
Write-Host "✅ Startup command configured" -ForegroundColor Green

# Deploy code
Write-Host "`nDeploying code..." -ForegroundColor Yellow
$deployChoice = Read-Host "Deploy now? (1=Local Git, 2=ZIP Deploy, 3=Skip) [1]"

if ($deployChoice -eq "2") {
    Write-Host "Creating deployment package..." -ForegroundColor Yellow
    if (Test-Path "deploy.zip") {
        Remove-Item "deploy.zip" -Force
    }
    Compress-Archive -Path * -DestinationPath deploy.zip -Force
    
    Write-Host "Deploying via ZIP..." -ForegroundColor Yellow
    az webapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $AppName `
        --src deploy.zip
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Code deployed" -ForegroundColor Green
    } else {
        Write-Host "❌ Deployment failed" -ForegroundColor Red
    }
    
    Remove-Item "deploy.zip" -Force
} elseif ($deployChoice -ne "3") {
    Write-Host "Setting up Local Git deployment..." -ForegroundColor Yellow
    $gitUrl = az webapp deployment source config-local-git `
        --resource-group $ResourceGroup `
        --name $AppName `
        --query url `
        --output tsv
    
    Write-Host "`n📝 Git deployment URL: $gitUrl" -ForegroundColor Cyan
    Write-Host "`nTo deploy, run:" -ForegroundColor Yellow
    Write-Host "  git init" -ForegroundColor White
    Write-Host "  git add ." -ForegroundColor White
    Write-Host "  git commit -m 'Initial deployment'" -ForegroundColor White
    Write-Host "  git remote add azure $gitUrl" -ForegroundColor White
    Write-Host "  git push azure master" -ForegroundColor White
}

# Enable HTTPS
Write-Host "`nEnabling HTTPS-only..." -ForegroundColor Yellow
az webapp update `
    --resource-group $ResourceGroup `
    --name $AppName `
    --https-only true
Write-Host "✅ HTTPS-only enabled" -ForegroundColor Green

# Get app URL
$appUrl = az webapp show `
    --resource-group $ResourceGroup `
    --name $AppName `
    --query defaultHostName `
    --output tsv

Write-Host "`n============================================" -ForegroundColor Green
Write-Host "✅ Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "`n🌐 App URL: https://$appUrl" -ForegroundColor Cyan
Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Deploy your code (if skipped)" -ForegroundColor White
Write-Host "  2. Update API keys in Azure Portal if needed" -ForegroundColor White
Write-Host "  3. Test the app: https://$appUrl" -ForegroundColor White
Write-Host "  4. Update Raspberry Pi with URL:" -ForegroundColor White
Write-Host "     python3 fire_detection_drone.py --backend https://$appUrl" -ForegroundColor Gray
Write-Host "`n📊 View logs:" -ForegroundColor Yellow
Write-Host "  az webapp log tail --resource-group $ResourceGroup --name $AppName" -ForegroundColor Gray
Write-Host "`n🔧 Manage in Portal:" -ForegroundColor Yellow
Write-Host "  https://portal.azure.com" -ForegroundColor Cyan
Write-Host ""
