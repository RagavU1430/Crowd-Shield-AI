# CROWD-SHIELD: Final Demo Flow
**Document ID:** CS-DOC-DEMO-01
**Version:** 1.0.0

---

## Demo Story for Judges

### Act 1: System Introduction (30 seconds)

1. Open CROWD-SHIELD at `http://localhost:5173`
2. Point out the header: **CROWD-SHIELD · SYSTEM ONLINE**
3. Show the mode toggle: **REAL VIDEO** | **SYNTHETIC DEMO**

> "CROWD-SHIELD is an AI-powered, human-in-the-loop crowd safety decision-support
> system. It separates perception from decision intelligence."

### Act 2: Synthetic Demo — The Decision Pipeline (3 minutes)

4. Select **SYNTHETIC DEMO** mode
5. Click **CRITICAL** scenario
6. Click **PLAY SCENARIO**
7. Watch the timeline progress:

```
00:00  Risk: ~25   SAFE
00:15  Risk: ~39   WATCH
00:30  Risk: ~56   HIGH
00:45  Risk: ~71   HIGH
01:00  Risk: ~84   CRITICAL
```

8. Point out the **WHY IS RISK CRITICAL?** explainability bars
9. Show the **SIGNAL PROGRESSION** charts (density, convergence, bottleneck)
10. Show the **CRITICAL ZONE: ZONE B** identification
11. Show the **WHAT-IF INTERVENTION SIMULATION**:

```
Continue Monitoring     84 → 84
Restrict Entrance A     84 → ~78
Open Exit C             84 → ~58
Redirect Flow           84 → ~47
Exit C + Redirect       84 → ~29  ★ RECOMMENDED
```

12. Point out **FEASIBILITY CHECKS** on each option
13. Click **APPROVE** on the recommended intervention
14. Show the **BEFORE / AFTER** visualization:

```
BEFORE: 84 / 100  CRITICAL
  → SIMULATED INTERVENTION: Open Exit C + Redirect Flow
AFTER:  29 / 100  WATCH
Risk Reduction: ~65%
```

15. Note the disclaimer: **SIMULATION ONLY — NOT A REAL-WORLD ACTION**

### Act 3: Real Video — The Perception Layer (2 minutes)

16. Switch to **REAL VIDEO** mode
17. Upload a crowd video file
18. Click **START ANALYSIS**
19. Watch YOLO detect actual people in real-time
20. Point out:
    - **Person count** (actual YOLO detections)
    - **Detection quality** indicator
    - **Estimated relative density** (NOT people/m²)
    - **Optical flow** analysis
    - **Risk score** computed from actual observations

> "Real video provides the perception layer using YOLOv8. The same risk engine
> processes actual observations. Synthetic scenarios validate the decision layer."

### Act 4: Key Differentiator (30 seconds)

> "Existing crowd monitoring: Detect → Alert.
>
> CROWD-SHIELD: Sense → Understand → Predict → Simulate → Recommend → Human Approve → Monitor → Adapt.
>
> The prototype separates perception from decision intelligence, allowing the risk
> and intervention engine to be validated with controlled synthetic scenarios while
> real video provides observable crowd inputs."

### Key Points to Emphasize

- **Same risk engine** processes both real and synthetic data
- **Human-in-the-loop**: AI recommends, human approves
- **Privacy**: No face recognition, no identity tracking, no biometrics
- **Transparency**: Risk formula is documented and configurable
- **Feasibility checks**: Prevents unsafe recommendations
- **Clear labeling**: Real vs. Synthetic is never ambiguous

### Don't Say

- ~~"We generated fake data because YOLO doesn't work"~~
- ~~"Our system can predict stampedes"~~
- ~~"The density values are people per square meter"~~

### Do Say

- "Synthetic scenarios validate the decision pipeline independently of detection quality"
- "The system provides decision support, not autonomous control"
- "All density values are relative estimates from image-space analysis"
