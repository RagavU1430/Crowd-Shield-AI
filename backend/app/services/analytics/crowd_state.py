import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import ZoneMetrics, RiskLevel
from app.services.simulation.venue_model import VenueModel

class CrowdStateEngine:
    """
    Computes zone-level and venue-wide spatial aggregation:
    - Density (pax / m²)
    - Capacity utilization %
    - Flow convergence index (inward vectors toward chokepoints)
    - Bottleneck pressure (inflow demand / egress capacity)
    """
    def __init__(self, venue_model: VenueModel):
        self.venue = venue_model

    def compute_zone_states(
        self,
        detections: List[Dict[str, Any]],
        flow_metrics: Dict[str, Any],
        frame_w: int = 640,
        frame_h: int = 480
    ) -> List[Dict[str, Any]]:
        """
        Groups detections into zones and calculates kinematic metrics.
        """
        zone_counts: Dict[str, int] = {}
        for z in self.venue.zones:
            zone_counts[z["zone_id"]] = 0

        # Assign each detection to a zone
        for det in detections:
            cx, cy = det["centroid"]
            zid = self.venue.map_point_to_zone(cx, cy, frame_w, frame_h)
            if zid:
                det["zone_id"] = zid
                zone_counts[zid] = zone_counts.get(zid, 0) + 1
            else:
                # Default to closest or unzoned
                det["zone_id"] = "UNZONED"

        results = []
        mean_speed = flow_metrics.get("mean_speed", 0.0)
        turbulence = flow_metrics.get("turbulence_index", 0.1)

        for z in self.venue.zones:
            zid = z["zone_id"]
            cnt = zone_counts.get(zid, 0)
            # Scale count up realistically to represent full venue sub-area if sample clip
            # For direct demo consistency, compute density = count / area
            area = z.get("area_sqm", 200.0)
            density = round(cnt / (area / 20.0), 2)  # density per m² scaled to visible viewport
            cap = z.get("max_capacity", 1000)
            occ_pct = round((cnt * 20) / cap * 100.0, 1)  # scaled to zone rated max

            # Bottleneck calculation
            is_chokepoint = z.get("is_critical_bottleneck_candidate", False)
            if is_chokepoint and cnt > 15:
                bottleneck_pressure = min(1.0, round(0.5 + (cnt / 40.0) * 0.5, 2))
            else:
                bottleneck_pressure = round(min(1.0, cnt / 60.0), 2)

            results.append({
                "zone_id": zid,
                "name": z["name"],
                "count": cnt,
                "capacity": cap,
                "occupancy_pct": occ_pct,
                "density_sqm": density,
                "mean_speed": mean_speed,
                "turbulence": turbulence,
                "bottleneck_pressure": bottleneck_pressure,
                "is_chokepoint": is_chokepoint
            })

        return results
