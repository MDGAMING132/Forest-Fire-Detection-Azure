# 🔥 Forest Fire Detection - Complete Deployment Guide

## System Architecture

```
┌─────────────────┐
│  Raspberry Pi 4 │
│   (on Drone)    │
│                 │
│  • Camera       │──┐
│  • GPS Module   │  │
│  • Fire Model   │  │
└─────────────────┘  │
                     │ WiFi/4G
                     │
                     ▼
          ┌────────────────┐
          │ Flask Backend  │
          │  (Server PC)   │
          │                │
          │  • API Server  │
          │  • Data Store  │
          └────────────────┘
                     │
                     │ HTTP
                     ▼
          ┌────────────────┐
          │   Frontend     │
          │  (Web Browser) │
          │                │
          │  • Map View    │
          │  • Alerts      │
          │  • Images      │
          └────────────────┘
```

## 🎯 Complete Setup Process

### Phase 1: Server Setup (Your Computer)

1. **Start the Backend Server**
   ```bash
   cd G:\Forest_Fire
   python backend\app.py
   ```
   The server will run on `http://YOUR_IP:8000`

2. **Find Your Server IP Address**
   ```powershell
   # Windows
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)
   ```

3. **Test the Backend**
   Open browser to `http://localhost:8000`
   You should see your forest fire detection interface.

### Phase 2: Raspberry Pi Setup

1. **Copy Files to Raspberry Pi**
   
   From Windows (PowerShell):
   ```powershell
   # Copy Python script
   scp "G:\Forest_Fire\raspberry_pi\fire_detection_drone.py" pi@raspberrypi.local:~/
   
   # Copy requirements
   scp "G:\Forest_Fire\raspberry_pi\requirements_rpi.txt" pi@raspberrypi.local:~/
   
   # Copy setup script
   scp "G:\Forest_Fire\raspberry_pi\setup_rpi.sh" pi@raspberrypi.local:~/
   
   # Copy model files
   scp "G:\Forest-fire-detection\final_model\fire and person.pt" pi@raspberrypi.local:~/fire_detection_models/
   scp "G:\Forest-fire-detection\final_model\aerial_images.pt" pi@raspberrypi.local:~/fire_detection_models/
   ```

   Or use alternative methods:
   - **WinSCP**: GUI file transfer tool
   - **USB Drive**: Copy files manually
   - **Git**: Push to repository and clone on Pi

2. **SSH into Raspberry Pi**
   ```bash
   ssh pi@raspberrypi.local
   # Default password: raspberry
   ```

3. **Run Setup Script**
   ```bash
   chmod +x setup_rpi.sh
   ./setup_rpi.sh
   ```

4. **Activate Python Environment**
   ```bash
   source ~/fire_detection_env/bin/activate
   ```

5. **Verify Installation**
   ```bash
   python3 -c "from ultralytics import YOLO; import cv2; print('✅ All packages OK')"
   ```

### Phase 3: Network Configuration

#### Option A: Same WiFi Network (Easiest for Testing)
1. Connect both devices to the same WiFi
2. Use server's IP address: `http://192.168.1.100:8000`

#### Option B: Mobile Hotspot (For Drone Operation)
1. Create hotspot on your phone
2. Connect both Raspberry Pi and server computer to hotspot
3. Find server IP in hotspot settings
4. Use that IP address

#### Option C: 4G/LTE Module (Advanced)
1. Install 4G module on Raspberry Pi
2. Use public IP or VPN
3. Configure firewall rules

### Phase 4: Testing

1. **Test Detection Locally (on Raspberry Pi)**
   ```bash
   # Replace 192.168.1.100 with your server IP
   python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --display --confidence 0.4
   ```

2. **Check Backend Receives Data**
   - Watch backend console for: `🔥 Fire alert received from...`
   - Open frontend in browser
   - Check "Fire Alerts" panel for incoming alerts

3. **Test Without Fire**
   - Point camera at non-fire objects
   - Should not send alerts

4. **Test With Fire (Safely!)**
   - Use images/videos of fire
   - Or use a lighter/candle at safe distance
   - Should trigger alerts

### Phase 5: Production Deployment

1. **Configure Auto-Start**
   ```bash
   # Edit service file
   nano ~/fire-detection.service
   
   # Update backend URL:
   ExecStart=/home/pi/fire_detection_env/bin/python3 /home/pi/fire_detection_drone.py --backend http://YOUR_SERVER_IP:8000 --camera 0 --confidence 0.5 --cooldown 10
   
   # Install service
   sudo cp ~/fire-detection.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable fire-detection.service
   sudo systemctl start fire-detection.service
   ```

2. **Check Service Status**
   ```bash
   sudo systemctl status fire-detection.service
   sudo journalctl -u fire-detection.service -f
   ```

3. **Disable Display for Headless Operation**
   Remove `--display` flag from service file

## 📊 Expected Data Flow

### When Fire is Detected:

1. **Raspberry Pi captures frame**
   - Camera: 640x480 @ 15 FPS
   - Processing: YOLO inference

2. **Detection triggers alert**
   - Confidence > threshold (default 0.5)
   - Cooldown prevents spam (default 5s)

3. **Alert sent to backend**
   ```json
   {
     "type": "fire",
     "confidence": 0.8542,
     "timestamp": "2026-01-28T14:30:45.123456",
     "location": {
       "latitude": 37.7749,
       "longitude": -122.4194,
       "altitude": 150.5,
       "coordinates": "37.774900, -122.419400"
     },
     "image": "data:image/jpeg;base64,...",
     "device": "Raspberry Pi 4 - Drone"
   }
   ```

4. **Backend stores alert**
   - Endpoint: `POST /api/fire-alert`
   - Stored in memory (last 100 alerts)

5. **Frontend displays alert**
   - Auto-refreshes every 5 seconds
   - Shows on map with drone icon 🚁
   - Displays image, confidence, GPS, time

## 🎛️ Configuration Parameters

### fire_detection_drone.py

| Parameter | Description | Default | Recommended Range |
|-----------|-------------|---------|-------------------|
| `--backend` | Backend server URL | Required | http://IP:8000 |
| `--camera` | Camera device index | 0 | 0-2 |
| `--confidence` | Min confidence (0-1) | 0.5 | 0.3-0.7 |
| `--cooldown` | Seconds between alerts | 5 | 5-30 |
| `--display` | Show video feed | False | Use for testing only |

### Performance Tuning

**For Higher Sensitivity (More False Positives):**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --confidence 0.3
```

**For Higher Precision (Fewer False Positives):**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --confidence 0.7
```

**For Frequent Updates:**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --cooldown 3
```

**For Battery Conservation:**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --cooldown 30
```

## 📍 GPS Integration

### Hardware Setup
1. **Connect GPS Module** (e.g., NEO-6M)
   - VCC → 5V (Pin 2)
   - GND → GND (Pin 6)
   - TX → GPIO 14 (Pin 8 - RX)
   - RX → GPIO 15 (Pin 10 - TX)

2. **Enable UART**
   ```bash
   sudo raspi-config
   # Interface Options → Serial Port
   # Login shell: NO
   # Serial port: YES
   ```

3. **Configure GPS Daemon**
   ```bash
   sudo nano /etc/default/gpsd
   ```
   ```
   START_DAEMON="true"
   GPSD_OPTIONS="-n"
   DEVICES="/dev/serial0"
   USBAUTO="true"
   ```

4. **Restart GPS Service**
   ```bash
   sudo systemctl restart gpsd
   sudo systemctl enable gpsd
   ```

5. **Test GPS**
   ```bash
   cgps -s
   # Wait for satellite fix (may take 1-5 minutes outdoors)
   ```

### Without GPS
If no GPS module, the system uses default coordinates (0, 0).
You can manually set coordinates in the code:
```python
self.current_lat = YOUR_LAT
self.current_lon = YOUR_LON
```

## 🔍 Troubleshooting

### Issue: "Models not found"
**Solution:**
```bash
ls -lh ~/fire_detection_models/
# Should show two .pt files
# If not, copy them again
```

### Issue: "Failed to open camera"
**Solution:**
```bash
# Check camera
vcgencmd get_camera
# Should show: supported=1 detected=1

# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable

# Test camera
raspistill -o test.jpg

# Check USB cameras
ls /dev/video*
```

### Issue: "Network error sending alert"
**Solution:**
```bash
# Test backend connectivity
curl http://YOUR_SERVER_IP:8000/config

# Check IP address
hostname -I

# Ping server
ping YOUR_SERVER_IP
```

### Issue: Low FPS / Slow Performance
**Solution:**
```bash
# Check temperature
vcgencmd measure_temp

# Check throttling
vcgencmd get_throttled
# 0x0 = OK

# Add cooling (heatsink/fan)
# Increase GPU memory
sudo nano /boot/config.txt
# Add: gpu_mem=256
```

### Issue: GPS not working
**Solution:**
```bash
# Check GPS daemon
sudo systemctl status gpsd

# Check device
ls /dev/serial0 /dev/ttyUSB0

# Monitor GPS
gpsmon

# View raw data
cat /dev/serial0
```

## 📈 Performance Expectations

### Raspberry Pi 4 (4GB/8GB)
- **FPS**: 3-8 fps (depending on model size)
- **Detection Time**: 200-500ms per frame
- **Power Draw**: 3-5W
- **Network Latency**: 50-200ms (local WiFi)

### Optimal Settings
- **Resolution**: 640x480 (good balance)
- **Confidence**: 0.5 (balanced sensitivity)
- **Cooldown**: 5-10 seconds
- **Alert Size**: ~100-200KB per alert with image

## 🔐 Security Recommendations

1. **Change Default Password**
   ```bash
   passwd
   ```

2. **Use SSH Keys**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id pi@raspberrypi
   ```

3. **Firewall on Server**
   ```bash
   # Only allow from specific IPs
   ```

4. **HTTPS** (Production)
   - Use reverse proxy (nginx)
   - Add SSL certificate

## 📊 Monitoring

### View Live Logs
```bash
# Service logs
sudo journalctl -u fire-detection.service -f

# System logs
tail -f /var/log/syslog
```

### Check System Status
```bash
# Temperature
watch -n 2 vcgencmd measure_temp

# CPU usage
htop

# Memory
free -h

# Disk
df -h
```

### Backend Monitoring
Check Flask console for:
- `🔥 Fire alert received from...` (success)
- Network errors (connection issues)
- Alert count

## 🎯 Success Indicators

✅ **Everything Working:**
- Raspberry Pi connects to backend
- Camera captures frames
- Fire detection runs (check FPS in logs)
- Alerts appear in backend console
- Frontend shows alerts on map
- Images load in frontend
- GPS coordinates update (if GPS enabled)

## 📞 Support Checklist

If something doesn't work:
1. ✓ Server backend running?
2. ✓ Server IP address correct?
3. ✓ Both devices on same network?
4. ✓ Model files copied?
5. ✓ Camera detected?
6. ✓ Python packages installed?
7. ✓ Firewall allows port 8000?

## 🚀 Quick Commands Reference

```bash
# Start detection (testing)
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --display

# Start detection (production)
python3 fire_detection_drone.py --backend http://192.168.1.100:8000

# View logs
sudo journalctl -u fire-detection.service -f

# Restart service
sudo systemctl restart fire-detection.service

# Check status
sudo systemctl status fire-detection.service

# Stop service
sudo systemctl stop fire-detection.service
```

## 📝 Notes

- First GPS fix may take 1-5 minutes outdoors
- Indoor GPS won't work (needs sky visibility)
- Battery life depends on usage pattern
- Consider power bank for extended drone flights
- Test thoroughly before actual deployment
- Keep firmware updated

---

**Ready to Deploy!** 🚁🔥

Follow the phases in order, test each step, and you'll have a working forest fire detection drone system!
