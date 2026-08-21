# CROWD-SHIELD — Hackathon Fast MVP Report

## 1. Executive summary

The emergency MVP is complete as a local, end-to-end decision-support prototype. It accepts a real uploaded video, runs pretrained YOLOv8n person detection, derives relative image-space crowd signals, calculates a transparent contextual risk trajectory, finds a critical 2x2 grid zone, simulates feasible what-if interventions, ranks the best feasible action, and requires explicit human approval or rejection. Approval changes only the displayed simulation state; no physical control is connected.

Long custom training was stopped safely at epoch 18 as instructed. Its checkpoints were preserved, but the pretrained root `yolov8n.pt` remains the default MVP model.

## 2. YOLO baseline

| Item | Result |
|---|---|
| Default model | Pretrained YOLOv8n |
| Class | COCO person, class 0 only |
| Device used for final video tests | RTX 3050, CUDA |
| Analysis rate | 3 sampled FPS |
| Outputs | Boxes, centroids, confidence, count, timestamp, annotated MP4, JSON, CSV |

Confidence is not accuracy. The available videos have no ground truth.

An optional custom checkpoint is preserved at `data/training/cc_mach_yolov8n_person/weights/best.pt`. At stop time: epoch 18, precision 0.59699, recall 0.32673, mAP50 0.32036, and mAP50–95 0.10260 on the dataset validation split. It is not used by default and was not evaluated on the reserved test videos.

## 3. Videos tested and actual results

All four original MP4s in `videos/` were processed without modification. None can be scientifically labeled “normal,” “dense,” or “incident” from filenames or ground truth; the results show sparse pretrained-model counts, so no incident-causality claim is made.

| Video | Frames | Max people | Mean confidence | Processing FPS | Peak risk | Trend | Critical zone |
|---|---:|---:|---:|---:|---:|---|---|
| `21-32-01` | 97 | 4 | 0.46611 | 2.447608 | 43.33 WATCH | Rapidly increasing | Zone A |
| `21-32-40` | 118 | 3 | 0.478657 | 3.359772 | 34.91 WATCH | Rapidly increasing | Zone C |
| `21-33-43` | 199 | 1 | 0.465141 | 3.570644 | 23.08 SAFE | Rapidly increasing | Zone C |
| `21-38-15` | 214 | 5 | 0.588968 | 3.423745 | 55.52 HIGH | Rapidly increasing | Zone D |

The HIGH result is a prototype signal driven by a short increase in estimated occupancy and person-ROI movement. It is not proof of a dangerous incident or a universal stampede threshold.

## 4. Crowd-state methodology

- **Person count:** exact count of retained YOLO class-0 predictions.
- **Relative density:** 65% visible bounding-box occupancy plus 35% count normalized to 25 visible people, clipped to 0–100. It is explicitly not people/m².
- **Density growth:** positive rolling relative-density slope, normalized to 0–100.
- **Movement:** downscaled Farneback optical flow with frame-wide median camera-motion compensation, measured only inside current person boxes.
- **Instability/conflict:** angular and speed dispersion across person-level residual flow vectors. A single person cannot create opposing-flow conflict alone.
- **Convergence:** positive alignment of person-level movement vectors toward the image center.
- **Bottleneck pressure:** `0.45 density + 0.25 density growth + 0.30 convergence`.

If detections are absent, the engine does not fabricate people or person-flow vectors.

## 5. Transparent risk formula

`Risk = 0.25 density + 0.15 density growth + 0.15 movement instability + 0.15 flow conflict + 0.15 convergence + 0.15 bottleneck pressure`

Scores are clipped to 0–100. Prototype labels are SAFE `<30`, WATCH `30–<55`, HIGH `55–<75`, and CRITICAL `>=75`. The three largest weighted contributors are returned for every frame. These thresholds are configurable prototype semantics, not scientifically universal safety limits.

## 6. Risk trajectory

A rolling linear regression calculates risk points per second. Labels are DECREASING below −0.35, STABLE from −0.35 to 0.35, INCREASING above 0.35, and RAPIDLY INCREASING above 2.0. Wording reports an evolving prototype pressure signal and never predicts that an incident will occur at a specific time.

## 7. Critical-zone methodology

Without calibrated venue geometry, each frame is divided into Zones A–D using a 2x2 grid. Each zone receives a relative score from local bounding-box occupancy, person count, convergence, conflict, and density growth. The highest-scoring zone is reported with contributors. It is an image-space region, not a mapped physical venue zone.

## 8. Intervention simulation

Five transparent options are evaluated: continue monitoring, restrict Entrance A, open Exit C, redirect incoming flow, and combine Exit C with redirection. Each option applies documented multipliers to risk inputs and recomputes the same risk formula. Every result is labeled **SIMULATION ONLY**.

Measured peak recommendations:

| Video | Best feasible recommendation | Current → simulated | Reduction |
|---|---|---:|---:|
| `21-32-01` | Open Exit C + Redirect Flow | 43.33 → 29.11 | 32.8% |
| `21-32-40` | Open Exit C + Redirect Flow | 34.91 → 22.51 | 35.5% |
| `21-33-43` | Continue Monitoring | 23.08 → 23.08 | 0.0% |
| `21-38-15` | Open Exit C + Redirect Flow | 55.52 → 32.51 | 41.4% |

## 9. Feasibility and recommendation logic

SAFE conditions recommend monitoring rather than unnecessary intervention. For elevated prototype risk, the engine chooses the lowest projected risk among feasible non-monitor actions. Redirection is rejected when destination Zone D reaches 85% relative occupancy. The demo topology treats Exit C as available; because `configs/venue_config.json` has no real venue topology, this assumption is clearly a demo constraint and not an operational fact.

## 10. Human-in-the-loop and post-intervention state

The dashboard exposes APPROVE and REJECT/OVERRIDE. Approval returns the selected before/after risk and reduction with: “SIMULATION ONLY — no physical control action was sent.” Rejection records the operator override. Both paths have automated tests.

## 11. Dashboard and demo workflow

1. Start the backend and frontend using the existing project commands.
2. Upload one of the videos from `videos/`.
3. Choose **Analyze real observations** for evidence-only results, or **Run demo scenario** for controlled pressure signals clearly labeled DEMO/SIMULATION.
4. Watch the annotated player and current people, relative density, movement, convergence, bottleneck, risk, trend, and critical zone.
5. Toggle Detection, Heatmap, and Flow overlays.
6. Review the risk trajectory and simulated intervention table.
7. Approve or reject the best feasible recommendation.
8. Explain that the system tests possible actions before presenting a decision to a human operator.

Demo mode never changes observed person boxes or counts. It supplies a deterministic controlled crowd-pressure trajectory only, with an always-visible simulation label.

## 12. Tests performed

- Backend/AI: **36 passed, 0 failed**.
- New focused tests cover the exact weighted formula, relative-density labeling, opposing vectors, explicit demo source, intervention ranking, approval, and rejection.
- Frontend production build: **PASS**, 22 modules, 381 ms in the final pre-report run.
- Frontend lint: exit 0 with 14 pre-existing unused-variable warnings in duplicate inactive page files.
- Four real-video runs: **PASS**, 628 sampled frames total, CUDA, generated JSON/CSV/annotated MP4s.

## 13. Known limitations and blockers

- No calibrated venue map or spatial reference: no people/m² or real exit/capacity claim.
- Sparse detections (maximum 1–5 per clip) do not validate dense-crowd performance.
- Person-box optical flow is still sensitive to camera movement, box jitter, occlusion, and missed detections.
- No ground-truth event labels; precision/recall for the videos and real safety accuracy are unknown.
- Intervention effects are transparent heuristics, not validated physical predictions.
- Processing ranged from 2.45 to 3.57 analyzed FPS on the final GPU run; the pipeline is demo/offline, not live CCTV.
- The empty venue configuration limits feasibility to the explicitly stated demo topology.
- The preserved epoch-18 custom model is experimental and not the default.

## 14. Completion status

Real video, pretrained YOLO detection, count, centroids, movement, relative density, risk, trajectory, critical zone, what-if simulation, feasibility, recommendation, human approval/rejection, post-intervention simulation, dashboard, simulation labeling, privacy, and real-video execution are implemented. Drone, satellite, IoT, live CCTV, identity recognition, and physical gate control were not added.
