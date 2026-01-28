#!/bin/bash
# Fire Detection System - Raspberry Pi 4 Setup Script
# Run this script on your Raspberry Pi to set up the system

echo "🔥 Forest Fire Detection System - Raspberry Pi 4 Setup"
echo "========================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

echo "📦 Step 1: Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

echo ""
echo "📦 Step 2: Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-opencv \
    libopencv-dev \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libharfbuzz0b \
    libwebp7 \
    libjasper1 \
    libilmbase25 \
    libopenexr25 \
    libgstreamer1.0-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libqtgui4 \
    libqt4-test \
    gpsd \
    gpsd-clients \
    python3-gps

echo ""
echo "📦 Step 3: Creating Python virtual environment..."
python3 -m venv ~/fire_detection_env
source ~/fire_detection_env/bin/activate

echo ""
echo "📦 Step 4: Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_rpi.txt

echo ""
echo "📦 Step 5: Downloading model files..."
# Create models directory if not exists
mkdir -p ~/fire_detection_models

echo "   Please copy the following model files to ~/fire_detection_models/:"
echo "   - fire and person.pt"
echo "   - aerial_images.pt"
echo ""
echo "   Or use scp from your computer:"
echo "   scp 'G:\Forest-fire-detection\final_model\fire and person.pt' pi@raspberrypi:~/fire_detection_models/"
echo "   scp 'G:\Forest-fire-detection\final_model\aerial_images.pt' pi@raspberrypi:~/fire_detection_models/"

echo ""
echo "📦 Step 6: Setting up camera..."
# Enable camera interface
sudo raspi-config nonint do_camera 0

echo ""
echo "📦 Step 7: Configuring GPS (optional)..."
echo "   If you have a GPS module connected, configure it now."
echo "   Edit /etc/default/gpsd to set the correct device (e.g., /dev/ttyUSB0)"

echo ""
echo "📦 Step 8: Setting up systemd service for auto-start..."
cat > ~/fire-detection.service << 'EOF'
[Unit]
Description=Forest Fire Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
Environment="PATH=/home/pi/fire_detection_env/bin"
ExecStart=/home/pi/fire_detection_env/bin/python3 /home/pi/fire_detection_drone.py --backend http://YOUR_SERVER_IP:8000 --camera 0 --confidence 0.5
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "   Service file created at ~/fire-detection.service"
echo "   To install the service:"
echo "   1. Edit ~/fire-detection.service and set YOUR_SERVER_IP"
echo "   2. sudo cp ~/fire-detection.service /etc/systemd/system/"
echo "   3. sudo systemctl daemon-reload"
echo "   4. sudo systemctl enable fire-detection.service"
echo "   5. sudo systemctl start fire-detection.service"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Copy model files to ~/fire_detection_models/"
echo "   2. Copy fire_detection_drone.py to /home/pi/"
echo "   3. Update backend URL in the service file or run manually with:"
echo "      python3 fire_detection_drone.py --backend http://YOUR_SERVER_IP:8000"
echo "   4. For testing with display: add --display flag"
echo "   5. For production (headless): remove --display flag"
echo ""
echo "🔧 Testing commands:"
echo "   # Test with display"
echo "   source ~/fire_detection_env/bin/activate"
echo "   python3 fire_detection_drone.py --backend http://192.168.1.100:8000 --display"
echo ""
echo "   # Run headless (production)"
echo "   python3 fire_detection_drone.py --backend http://192.168.1.100:8000"
echo ""
echo "📊 Monitor logs:"
echo "   sudo journalctl -u fire-detection.service -f"
echo ""
