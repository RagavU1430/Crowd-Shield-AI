/** Synthetic scenario API client for CROWD-SHIELD demo mode.
 * Supports online FastAPI connection and client-side fallback for Netlify static deployments.
 */
import syntheticDataset from "../data/synthetic_crowd_scenarios.json";

const BASE_URL = (import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8010").replace(/\/$/, "");

const SCENARIO_DESCRIPTIONS = {
  SAFE: "Fluid crowd movement with low density & open bottlenecks.",
  ESCALATING: "Gradual congestion buildup with increasing bottleneck pressure.",
  CRITICAL: "Severe crowd surge with critical density & bottleneck pressure.",
};

async function handleResponse(response, fallback) {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || body?.detail || fallback);
  }
  return response.json();
}

function _localScenarios() {
  const scenarioNames = Object.keys(syntheticDataset.scenarios || {});
  return scenarioNames.map((name) => ({
    name,
    description: SCENARIO_DESCRIPTIONS[name] || `${name} crowd safety scenario`,
    duration_seconds: syntheticDataset.metadata?.duration_sec || 300,
    records_count: syntheticDataset.scenarios[name]?.length || 0,
  }));
}

function _localAnalyze(name) {
  const scenarioKey = Object.keys(syntheticDataset.scenarios || {}).find((k) => k === name) || "CRITICAL";
  const records = syntheticDataset.scenarios[scenarioKey] || syntheticDataset.scenarios["CRITICAL"] || [];

  const timestamps = Array.from(new Set(records.map((r) => r.timestamp))).sort((a, b) => a - b);
  const timeline = timestamps.map((ts) => {
    const zRecs = records.filter((r) => r.timestamp === ts);
    const worst = zRecs.reduce((prev, curr) => (curr.density_score > prev.density_score ? curr : prev), zRecs[0]);

    const density = worst.density_score;
    const density_growth = worst.density_growth;
    const movement_instability = worst.movement_score;
    const conflict = worst.conflict_score;
    const convergence = worst.convergence_score;
    const bottleneck = Math.min(100, Math.round(0.45 * density + 0.25 * density_growth + 0.30 * convergence));

    const risk_score = Math.min(
      100,
      Math.round(
        0.25 * density +
          0.15 * density_growth +
          0.15 * movement_instability +
          0.15 * conflict +
          0.15 * convergence +
          0.15 * bottleneck
      )
    );

    const risk_level = risk_score < 30 ? "SAFE" : risk_score < 55 ? "WATCH" : risk_score < 75 ? "HIGH" : "CRITICAL";

    const zones = zRecs.map((zr) => ({
      zone_id: zr.zone,
      count: Math.round(zr.detected_occupancy),
      relative_density: zr.density_score,
      risk_score: Math.min(
        100,
        Math.round(
          0.25 * zr.density_score +
            0.15 * zr.density_growth +
            0.15 * zr.movement_score +
            0.15 * zr.conflict_score +
            0.15 * zr.convergence_score +
            0.15 * zr.bottleneck_score
        )
      ),
    }));

    return {
      timestamp: ts,
      person_count: Math.round(worst.detected_occupancy),
      relative_density: density,
      density_label: worst.density_label || risk_level,
      risk_score,
      risk_level,
      risk_trend: worst.trend || (density_growth > 2 ? "INCREASING" : "STABLE"),
      risk_slope: worst.slope || 0,
      movement_speed: worst.movement_score,
      dominant_direction_deg: worst.direction_deg || 90,
      flow_conflict: worst.conflict_score,
      convergence: worst.convergence_score,
      bottleneck_pressure: bottleneck,
      critical_zone: worst.zone,
      zones,
      top_contributors: ["High relative occupancy", "Bottleneck pressure"],
    };
  });

  const lastState = timeline[timeline.length - 1] || {
    timestamp: 0,
    person_count: 50,
    relative_density: 30,
    density_label: "WATCH",
    risk_score: 45,
    risk_level: "WATCH",
    risk_trend: "STABLE",
    risk_slope: 0,
    movement_speed: 15,
    dominant_direction_deg: 90,
    flow_conflict: 10,
    convergence: 15,
    bottleneck_pressure: 20,
    critical_zone: "ZONE_A",
    zones: [],
    top_contributors: ["Moderate crowd occupancy"],
  };

  const interventions = [
    {
      option_id: "EXIT_AND_REDIRECT",
      title: "Open Emergency Relief Gate B & Divert Ingress",
      current_risk: lastState.risk_score,
      projected_risk: Math.max(15, Math.round(lastState.risk_score * 0.45)),
      risk_reduction_percent: 55,
      feasible: true,
      feasibility_reason: "Directly relieves bottleneck pressure in critical zone",
      recommended: true,
    },
    {
      option_id: "HOLD_INFLOW",
      title: "Temporarily Hold Ingress Stream for 120s",
      current_risk: lastState.risk_score,
      projected_risk: Math.max(25, Math.round(lastState.risk_score * 0.65)),
      risk_reduction_percent: 35,
      feasible: true,
      feasibility_reason: "Prevents further density growth",
      recommended: false,
    },
  ];

  return {
    scenario: {
      name: scenarioKey,
      description: SCENARIO_DESCRIPTIONS[scenarioKey] || `${scenarioKey} crowd safety scenario`,
      duration_seconds: syntheticDataset.metadata?.duration_sec || 300,
    },
    analysis: {
      mode: "DEMO_SIMULATION",
      records_analyzed: records.length,
      current_state: lastState,
      timeline,
      interventions,
      recommended_intervention: interventions[0],
    },
  };
}

export async function listScenarios() {
  try {
    const response = await fetch(`${BASE_URL}/api/synthetic/scenarios`);
    return await handleResponse(response, "Could not load scenarios");
  } catch {
    return _localScenarios();
  }
}

export async function getScenario(name) {
  try {
    const response = await fetch(`${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(name)}`);
    return await handleResponse(response, "Could not load scenario");
  } catch {
    const scenarios = _localScenarios();
    return scenarios.find((s) => s.name === name) || scenarios[0];
  }
}

export async function analyzeScenario(name) {
  try {
    const response = await fetch(`${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(name)}/analyze`, {
      method: "POST",
    });
    return await handleResponse(response, "Scenario analysis failed");
  } catch {
    return _localAnalyze(name);
  }
}

export async function approveSyntheticIntervention(scenarioName, optionId) {
  try {
    const response = await fetch(
      `${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(scenarioName)}/interventions/${encodeURIComponent(optionId)}/approve`,
      { method: "POST" }
    );
    return await handleResponse(response, "Approval simulation failed");
  } catch {
    const analysisData = _localAnalyze(scenarioName);
    const opt = analysisData.analysis.interventions.find((i) => i.option_id === optionId);
    return {
      status: "SIMULATED_INTERVENTION_APPLIED",
      message: `Simulated intervention '${opt?.title}' authorized.`,
      option: opt,
    };
  }
}

export async function rejectSyntheticIntervention(scenarioName) {
  try {
    const response = await fetch(
      `${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(scenarioName)}/interventions/reject`,
      { method: "POST" }
    );
    return await handleResponse(response, "Rejection failed");
  } catch {
    return {
      status: "REJECTED_BY_OPERATOR",
      reason: "Simulated intervention override recorded.",
    };
  }
}
