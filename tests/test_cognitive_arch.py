
import sys
import os
import unittest
import json

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from sat_filter import sat_filter
from handshake import handshake
from fusion_voting import fusion_engine
from fire_spread import fire_spread

class TestCognitiveArchitecture(unittest.TestCase):
    
    def test_level1_temporal_persistence(self):
        """Level 1: Verify filtering logic"""
        # Case A: Hotspot significantly hotter than baseline
        hotspot = {"latitude": 10.0, "longitude": 20.0, "brightness": 350.0}
        # Mock baseline to be 300
        sat_filter.get_historic_baseline = lambda lat, lon: 300.0
        
        result = sat_filter.analyze_temporal_persistence(hotspot)
        self.assertTrue(result['verified'])
        self.assertGreater(result['confidence'], 0.5)
        
        # Case B: Hotspot close to baseline (False Positive)
        hotspot_cold = {"latitude": 10.0, "longitude": 20.0, "brightness": 310.0}
        result_cold = sat_filter.analyze_temporal_persistence(hotspot_cold)
        self.assertFalse(result_cold['verified'])

    def test_level2_adaptive_handshake(self):
        """Level 2: Verify threshold adaptation"""
        # High confidence -> Low thresholds
        config_high = handshake.calculate_drone_config(sat_confidence=0.9)
        # Low confidence -> High thresholds
        config_low = handshake.calculate_drone_config(sat_confidence=0.1)
        
        # Expect lower threshold for high confidence
        self.assertLess(config_high['adapted_thresholds']['vision_min_conf'], 
                        config_low['adapted_thresholds']['vision_min_conf'])
                        
    def test_level3_failure_mode(self):
        """Level 3: FAILURE MODE TEST (Vision Fails)"""
        # Setup: Vision is blind (0.0), but Audio/Chem are high
        vision_res = {"normalized_conf": 0.0}
        audio_res = {"confidence": 0.95}
        chem_res = {"confidence": 0.95}
        
        # Weights: Vision(0.4) + Audio(0.3) + Chem(0.3)
        # Score = (0*0.4) + (0.95*0.3) + (0.95*0.3) = 0.57
        # 0.57 > 0.5 -> Should be SMOKE WITHOUT FLAME
        
        trace = fusion_engine.fuse_data(vision_res, audio_res, chem_res)
        
        print(f"\n[Failure Test] Score: {trace['final_score']} | Decision: {trace['decision']}")
        
        self.assertTrue(trace['final_score'] > 0.5)
        self.assertIn("SMOKE", trace['decision'])
        self.assertTrue(trace['triggered_sniffer'])

    def test_level4_fire_spread(self):
        """Level 4: Verify spread cone calculation"""
        cone = fire_spread.calculate_spread_cone(10.0, 10.0, wind_speed_kmh=20.0, wind_bearing=0)
        
        # Expect head to be north of origin (bearing 0)
        self.assertGreater(cone['head']['lat'], cone['origin']['lat'])
        self.assertAlmostEqual(cone['head']['lon'], cone['origin']['lon'], delta=0.01)

if __name__ == '__main__':
    unittest.main()
