
import random
import numpy as np

class AcousticFFT:
    """
    Level 3B: Acoustic Module (The Senses)
    
    Responsibility:
    - FFT-based detection in 50–200 Hz band (characteristic fire roar).
    - Wind noise filtering.
    - Output Audio_Conf [0,1].
    """
    
    def __init__(self):
        self.frequency_band = (50, 200) # Hz
        self.last_energy = 50.0 # State for smoothing
        
    def analyze_audio(self, audio_chunk=None, simulate_fire_intensity=None):
        """
        Analyze audio chunk for fire signature.
        If simulate_fire_intensity is provided (0.0-1.0), bias the simulation.
        """
        # Simulation Hook:
        # If we have a strong visual fire, audio 'hears' it too.
        if simulate_fire_intensity is not None and simulate_fire_intensity > 0.6:
             target_energy = simulate_fire_intensity * 100 # map 0.9 -> 90
             # Move towards target
             if self.last_energy < target_energy: self.last_energy += 5
             else: self.last_energy -= 2
        else:
             # Regular random walk
             change = random.uniform(-5, 5)
             self.last_energy = max(0, min(100, self.last_energy + change))
        # SIMULATION HOOK
        # Simulate spectral energy
        
        # 1. Simulate Energy in Fire Band (50-200Hz)
        fire_band_energy = self.last_energy
        
        # 2. Simulate Wind Noise (Low frequency rumble < 50Hz)
        wind_energy = random.uniform(0, 50)
        
        # Logic: Fire has high energy in 50-200Hz relative to wind
        ratio = 0
        if wind_energy > 0:
            ratio = fire_band_energy / wind_energy
        else:
            ratio = fire_band_energy
            
        # Normalize to confidence
        # Heuristic: Ratio > 2.0 is likely fire
        confidence = 0.0
        if ratio > 2.0:
            confidence = min(1.0, 0.5 + (ratio * 0.1))
        elif fire_band_energy > 80:
             confidence = min(1.0, fire_band_energy / 120.0)
            
        result = {
            "fire_band_energy": round(fire_band_energy, 2),
            "wind_energy": round(wind_energy, 2),
            "ratio": round(ratio, 2),
            "confidence": round(confidence, 2)
        }
        
        return result

acoustic_module = AcousticFFT()
