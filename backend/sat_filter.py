
import random
from datetime import datetime, timedelta

class SatelliteFilter:
    """
    Level 1: Intelligent Macro-Detection (The Eye)
    
    Responsibility:
    - Ingest satellite hotspot data.
    - Perform Temporal Persistence Analysis.
    - specialized filter to reject false positives based on historic thermal baselines.
    """
    
    def __init__(self):
        # Simulation hook: In a real system, this would be a database connection
        self.history_db = {} 
        
    def get_historic_baseline(self, lat, lon):
        """
        Get the mean temperature for this pixel over the last 30 days (same time window).
        
        Simulation Hook:
        If no real history exists, simulate a baseline based on location/season.
        """
        # SIMULATION: Generate a realistic baseline temperature (Kelvin)
        # Normal ground temp ~300K (27C). 
        # Fire hotspots are usually > 320K.
        # We simulate a baseline of non-fire ground temperature.
        return 300.0 + random.uniform(-5, 5)

    def analyze_temporal_persistence(self, hotspot):
        """
        Analyze if a hotspot is statistically significant compared to history.
        
        Logic:
        If Current_Temp > Historic_Baseline + 20K:
            Mark as Potential Fire
        Else:
            Reject as false positive (e.g. urban heat island, warm rocks)
        """
        lat = hotspot.get('latitude')
        lon = hotspot.get('longitude')
        current_temp = hotspot.get('brightness', 0) # VIIRS Brightness temperature in Kelvin
        
        if not lat or not lon or not current_temp:
            return {
                "verified": False,
                "reason": "Missing data",
                "confidence": 0.0
            }

        baseline = self.get_historic_baseline(lat, lon)
        threshold = baseline + 20.0 # 20K rise threshold
        
        is_potential_fire = current_temp > threshold
        
        # Calculate confidence based on how much it exceeds the threshold
        # Cap at 1.0
        confidence = 0.0
        if is_potential_fire:
            excess = current_temp - threshold
            confidence = min(1.0, 0.5 + (excess / 50.0)) # 0.5 base for passing threshold, + up to 0.5 more
        
        result = {
            "verified": is_potential_fire,
            "latitude": lat,
            "longitude": lon,
            "current_temp": current_temp,
            "historic_baseline": baseline,
            "delta": current_temp - baseline,
            "confidence": round(confidence, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[Level 1] Satellite Trigger Analysis: {result}")
        return result

# Singleton
sat_filter = SatelliteFilter()
