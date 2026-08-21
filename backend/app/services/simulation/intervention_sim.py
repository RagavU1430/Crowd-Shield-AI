from typing import List, Dict, Any, Optional
from app.models.schemas import InterventionOption
from app.services.simulation.venue_model import VenueModel
from app.services.simulation.feasibility import FeasibilityEngine

class InterventionSimulator:
    """
    Generates and virtually tests discrete candidate interventions against the live/peak crowd state.
    Calculates simulated risk reduction (Delta R) and validates feasibility.
    """
    def __init__(self, venue_model: VenueModel):
        self.venue = venue_model
        self.feasibility = FeasibilityEngine(venue_model)

    def evaluate_interventions(
        self,
        current_risk: int,
        critical_zone_id: Optional[str],
        zone_metrics_list: List[Dict[str, Any]]
    ) -> List[InterventionOption]:
        """
        Evaluates 4 discrete operational interventions for the critical zone state.
        """
        zones_map = {z["zone_id"]: z for z in zone_metrics_list}
        critical_zone = zones_map.get(critical_zone_id or "ZONE_B", {})

        options: List[InterventionOption] = []

        # Option 1: Close Entry Gate A (Inflow restriction only)
        # Physics: Halts inflow, but trapped density remains high and turbulence persists -> Risk increases slightly or stays high
        p_risk_1 = min(100, current_risk + 5) if current_risk > 70 else current_risk
        is_feas_1, status_1, reason_1 = self.feasibility.validate_action(
            "RESTRICT_INFLOW", critical_zone, zones_map, {"gate_id": "GATE_A"}
        )
        options.append(InterventionOption(
            option_id="OPT_01",
            title="Option 1: Close Gate A (Inflow Restriction Only)",
            action_type="RESTRICT_INFLOW",
            projected_risk=p_risk_1,
            risk_delta=p_risk_1 - current_risk,
            feasibility=is_feas_1,
            feasibility_status=status_1,
            reason=reason_1,
            is_recommended=False,
            details={"gate": "GATE_A", "action": "CLOSE"}
        ))

        # Option 2: Open Emergency Exit C
        # Physics: Provides outward egress -> Significant density dissipation
        p_risk_2 = max(20, int(current_risk * 0.65))
        is_feas_2, status_2, reason_2 = self.feasibility.validate_action(
            "OPEN_EMERGENCY_EXIT", critical_zone, zones_map, {"exit_id": "EXIT_C_FROM_ZONE_B"}
        )
        options.append(InterventionOption(
            option_id="OPT_02",
            title="Option 2: Open Emergency Exit C",
            action_type="OPEN_EMERGENCY_EXIT",
            projected_risk=p_risk_2,
            risk_delta=p_risk_2 - current_risk,
            feasibility=is_feas_2,
            feasibility_status=status_2,
            reason=reason_2,
            is_recommended=False,
            details={"exit": "EXIT_C", "action": "OPEN", "throughput": "10 pax/s"}
        ))

        # Option 3: Redirect Incoming Flow via East Bypass Corridor D
        # Physics: Diverts upstream streams away from chokepoint -> Inward convergence drops
        p_risk_3 = max(20, int(current_risk * 0.50))
        is_feas_3, status_3, reason_3 = self.feasibility.validate_action(
            "REDIRECT_FLOW", critical_zone, zones_map, {"target_zone": "ZONE_D"}
        )
        options.append(InterventionOption(
            option_id="OPT_03",
            title="Option 3: Redirect Incoming Flow via Bypass Corridor D",
            action_type="REDIRECT_FLOW",
            projected_risk=p_risk_3,
            risk_delta=p_risk_3 - current_risk,
            feasibility=is_feas_3,
            feasibility_status=status_3,
            reason=reason_3,
            is_recommended=False,
            details={"diversion_path": "CORRIDOR_A_TO_D", "action": "DIVERT_70%"}
        ))

        # Option 4: Open Exit C + Redirect Incoming Flow (Synergistic Best Option)
        # Physics: Dual relief -> Maximum risk reduction into Safe tier
        p_risk_4 = max(15, int(current_risk * 0.33))
        is_feas_4, status_4, reason_4 = self.feasibility.validate_action(
            "COMBO_EXIT_AND_REDIRECT", critical_zone, zones_map, {"exit_id": "EXIT_C", "target_zone": "ZONE_D"}
        )
        options.append(InterventionOption(
            option_id="OPT_04",
            title="Option 4: Open Exit C + Redirect Incoming Flow (Synergistic Combo)",
            action_type="COMBO_EXIT_AND_REDIRECT",
            projected_risk=p_risk_4,
            risk_delta=p_risk_4 - current_risk,
            feasibility=is_feas_4,
            feasibility_status=status_4,
            reason=reason_4,
            is_recommended=True,
            details={"exit": "EXIT_C", "diversion": "CORRIDOR_A_TO_D", "action": "DUAL_INTERVENTION"}
        ))

        return options
