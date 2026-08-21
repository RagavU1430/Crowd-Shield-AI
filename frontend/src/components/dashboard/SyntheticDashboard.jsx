import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { analyzeScenario, approveSyntheticIntervention, rejectSyntheticIntervention } from "../../services/syntheticApi";
import { startContinuousCriticalBeep, stopContinuousCriticalBeep } from "../../utils/audioAlert";

const SCENARIOS = [
  { id: "SAFE", label: "SAFE", desc: "Stable low-pressure crowd" },
  { id: "ESCALATING", label: "ESCALATING", desc: "Gradually increasing pressure" },
  { id: "CRITICAL", label: "CRITICAL", desc: "Rapid buildup toward critical risk" },
];

const compassDirection = (deg) => {
  if (deg === undefined || deg === null) return "N/A";
  const labels = ["EAST", "SE", "SOUTH", "SW", "WEST", "NW", "NORTH", "NE"];
  return labels[Math.round((((deg % 360) + 360) % 360) / 45) % 8];
};

const formatTime = (secs) => {
  if (!secs || isNaN(secs) || secs < 0) return "0:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
};

export const SyntheticDashboard = () => {
  const [scenario, setScenario] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [playIndex, setPlayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [decision, setDecision] = useState(null);
  const [confirmApproval, setConfirmApproval] = useState(false);

  const [reportedToStaff, setReportedToStaff] = useState(false);
  const [reportedTime, setReportedTime] = useState(null);

  const timerRef = useRef(null);

  const timeline = analysis?.timeline ?? [];
  const state = timeline[playIndex] ?? null;
  const interventions = analysis?.summary?.interventions ?? [];
  const recommended = interventions.find((i) => i.recommended);

  const handleReportToGroundStaff = () => {
    setReportedToStaff(true);
    setReportedTime(new Date().toLocaleTimeString());
    stopContinuousCriticalBeep();
  };

  // Continuous emergency beep loop when risk reaches CRITICAL until reported
  useEffect(() => {
    if (state?.risk_level === "CRITICAL" && !reportedToStaff) {
      startContinuousCriticalBeep();
    } else {
      stopContinuousCriticalBeep();
    }
    return () => stopContinuousCriticalBeep();
  }, [state?.risk_level, reportedToStaff]);

  // Play/pause logic
  useEffect(() => {
    if (playing && playIndex < timeline.length - 1) {
      timerRef.current = setTimeout(() => setPlayIndex((i) => i + 1), 400);
    } else if (playIndex >= timeline.length - 1) {
      setPlaying(false);
    }
    return () => clearTimeout(timerRef.current);
  }, [playing, playIndex, timeline.length]);

  const loadScenario = useCallback(async (name) => {
    setScenario(name);
    setAnalysis(null);
    setPlayIndex(0);
    setPlaying(false);
    setDecision(null);
    setError(null);
    setConfirmApproval(false);
    setLoading(true);
    try {
      const result = await analyzeScenario(name);
      setAnalysis(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const approve = async () => {
    if (!recommended) return;
    try {
      setDecision(await approveSyntheticIntervention(scenario, recommended.option_id));
      setConfirmApproval(false);
    } catch (e) {
      setError(e.message);
    }
  };

  const reject = async () => {
    try {
      setDecision(await rejectSyntheticIntervention(scenario));
    } catch (e) {
      setError(e.message);
    }
  };

  const compactRisk = timeline.filter((_, i) => i % Math.max(1, Math.ceil(timeline.length / 80)) === 0);
  const topContributors = state?.top_contributors ?? [];
  const zones = state?.zones ?? [];
  const zoneReasons = state?.critical_zone_reasons ?? [];

  // Signal chart data (only the points up to current playback)
  const visibleTimeline = timeline.slice(0, playIndex + 1);

  return (
    <section className="dashboard-shell command-center synthetic-mode">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow">CROWD-SHIELD · UPLOADED VIDEO DYNAMICS</p>
          <h2>Uploaded Video Crowd Scenarios</h2>
          <p>Context-Aware Predictive Crowd Safety</p>
        </div>
        <div className="system-status">
          <span className="status-dot online" /> SYSTEM ONLINE
          <span className="mode-badge synthetic">UPLOADED VIDEO DATA</span>
        </div>
      </div>

      <div className="demo-banner">
        DATA FROM UPLOADED VIDEOS — Benchmark crowd scenarios derived from recorded crowd footage for risk & intervention modeling.
      </div>

      {error && <p className="error-message" role="alert">{error}</p>}

      {/* Scenario Selector */}
      <section className="glass-panel scenario-selector">
        <p className="panel-title">SELECT SCENARIO</p>
        <div className="scenario-buttons">
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              className={`scenario-btn ${scenario === s.id ? "active" : ""} tier-${s.id.toLowerCase()}`}
              onClick={() => loadScenario(s.id)}
              disabled={loading}
            >
              <strong>{s.label}</strong>
              <span>{s.desc}</span>
            </button>
          ))}
        </div>
      </section>

      {loading && (
        <div className="status-card">
          <span className="analysis-spinner" />
          <div>
            <strong>ANALYZING SCENARIO...</strong>
            <span>Running risk engine on synthetic dataset</span>
          </div>
        </div>
      )}

      {analysis && (
        <>
          {/* Timeline Player */}
          <section className="glass-panel timeline-player">
            <p className="panel-title">SCENARIO TIMELINE <span className="simulation-tag">SIMULATION</span></p>
            <div className="player-controls">
              <button onClick={() => { setPlayIndex(0); setPlaying(false); setDecision(null); setConfirmApproval(false); }}>⟳ RESET</button>
              <button onClick={() => setPlaying(!playing)} className="primary-action">
                {playing ? "⏸ PAUSE" : "▶ PLAY SCENARIO"}
              </button>
              <span className="time-display">
                {state ? formatTime(state.timestamp) : "0:00"}
                {" / "}
                {timeline.length ? formatTime(timeline[timeline.length - 1].timestamp) : "0:00"}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={Math.max(0, timeline.length - 1)}
              value={playIndex}
              onChange={(e) => { setPlayIndex(+e.target.value); setPlaying(false); }}
              className="timeline-slider"
            />
          </section>

          {state?.risk_level === "CRITICAL" && (
            <div className="ground-staff-emergency-panel">
              <div className="alert-badge-group">
                <span className="emergency-pulse-icon">🚨</span>
                <div>
                  <h4>CRITICAL CROWD SAFETY EMERGENCY DETECTED</h4>
                  <p>Severe density & bottleneck pressure in <strong>{state.critical_zone || "Zone A"}</strong>. Immediate ground response required.</p>
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
            {/* Risk Display */}
            <div className="glass-panel">
              <p className="panel-title">CURRENT RISK <span className="simulation-tag">ESTIMATED</span></p>
              <div className={`risk-display tier-${(state?.risk_level ?? "safe").toLowerCase()}`}>
                <strong>{state?.risk_score?.toFixed(0) ?? "—"}</strong>
                <span>/ 100</span>
                <b>{state?.risk_level ?? "WAITING"}</b>
              </div>
              <p className="trend">Trend: {state?.risk_trend ?? "—"} ({state?.risk_slope?.toFixed(2) ?? "0"}/s)</p>
              <p className="why-label">WHY IS RISK {state?.risk_level ?? "—"}?</p>
              {topContributors.length ? (
                <div className="contributor-bars">
                  {topContributors.map((name) => {
                    const signalKey = name.toLowerCase().replace(/ /g, "_");
                    const value = state?.[signalKey] ?? state?.density ?? 0;
                    return (
                      <div key={name} className="contributor-bar">
                        <span className="bar-label">{name}</span>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${Math.min(100, value)}%` }} />
                        </div>
                        <span className="bar-value">{value.toFixed(0)}</span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="signal-unavailable">Insufficient contributing-signal data</p>
              )}
            </div>

            {/* Crowd State */}
            <div className="glass-panel">
              <p className="panel-title">CROWD STATE <span className="simulation-tag">ESTIMATED</span></p>
              <div className="state-list">
                <span>Detected occupancy <b>{state?.person_count ?? 0}</b></span>
                <span>Relative density <b>{state?.density_label ?? "—"} ({state?.relative_density?.toFixed(0) ?? 0})</b></span>
                <span>Density growth <b>{state?.density_growth?.toFixed(0) ?? "—"}</b></span>
                <span>Movement <b>{state ? `${state.movement_speed?.toFixed(0)} · ${compassDirection(state.dominant_direction_deg)}` : "—"}</b></span>
                <span>Flow conflict <b>{state?.flow_conflict?.toFixed(0) ?? "—"}</b></span>
                <span>Flow convergence <b>{state ? `${state.convergence?.toFixed(0)} · ${state.convergence >= 45 ? "DETECTED" : "LOW"}` : "—"}</b></span>
                <span>Bottleneck <b>{state ? `${state.bottleneck_pressure?.toFixed(0)} · ${state.bottleneck_pressure >= 55 ? "DETECTED" : "NOT DETECTED"}` : "—"}</b></span>
              </div>
            </div>

            {/* Signal Charts */}
            <div className="glass-panel signal-charts">
              <p className="panel-title">SIGNAL PROGRESSION <span className="simulation-tag">TIMELINE</span></p>
              <div className="chart-grid">
                {["density", "density_growth", "convergence", "flow_conflict", "bottleneck_pressure"].map((key) => (
                  <div key={key} className="mini-chart">
                    <span className="chart-label">{key.replace(/_/g, " ").toUpperCase()}</span>
                    <div className="chart-bars">
                      {visibleTimeline.filter((_, i) => i % Math.max(1, Math.ceil(visibleTimeline.length / 30)) === 0).map((p, i) => (
                        <div
                          key={i}
                          className={`chart-bar ${p[key] >= 75 ? "critical" : p[key] >= 55 ? "high" : p[key] >= 30 ? "watch" : "safe"}`}
                          style={{ height: `${Math.max(3, p[key])}%` }}
                          title={`${p.timestamp}s: ${p[key]?.toFixed(1)}`}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Risk Trajectory */}
          <section className="glass-panel risk-timeline">
            <p className="panel-title">RISK TRAJECTORY <span className="simulation-tag">TIMELINE</span></p>
            <div className="risk-bars">
              {compactRisk.map((p, i) => (
                <div
                  key={i}
                  className={i <= Math.floor(playIndex / Math.max(1, Math.ceil(timeline.length / 80))) ? "active" : "future"}
                  style={{ height: `${Math.max(3, p.risk_score)}%` }}
                  title={`${p.timestamp}s · Risk ${p.risk_score?.toFixed(0)}`}
                />
              ))}
            </div>
          </section>

          {/* Critical Zone */}
          {state && (
            <section className="glass-panel critical-zone-panel">
              <div>
                <p className="panel-title">CRITICAL ZONE <span className="simulation-tag">ANALYSIS</span></p>
                <strong className="critical-zone-name">{state.critical_zone ?? "N/A"}</strong>
                <p>{zoneReasons.join(" · ")}</p>
              </div>
              {zones.length > 0 && (
                <div className="zone-grid">
                  {zones.map((zone) => (
                    <div key={zone.zone_id} className={zone.zone_id === state.critical_zone ? "zone-critical" : ""}>
                      <b>{zone.zone_id}</b>
                      <span>{zone.count} people</span>
                      <span>Risk {zone.risk_score?.toFixed(0)}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          )}

          {/* What-If Interventions */}
          <section className="glass-panel">
            <p className="panel-title">WHAT-IF INTERVENTION SIMULATION <span className="simulation-tag">SIMULATION ONLY</span></p>
            {interventions.length > 0 ? (
              <div className="intervention-grid">
                {interventions.map((option) => (
                  <article
                    key={option.option_id}
                    className={`intervention-item ${option.recommended ? "recommended" : ""} ${!option.feasible ? "rejected" : ""}`}
                  >
                    <div className="opt-head">
                      <span>{option.title}</span>
                      <b>{option.current_risk?.toFixed(0)} → {option.projected_risk?.toFixed(0)}</b>
                    </div>
                    <p>{option.feasible ? "FEASIBLE" : "REJECTED"} · {option.feasibility_reason}</p>
                    {option.recommended && <strong>★ BEST FEASIBLE INTERVENTION</strong>}
                  </article>
                ))}
              </div>
            ) : (
              <p className="signal-unavailable">Intervention simulation unavailable</p>
            )}
          </section>

          {/* AI Recommendation + Human Approval */}
          {recommended && !decision && (
            <div className="hitl-banner">
              <div>
                <b>AI RECOMMENDATION</b>
                <p>
                  {recommended.title}: projected {recommended.current_risk?.toFixed(0)} → {recommended.projected_risk?.toFixed(0)} ·{" "}
                  {recommended.risk_reduction_percent}% reduction
                </p>
                <small>Lowest simulated risk among feasible interventions. Human authorization is required.</small>
              </div>
              <div className="button-row">
                <button className="btn-approve" onClick={() => setConfirmApproval(true)}>APPROVE</button>
                <button className="btn-reject" onClick={reject}>REJECT / OVERRIDE</button>
              </div>
            </div>
          )}

          {confirmApproval && recommended && (
            <div className="confirmation-box" role="dialog" aria-modal="true" aria-label="Confirm simulated intervention">
              <div>
                <b>CONFIRMATION</b>
                <p>Approve simulated intervention &ldquo;{recommended.title}&rdquo;?</p>
              </div>
              <div className="button-row">
                <button className="btn-approve" onClick={approve}>CONFIRM</button>
                <button className="btn-reject" onClick={() => setConfirmApproval(false)}>CANCEL</button>
              </div>
            </div>
          )}

          {decision && (
            <div className={`decision-result ${decision.option ? "approved-result" : ""}`}>
              <strong>{decision.option ? "SIMULATED INTERVENTION APPLIED" : decision.status}</strong>
              <p>{decision.message ?? decision.reason}</p>
              {decision.option && (
                <div className="before-after">
                  <div>
                    <small>BEFORE</small>
                    <b>{decision.option.current_risk?.toFixed(0)} / 100</b>
                  </div>
                  <span>→</span>
                  <div className="applied-action">
                    <small>SIMULATED INTERVENTION</small>
                    <b>{decision.option.title}</b>
                  </div>
                  <span>→</span>
                  <div>
                    <small>AFTER</small>
                    <b>{decision.option.projected_risk?.toFixed(0)} / 100</b>
                  </div>
                </div>
              )}
              {decision.option && (
                <p className="simulation-result-note">
                  Risk reduction: {decision.option.risk_reduction_percent}% · SIMULATED RESULT — NOT A REAL-WORLD ACTION
                </p>
              )}
            </div>
          )}
        </>
      )}

      <p className="disclaimer-banner">
        Prototype decision support only. This scenario dataset is derived from uploaded video benchmarks for prototype validation
        of the risk and intervention engine. No facial recognition, identity tracking, or biometric profiles are used.
      </p>
    </section>
  );
};
