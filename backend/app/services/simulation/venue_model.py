import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import networkx as nx
from app.config import VENUE_CONFIG_PATH

class VenueModel:
    """
    Manages the physical/geometric venue topology, zone boundaries, rated capacities,
    and directed egress network graph.
    """
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or VENUE_CONFIG_PATH
        self.venue_data: Dict[str, Any] = {}
        self.graph = nx.DiGraph()
        self.zones: List[Dict[str, Any]] = []
        self.gates: List[Dict[str, Any]] = []
        self.is_loaded = False
        self.load_venue()

    def load_venue(self):
        if self.config_path and Path(self.config_path).exists():
            with open(self.config_path, "r") as f:
                self.venue_data = json.load(f)
            self.zones = self.venue_data.get("zones", [])
            self.gates = self.venue_data.get("gates_and_passages", [])
            self._build_graph()
            self.is_loaded = True
        else:
            self.is_loaded = False

    def _build_graph(self):
        self.graph.clear()
        for zone in self.zones:
            self.graph.add_node(
                zone["zone_id"],
                name=zone["name"],
                max_capacity=zone["max_capacity"],
                area_sqm=zone["area_sqm"]
            )
        for gate in self.gates:
            self.graph.add_edge(
                gate["source"],
                gate["target"],
                edge_id=gate["edge_id"],
                type=gate["type"],
                max_throughput=gate["max_throughput_pax_sec"],
                status=gate.get("current_status", "OPEN")
            )

    def map_point_to_zone(self, norm_x: float, norm_y: float, frame_w: int = 640, frame_h: int = 480) -> Optional[str]:
        """
        Maps a normalized point [0-1] to a venue zone polygon.
        """
        if not self.is_loaded:
            return None

        # Convert normalized coordinates to absolute polygon space
        px = norm_x * frame_w
        py = norm_y * frame_h

        for zone in self.zones:
            poly = zone.get("polygon", [])
            if self._point_in_polygon(px, py, poly):
                return zone["zone_id"]
        return None

    @staticmethod
    def _point_in_polygon(x: float, y: float, poly: List[List[float]]) -> bool:
        """Ray-casting algorithm for point-in-polygon check."""
        num = len(poly)
        if num < 3:
            return False
        inside = False
        j = num - 1
        for i in range(num):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-6) + xi):
                inside = not inside
            j = i
        return inside

    def get_zone_by_id(self, zone_id: str) -> Optional[Dict[str, Any]]:
        for z in self.zones:
            if z["zone_id"] == zone_id:
                return z
        return None
