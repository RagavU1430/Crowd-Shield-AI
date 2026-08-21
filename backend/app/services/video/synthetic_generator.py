import cv2
import numpy as np
import os
from pathlib import Path
from typing import Tuple

def generate_benchmark_crowd_video(
    output_path: Path,
    duration_sec: int = 15,
    fps: int = 20,
    resolution: Tuple[int, int] = (640, 480)
) -> Path:
    """
    Generates a realistic benchmark crowd video demonstrating:
    - Phase 1 (0-4s): Normal crowd flow into North Plaza (SAFE)
    - Phase 2 (4-8s): Increasing queue density at Stage Concourse (WATCH)
    - Phase 3 (8-12s): Chokepoint bottleneck & flow conflict (HIGH -> CRITICAL)
    - Phase 4 (12-15s): Evolving crowd-crush condition
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = resolution
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))

    # Initialize simulated crowd particles
    np.random.seed(42)
    num_particles = 180
    
    # Particle states: x, y, vx, vy, color_type
    particles = []
    for i in range(num_particles):
        particles.append({
            "x": np.random.uniform(50, w - 50),
            "y": np.random.uniform(50, h - 50),
            "vx": np.random.uniform(-1.0, 1.0),
            "vy": np.random.uniform(-1.0, 1.0),
            "radius": int(np.random.uniform(4, 7)),
            "group": i % 3
        })

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        
        # Background: Dark navy concourse layout
        frame = np.full((h, w, 3), (25, 20, 15), dtype=np.uint8)

        # Draw structural walls & corridors
        cv2.rectangle(frame, (40, 40), (w - 40, h - 40), (60, 50, 40), 2)
        # Chokepoint wall in middle
        cv2.line(frame, (300, 40), (300, 180), (80, 70, 60), 4)
        cv2.line(frame, (300, 260), (300, h - 40), (80, 70, 60), 4)
        # Chokepoint passage label
        cv2.putText(frame, "CHOKEPOINT GATE", (240, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (120, 150, 180), 1)

        # Zone Labels
        cv2.putText(frame, "ZONE A (PLAZA)", (70, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 120, 140), 1)
        cv2.putText(frame, "ZONE B (STAGE)", (380, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 120, 140), 1)

        # Physics: As time progresses, particles converge toward the chokepoint (300, 220)
        convergence_factor = min(1.0, t / (duration_sec * 0.7))
        target_x, target_y = 300.0, 220.0

        for p in particles:
            if t > 4.0:
                # Steer toward Zone B chokepoint
                dx = target_x - p["x"]
                dy = target_y - p["y"]
                dist = np.sqrt(dx**2 + dy**2) + 1e-4
                
                if p["group"] == 0:  # Inflow stream from left
                    p["vx"] = 0.7 * p["vx"] + 0.3 * (dx / dist * 2.5 * convergence_factor)
                    p["vy"] = 0.7 * p["vy"] + 0.3 * (dy / dist * 2.5 * convergence_factor)
                elif p["group"] == 1:  # Opposing stream from right (Flow conflict)
                    if t > 7.0:
                        p["vx"] = 0.7 * p["vx"] + 0.3 * (-dx / dist * 1.8 * convergence_factor)
                        p["vy"] = 0.7 * p["vy"] + 0.3 * (dy / dist * 1.5 * convergence_factor)
                else:
                    p["vx"] += np.random.uniform(-0.3, 0.3)
                    p["vy"] += np.random.uniform(-0.3, 0.3)

            # Update position
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # Boundary collision
            if p["x"] < 50 or p["x"] > w - 50:
                p["vx"] *= -1.0
            if p["y"] < 50 or p["y"] > h - 50:
                p["vy"] *= -1.0

            # Draw person (head + shoulders silhouette)
            px, py = int(p["x"]), int(p["y"])
            # Outer shoulder circle
            cv2.circle(frame, (px, py), p["radius"] + 2, (180, 190, 200), -1)
            # Head circle
            cv2.circle(frame, (px, py - 2), p["radius"] - 1, (240, 220, 200), -1)

        # Video timestamp overlay
        time_str = f"{int(t//60):02d}:{int(t%60):02d}.{int((t%1)*10):01d}"
        cv2.putText(frame, f"CROWD-SHIELD BENCHMARK FEED | T={time_str}", (50, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 200, 240), 1)

        out.write(frame)

    out.release()
    return output_path
