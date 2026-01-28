"""
Forest Fire Detection System - Laptop Testing Version
Detects fire using YOLO models and sends alerts to Azure backend
Works with regular webcam on Windows/Mac/Linux
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

class FireDetectionLaptop:
    def __init__(self, backend_url="https://forest-fire-detection-dddzhfg0fkd7h6c3.centralindia-01.azurewebsites.net", confidence_threshold=0.5):
        """
        Initialize Fire Detection System for Laptop Testing
        
        Args:
            backend_url: URL of your Azure backend server
            confidence_threshold: Minimum confidence for fire detection (0-1)
        """
        self.backend_url = backend_url
        self.confidence_threshold = confidence_threshold
        self.last_alert_time = 0
        self.alert_cooldown = 5  # Send alert every 5 seconds max
        
        # Default test coordinates (you can change these)
        self.test_lat = 23.456789
        self.test_lon = 78.123456
        self.test_altitude = 120.0
        
        # Load models
        base_dir = os.path.dirname(os.path.abspath(__file__))
        models_dir = os.path.join(os.path.dirname(base_dir), "Forest-fire-detection", "final_model")
        
        self.m1_path = os.path.join(models_dir, "fire and person.pt")
        self.m2_path = os.path.join(models_dir, "aerial_images.pt")
        
        # Check if models exist
        if not os.path.exists(self.m1_path):
            raise FileNotFoundError(f"Model not found: {self.m1_path}")
        if not os.path.exists(self.m2_path):
            raise FileNotFoundError(f"Model not found: {self.m2_path}")
        
        print("🔥 Loading YOLO models...")
        self.model1 = YOLO(self.m1_path)
        self.model2 = YOLO(self.m2_path)
        print("✅ Models loaded successfully!")
        
        # Alert sending thread
        self.alert_active = False
        
    def _frame_to_base64(self, frame):
        """Convert OpenCV frame to base64 string"""
        # Resize if too large (max 800px width)
        height, width = frame.shape[:2]
        if width > 800:
            scale = 800 / width
            new_width = 800
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Encode to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_str = base64.b64encode(buffer).decode('utf-8')
        return img_str
    
    def _send_alert(self, alert_data):
        """Send alert to backend server"""
        try:
            endpoint = f"{self.backend_url}/api/fire-alert"
            print(f"\n📡 Sending alert to: {endpoint}")
            print(f"📍 Coordinates being sent: Lat={alert_data['location']['latitude']}, Lon={alert_data['location']['longitude']}")
            
            response = requests.post(
                endpoint,
                json=alert_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Alert sent successfully! Response: {response.json()}")
                return True
            else:
                print(f"❌ Alert failed: Status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error sending alert: {e}")
            return False
        except Exception as e:
            print(f"❌ Error sending alert: {e}")
            return False
    
    def _create_alert(self, frame, detections):
        """Create alert data structure"""
        timestamp = datetime.now().isoformat()
        
        # Find highest confidence fire detection
        fire_detections = [d for d in detections if d['label'].lower().startswith('fire')]
        max_confidence = max([d['confidence'] for d in fire_detections])
        
        alert_data = {
            "type": "drone",
            "timestamp": timestamp,
            "confidence": round(max_confidence, 4),
            "location": {
                "type": "drone",
                "latitude": self.test_lat,
                "longitude": self.test_lon,
                "altitude": self.test_altitude,
                "coordinates": f"{self.test_lat:.6f}, {self.test_lon:.6f}",
                "city": "Laptop Test Location",
                "country": "Test Area"
            },
            "image": self._frame_to_base64(frame),
            "bbox": [d['bbox'] for d in fire_detections],
            "detectionCount": len(fire_detections)
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
        annotated_frame = frame.copy()
        
        # Process Model 1 results
        for result in results1:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = result.names[cls]
                
                all_boxes.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': conf,
                    'label': label,
                    'model': 'fire_person'
                })
                
                # Draw on frame
                color = (0, 0, 255) if 'fire' in label.lower() else (0, 255, 0)
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(annotated_frame, f"{label} {conf:.2f}", (int(x1), int(y1)-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Process Model 2 results
        for result in results2:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = result.names[cls]
                
                all_boxes.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': conf,
                    'label': label,
                    'model': 'aerial'
                })
                
                # Draw on frame
                color = (0, 165, 255)  # Orange for aerial model
                cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(annotated_frame, f"{label} {conf:.2f}", (int(x1), int(y1)-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Check for fire detections
        fire_detected = any('fire' in box['label'].lower() for box in all_boxes)
        
        # Send alert if fire detected and cooldown passed
        if fire_detected:
            current_time = time.time()
            if current_time - self.last_alert_time > self.alert_cooldown:
                print(f"\n🔥 FIRE DETECTED! Confidence: {max([b['confidence'] for b in all_boxes if 'fire' in b['label'].lower()]):.2%}")
                alert_data = self._create_alert(frame, all_boxes)
                self._send_alert(alert_data)
                self.last_alert_time = current_time
        
        return annotated_frame, fire_detected

    def run_webcam(self, camera_index=0):
        """
        Run fire detection on webcam feed
        
        Args:
            camera_index: Camera device index (0 for default webcam)
        """
        print(f"\n🎥 Starting webcam capture (device {camera_index})...")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print("❌ Error: Could not open webcam")
            return
        
        # Set resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        print("\n✅ Webcam started!")
        print("📋 Instructions:")
        print("   - Press 'q' to quit")
        print("   - Press 's' to send manual test alert")
        print("   - Show fire images to the camera to test detection")
        print(f"\n🌐 Backend: {self.backend_url}")
        print(f"📍 Test Location: {self.test_lat}, {self.test_lon}\n")
        
        frame_count = 0
        fps_start_time = time.time()
        fps = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error reading frame")
                break
            
            # Run detection
            annotated_frame, fire_detected = self.detect_and_alert(frame)
            
            # Calculate FPS
            frame_count += 1
            if frame_count % 30 == 0:
                fps = 30 / (time.time() - fps_start_time)
                fps_start_time = time.time()
            
            # Add status text
            status_color = (0, 0, 255) if fire_detected else (0, 255, 0)
            status_text = "🔥 FIRE DETECTED!" if fire_detected else "✓ Monitoring..."
            
            # Add black background rectangle for text visibility
            text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            cv2.rectangle(annotated_frame, (5, 5), (text_size[0] + 15, 45), (0, 0, 0), -1)
            cv2.putText(annotated_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            
            # FPS with background
            fps_text = f"FPS: {fps:.1f}"
            fps_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            cv2.rectangle(annotated_frame, (5, 50), (fps_size[0] + 15, 75), (0, 0, 0), -1)
            cv2.putText(annotated_frame, fps_text, (10, 65), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show frame
            cv2.imshow('Fire Detection - Press Q to quit, S to send test alert', annotated_frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\n👋 Stopping...")
                break
            elif key == ord('s'):
                print("\n📤 Sending manual test alert...")
                test_data = {
                    "type": "drone",
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 0.99,
                    "location": {
                        "type": "drone",
                        "latitude": self.test_lat,
                        "longitude": self.test_lon,
                        "altitude": self.test_altitude,
                        "coordinates": f"{self.test_lat:.6f}, {self.test_lon:.6f}",
                        "city": "Manual Test Alert",
                        "country": "Test Area"
                    },
                    "image": self._frame_to_base64(frame),
                    "bbox": [],
                    "detectionCount": 1
                }
                self._send_alert(test_data)
        
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Cleanup complete!")


def main():
    """Main function"""
    print("="*60)
    print("🔥 FOREST FIRE DETECTION SYSTEM - LAPTOP VERSION")
    print("="*60)
    
    try:
        # Initialize detector
        detector = FireDetectionLaptop(
            backend_url="https://forest-fire-detection-dddzhfg0fkd7h6c3.centralindia-01.azurewebsites.net",
            confidence_threshold=0.4  # Lower threshold for testing
        )
        
        # Run webcam detection
        detector.run_webcam(camera_index=0)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure your YOLO models are in the correct location:")
        print("   G:\\Forest-fire-detection\\final_model\\fire and person.pt")
        print("   G:\\Forest-fire-detection\\final_model\\aerial_images.pt")
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
