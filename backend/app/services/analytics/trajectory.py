import numpy as np
from typing import List, Dict, Any, Tuple
from app.models.schemas import TrajectoryTrend

class RiskTrajectoryEngine:
    """
    Computes 1st order temporal derivative (slope dR/dt) over rolling window
    and classifies trend into DECREASING, STABLE, INCREASING, RAPIDLY_INCREASING.
    """
    def __init__(self, window_size: int = 6):
        self.window_size = window_size
        self.history: List[Tuple[float, int]] = []  # (timestamp, risk_score)

    def reset(self):
        self.history.clear()

    def update_and_evaluate(self, timestamp_sec: float, current_risk: int) -> Tuple[TrajectoryTrend, float]:
        """
        Appends current risk sample and calculates trend slope.
        """
        self.history.append((timestamp_sec, current_risk))
        if len(self.history) > self.window_size:
            self.history.pop(0)

        if len(self.history) < 2:
            return TrajectoryTrend.STABLE, 0.0

        times = np.array([h[0] for h in self.history])
        risks = np.array([h[1] for h in self.history])

        # Normalize time delta
        dt = times - times[0]
        if dt[-1] < 1e-4:
            return TrajectoryTrend.STABLE, 0.0

        # Linear regression slope (dR / dt in points per second)
        slope, _ = np.polyfit(dt, risks, 1)

        if slope > 0.45:
            trend = TrajectoryTrend.RAPIDLY_INCREASING
        elif slope > 0.15:
            trend = TrajectoryTrend.INCREASING
        elif slope < -0.20:
            trend = TrajectoryTrend.DECREASING
        else:
            trend = TrajectoryTrend.STABLE

        return trend, round(float(slope), 3)
