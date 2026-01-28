# Fire Alert Integration Setup

## Changes Made:
✅ Added 3 new API endpoints for fire detection alerts
✅ Added CORS support for cross-origin requests
✅ No existing code was modified - only additions

## New Endpoints:
- `POST /api/fire-alert` - Receives fire alerts from webcam AI
- `GET /api/fire-alerts` - Gets all fire alerts
- `GET /api/fire-alert/<id>` - Gets specific alert with image

## Setup Instructions:

### 1. Install Dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Server:
```bash
python app.py
```
Server runs on: `http://0.0.0.0:8000` (accessible at `http://localhost:8000`)

### 3. Test API:
```bash
# Check if server is running
curl http://localhost:8000/config

# View fire alerts (empty at start)
curl http://localhost:8000/api/fire-alerts
```

## For the Detection Laptop:

Your friend (who runs the webcam fire detection) should use:
```bash
python fire_detection_server.py --dashboard http://YOUR-IP:8000
```

Replace `YOUR-IP` with your IPv4 address from `ipconfig`

Example: `http://172.22.243.10:8000`

## View Alerts:

Open in browser:
- All alerts: `http://localhost:8000/api/fire-alerts`
- With images: `http://localhost:8000/api/fire-alerts?includeImages=true`

Or integrate into your existing map dashboard!
