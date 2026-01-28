# 🌐 Azure Deployment Guide - Forest Fire Detection System

## 📋 Prerequisites

1. **Azure Account**: [Create free account](https://azure.microsoft.com/free/)
2. **Azure CLI**: [Install Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)
3. **Git**: [Install Git](https://git-scm.com/downloads)

## 🚀 Quick Deployment (Azure App Service)

### Method 1: Azure Portal (Easiest)

#### Step 1: Create App Service

1. **Login to Azure Portal**: https://portal.azure.com
2. Click **"Create a resource"** → **"Web App"**
3. Configure:
   - **Resource Group**: Create new → `forest-fire-rg`
   - **Name**: `forest-fire-detection` (must be globally unique)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux
   - **Region**: Choose closest to your location
   - **Pricing Plan**: 
     - Free (F1) for testing
     - Basic (B1) or higher for production
4. Click **"Review + Create"** → **"Create"**

#### Step 2: Configure Application Settings

1. Go to your App Service → **Configuration** → **Application settings**
2. Add the following settings:

| Name | Value | Description |
|------|-------|-------------|
| `FIRMS_MAP_KEY` | your_key | NASA FIRMS API key |
| `FIRMS_WMS_URL` | https://firms.modaps.eosdis.nasa.gov/wms/ | FIRMS WMS URL |
| `ENABLE_FIRMS_WMS` | true | Enable WMS |
| `FIRMS_DAYS_DEFAULT` | 1 | Default days |
| `OPENWEATHER_KEY` | your_key | OpenWeather API key |
| `SENTINELHUB_CLIENT_ID` | your_id | Sentinel Hub ID (optional) |
| `SENTINELHUB_CLIENT_SECRET` | your_secret | Sentinel Hub secret (optional) |
| `SENTINEL_WMS_URL` | https://tiles.maps.eox.at/wms | Sentinel WMS URL |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | true | Enable build |
| `PORT` | 8000 | Application port |

3. Click **"Save"**

#### Step 3: Deploy Code

**Option A: GitHub Integration (Recommended)**

1. Go to **Deployment Center**
2. Choose **GitHub** as source
3. Authorize Azure to access GitHub
4. Select your repository and branch
5. Click **"Save"**
6. Azure will automatically deploy on every push

**Option B: Local Git Deployment**

1. Go to **Deployment Center**
2. Choose **Local Git**
3. Click **"Save"**
4. Copy the Git URL

On your computer:
```powershell
# Initialize git repository
cd G:\Forest_Fire
git init
git add .
git commit -m "Initial commit for Azure deployment"

# Add Azure remote
git remote add azure <your-git-url-from-azure>

# Deploy
git push azure master
```

**Option C: ZIP Deploy**

```powershell
# Install Azure CLI
# https://docs.microsoft.com/cli/azure/install-azure-cli

# Login
az login

# Create ZIP file (excluding unnecessary files)
cd G:\Forest_Fire
Compress-Archive -Path * -DestinationPath deploy.zip -Force

# Deploy
az webapp deployment source config-zip `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --src deploy.zip
```

#### Step 4: Configure Startup Command

1. Go to **Configuration** → **General settings**
2. Set **Startup Command**:
   ```bash
   gunicorn --bind=0.0.0.0:$PORT --timeout 600 backend.app:app
   ```
3. Click **"Save"**

#### Step 5: Verify Deployment

1. Go to **Overview** → Click your app URL
2. Should see: `https://forest-fire-detection.azurewebsites.net`
3. Test endpoints:
   - `/` - Frontend
   - `/config` - Configuration
   - `/api/fire-alerts` - Fire alerts API

### Method 2: Azure CLI (Advanced)

```powershell
# Login to Azure
az login

# Set subscription (if you have multiple)
az account set --subscription "Your Subscription Name"

# Create resource group
az group create --name forest-fire-rg --location eastus

# Create App Service plan
az appservice plan create `
  --name forest-fire-plan `
  --resource-group forest-fire-rg `
  --sku B1 `
  --is-linux

# Create web app
az webapp create `
  --resource-group forest-fire-rg `
  --plan forest-fire-plan `
  --name forest-fire-detection `
  --runtime "PYTHON:3.11"

# Configure app settings
az webapp config appsettings set `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --settings `
    FIRMS_MAP_KEY="your_key" `
    OPENWEATHER_KEY="your_key" `
    ENABLE_FIRMS_WMS="true" `
    PORT="8000" `
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Set startup command
az webapp config set `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --startup-file "gunicorn --bind=0.0.0.0:8000 --timeout 600 backend.app:app"

# Deploy from local git
az webapp deployment source config-local-git `
  --resource-group forest-fire-rg `
  --name forest-fire-detection

# Get deployment URL
az webapp deployment list-publishing-credentials `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --query scmUri `
  --output tsv

# Add remote and push
git remote add azure <deployment-url>
git push azure master
```

## 📡 Update Raspberry Pi Configuration

After deploying to Azure, update your Raspberry Pi:

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi

# Edit the service file
nano ~/fire-detection.service
```

Change the backend URL:
```ini
ExecStart=/home/pi/fire_detection_env/bin/python3 /home/pi/fire_detection_drone.py --backend https://forest-fire-detection.azurewebsites.net --camera 0 --confidence 0.5
```

Restart service:
```bash
sudo systemctl daemon-reload
sudo systemctl restart fire-detection.service
sudo journalctl -u fire-detection.service -f
```

Or run manually:
```bash
python3 fire_detection_drone.py --backend https://forest-fire-detection.azurewebsites.net --display
```

## 🔧 Configuration

### Custom Domain (Optional)

1. Go to **Custom domains** in Azure Portal
2. Click **"Add custom domain"**
3. Follow instructions to configure DNS
4. Add SSL certificate (free with App Service Managed Certificate)

### CORS Configuration

If you need to allow specific origins:

```python
# In backend/app.py
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://yourdomain.com",
            "https://forest-fire-detection.azurewebsites.net"
        ]
    }
})
```

### SSL/HTTPS

Azure App Service provides free SSL certificate:
1. Go to **TLS/SSL settings**
2. **Private Key Certificates** → **Create App Service Managed Certificate**
3. Add binding to your domain

## 📊 Monitoring & Logging

### View Live Logs

**Azure Portal:**
1. Go to **Log stream** in your App Service
2. View real-time application logs

**Azure CLI:**
```powershell
az webapp log tail `
  --resource-group forest-fire-rg `
  --name forest-fire-detection
```

### Application Insights (Recommended)

1. **Create Application Insights**:
   ```powershell
   az monitor app-insights component create `
     --app forest-fire-insights `
     --location eastus `
     --resource-group forest-fire-rg
   ```

2. **Get Instrumentation Key**:
   ```powershell
   az monitor app-insights component show `
     --app forest-fire-insights `
     --resource-group forest-fire-rg `
     --query instrumentationKey
   ```

3. **Add to App Settings**:
   ```powershell
   az webapp config appsettings set `
     --resource-group forest-fire-rg `
     --name forest-fire-detection `
     --settings APPINSIGHTS_INSTRUMENTATIONKEY="your-key"
   ```

### Metrics to Monitor

- **CPU Usage**: Should be < 70%
- **Memory Usage**: Should be < 80%
- **Response Time**: Should be < 2s
- **HTTP Status Codes**: Monitor 4xx and 5xx errors
- **Request Count**: Track traffic

## 🔒 Security Best Practices

### 1. Environment Variables
Never commit `.env` file with real keys to Git:
```powershell
# Ensure .gitignore includes .env
echo ".env" >> .gitignore
```

### 2. Authentication (Optional)
Add Azure Active Directory authentication:
```powershell
az webapp auth update `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --enabled true `
  --action LoginWithAzureActiveDirectory
```

### 3. Network Security
Configure IP restrictions:
```powershell
# Allow only specific IPs
az webapp config access-restriction add `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --rule-name "AllowRaspberryPi" `
  --action Allow `
  --ip-address YOUR_PI_IP/32 `
  --priority 100
```

### 4. HTTPS Only
```powershell
az webapp update `
  --resource-group forest-fire-rg `
  --name forest-fire-detection `
  --https-only true
```

## 💰 Cost Optimization

### Free Tier (F1)
- **Cost**: $0/month
- **Limitations**: 
  - 1GB storage
  - 60 minutes CPU/day
  - No auto-scaling
- **Use for**: Testing only

### Basic Tier (B1)
- **Cost**: ~$13/month
- **Features**:
  - 1.75GB RAM
  - Unlimited CPU
  - Custom domains
  - SSL
- **Use for**: Small deployments

### Standard Tier (S1)
- **Cost**: ~$70/month
- **Features**:
  - Auto-scaling
  - Staging slots
  - Daily backups
- **Use for**: Production

### Cost Saving Tips
1. **Use Free Tier for testing**
2. **Stop app when not in use**:
   ```powershell
   az webapp stop --resource-group forest-fire-rg --name forest-fire-detection
   ```
3. **Auto-shutdown schedule**
4. **Monitor usage with Azure Cost Management**

## 🔄 Continuous Deployment

### GitHub Actions (Recommended)

Azure automatically creates a workflow file. You can customize it:

`.github/workflows/main_forest-fire-detection.yml`:
```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: 'forest-fire-detection'
        publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## 🐛 Troubleshooting

### Issue: Application not starting

**Check logs:**
```powershell
az webapp log tail --resource-group forest-fire-rg --name forest-fire-detection
```

**Common causes:**
1. Missing dependencies in `requirements.txt`
2. Wrong startup command
3. Port mismatch
4. Missing environment variables

**Solution:**
```powershell
# Restart app
az webapp restart --resource-group forest-fire-rg --name forest-fire-detection

# Check configuration
az webapp config show --resource-group forest-fire-rg --name forest-fire-detection
```

### Issue: 502 Bad Gateway

**Cause:** Application crashed or timeout

**Solution:**
1. Increase timeout in startup command:
   ```bash
   gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 backend.app:app
   ```
2. Check application logs
3. Verify environment variables

### Issue: Static files not loading

**Cause:** Incorrect path configuration

**Solution:**
Ensure `app.py` has correct static folder:
```python
app = Flask(__name__, static_folder=BASE_DIR, static_url_path="")
```

### Issue: Raspberry Pi can't connect

**Check:**
1. Azure URL is correct
2. Firewall allows outbound connections
3. Azure App Service is running
4. Test manually:
   ```bash
   curl https://forest-fire-detection.azurewebsites.net/config
   ```

## 📈 Scaling

### Vertical Scaling (Upgrade tier)
```powershell
az appservice plan update `
  --resource-group forest-fire-rg `
  --name forest-fire-plan `
  --sku S1
```

### Horizontal Scaling (More instances)
```powershell
az appservice plan update `
  --resource-group forest-fire-rg `
  --name forest-fire-plan `
  --number-of-workers 3
```

### Auto-scaling (Standard tier and above)
```powershell
az monitor autoscale create `
  --resource-group forest-fire-rg `
  --resource forest-fire-plan `
  --resource-type Microsoft.Web/serverfarms `
  --name autoscale-plan `
  --min-count 1 `
  --max-count 5 `
  --count 1

az monitor autoscale rule create `
  --resource-group forest-fire-rg `
  --autoscale-name autoscale-plan `
  --condition "CpuPercentage > 70 avg 5m" `
  --scale out 1
```

## ✅ Deployment Checklist

- [ ] Azure account created
- [ ] Resource group created
- [ ] App Service created
- [ ] Environment variables configured
- [ ] API keys added
- [ ] Code deployed
- [ ] Application is running
- [ ] Frontend accessible via URL
- [ ] API endpoints working
- [ ] Raspberry Pi updated with Azure URL
- [ ] Raspberry Pi can send alerts
- [ ] Alerts appear in frontend
- [ ] Logs configured
- [ ] Monitoring enabled
- [ ] SSL/HTTPS enabled
- [ ] Custom domain configured (optional)
- [ ] Backup configured

## 🎯 Quick Test

After deployment:

```powershell
# Test backend
curl https://forest-fire-detection.azurewebsites.net/config

# Test fire alerts endpoint
curl https://forest-fire-detection.azurewebsites.net/api/fire-alerts

# Test from Raspberry Pi
python3 fire_detection_drone.py --backend https://forest-fire-detection.azurewebsites.net
```

## 📚 Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure CLI Reference](https://docs.microsoft.com/cli/azure/)
- [Python on Azure](https://docs.microsoft.com/azure/developer/python/)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)

## 🎉 Success!

Your Forest Fire Detection System is now deployed on Azure!

**Access your app**: `https://forest-fire-detection.azurewebsites.net`

**Next steps:**
1. Configure your Raspberry Pi with the Azure URL
2. Set up monitoring and alerts
3. Configure auto-scaling for production
4. Add custom domain and SSL
5. Implement authentication if needed

---

**Need Help?** Check logs with:
```powershell
az webapp log tail --resource-group forest-fire-rg --name forest-fire-detection
```
