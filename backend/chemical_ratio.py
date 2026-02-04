
import random

class ChemicalRatio:
    """
    Level 3C: Chemical Ratio Module (The Senses)
    
    Responsibility:
    - Analyze gas ratios to distinguish fire from false alarms.
    - CO/CO2 > 0.1 -> Smoldering biomass
    - NOx/CO > 0.5 -> Vehicle exhaust (false alarm)
    - Output Chem_Conf [0,1].
    """
    
    def analyze_gas(self, sensor_readings=None, simulate_fire_intensity=None):
        """
        Analyze gas sensor readings.
        If simulate_fire_intensity is provided, bias the simulation.
        """
        # SIMULATION HOOK
        co = random.uniform(0, 5)
        co2 = random.uniform(400, 450)
        nox = random.uniform(0, 10)
        
        # Bias towards fire if visual detection is strong
        if simulate_fire_intensity is not None and simulate_fire_intensity > 0.6:
            # Force "Smoldering Fire" signature (High CO, High CO2)
            co = random.uniform(50, 150)
            co2 = random.uniform(600, 900)
            nox = random.uniform(5, 20)
        elif random.random() > 0.8: 
            # Occasional random event (Vehicle or Fire)
            if random.random() > 0.5:
                # Fire
                co = random.uniform(20, 150)
                co2 = random.uniform(500, 800)
            else:
                # Vehicle (False Alarm)
                co = random.uniform(10, 50)
                nox = random.uniform(50, 100)

        # Avoid div by zero
        co_co2_ratio = co / co2 if co2 > 0 else 0
        nox_co_ratio = nox / co if co > 0 else 0
        
        # Confidence calculation
        confidence = 0.0
        
        # Fire Signatures
        if co_co2_ratio > 0.1:
            confidence += 0.6 # Strong indicator
        if co > 50:
            confidence += 0.3
            
        # False Positive Filter (Vehicle)
        if nox_co_ratio > 0.5:
            confidence *= 0.2 # Penalty for likely vehicle
            
        return {
            "co_ppm": round(co, 2),
            "co2_ppm": round(co2, 2),
            "nox_ppm": round(nox, 2),
            "co_co2_ratio": round(co_co2_ratio, 4),
            "nox_co_ratio": round(nox_co_ratio, 4),
            "confidence": min(1.0, round(confidence, 2))
        }

chemical_module = ChemicalRatio()
