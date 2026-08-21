import cv2
import numpy as np
from typing import Dict, Any, List, Tuple

class OpticalFlowAnalyzer:
    """
    Computes Farneback dense optical flow between sampled frames to estimate:
    - Crowd movement velocities (vx, vy)
    - Mean flow speed and direction
    - Directional turbulence / entropy (turbulence index)
    - Convergence toward bottlenecks
    """
    def __init__(self):
        self.prev_gray = None

    def reset(self):
        self.prev_gray = None

    def compute_flow(self, current_frame: np.ndarray, detections: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        """
        Computes flow field and velocity metrics between previous and current frames.
        """
        gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        if gray.shape[1] > 480:
            scale = 480 / gray.shape[1]
            gray = cv2.resize(gray, (480, max(1, round(gray.shape[0] * scale))), interpolation=cv2.INTER_AREA)
        h, w = gray.shape

        if self.prev_gray is None:
            self.prev_gray = gray
            return {
                "mean_speed": 0.0,
                "turbulence_index": 0.0,
                "dominant_angle_deg": 0.0,
                "grid_vectors": []
            }

        # Farneback Optical Flow calculation
        flow = cv2.calcOpticalFlowFarneback(
            self.prev_gray, gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        self.prev_gray = gray

        raw_u = flow[..., 0]
        raw_v = flow[..., 1]
        # Approximate global camera motion and analyze residual image-space motion.
        camera_vx = float(np.median(raw_u))
        camera_vy = float(np.median(raw_v))
        u = raw_u - camera_vx
        v = raw_v - camera_vy
        magnitude = np.sqrt(u**2 + v**2)
        angles = np.arctan2(v, u)

        # Compute directional turbulence (entropy of velocity angles)
        # When all move in unison -> turbulence ~ 0. When opposing streams collide -> turbulence -> 1.0
        person_mask = np.zeros_like(magnitude, dtype=bool)
        source_h, source_w = current_frame.shape[:2]
        scale_x, scale_y = w / source_w, h / source_h
        for detection in detections or []:
            x1, y1, x2, y2 = detection["bbox"]
            xa, ya = max(0, int(x1 * scale_x)), max(0, int(y1 * scale_y))
            xb, yb = min(w, int(np.ceil(x2 * scale_x))), min(h, int(np.ceil(y2 * scale_y)))
            if xb > xa and yb > ya:
                person_mask[ya:yb, xa:xb] = True
        active_mask = (magnitude > 0.5) & person_mask
        mean_speed = float(np.mean(magnitude[active_mask])) if np.any(active_mask) else 0.0
        if np.sum(active_mask) > 10:
            active_angles = angles[active_mask]
            hist, _ = np.histogram(active_angles, bins=8, range=(-np.pi, np.pi))
            hist = hist / np.sum(hist)
            # Shannon entropy normalized
            entropy = -np.sum([p * np.log2(p) for p in hist if p > 0]) / 3.0  # max log2(8)=3
            turbulence = float(np.clip(entropy, 0.0, 1.0))
            
            # Dominant angle
            dominant_bin = np.argmax(hist)
            dominant_angle = float(np.degrees(-np.pi + (dominant_bin + 0.5) * (2 * np.pi / 8)))
        else:
            turbulence = 0.1
            dominant_angle = 0.0

        # One robust residual vector per detected person for frontend display.
        grid_vectors = []
        for detection in detections or []:
            x1, y1, x2, y2 = detection["bbox"]
            xa, ya = max(0, int(x1 * scale_x)), max(0, int(y1 * scale_y))
            xb, yb = min(w, int(np.ceil(x2 * scale_x))), min(h, int(np.ceil(y2 * scale_y)))
            if xb <= xa or yb <= ya:
                continue
            roi_mag = magnitude[ya:yb, xa:xb]
            roi_active = roi_mag > 0.5
            if not np.any(roi_active):
                continue
            vx = float(np.median(u[ya:yb, xa:xb][roi_active]))
            vy = float(np.median(v[ya:yb, xa:xb][roi_active]))
            grid_vectors.append({"x": round(float(detection["centroid"][0]) / source_w, 3), "y": round(float(detection["centroid"][1]) / source_h, 3), "vx": round(vx / 10.0, 3), "vy": round(vy / 10.0, 3), "speed": round(float(np.hypot(vx, vy)), 2)})

        return {
            "mean_speed": round(mean_speed, 3),
            "turbulence_index": round(turbulence, 3),
            "dominant_angle_deg": round(dominant_angle, 1),
            "grid_vectors": grid_vectors,
            "camera_motion": {"vx": round(camera_vx, 3), "vy": round(camera_vy, 3)},
            "camera_motion_compensated": True,
        }
