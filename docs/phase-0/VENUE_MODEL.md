# CROWD-SHIELD: Venue Digital Model & Graph Representation
**Document ID:** CS-DOC-P0-07  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** Spatial Venue Graph & Topology Modeling  

---

## 1. Graph Topology Overview

The venue is represented mathematically as a directed, capacitated network flow graph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E}, \mathcal{C}, \mathcal{W})$$

- $\mathcal{V} = \{ Z_1, Z_2, \dots, Z_n \} \cup \{ \text{Inlets}, \text{Outlets} \}$: Set of venue zones and external boundaries.
- $\mathcal{E} \subseteq \mathcal{V} \times \mathcal{V}$: Directed corridors, gates, and exit pathways between zones.
- $\mathcal{C}: \mathcal{E} \to \mathbb{R}^+$: Maximum throughput capacity of each passage ($\text{people}/\text{second}$).
- $\mathcal{W}: \mathcal{V} \to \mathbb{R}^+$: Maximum rated physical capacity of each zone ($C_{\max, k}$).

```
[ Gate A (Inflow: 300/min) ] ──────────► [ Zone A (Waiting Concourse) ]
                                                      │
                                                      ▼
[ Gate B (Inflow: 250/min) ] ──────────► [ Zone B (Main Concourse - CHOKEPOINT) ] ────► [ Exit C (Emergency Exit) ]
                                                      │
                                                      ▼
                                         [ Zone D (Perimeter Corridor) ] ────────► [ Main Gate 1 (Standard Exit) ]
```

---

## 2. Standard Benchmark Venue Configuration (`venue_config.json`)

The default MVP layout models a high-traffic concert / festival arena concourse:

```json
{
  "venue_id": "VENUE_STADIUM_ARENA_01",
  "name": "Metro Grand Arena - Sector East Concourse",
  "total_max_capacity": 4500,
  "zones": [
    {
      "zone_id": "ZONE_A",
      "name": "North Entry Plaza",
      "polygon": [[50, 50], [250, 50], [250, 200], [50, 200]],
      "area_sqm": 350.0,
      "max_capacity": 1200,
      "warning_density_sqm": 3.0,
      "critical_density_sqm": 5.0
    },
    {
      "zone_id": "ZONE_B",
      "name": "Main Stage Front Concourse",
      "polygon": [[260, 50], [550, 50], [550, 220], [260, 220]],
      "area_sqm": 200.0,
      "max_capacity": 1000,
      "warning_density_sqm": 3.5,
      "critical_density_sqm": 5.5,
      "is_critical_bottleneck_candidate": true
    },
    {
      "zone_id": "ZONE_C",
      "name": "South Exhibition Hall",
      "polygon": [[50, 220], [250, 220], [250, 420], [50, 420]],
      "area_sqm": 400.0,
      "max_capacity": 1500,
      "warning_density_sqm": 3.0,
      "critical_density_sqm": 5.0
    },
    {
      "zone_id": "ZONE_D",
      "name": "East Bypass Corridor",
      "polygon": [[260, 230], [550, 230], [550, 420], [260, 420]],
      "area_sqm": 300.0,
      "max_capacity": 800,
      "warning_density_sqm": 2.5,
      "critical_density_sqm": 4.5
    }
  ],
  "gates_and_passages": [
    {
      "edge_id": "GATE_A_TO_ZONE_A",
      "source": "EXTERNAL_ENTRY_NORTH",
      "target": "ZONE_A",
      "type": "ENTRY_GATE",
      "is_controllable": true,
      "max_throughput_pax_sec": 8.0,
      "current_status": "OPEN"
    },
    {
      "edge_id": "CORRIDOR_A_TO_B",
      "source": "ZONE_A",
      "target": "ZONE_B",
      "type": "INTERNAL_CORRIDOR",
      "is_controllable": true,
      "max_throughput_pax_sec": 5.0,
      "current_status": "OPEN",
      "is_bottleneck": true
    },
    {
      "edge_id": "EXIT_C_FROM_ZONE_B",
      "source": "ZONE_B",
      "target": "EXTERNAL_SAFETY_PERIMETER",
      "type": "EMERGENCY_EXIT",
      "is_controllable": true,
      "max_throughput_pax_sec": 10.0,
      "current_status": "CLOSED"
    },
    {
      "edge_id": "BYPASS_CORRIDOR_A_TO_D",
      "source": "ZONE_A",
      "target": "ZONE_D",
      "type": "DIVERSION_CORRIDOR",
      "is_controllable": true,
      "max_throughput_pax_sec": 6.5,
      "current_status": "STANDBY"
    }
  ]
}
```

---

## 3. Network Dynamics & Routing Calculations

Using **NetworkX**, CROWD-SHIELD computes instantaneous shortest evacuation paths, maximum network flow (Edmonds-Karp / Dinic's algorithm), and edge bottleneck stress indices:

1. **Edge Bottleneck Stress:**
   $$\sigma(e) = \frac{\phi_{\text{demand}}(e)}{\mathcal{C}(e)}$$
   When $\sigma(e) > 1.0$, edge $e$ is flagged as an active chokepoint.

2. **Downstream Safety Invariant:**
   Before rerouting flow from Zone $A$ to Zone $D$, the system checks:
   $$\text{Occupancy}(Z_D) + \Delta \text{Flux}(A \to D) \cdot \Delta t \le 0.85 \times C_{\max}(Z_D)$$
   Preventing risk cascade from one zone to another.
