class LCAEngine:
    def __init__(self):
        # Specific weights and impact factors per material
        self.metal_coeffs = {
            "Gold": {"e_weight": 0.95, "w_weight": 0.75, "co2_factor": 15.0, "base_threshold": 25},
            "Lithium": {"e_weight": 0.40, "w_weight": 0.90, "co2_factor": 8.0, "base_threshold": 30},
            "Uranium": {"e_weight": 0.85, "w_weight": 0.65, "co2_factor": 12.0, "base_threshold": 20},
            "Coal": {"e_weight": 0.35, "w_weight": 0.55, "co2_factor": 2.8, "base_threshold": 35},
            "Iron": {"e_weight": 0.60, "w_weight": 0.30, "co2_factor": 1.9, "base_threshold": 45},
            "Steel": {"e_weight": 0.75, "w_weight": 0.20, "co2_factor": 2.6, "base_threshold": 50},
            "Copper": {"e_weight": 0.55, "w_weight": 0.45, "co2_factor": 3.2, "base_threshold": 40},
            "General": {"e_weight": 0.50, "w_weight": 0.50, "co2_factor": 2.5, "base_threshold": 40}
        }

    def analyze(self, site_type, purity, energy, water, production):
        prod_val = max(float(production), 1.0)
        conf = self.metal_coeffs.get(site_type, self.metal_coeffs["General"])
        
        energy_intensity = float(energy) / prod_val
        water_intensity = float(water) / prod_val
        
        # Base Impact Score
        impact_score = (energy_intensity * conf['e_weight']) + (water_intensity * conf['w_weight'])
        if float(purity) < 40:
            impact_score *= 1.35 

        # Classification
        if impact_score > conf['base_threshold'] * 2.0:
            zone, color, level = "CRITICAL: RED ZONE", "#ff4d4d", "Critical"
        elif impact_score > conf['base_threshold']:
            zone, color, level = "WARNING: ORANGE ZONE", "#ffa500", "Warning"
        else:
            zone, color, level = "STABLE: GREEN ZONE", "#2ecc71", "Sustainable"

        # Calculate a dynamic radius based on the impact score (e.g., Score * 800 meters)
        calculated_radius = round(impact_score * 800, 2)

        return {
            "score": round(impact_score, 2),
            "zone": zone,
            "color": color,
            "level": level,
            "impact_radius_meters": calculated_radius, # New Field
            "impact_radius_km": round(calculated_radius / 1000, 2), # New Field for UI
            "co2_footprint_kg": round(float(energy) * conf['co2_factor'], 2),
            "environmental_impacts": self.generate_impact_report(site_type, impact_score, water_intensity, prod_val),
            "solutions": self.generate_solutions(site_type, energy_intensity, water_intensity, level)
        }

    def generate_impact_report(self, metal, score, w_int, prod):
        # Quantitative Impact Assessment Logic
        return [
            f"Land Degradation: Approximately {round(score * 0.15, 2)} hectares affected in the immediate vicinity.",
            f"Aquifer Stress: {round(w_int * 0.08, 2)}% estimated drop in local groundwater table per annum.",
            f"Atmospheric Load: {round(prod * 0.015, 2)} kg of particulate matter (PM10/PM2.5) emitted daily.",
            f"Biodiversity Score: Local ecosystem stability reduced by {round(score/5, 1)}% due to operations."
        ]

    def generate_solutions(self, site_type, e_int, w_int, level):
        if level == "Sustainable":
            return ["Site operates within ESG norms.", "Continue quarterly biodiversity audits."]
        
        sols = [f"Deploy {site_type}-specific tailing treatment."]
        if w_int > 50: sols.append("Implement Zero Liquid Discharge (ZLD) closed-loop water recovery.")
        if e_int > 30: sols.append("Install AI-monitored Variable Frequency Drives (VFD) for energy optimization.")
        return sols