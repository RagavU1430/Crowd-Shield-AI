/** Synthetic scenario API client for CROWD-SHIELD demo mode. */

const BASE_URL = (import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8010").replace(/\/$/, "");

async function handleResponse(response, fallback) {
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message || body?.detail || fallback);
  }
  return response.json();
}

export async function listScenarios() {
  const response = await fetch(`${BASE_URL}/api/synthetic/scenarios`);
  return handleResponse(response, "Could not load scenarios");
}

export async function getScenario(name) {
  const response = await fetch(`${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(name)}`);
  return handleResponse(response, "Could not load scenario");
}

export async function analyzeScenario(name) {
  const response = await fetch(`${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(name)}/analyze`, {
    method: "POST",
  });
  return handleResponse(response, "Scenario analysis failed");
}

export async function approveSyntheticIntervention(scenarioName, optionId) {
  const response = await fetch(
    `${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(scenarioName)}/interventions/${encodeURIComponent(optionId)}/approve`,
    { method: "POST" }
  );
  return handleResponse(response, "Approval simulation failed");
}

export async function rejectSyntheticIntervention(scenarioName) {
  const response = await fetch(
    `${BASE_URL}/api/synthetic/scenarios/${encodeURIComponent(scenarioName)}/interventions/reject`,
    { method: "POST" }
  );
  return handleResponse(response, "Rejection failed");
}
