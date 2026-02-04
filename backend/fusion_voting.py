
class FusionVoting:
    """
    Level 3D: Cross-Modal Fusion Voting (The Senses)
    
    Responsibility:
    - Aggregate Vision, Audio, Chemical scores.
    - Apply Weighted Voting.
    - Provide Explainability (DecisionTrace).
    """
    
    def __init__(self):
        self.weights = {
            "vision": 0.4,
            "audio": 0.3,
            "chemical": 0.3
        }
        
    def fuse_data(self, vision_result, audio_result, chem_result):
        """
        Calculate Final Score and Decision.
        
        Formula: Final_Score = (0.4 * Vision) + (0.3 * Audio) + (0.3 * Chem)
        """
        v_conf = vision_result.get("normalized_conf", 0.0)
        a_conf = audio_result.get("confidence", 0.0)
        c_conf = chem_result.get("confidence", 0.0)
        
        # Weighted Sum
        final_score = (v_conf * self.weights["vision"]) + \
                      (a_conf * self.weights["audio"]) + \
                      (c_conf * self.weights["chemical"])
                      
        final_score = round(final_score, 2)
        
        # Decision Rules
        decision = "NORMAL"
        triggered_sniffer = False
        
        # Override: If Vision is VERY clear, force at least Warning
        # This prevents "Safe" state when we clearly see fire but other sensors are lagging
        effective_score = final_score
        if v_conf > 0.8 and final_score < 0.6:
            effective_score = 0.65
        
        if effective_score > 0.8:
            decision = "CRITICAL FIRE"
            triggered_sniffer = True # Urgent response
        elif 0.5 < effective_score <= 0.8:
            decision = "SMOKE WITHOUT FLAME"
            triggered_sniffer = True # Sniffer needed to locate source
        else:
            decision = "SAFE"
            triggered_sniffer = False
            
        # Explainability: Levels Passed & Reasoning
        levels_passed = ["Level 1 (Satellite)", "Level 2 (Atmospheric)"]
        if final_score > 0.5:
             levels_passed.append("Level 3 (Multi-Modal)")
        
        reasoning = self._generate_reasoning(v_conf, a_conf, c_conf, final_score)

        # Explainability Artifact
        decision_trace = {
            "vision_conf": v_conf,
            "audio_conf": a_conf,
            "chem_conf": c_conf,
            "weights": self.weights,
            "final_score": final_score,
            "decision": decision,
            "min_levels_passed": levels_passed,
            "reasoning": reasoning,
            "triggered_sniffer": triggered_sniffer,
            "framework_version": "v1.0"
        }
        
        print(f"[Level 3] Fusion Decision: {decision} (Score: {final_score}) | Why: {reasoning}")
        return decision_trace

    def _generate_reasoning(self, v, a, c, score):
        """Generate human-readable explanation."""
        reasons = []
        if v > 0.6: reasons.append(f"Vision Confirmed ({int(v*100)}%)")
        if a > 0.6: reasons.append("Acoustic Anomaly")
        if c > 0.6: reasons.append("Chemical Signature")
        
        if score > 0.9:
            return "CRITICAL: " + " + ".join(reasons)
        elif score > 0.5:
            return "WARNING: " + " + ".join(reasons)
        else:
            return "Stable: No significant aggregation."
        
        print(f"[Level 3] Fusion Decision: {decision} (Score: {final_score})")
        return decision_trace

fusion_engine = FusionVoting()
