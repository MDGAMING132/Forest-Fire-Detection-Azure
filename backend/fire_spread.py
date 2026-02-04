
import math

class FireSpreadModel:
    """
    Level 4: Fire Spread & Routing (The Brain)
    
    Responsibility:
    - Simplified Rothermel spread model.
    - Calculate 1-hour spread cone based on wind vector.
    """
    
    def calculate_spread_cone(self, origin_lat, origin_lon, wind_speed_kmh, wind_bearing):
        """
        Calculate the predicted fire front after 1 hour.
        
        Args:
            wind_bearing: 0-360 degrees (0 = North)
        """
        # 1. Estimate Rate of Spread (ROS) in km/h
        # Heuristic: ROS approx 10% of wind speed for moderate fuel
        ros = max(0.1, wind_speed_kmh * 0.1) 
        
        # 2. Calculate major axis length (1 hour spread)
        distance_km = ros * 1.0 # 1 hour
        
        # 3. Predict new point
        # Convert to lat/lon delta (approx)
        # 1 deg lat ~ 111 km
        delta_lat = (distance_km / 111.0) * math.cos(math.radians(wind_bearing))
        delta_lon = (distance_km / 111.0) * math.sin(math.radians(wind_bearing))
        
        spread_lat = origin_lat + delta_lat
        spread_lon = origin_lon + delta_lon
        
        # 4. Generate Cone Polygon (Simplified Triangle/Sector)
        # Width of cone impacted by wind variance (random noise)
        flank_angle = 30 # degrees spread
        
        cone = {
            "origin": {"lat": origin_lat, "lon": origin_lon},
            "head": {"lat": spread_lat, "lon": spread_lon},
            "ros_kmh": ros,
            "area_risk_km2": 0.5 * distance_km * (distance_km * math.tan(math.radians(flank_angle))),
            "message": f"Predicted spread {distance_km:.2f}km @ {wind_bearing} deg in 1 hr"
        }
        
        print(f"[Level 4] Fire Spread: {cone['message']}")
        return cone

fire_spread = FireSpreadModel()
