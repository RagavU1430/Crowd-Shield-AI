import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from app.config import (
    WEIGHT_DENSITY, WEIGHT_CAPACITY, WEIGHT_TURBULENCE, WEIGHT_BOTTLENECK,
    RISK_THRESHOLDS
)
from app.models.schemas import RiskLevel

class ContextualRiskEngine:
    """
    Computes normalized Contextual Crowd-Crush Risk Score (0-100).
    Combines Density Factor, Capacity Utilization, Turbulence / Opposing flow, and Bottleneck Pressure.
    """
    def __init__(self):
        pass

    def evaluate_zone_risk(self, zone_metrics: Dict[str, Any]) -> Tuple[int, RiskLevel, List[str]]:
        """
        Calculates 0-100 risk score and contributing factors for a single zone.
        """
        density = zone_metrics.get("density_sqm", 0.0)
        occ_pct = zone_metrics.get("occupancy_pct", 0.0)
        turbulence = zone_metrics.get("turbulence", 0.1)
        bottleneck = zone_metrics.get("bottleneck_pressure", 0.0)

        # Factor normalizations [0 - 1.0]
        # Critical density benchmark = 5.0 pax/m²
        f_density = min(1.0, density / 5.0)
        f_capacity = min(1.0, occ_pct / 100.0)
        f_turbulence = min(1.0, turbulence)
        f_bottleneck = min(1.0, bottleneck)

        raw_score = (
            WEIGHT_DENSITY * f_density +
            WEIGHT_CAPACITY * f_capacity +
            WEIGHT_TURBULENCE * f_turbulence +
            WEIGHT_BOTTLENECK * f_bottleneck
        ) * 100.0

        risk_score = int(np.clip(round(raw_score), 0, 100))

        # Classify Level
        if risk_score <= 30:
            level = RiskLevel.SAFE
        elif risk_score <= 55:
            level = RiskLevel.WATCH
        elif risk_score <= 75:
            level = RiskLevel.HIGH
        else:
            level = RiskLevel.CRITICAL

        # Identify primary contributing factors
        factors = []
        if f_density > 0.6:
            factors.append("High Crowd Density (>3.0 pax/m²)")
        if f_capacity > 0.75:
            factors.append("Elevated Capacity Utilization (>75%)")
        if f_turbulence > 0.5:
            factors.append("Flow Instability / Opposing Directional Conflict")
        if f_bottleneck > 0.6:
            factors.append("Bottleneck Chokepoint Ingress Pressure")

        if not factors:
            factors.append("Normal Fluid Movement")

        return risk_score, level, factors

    def evaluate_global_risk(
        self,
        zone_metrics_list: List[Dict[str, Any]],
        overall_flow: Dict[str, Any]
    ) -> Tuple[int, RiskLevel, Optional[str], List[str]]:
        """
        Computes overall venue global risk score and isolates critical zone.
        """
        if not zone_metrics_list:
            # Fallback video-only risk estimation
            spd = overall_flow.get("mean_speed", 1.0)
            turb = overall_flow.get("turbulence_index", 0.1)
            score = int(np.clip(30 + turb * 40 + (1.0 / (spd + 0.1)) * 10, 0, 100))
            level = RiskLevel.WATCH if score > 30 else RiskLevel.SAFE
            return score, level, None, ["Video-Only Grid Analysis"]

        highest_score = 0
        critical_zone = None
        top_factors = []

        for zm in zone_metrics_list:
            score, level, factors = self.evaluate_zone_risk(zm)
            zm["risk_score"] = score
            zm["risk_level"] = level
            if score > highest_score:
                highest_score = score
                critical_zone = zm["zone_id"]
                top_factors = factors

        if highest_score <= 30:
            global_level = RiskLevel.SAFE
        elif highest_score <= 55:
            global_level = RiskLevel.WATCH
        elif highest_score <= 75:
            global_level = RiskLevel.HIGH
        else:
            global_level = RiskLevel.CRITICAL

        return highest_score, global_level, critical_zone, top_factors
