
import random
import datetime

class VisionDetector:
    """
    Level 3A: Vision Module (The Senses)
    
    Responsibility:
    - Detect visual anomalies (Fire/Smoke).
    - Can run in Simulation Mode OR Real Mode (if updated externally).
    """

    def __init__(self):
        # Simulation parameters
        self.simulated_conf = 0.85
        
        # Real detection state
        self.last_real_detection = {
            "confidence": None,
            "image_path": None,
            "timestamp": None
        }

    def detect_fire(self, frame=None):
        """
        Level 3A: Vision Analysis.
        If real detection data is available (within last 10s), use it.
        Otherwise, fall back to simulation.
        """
        # Check for recent real detection (valid for 10 seconds)
        if self.last_real_detection["confidence"] is not None:
             time_diff = datetime.datetime.now() - self.last_real_detection["timestamp"]
             if time_diff.total_seconds() < 10:
                 return {
                     "normalized_conf": self.last_real_detection["confidence"],
                     "bbox": [100, 100, 200, 200], # Placeholder or pass real bbox
                     "source": "REAL_YOLO_FEED",
                     "image_path": self.last_real_detection["image_path"],
                     "timestamp": self.last_real_detection["timestamp"].isoformat()
                 }
             else:
                 # Reset if too old
                 self.last_real_detection["confidence"] = None

        # Fallback to Simulation
        # Simulate high confidence if triggered for test, else random low/med
        # For this demo, we'll randomize a bit but kept high for easy verification
        conf = random.uniform(0.7, 0.95)
        
        return {
            "normalized_conf": conf,
            "bbox": [10, 20, 100, 150],
            "source": "SIMULATION"
        }

    def update_detection(self, confidence, image_path, lat=None, lon=None, p_count=0, a_count=0):
        """Override simulation with real data from live_monitor.py"""
        
        # Exponential Moving Average (EMA) for stability
        # New value affects 30%, old value kept 70%
        current_conf = self.last_real_detection.get("confidence") or 0.0
        if current_conf is None: current_conf = 0.0
        smoothed_conf = (0.7 * current_conf) + (0.3 * confidence)
        
        # Immediate jump up for safety, slow decay down
        if confidence > current_conf:
             smoothed_conf = confidence # React fast to fire
        
        self.last_real_detection = {
            "confidence": smoothed_conf,
            "image_path": image_path,
            "lat": lat,
            "lon": lon,
            "persons": p_count,
            "animals": a_count,
            "timestamp": datetime.datetime.now()
        }
        print(f"[Vision] Updated with Real Detection: {confidence} -> {smoothed_conf:.2f} (Image: {image_path}) | P:{p_count} A:{a_count}")

    def get_last_detection(self):
        return self.last_real_detection

vision_model = VisionDetector()
