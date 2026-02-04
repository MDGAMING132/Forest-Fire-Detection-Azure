
import random
import math

class SnifferNavigation:
    """
    Level 4: Autonomous Localization (The Brain)
    
    Responsibility:
    - Execute Sniffer Mode (Bio-Inspired Gradient Descent).
    - Zig-zag movement to follow max(dConcentration/dt).
    - Termination condition: Gradient stabilizes below epsilon or visual confirmation.
    """
    
    def __init__(self):
        self.current_lat = 0
        self.current_lon = 0
        self.path_history = []
        
    def generate_sniffer_path(self, start_lat, start_lon, steps=10):
        """
        Simulate a zig-zag path towards a source.
        
        Simulation Hook:
        Generate a path that spirals/zig-zags towards a target point.
        """
        path = []
        lat, lon = start_lat, start_lon
        
        # Simulate localizing a source approx 0.005 degrees away (~500m)
        target_lat = start_lat + 0.005
        target_lon = start_lon + 0.003
        
        epsilon = 0.0001
        vision_conf = 0.0
        
        for i in range(steps):
             # 1. Zig-zag logic: Add noise perpendicular to direction
             progress = i / steps
             
             # Lerp towards target
             new_lat = lat + (target_lat - lat) * 0.2
             new_lon = lon + (target_lon - lon) * 0.2
             
             # Add Zig-Zag (Sine wave modulation)
             offset = math.sin(i) * 0.001 * (1.0 - progress) # Amplitude decreases as we get closer
             new_lon += offset
             
             # 2. Check Exit Conditions
             dist_to_target = math.sqrt((target_lat - new_lat)**2 + (target_lon - new_lon)**2)
             
             # Condition A: Gradient stabilizes (proximity)
             if dist_to_target < epsilon:
                 print("[Level 4] Sniffer Mode Terminated: Source Localized (Gradient Stabilized).")
                 break
                 
             # Condition B: Visual Confirmation > 0.7
             # Simulate vision getting clearer as we get closer
             vision_conf = 0.1 + (progress * 0.8) 
             if vision_conf > 0.7:
                 print(f"[Level 4] Sniffer Mode Terminated: Visual Confirmation ({vision_conf:.2f}).")
                 path.append({"lat": new_lat, "lon": new_lon, "step": i, "status": "CONFIRMED"})
                 break
            
             path.append({"lat": new_lat, "lon": new_lon, "step": i, "status": "SEARCHING"})
             lat, lon = new_lat, new_lon
             
        self.path_history = path
        return path

sniffer_nav = SnifferNavigation()
