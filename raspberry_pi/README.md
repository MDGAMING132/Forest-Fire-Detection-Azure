# 🔥 Forest Fire Detection System - Raspberry Pi 4 Deployment Guide

## 🎯 Overview
This system deploys YOLO-based fire detection on a Raspberry Pi 4 mounted on a drone. When fire is detected, it automatically sends alerts with images, GPS coordinates, timestamp, and confidence scores to your frontend via the Flask backend.

## 📋 Hardware Requirements
- **Raspberry Pi 4** (4GB RAM minimum, 8GB recommended)
- **Camera**: Raspberry Pi Camera Module V2 or USB webcam
- **GPS Module** (optional but recommended): NEO-6M or similar
- **Power**: Battery pack suitable for drone operation
- **SD Card**: 32GB+ (Class 10 or better)
- **Cooling**: Heat sinks and/or small fan (recommended)

## 🚀 Quick Start

### 1. Prepare Your Raspberry Pi

```bash
# On your Raspberry Pi, download the setup files
mkdir -p ~/fire_detection
cd ~/fire_detection

# Copy files from this repository to your Pi
# You can use scp, USB drive, or git clone
```

### 2. Run Setup Script

```bash
chmod +x setup_rpi.sh
./setup_rpi.sh
```

### 3. Transfer Model Files

From your Windows computer:
```powershell
# Replace 'pi@raspberrypi' with your Pi's actual hostname/IP
scp "G:\Forest-fire-detection\final_model\fire and person.pt" pi@raspberrypi:~/fire_detection_models/
scp "G:\Forest-fire-detection\final_model\aerial_images.pt" pi@raspberrypi:~/fire_detection_models/
scp "G:\Forest_Fire\raspberry_pi\fire_detection_drone.py" pi@raspberrypi:~/
```

Or use WinSCP, FileZilla, or copy via USB drive.

### 4. Configure Backend URL

Edit the Python script or use command-line arguments:
```bash
# Replace 192.168.1.100 with your backend server's IP
python3 fire_detection_drone.py --backend http://192.168.1.100:8000
```

## 🔧 Configuration Options

### Command Line Arguments

```bash
python3 fire_detection_drone.py [OPTIONS]

Options:
  --backend URL         Backend server URL (default: http://192.168.1.100:8000)
  --camera INDEX        Camera device index (default: 0)
  --confidence FLOAT    Detection confidence threshold 0-1 (default: 0.5)
  --display            Enable video display (for testing only)
  --cooldown SECONDS   Seconds between alerts (default: 5)
```

### Examples

**Testing with display:**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --display --confidence 0.4
```

**Production (headless):**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --confidence 0.5 --cooldown 10
```

**High sensitivity:**
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --confidence 0.3
```

## 📍 GPS Setup

### Hardware Connection
1. Connect GPS module to Raspberry Pi:
   - VCC → 5V
   - GND → GND
   - TX → GPIO 14 (RX)
   - RX → GPIO 15 (TX)

### Software Configuration

```bash
# Install GPS daemon
sudo apt-get install gpsd gpsd-clients python3-gps

# Configure GPS device
sudo nano /etc/default/gpsd

# Add/modify these lines:
START_DAEMON="true"
GPSD_OPTIONS="-n"
DEVICES="/dev/ttyUSB0"  # or /dev/serial0 for Pi GPIO
USBAUTO="true"
GPSD_SOCKET="/var/run/gpsd.sock"

# Restart GPS daemon
sudo systemctl restart gpsd
sudo systemctl enable gpsd

# Test GPS
cgps -s
```

## 🔄 Auto-Start on Boot

### Setup Systemd Service

1. Edit the service file:
```bash
nano ~/fire-detection.service
```

2. Update the backend URL:
```ini
ExecStart=/home/pi/fire_detection_env/bin/python3 /home/pi/fire_detection_drone.py --backend http://YOUR_SERVER_IP:8000 --camera 0 --confidence 0.5
```

3. Install and enable:
```bash
sudo cp ~/fire-detection.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fire-detection.service
sudo systemctl start fire-detection.service
```

4. Check status:
```bash
sudo systemctl status fire-detection.service
sudo journalctl -u fire-detection.service -f
```

## 📡 Network Configuration

### WiFi Setup
```bash
sudo raspi-config
# Select: System Options → Wireless LAN
# Enter SSID and password
```

### Static IP (Recommended)
```bash
sudo nano /etc/dhcpcd.conf

# Add at the end:
interface wlan0
static ip_address=192.168.1.50/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8
```

### Mobile Hotspot (Drone Operation)
Configure your phone/mobile hotspot and connect the Pi to it.

## 📊 Alert Data Structure

The system sends the following JSON to your backend:

```json
{
  "type": "fire",
  "confidence": 0.8542,
  "timestamp": "2026-01-28T14:30:45.123456",
  "location": {
    "type": "drone",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 150.5,
    "coordinates": "37.774900, -122.419400",
    "city": "Drone Location",
    "country": "Detection Area"
  },
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "bbox": [[100, 150, 250, 300]],
  "detectionCount": 1,
  "device": "Raspberry Pi 4 - Drone",
  "source": "aerial_camera"
}
```

## 🔍 Frontend Integration

Your existing frontend already has the endpoints configured:
- `POST /api/fire-alert` - Receives alerts from Raspberry Pi
- `GET /api/fire-alerts` - Retrieves all alerts
- `GET /api/fire-alert/<id>` - Gets specific alert with image

The fire alerts will automatically appear in your frontend interface!

## ⚡ Performance Optimization

### Raspberry Pi 4 Settings

**Increase GPU memory:**
```bash
sudo nano /boot/config.txt
# Add or modify:
gpu_mem=256
```

**Overclock (optional, ensure cooling):**
```bash
sudo nano /boot/config.txt
# Add:
over_voltage=6
arm_freq=2000
```

**Disable GUI (for headless):**
```bash
sudo raspi-config
# System Options → Boot / Auto Login → Console
```

### Camera Optimization

The script automatically sets optimal camera parameters:
- Resolution: 640x480
- FPS: 15
- JPEG quality: 85%

You can modify these in `fire_detection_drone.py`:
```python
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 15)
```

## 🐛 Troubleshooting

### Camera Not Detected
```bash
# Check camera
vcgencmd get_camera

# Enable camera interface
sudo raspi-config
# Interface Options → Camera → Enable

# Reboot
sudo reboot
```

### Models Not Loading
```bash
# Verify model files exist
ls -lh ~/fire_detection_models/

# Check permissions
chmod 644 ~/fire_detection_models/*.pt

# Update model paths in fire_detection_drone.py if needed
```

### GPS Not Working
```bash
# Check GPS daemon
sudo systemctl status gpsd

# Test GPS connection
cgps -s
# or
gpsmon

# Check device
ls /dev/tty*
# Look for /dev/ttyUSB0 or /dev/serial0
```

### Network Connection Issues
```bash
# Test backend connectivity
curl http://YOUR_SERVER_IP:8000/config

# Check WiFi
iwconfig

# Ping test
ping 8.8.8.8
```

### Low FPS / Performance Issues
```bash
# Monitor CPU/GPU temperature
vcgencmd measure_temp

# Monitor system resources
htop

# Check throttling
vcgencmd get_throttled
# 0x0 = OK, anything else indicates throttling
```

## 📈 Monitoring

### Real-time Logs
```bash
# Service logs
sudo journalctl -u fire-detection.service -f

# System logs
tail -f /var/log/syslog

# GPS logs
tail -f /var/log/gpsd.log
```

### System Stats
```bash
# Temperature
watch -n 2 vcgencmd measure_temp

# Memory usage
free -h

# Disk usage
df -h
```

## 🔒 Security Recommendations

1. **Change default password:**
   ```bash
   passwd
   ```

2. **Update system regularly:**
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

3. **Use SSH keys instead of password:**
   ```bash
   ssh-keygen -t rsa -b 4096
   ssh-copy-id pi@raspberrypi
   ```

4. **Firewall (optional):**
   ```bash
   sudo apt-get install ufw
   sudo ufw allow ssh
   sudo ufw enable
   ```

## 🧪 Testing

### Test Detection Locally
```bash
python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --display
```

### Test Without Backend
Modify the script to save alerts locally:
```python
# Comment out the backend sending in _send_alert()
# Add file saving instead
```

### Simulate Fire Detection
Use test images or videos:
```python
# In fire_detection_drone.py, replace camera with video file
cap = cv2.VideoCapture("test_fire_video.mp4")
```

## 📚 Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [OpenCV on Raspberry Pi](https://opencv.org/)
- [Ultralytics YOLO](https://docs.ultralytics.com/)
- [GPS on Raspberry Pi](https://gpsd.gitlab.io/gpsd/)

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review system logs
3. Verify all connections and configurations
4. Test components individually

## 📄 License

This fire detection system is provided as-is for forest fire monitoring and prevention purposes.
