"""
Forest Fire Detection System for Raspberry Pi 4 (Drone Deployment)
Detects fire using YOLO models and sends alerts to backend server
"""
from ultralytics import YOLO
import cv2
import numpy as np
import os
import requests
import base64
import json
from datetime import datetime
import time
import threading
import queue

# Try to import GPS library for drone location
try:
    import gpsd
    GPS_AVAILABLE = True
except ImportError:
    GPS_AVAILABLE = False
    print("⚠️ GPS library not available. Using default coordinates.")

class FireDetectionDrone:
    def __init__(self, backend_url="http://YOUR_SERVER_IP:8000", confidence_threshold=0.5):
        """
        Initialize Fire Detection System for Raspberry Pi
        
        Args:
            backend_url: URL of your Flask backend server
            confidence_threshold: Minimum confidence for fire detection (0-1)
        """
        self.backend_url = backend_url
        self.confidence_threshold = confidence_threshold
        self.alert_queue = queue.Queue()
        self.last_alert_time = 0
        self.alert_cooldown = 5  # Send alert every 5 seconds max
        
        # GPS coordinates
        self.current_lat = 0.0
        self.current_lon = 0.0
        self.current_altitude = 0.0
        
        # Load models
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(os.path.dirname(base_dir), "Forest-fire-detection", "final_model")
        
        self.m1_path = os.path.join(models_dir, "fire and person.pt")
        self.m2_path = os.path.join(models_dir, "aerial_images.pt")
        
        print("🚀 Initializing Fire Detection System for Raspberry Pi...")
        print(f"📡 Backend URL: {self.backend_url}")
        print(f"🎯 Confidence Threshold: {self.confidence_threshold}")
        
        self._load_models()
        self._init_gps()
        
        # Start alert sender thread
        self.alert_thread = threading.Thread(target=self._alert_sender, daemon=True)
        self.alert_thread.start()
    
    def _load_models(self):
        """Load YOLO models for fire detection"""
        if not os.path.exists(self.m1_path) or not os.path.exists(self.m2_path):
            print(f"❌ Models not found!")
            print(f"   Looking for: {self.m1_path}")
            print(f"   Looking for: {self.m2_path}")
            raise FileNotFoundError("Model files not found")
        
        print(f"📦 Loading M1 (Fire & Person): {os.path.basename(self.m1_path)}")
        self.model1 = YOLO(self.m1_path)
        
        print(f"📦 Loading M2 (Aerial Images): {os.path.basename(self.m2_path)}")
        self.model2 = YOLO(self.m2_path)
        
        print("✅ Models loaded successfully!")
    
    def _init_gps(self):
        """Initialize GPS connection if available"""
        if GPS_AVAILABLE:
            try:
                gpsd.connect()
                print("📍 GPS connected successfully")
            except Exception as e:
                print(f"⚠️ GPS connection failed: {e}")
                print("   Using default coordinates")
        else:
            print("📍 GPS not available, using default coordinates")
    
    def _get_gps_location(self):
        """Get current GPS coordinates from drone"""
        if GPS_AVAILABLE:
            try:
                packet = gpsd.get_current()
                if packet.mode >= 2:  # 2D or 3D fix
                    self.current_lat = packet.lat
                    self.current_lon = packet.lon
                    if packet.mode >= 3:
                        self.current_altitude = packet.alt
                    return True
            except Exception as e:
                print(f"⚠️ GPS read error: {e}")
        return False
    
    def _frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 string for transmission"""
        # Resize for transmission (reduce bandwidth)
        height, width = frame.shape[:2]
        max_dimension = 800
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            frame = cv2.resize(frame, None, fx=scale, fy=scale)
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"
    
    def _send_alert(self, alert_data):
        """Send fire alert to backend server"""
        try:
            response = requests.post(
                f"{self.backend_url}/api/fire-alert",
                json=alert_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Alert sent successfully! Alert ID: {result.get('alertId')}")
                return True
            else:
                print(f"❌ Alert failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Network error sending alert: {e}")
            return False
    
    def _alert_sender(self):
        """Background thread to send alerts without blocking detection"""
        while True:
            try:
                alert = self.alert_queue.get()
                self._send_alert(alert)
                self.alert_queue.task_done()
            except Exception as e:
                print(f"❌ Alert sender error: {e}")
    
    def _create_alert(self, frame, detections):
        """Create alert data structure"""
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Get GPS location
        self._get_gps_location()
        
        # Find highest confidence fire detection
        fire_detections = [d for d in detections if d['label'].lower().startswith('fire')]
        max_confidence = max([d['confidence'] for d in fire_detections])
        
        alert_data = {
            "type": "fire",
            "confidence": round(max_confidence, 4),
            "timestamp": timestamp,
            "location": {
                "type": "drone",
                "latitude": self.current_lat,
                "longitude": self.current_lon,
                "altitude": self.current_altitude,
                "coordinates": f"{self.current_lat:.6f}, {self.current_lon:.6f}",
                "city": "Drone Location",
                "country": "Detection Area"
            },
            "image": self._frame_to_base64(frame),
            "bbox": [d['bbox'] for d in fire_detections],
            "detectionCount": len(fire_detections),
            "device": "Raspberry Pi 4 - Drone",
            "source": "aerial_camera"
        }
        
        return alert_data
    
    def detect_and_alert(self, frame):
        """
        Run fire detection on frame and send alert if fire detected
        
        Args:
            frame: OpenCV frame from camera
            
        Returns:
            annotated_frame: Frame with detection boxes
            fire_detected: Boolean indicating if fire was detected
        """
        # Run inference on both models
        results1 = self.model1(frame, verbose=False, conf=self.confidence_threshold)
        results2 = self.model2(frame, verbose=False, conf=self.confidence_threshold)
        
        # Process all detections
        all_boxes = []
        all_confidences = []
        all_labels = []
        detections = []
        fire_detected = False
        
        # Color mapping (BGR for OpenCV)
        colors = {
            'person': (0, 255, 0),   # Green
            'fire': (0, 0, 255),     # Red
            'animal': (255, 255, 0)  # Cyan
        }
        
        def process_results(results, model):
            nonlocal fire_detected
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    w, h = x2 - x1, y2 - y1
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    cls_name = model.names[cls].lower()
                    
                    # Determine color and label
                    if 'person' in cls_name:
                        color = colors['person']
                        label = 'Person'
                    elif 'fire' in cls_name:
                        color = colors['fire']
                        label = 'Fire'
                        fire_detected = True
                    elif 'animal' in cls_name:
                        color = colors['animal']
                        label = 'Animal'
                    else:
                        color = (255, 255, 255)
                        label = cls_name.capitalize()
                    
                    all_boxes.append([x1, y1, w, h])
                    all_confidences.append(conf)
                    label_str = f"{label} {conf:.2f}"
                    all_labels.append((label_str, color))
                    
                    detections.append({
                        'label': label,
                        'confidence': conf,
                        'bbox': [x1, y1, x2, y2]
                    })
        
        process_results(results1, self.model1)
        process_results(results2, self.model2)
        
        # Apply Non-Maximum Suppression (NMS)
        annotated_frame = frame.copy()
        if len(all_boxes) > 0:
            indices = cv2.dnn.NMSBoxes(
                all_boxes, all_confidences, 
                self.confidence_threshold, 0.45
            )
            
            if len(indices) > 0:
                indices = indices.flatten()
                for i in indices:
                    box = all_boxes[i]
                    x1, y1, w, h = box
                    x2, y2 = x1 + w, y1 + h
                    label_text, color = all_labels[i]
                    
                    # Draw detection box
                    cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        annotated_frame, label_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2
                    )
        
        # Send alert if fire detected (with cooldown)
        current_time = time.time()
        if fire_detected and (current_time - self.last_alert_time) > self.alert_cooldown:
            print(f"🔥 FIRE DETECTED! Confidence: {max([d['confidence'] for d in detections if d['label'].lower() == 'fire']):.2%}")
            alert_data = self._create_alert(frame, detections)
            self.alert_queue.put(alert_data)
            self.last_alert_time = current_time
        
        return annotated_frame, fire_detected
    
    def run_camera_detection(self, camera_index=0, display=False):
        """
        Run continuous fire detection from camera
        
        Args:
            camera_index: Camera device index (0 for default)
            display: Whether to display video feed (False for headless Raspberry Pi)
        """
        print(f"\n🎥 Starting camera detection...")
        print(f"   Camera: {camera_index}")
        print(f"   Display: {'Enabled' if display else 'Disabled (Headless)'}")
        print(f"   Press Ctrl+C to stop\n")
        
        cap = cv2.VideoCapture(camera_index)
        
        # Optimize for Raspberry Pi
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 15)
        
        if not cap.isOpened():
            print(f"❌ Failed to open camera {camera_index}")
            return
        
        frame_count = 0
        fps_start = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Failed to read frame")
                    break
                
                # Run detection
                annotated_frame, fire_detected = self.detect_and_alert(frame)
                
                # Calculate FPS
                frame_count += 1
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_start)
                    print(f"📊 FPS: {fps:.1f} | Frames: {frame_count} | Fire: {'🔥 YES' if fire_detected else '✓ NO'}")
                    fps_start = time.time()
                
                # Display if enabled
                if display:
                    # Add info overlay
                    cv2.putText(
                        annotated_frame, f"Drone Fire Detection - {datetime.now().strftime('%H:%M:%S')}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                    )
                    cv2.putText(
                        annotated_frame, f"GPS: {self.current_lat:.6f}, {self.current_lon:.6f}", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                    )
                    
                    cv2.imshow("Fire Detection - Drone", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
        except KeyboardInterrupt:
            print("\n⚠️ Detection stopped by user")
        finally:
            cap.release()
            if display:
                cv2.destroyAllWindows()
            print("✅ Camera released")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fire Detection System for Raspberry Pi Drone')
    parser.add_argument('--backend', type=str, default='http://192.168.1.100:8000',
                        help='Backend server URL (e.g., http://192.168.1.100:8000)')
    parser.add_argument('--camera', type=int, default=0,
                        help='Camera device index (default: 0)')
    parser.add_argument('--confidence', type=float, default=0.5,
                        help='Detection confidence threshold (default: 0.5)')
    parser.add_argument('--display', action='store_true',
                        help='Display video feed (use for testing, not for headless operation)')
    parser.add_argument('--cooldown', type=int, default=5,
                        help='Seconds between alerts (default: 5)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🔥 FOREST FIRE DETECTION SYSTEM - DRONE DEPLOYMENT")
    print("="*60)
    
    try:
        detector = FireDetectionDrone(
            backend_url=args.backend,
            confidence_threshold=args.confidence
        )
        detector.alert_cooldown = args.cooldown
        detector.run_camera_detection(
            camera_index=args.camera,
            display=args.display
        )
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
