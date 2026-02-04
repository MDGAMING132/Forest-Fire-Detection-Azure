
import cv2
import time
import requests
import base64
import json
import datetime
import os
from ultralytics import YOLO

# Configuration
API_URL = "http://127.0.0.1:8000/api/vision-trigger"
MODEL_DIR = "G:/Forest-fire-detection/final_model"
MODEL_1_PATH = os.path.join(MODEL_DIR, "fire and person.pt")
MODEL_2_PATH = os.path.join(MODEL_DIR, "aerial_images.pt")

# IP-Based Geolocation
def get_real_coordinates():
    try:
        resp = requests.get('https://ipinfo.io/json', timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                print(f"[Geo] Automatically detected location: {loc}")
                return float(loc[0]), float(loc[1])
    except Exception as e:
        print(f"[Geo] Failed to get IP location: {e}")
    
    print("[Geo] Using default India coordinates.")
    return 20.5937, 78.9629 # Default Center of India

# Dynamic Coordinates
DRONE_LAT, DRONE_LON = get_real_coordinates()

class CognitiveMonitor:
    def __init__(self):
        print("[System] Initializing Cognitive Fire-Grid Monitor...")
        
        # Load Models
        try:
            print(f"[Loader] Loading Fire/Person Model: {MODEL_1_PATH}")
            self.model1 = YOLO(MODEL_1_PATH)
            print(f"[Loader] Loading Aerial Model: {MODEL_2_PATH}")
            self.model2 = YOLO(MODEL_2_PATH)
            print("[System] Models Loaded successfully.")
        except Exception as e:
            print(f"[Error] Failed to load models: {e}")
            exit(1)
            
        self.last_alert_time = 0
        self.last_lat = 0.0
        self.last_lon = 0.0
        self.alert_cooldown = 5 # seconds
        self.cap = cv2.VideoCapture(0) # 0 for Webcam
        
        if not self.cap.isOpened():
            print("[Error] Could not open webcam.")
            exit(1)

    def run(self):
        print("[System] Monitoring Feed... Press 'q' to quit.")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Run Inference
            results1 = self.model1(frame, verbose=False, conf=0.6)
            # results2 = self.model2(frame, verbose=False, conf=0.6) # Optional: fuse both
            
            fire_detected = False
            max_conf = 0.0
            
            # Check for Fire and Count Objects
            person_count = 0
            animal_count = 0
            ANIMAL_CLASSES = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23] # COCO IDs

            for r in results1:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    cls_name = self.model1.names[cls_id].lower()

                    if 'fire' in cls_name:
                        fire_detected = True
                        max_conf = max(max_conf, conf)
                        # Box drawing is handled by plot()
                    elif cls_id == 0: # Person
                        person_count += 1
                    elif cls_id in ANIMAL_CLASSES:
                        animal_count += 1

            if fire_detected:
                # ----------------
                # SMART RATE LIMIT
                # ----------------
                current_time = time.time()
                time_diff = current_time - self.last_alert_time
                loc_delta = abs(DRONE_LAT - self.last_lat) + abs(DRONE_LON - self.last_lon)
                
                # Check if we should alert (New Loc OR Time > 60s)
                if loc_delta > 0.001 or time_diff > 60:
                    self.last_alert_time = current_time
                    self.last_lat = DRONE_LAT
                    self.last_lon = DRONE_LON
                    
                    # Pass results1[0] because plot() is a method of a Result object, and we have a list of one result
                    self.trigger_alert(frame, max_conf, person_count, animal_count, results1[0])
                
            # Display Feed
            annotated_frame = results1[0].plot() 
            cv2.imshow("Cognitive Monitor (Live)", annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        self.cap.release()
        cv2.destroyAllWindows()

    def trigger_alert(self, frame, confidence, person_count, animal_count, result):
        print(f"\n[ALERT] Fire Detected! Confidence: {confidence:.2f}")
        print(f"       Risk Assessment: {person_count} Persons, {animal_count} Animals nearby.")
        
        # Draw Bounding Boxes
        annotated_frame = result.plot()
        
        # Encode Image
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        payload = {
            "image": img_b64,
            "confidence": float(confidence),
            "lat": DRONE_LAT,
            "lon": DRONE_LON,
            "timestamp": datetime.datetime.now().isoformat(),
            "person_count": person_count,
            "animal_count": animal_count
        }
        
        try:
            resp = requests.post(API_URL, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print("="*60)
                print(f"✅ SYSTEM RESPONSE RECEIVED")
                print(f"📍 Coordinates: {DRONE_LAT}, {DRONE_LON}")
                print(f"📊 Confidence: {confidence*100:.1f}%")
                print(f"🛡️ Levels Passed: {', '.join(data.get('levels_passed', []))}")
                print(f"🧠 Reasoning: {data.get('reasoning', 'N/A')}")
                print(f"📂 Evidence Saved: {data.get('saved_image')}")
                print("="*60)
            else:
                print(f"[Error] Backend rejected alert: {resp.text}")
        except Exception as e:
            print(f"[Error] Failed to send alert: {e}")

if __name__ == "__main__":
    monitor = CognitiveMonitor()
    monitor.run()
