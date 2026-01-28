# 🚀 Quick Azure Deployment - Forest Fire Detection

## Choose Your Deployment Method

### ⚡ Method 1: One-Click PowerShell Script (Easiest)

```powershell
# Run from G:\Forest_Fire directory
.\deploy_azure.ps1 -AppName "your-unique-app-name"
```

**Prompts you will see:**
1. Azure login (opens browser)
2. FIRMS API key (optional)
3. OpenWeather API key (optional)
4. Deployment method choice

**Time: 5-10 minutes**

---

### 🎯 Method 2: Azure Portal (Guided)

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2Fyour-repo%2Fazuredeploy.json)

**Steps:**
1. Click "Deploy to Azure" button
2. Sign in to Azure Portal
3. Fill in the form:
   - **App Name**: Choose unique name
   - **Resource Group**: Create new or use existing
   - **SKU**: B1 (recommended) or F1 (free)
   - **API Keys**: Add your keys (optional)
4. Click "Review + Create"
5. Click "Create"

**Time: 5 minutes**

---

### 💻 Method 3: Azure CLI

```powershell
# Login
az login

# Set variables
$APP_NAME = "forest-fire-detection"
$RG = "forest-fire-rg"
$LOCATION = "eastus"

# Create resources
az group create --name $RG --location $LOCATION

az appservice plan create `
  --name "plan-$APP_NAME" `
  --resource-group $RG `
  --sku B1 `
  --is-linux

az webapp create `
  --resource-group $RG `
  --plan "plan-$APP_NAME" `
  --name $APP_NAME `
  --runtime "PYTHON:3.11"

# Configure
az webapp config set `
  --resource-group $RG `
  --name $APP_NAME `
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers 2 backend.app:app"

# Deploy
az webapp deployment source config-zip `
  --resource-group $RG `
  --name $APP_NAME `
  --src deploy.zip
```

**Time: 10 minutes**

---

### 📦 Method 4: GitHub Actions (CI/CD)

1. **Fork/Push code to GitHub**

2. **Get Publish Profile:**
   ```powershell
   az webapp deployment list-publishing-profiles `
     --resource-group forest-fire-rg `
     --name forest-fire-detection `
     --xml
   ```

3. **Add GitHub Secret:**
   - Go to repo → Settings → Secrets → New secret
   - Name: `AZURE_WEBAPP_PUBLISH_PROFILE`
   - Value: Paste the XML from step 2

4. **Create workflow:** `.github/workflows/azure-deploy.yml`
   ```yaml
   name: Deploy to Azure
   on: [push]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - uses: azure/webapps-deploy@v2
           with:
             app-name: 'forest-fire-detection'
             publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
   ```

**Time: 15 minutes (one-time setup), then automatic**

---

## 🔑 Get Your API Keys

### NASA FIRMS
1. Visit: https://firms.modaps.eosdis.nasa.gov/api/area/
2. Request MAP_KEY
3. Add to Azure: `FIRMS_MAP_KEY`

### OpenWeather
1. Visit: https://openweathermap.org/api
2. Sign up for free API key
3. Add to Azure: `OPENWEATHER_KEY`

---

## ✅ Post-Deployment Checklist

After deployment:

- [ ] **Test App URL**: Visit `https://your-app-name.azurewebsites.net`
- [ ] **Check Config**: Visit `/config` endpoint
- [ ] **Test API**: Visit `/api/fire-alerts`
- [ ] **Add API Keys** (if skipped):
  ```powershell
  az webapp config appsettings set `
    --resource-group forest-fire-rg `
    --name forest-fire-detection `
    --settings FIRMS_MAP_KEY="your-key" OPENWEATHER_KEY="your-key"
  ```
- [ ] **Update Raspberry Pi**:
  ```bash
  python3 fire_detection_drone.py --backend https://your-app-name.azurewebsites.net
  ```
- [ ] **Enable Monitoring**: Set up Application Insights
- [ ] **Configure Alerts**: Set up alerts for downtime/errors

---

## 🔧 Common Commands

### View Logs
```powershell
az webapp log tail --resource-group forest-fire-rg --name forest-fire-detection
```

### Restart App
```powershell
az webapp restart --resource-group forest-fire-rg --name forest-fire-detection
```

### Update Settings
```powershell
az webapp config appsettings set `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --settings KEY=VALUE
```

### Stop App (Save Money)
```powershell
az webapp stop --resource-group forest-fire-rg --name forest-fire-detection
```

### Start App
```powershell
az webapp start --resource-group forest-fire-rg --name forest-fire-detection
```

### Delete Everything
```powershell
az group delete --name forest-fire-rg --yes
```

---

## 💰 Pricing

| Tier | Cost/Month | CPU | RAM | Storage | Auto-Scale |
|------|------------|-----|-----|---------|------------|
| **F1** (Free) | $0 | 60 min/day | 1GB | 1GB | ❌ |
| **B1** (Basic) | ~$13 | Unlimited | 1.75GB | 10GB | ❌ |
| **S1** (Standard) | ~$70 | Unlimited | 1.75GB | 50GB | ✅ |

**Recommendation:**
- **Testing**: F1 (Free)
- **Production**: B1 or S1

---

## 🆘 Troubleshooting

### App won't start
```powershell
# Check logs
az webapp log tail -g forest-fire-rg -n forest-fire-detection

# Verify startup command
az webapp config show -g forest-fire-rg -n forest-fire-detection --query "siteConfig.appCommandLine"
```

### 502 Bad Gateway
- Increase timeout: `--timeout 600` in startup command
- Check worker count: `--workers 2`
- Verify Python version: `PYTHON:3.11`

### Static files not loading
- Check `static_folder` in app.py
- Verify files are deployed: Check Kudu console

---

## 📚 Full Documentation

- [Complete Azure Deployment Guide](./AZURE_DEPLOYMENT.md)
- [Raspberry Pi Setup Guide](./raspberry_pi/README.md)
- [Deployment Guide](./raspberry_pi/DEPLOYMENT_GUIDE.md)

---

## 🎉 Success!

Once deployed, your app will be available at:
**`https://your-app-name.azurewebsites.net`**

Test it:
```powershell
# Check if running
curl https://your-app-name.azurewebsites.net/config

# Send test alert from Raspberry Pi
python3 fire_detection_drone.py --backend https://your-app-name.azurewebsites.net
```

**Need help?** Check the full [AZURE_DEPLOYMENT.md](./AZURE_DEPLOYMENT.md) guide.
