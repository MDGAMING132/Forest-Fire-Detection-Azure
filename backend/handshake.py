
class AdaptiveHandshake:
    """
    Level 2: Adaptive Handshake (The Nervous System)
    
    Responsibility:
    - Receive confidence score from Level 1 (Satellite).
    - Dynamically tune drone sensor thresholds before dispatch.
    - Logic: Higher satellite confidence -> Lower drone threshold (more sensitive).
             Lower satellite confidence -> Higher drone threshold (needs stronger verification).
    """
    
    def __init__(self):
        self.base_thresholds = {
            "vision_conf": 0.6,
            "thermal_temp": 50.0, # Celsius
            "smoke_density": 0.4
        }
        
    def calculate_drone_config(self, sat_confidence):
        """
        Calculate mission configuration and sensor thresholds.
        
        Formula: Drone_Threshold = Base_Threshold * (1 - (Confidence_Score * 0.5))
        (We don't drop to 0, but we reduce threshold by up to 50% for high confidence)
        """
        if sat_confidence is None:
            sat_confidence = 0.0
            
        # Tuning factor: How much does sat confidence affect drone sensitivity?
        # 0.5 means meaningful but not reckless reduction.
        tuning_factor = sat_confidence * 0.5
        multiplier = 1.0 - tuning_factor
        
        adapted_thresholds = {
            "vision_min_conf": round(self.base_thresholds['vision_conf'] * multiplier, 2),
            "thermal_min_temp": round(self.base_thresholds['thermal_temp'] * multiplier, 1),
            "smoke_min_density": round(self.base_thresholds['smoke_density'] * multiplier, 2)
        }
        
        config = {
            "mission_id": f"mission_{int(sat_confidence*100)}",
            "sensitivity_level": "HIGH" if sat_confidence > 0.8 else "MEDIUM" if sat_confidence > 0.5 else "LOW",
            "adapted_thresholds": adapted_thresholds,
            "explanation": f"Satellite confidence {sat_confidence:.2f} adapted thresholds by -{int(tuning_factor*100)}%"
        }
        
        print(f"[Level 2] Adaptive Handshake Config: {config}")
        return config

handshake = AdaptiveHandshake()
