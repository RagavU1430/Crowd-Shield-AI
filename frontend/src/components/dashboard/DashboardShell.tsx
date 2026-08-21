import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAnalysisStatus } from "../../hooks/useAnalysisStatus";
import { approveIntervention, assetUrl, getPersonDetections, rejectIntervention, startPersonDetection, videoUrl } from "../../services/api";
import type { DetectionJob, VideoUploadResponse } from "../../types/api";
import { startContinuousCriticalBeep, stopContinuousCriticalBeep } from "../../utils/audioAlert";
import { VideoViewer } from "../video/VideoViewer";

type Props = { upload: VideoUploadResponse; onReset: () => void };

const compassDirection = (degrees?: number) => {
  if (degrees === undefined) return "N/A";
  const labels = ["EAST", "SOUTH-EAST", "SOUTH", "SOUTH-WEST", "WEST", "NORTH-WEST", "NORTH", "NORTH-EAST"];
  return labels[Math.round((((degrees % 360) + 360) % 360) / 45) % 8];
};

export const DashboardShell = ({ upload, onReset }: Props) => {
  const { job: uploadJob, error: uploadError } = useAnalysisStatus(upload.job_id);
  const [detection, setDetection] = useState<DetectionJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [decision, setDecision] = useState<any>(null);
  const [showDetection, setShowDetection] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [showFlow, setShowFlow] = useState(false);
  const [confirmApproval, setConfirmApproval] = useState(false);

  const [reportedToStaff, setReportedToStaff] = useState(false);
  const [reportedTime, setReportedTime] = useState<string | null>(null);

  const handleReportToGroundStaff = () => {
    setReportedToStaff(true);
    setReportedTime(new Date().toLocaleTimeString());
    stopContinuousCriticalBeep();
  };

  useEffect(() => {
    if (!detection || ["COMPLETED", "FAILED"].includes(detection.status)) return;
    const timer = setInterval(() => getPersonDetections(upload.job_id).then(setDetection).catch((e) => setError(e.message)), 1000);
    return () => clearInterval(timer);
  }, [detection, upload.job_id]);

  const begin = useCallback(async (demoMode: boolean) => {
    setError(null);
    setDecision(null);
    setConfirmApproval(false);
    try {
      setDetection(await startPersonDetection(upload.job_id, demoMode));
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Analysis could not start";
      if (/missing job|job not found/i.test(message)) { onReset(); return; }
      setError(message);
    }
  }, [upload.job_id, onReset]);

  const result = detection?.result;
  const state = useMemo(() => {
    if (!result?.crowd_timeline?.length) return null;
    return result.crowd_timeline.reduce((a, b) => Math.abs(b.timestamp-currentTime) < Math.abs(a.timestamp-currentTime) ? b : a);
  }, [result, currentTime]);

  const observation = useMemo(() => {
    if (!result?.timeline.length) return null;
    return result.timeline.reduce((a, b) => Math.abs(b.timestamp-currentTime) < Math.abs(a.timestamp-currentTime) ? b : a);
  }, [result, currentTime]);

  const isCritical = (state?.risk_level === "CRITICAL") || ((observation?.person_count ?? 0) >= 200) || ((state?.person_count ?? 0) >= 200);

  useEffect(() => {
    if (isCritical && !reportedToStaff) {
      startContinuousCriticalBeep();
    } else {
      stopContinuousCriticalBeep();
    }
    return () => stopContinuousCriticalBeep();
  }, [isCritical, reportedToStaff]);
  const countTrend = useMemo(() => {
    const points = result?.timeline ?? [];
    if (points.length < 4) return "INSUFFICIENT DATA";
    const window = Math.max(2, Math.floor(points.length / 5));
    const early = points.slice(-window * 2, -window).reduce((sum, p) => sum + p.person_count, 0) / window;
    const late = points.slice(-window).reduce((sum, p) => sum + p.person_count, 0) / window;
    return late > early * 1.05 ? "↑ INCREASING" : late < early * .95 ? "↓ DECREASING" : "→ STABLE";
  }, [result]);
  const densityTrend = state ? (state.density_growth > 8 ? "↑ INCREASING" : "→ STABLE") : "—";
  const recommended = result?.summary.interventions?.find((item) => item.recommended);
  const displayVideo = showDetection && result?.artifacts.annotated_video ? assetUrl(result.artifacts.annotated_video) : videoUrl(upload.video_id);
  const compactRisk = (result?.crowd_timeline ?? []).filter((_, i, all) => i % Math.max(1, Math.ceil(all.length/80)) === 0);
  const topContributors = state?.top_contributors ?? [];
  const zoneReasons = state?.critical_zone_reasons ?? ["Highest relative grid score"];
  const zones = state?.zones ?? [];
  const interventions = result?.summary.interventions ?? [];

  const approve = async () => {
    if (!recommended) return;
    try {
      setDecision(await approveIntervention(upload.job_id, recommended.option_id));
      setConfirmApproval(false);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Approval failed"); }
  };
  const reject = async () => {
    try { setDecision(await rejectIntervention(upload.job_id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Rejection failed"); }
  };

  return <section className="dashboard-shell command-center">
    <div className="dashboard-heading"><div><p className="eyebrow">CROWD-SHIELD · COMMAND CENTER</p><h2>{upload.filename}</h2><p>Context-Aware Predictive Crowd Safety</p></div><button className="secondary" onClick={onReset}>Upload another</button></div>
    {(uploadError || error) && <p className="error-message" role="alert">{uploadError || error}</p>}

    {!detection && uploadJob?.status !== "COMPLETED" && <div className="status-card auto-analysis-card"><span className="analysis-spinner"/><div><strong>{uploadJob?.status ?? "PREPARING"}</strong><span>Validating the uploaded video and reading metadata…</span></div></div>}
    {!detection && uploadJob?.status === "COMPLETED" && <section className="glass-panel analysis-ready">
      <div><p className="panel-title">VIDEO READY FOR ANALYSIS</p><h3>{upload.filename}</h3></div>
      <dl className="metadata-grid"><div><dt>Duration</dt><dd>{upload.duration.toFixed(1)} s</dd></div><div><dt>Resolution</dt><dd>{upload.width} × {upload.height}</dd></div><div><dt>Source FPS</dt><dd>{upload.fps.toFixed(2)}</dd></div><div><dt>Frames</dt><dd>{upload.frame_count}</dd></div></dl>
      <div className="analysis-actions"><button className="primary-action" onClick={() => begin(false)}>START ANALYSIS</button><button className="secondary" onClick={() => begin(true)}>RUN DEMO / SIMULATION</button></div>
      <p className="analysis-note">Normal mode reports only computed observations. Demo mode clearly labels controlled crowd-pressure signals.</p>
    </section>}
    {detection && detection.status !== "COMPLETED" && <div className={`status-card ${detection.status === "FAILED" ? "analysis-failed" : ""}`} aria-live="polite"><span className={detection.status === "FAILED" ? "" : "analysis-spinner"}/><div><strong>{detection.status === "FAILED" ? "ANALYSIS FAILED" : "ANALYZING…"}</strong><span>{detection.stage}</span></div>{detection.status === "FAILED" ? <button onClick={() => begin(false)}>Retry analysis</button> : <progress max="100" value={detection.progress}/>}</div>}
    {result?.analysis.mode === "DEMO_SIMULATION" && <div className="demo-banner">DEMO / SIMULATION — boxes and people counts are observed; crowd-pressure signals are controlled for demonstration.</div>}
    {result?.analysis.mode !== "DEMO_SIMULATION" && result && <div className="retrospective-banner"><b>RETROSPECTIVE ANALYSIS</b><span>This is a retrospective prototype analysis of observable crowd dynamics in recorded footage. It does not establish causality, guarantee prediction, or demonstrate that the incident could have been prevented.</span></div>}

    {isCritical && (
      <div className="ground-staff-emergency-panel">
        <div className="alert-badge-group">
          <span className="emergency-pulse-icon">🚨</span>
          <div>
            <h4>CRITICAL CROWD SAFETY EMERGENCY DETECTED</h4>
            <p>Severe density & bottleneck pressure (Detections: {observation?.person_count ?? state?.person_count ?? 200}+ people). Immediate ground response required.</p>
          </div>
        </div>
        {reportedToStaff ? (
          <div className="staff-notified-pill">
            ✅ REPORTED TO GROUND STAFF ({reportedTime}) — ALARM SILENCED
          </div>
        ) : (
          <button className="btn-report-ground-staff" onClick={handleReportToGroundStaff}>
            📢 REPORTED TO THE GROUND STAFF (OFF ALARM)
          </button>
        )}
      </div>
    )}

    <div className="command-grid">
      <div className="glass-panel"><p className="panel-title">VIDEO INTELLIGENCE</p><VideoViewer src={displayVideo} onTimeUpdate={setCurrentTime} heatmapLevel={showHeatmap ? state?.relative_density ?? 0 : null} flowAngle={showFlow ? state?.dominant_direction_deg ?? 0 : null} zones={showHeatmap ? state?.zones ?? null : null}/><div className="overlay-toggles"><button className={`toggle-btn ${showDetection ? "active" : ""}`} onClick={() => setShowDetection(v => !v)}>Detection {showDetection ? "ON" : "OFF"}</button><button className={`toggle-btn ${showHeatmap ? "active" : ""}`} onClick={() => setShowHeatmap(v => !v)}>Heatmap {showHeatmap ? "ON" : "OFF"}</button><button className={`toggle-btn ${showFlow ? "active" : ""}`} onClick={() => setShowFlow(v => !v)}>Flow {showFlow ? "ON" : "OFF"}</button></div></div>
      <div className="glass-panel"><p className="panel-title">CURRENT RISK <span className="simulation-tag">ESTIMATED</span></p><div className={`risk-display tier-${(isCritical ? "critical" : (state?.risk_level ?? "safe")).toLowerCase()}`}><strong>{isCritical ? Math.max(78, state?.risk_score ?? 78).toFixed(0) : (state?.risk_score.toFixed(0) ?? "—")}</strong><span>/ 100</span><b>{isCritical ? "CRITICAL" : (state?.risk_level ?? "WAITING")}</b></div><p className="trend">Trend: {state?.risk_trend ?? "—"} ({state?.risk_slope.toFixed(2) ?? "0"}/s)</p><p className="why-label">WHY?</p>{topContributors.length ? <ol>{topContributors.map((x) => <li key={x}>{x}</li>)}</ol> : <p className="signal-unavailable">Insufficient contributing-signal data</p>}</div>
      <div className="glass-panel"><p className="panel-title">CROWD STATE</p><div className="state-list"><span>Current people <b>{observation?.person_count ?? 0}</b></span><span>Average / peak <b>{result ? `${result.summary.average_people_detected.toFixed(0)} / ${result.summary.maximum_people_detected}` : "—"}</b></span><span>Count trend <b>{countTrend}</b></span><span>Estimated relative density <b>{state?.density_label ?? "—"} ({state?.relative_density.toFixed(0) ?? 0})</b></span><span>Density trend <b>{densityTrend}</b></span><span>Movement <b>{state ? (state.movement_available ? `${state.movement_speed.toFixed(0)} · ${compassDirection(state.dominant_direction_deg)}` : "SIGNAL UNAVAILABLE") : "—"}</b></span><span>Flow conflict <b>{state?.flow_conflict.toFixed(0) ?? "—"}</b></span><span>Flow convergence <b>{state ? `${state.convergence.toFixed(0)} · ${state.convergence >= 45 ? "DETECTED" : "LOW"}` : "—"}</b></span><span>Bottleneck <b>{state ? `${state.bottleneck_pressure.toFixed(0)} · ${state.bottleneck_pressure >= 55 ? "DETECTED" : "NOT DETECTED"}` : "—"}</b></span></div></div>
    </div>

    {result && <>
      <section className="glass-panel risk-timeline"><p className="panel-title">RISK TRAJECTORY</p><div className="risk-bars">{compactRisk.map(p => <div key={p.frame_index} style={{height: `${Math.max(3,p.risk_score)}%`}} title={`${p.timestamp.toFixed(1)}s · ${p.risk_score}`}/>)}</div></section>
      {state && <section className="glass-panel critical-zone-panel"><div><p className="panel-title">CRITICAL ZONE</p><strong className="critical-zone-name">{state.critical_zone ?? "N/A"}</strong><p>{zoneReasons.join(" · ")}</p><small>Relative 2×2 image-region assessment. Venue context unavailable.</small></div>{zones.length ? <div className="zone-grid">{zones.map(zone => <div key={zone.zone_id} className={zone.zone_id === state.critical_zone ? "zone-critical" : ""}><b>{zone.zone_id}</b><span>{zone.count} people</span><span>Risk {zone.risk_score.toFixed(0)}</span></div>)}</div> : <p className="signal-unavailable">Detailed zone data is unavailable for this completed legacy result. Run analysis again to generate it.</p>}</section>}
      <section className="glass-panel"><p className="panel-title">WHAT-IF INTERVENTION SIMULATION <span className="simulation-tag">SIMULATION ONLY</span></p>{interventions.length ? <div className="intervention-grid">{interventions.map(option => <article key={option.option_id} className={`intervention-item ${option.recommended ? "recommended" : ""} ${!option.feasible ? "rejected" : ""}`}><div className="opt-head"><span>{option.title}</span><b>{option.current_risk.toFixed(0)} → {option.projected_risk.toFixed(0)}</b></div><p>{option.feasible ? "FEASIBLE" : "REJECTED"} · {option.feasibility_reason}</p>{option.recommended && <strong>★ BEST FEASIBLE INTERVENTION</strong>}</article>)}</div> : <p className="signal-unavailable">Intervention simulation is unavailable for this legacy result. Run analysis again.</p>}</section>
      {recommended && <div className="hitl-banner"><div><b>AI RECOMMENDATION</b><p>{recommended.title}: projected {recommended.current_risk.toFixed(0)} → {recommended.projected_risk.toFixed(0)} · {recommended.risk_reduction_percent}% reduction</p><small>Lowest simulated risk among feasible interventions. Human authorization is required.</small></div><div className="button-row"><button className="btn-approve" onClick={() => setConfirmApproval(true)}>APPROVE</button><button className="btn-reject" onClick={reject}>REJECT / OVERRIDE</button></div></div>}
      {confirmApproval && recommended && <div className="confirmation-box" role="dialog" aria-modal="true" aria-label="Confirm simulated intervention"><div><b>CONFIRMATION</b><p>Approve simulated intervention “{recommended.title}”?</p></div><div className="button-row"><button className="btn-approve" onClick={approve}>CONFIRM</button><button className="btn-reject" onClick={() => setConfirmApproval(false)}>CANCEL</button></div></div>}
      {decision && <div className={`decision-result ${decision.option ? "approved-result" : ""}`}><strong>{decision.option ? "SIMULATED INTERVENTION APPLIED" : decision.status}</strong><p>{decision.message ?? decision.reason}</p>{decision.option && <div className="before-after"><div><small>BEFORE</small><b>{decision.option.current_risk.toFixed(0)} / 100</b></div><span>→</span><div className="applied-action"><small>SIMULATED INTERVENTION</small><b>{decision.option.title}</b></div><span>→</span><div><small>AFTER</small><b>{decision.option.projected_risk.toFixed(0)} / 100</b></div></div>}{decision.option && <p className="simulation-result-note">Risk reduction: {decision.option.risk_reduction_percent}% · SIMULATED RESULT — NOT A REAL-WORLD ACTION</p>}</div>}
      <div className="artifact-links"><a href={assetUrl(result.artifacts.detections_json)}>JSON intelligence</a><a href={assetUrl(result.artifacts.frame_summary_csv)}>CSV observations</a></div>
    </>}
    <p className="disclaimer-banner">Prototype decision support only. Relative image-space density is not people/m². Thresholds and interventions are simulated, not scientifically universal or connected to physical gates. Person detection is used for aggregate crowd analysis only—no facial recognition, identity tracking, biometric profiles, or autonomous infrastructure control.</p>
  </section>;
};
