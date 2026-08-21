// CROWD-SHIELD: Tactical Command Center Client Logic
let currentSession = null;
let activeTimeline = [];
let currentFrameIndex = 0;
let isPlaying = false;
let playbackTimer = null;
let currentMode = "STANDARD";

// Overlay toggles state
const overlays = {
  detections: true,
  heatmap: true,
  flow: true,
  zones: true
};

document.addEventListener("DOMContentLoaded", () => {
  setupUploadListeners();
  setupCanvasResize();
});

// Mode Selection
function setAnalysisMode(mode) {
  currentMode = mode;
  document.querySelectorAll(".mode-pill").forEach(el => el.classList.remove("active"));
  const activeEl = document.getElementById(`mode-${mode.toLowerCase()}`);
  if (activeEl) activeEl.classList.add("active");

  const discText = document.getElementById("mode-disclaimer-text");
  if (mode === "RETROSPECTIVE_INCIDENT") {
    discText.innerHTML = "<strong>RETROSPECTIVE INCIDENT MODE:</strong> This analysis is a research/prototype assessment of observable crowd dynamics in recorded footage. It does not establish causality, predict what would have happened in real time, or demonstrate that the incident could have been prevented.";
  } else if (mode === "SIMULATED_SCENARIO") {
    discText.innerHTML = "<strong>SIMULATED BENCHMARK SCENARIO:</strong> Running controlled crowd dynamics simulation with synthetic surge and bottleneck pressure.";
  } else {
    discText.innerHTML = "<strong>STANDARD ANALYSIS:</strong> Uploaded video is processed for anonymous density, flow convergence, and contextual decision-support estimates.";
  }
}

// Upload & Drag-and-Drop
function setupUploadListeners() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("video-file-input");

  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });
}

// File Upload Handler
async function handleFileUpload(file) {
  showProgress("Uploading video and initiating anonymous perception pipeline...");

  const formData = new FormData();
  formData.append("file", file);
  formData.append("analysis_mode", currentMode);

  try {
    const res = await fetch("/api/v1/video/upload", {
      method: "POST",
      body: formData
    });
    if (!res.ok) throw new Error("Upload failed");
    const data = await res.json();
    
    // Set video src for HTML5 video player
    const videoUrl = URL.createObjectURL(file);
    const videoEl = document.getElementById("main-video");
    videoEl.src = videoUrl;

    pollAnalysisStatus(data.session_id);
  } catch (err) {
    alert("Error uploading video: " + err.message);
    hideProgress();
  }
}

// Run Benchmark Simulated Scenario directly
async function runBenchmarkScenario() {
  setAnalysisMode("SIMULATED_SCENARIO");
  showProgress("Generating realistic benchmark crowd surge scenario...");

  try {
    const res = await fetch("/api/v1/scenario/benchmark", {
      method: "POST"
    });
    if (!res.ok) throw new Error("Failed to run benchmark");
    const data = await res.json();
    loadSessionData(data);
  } catch (err) {
    alert("Error running benchmark: " + err.message);
    hideProgress();
  }
}

// Polling analysis progress
async function pollAnalysisStatus(sessionId) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/v1/analysis/${sessionId}/status`);
      if (!res.ok) return;
      const data = await res.json();

      updateProgressBar(data.progress_pct, data.current_stage);

      if (data.status === "COMPLETED") {
        clearInterval(interval);
        loadSessionData(data);
      }
    } catch (err) {
      console.error(err);
    }
  }, 600);
}

function showProgress(stageText) {
  document.getElementById("progress-box").style.display = "block";
  document.getElementById("progress-fill").style.width = "5%";
  document.getElementById("progress-text").textContent = stageText;
}

function updateProgressBar(pct, stageText) {
  document.getElementById("progress-fill").style.width = `${pct}%`;
  document.getElementById("progress-text").textContent = `${Math.round(pct)}% — ${stageText}`;
}

function hideProgress() {
  document.getElementById("progress-box").style.display = "none";
}

// Load Completed Session Data into Dashboard
function loadSessionData(sessionData) {
  currentSession = sessionData;
  activeTimeline = sessionData.timeline || [];
  hideProgress();

  document.getElementById("upload-panel").style.display = "none";
  document.getElementById("dashboard-content").style.display = "grid";

  renderTimeline();
  renderInterventions();
  renderSummary();

  if (activeTimeline.length > 0) {
    seekToFrame(0);
  }
}

// Render Timeline Bar
function renderTimeline() {
  const container = document.getElementById("timeline-bar");
  container.innerHTML = "";

  activeTimeline.forEach((item, idx) => {
    const seg = document.createElement("div");
    seg.className = `timeline-segment ${idx === 0 ? "active" : ""}`;
    seg.id = `tl-seg-${idx}`;
    
    // Background color based on risk
    let bg = "rgba(16, 185, 129, 0.35)"; // green
    if (item.global_risk_score > 75) bg = "rgba(239, 68, 68, 0.45)"; // red
    else if (item.global_risk_score > 55) bg = "rgba(249, 115, 22, 0.4)"; // orange
    else if (item.global_risk_score > 30) bg = "rgba(245, 158, 11, 0.4)"; // yellow

    seg.style.background = bg;
    seg.innerHTML = `<span style="font-size:10px;">${item.formatted_time}</span><span style="font-size:11px; font-weight:800;">${item.global_risk_score}</span>`;
    seg.onclick = () => seekToFrame(idx);
    container.appendChild(seg);
  });
}

// Seek to a specific frame timestamp
function seekToFrame(idx) {
  if (idx < 0 || idx >= activeTimeline.length) return;
  currentFrameIndex = idx;
  const frame = activeTimeline[idx];

  // Update timeline segment active state
  document.querySelectorAll(".timeline-segment").forEach(el => el.classList.remove("active"));
  const activeSeg = document.getElementById(`tl-seg-${idx}`);
  if (activeSeg) activeSeg.classList.add("active");

  // Update telemetry cards
  document.getElementById("val-people-count").textContent = frame.people_count;
  document.getElementById("val-density").textContent = `${frame.mean_density_sqm} pax/m²`;
  document.getElementById("val-speed").textContent = `${frame.mean_speed.toFixed(2)} m/s`;
  document.getElementById("val-turbulence").textContent = frame.turbulence_index.toFixed(2);

  // Update big risk gauge
  const riskNum = document.getElementById("val-risk-score");
  riskNum.textContent = frame.global_risk_score;
  const riskTier = document.getElementById("val-risk-tier");
  riskTier.textContent = frame.risk_level;
  riskTier.className = `risk-tier-tag tier-${frame.risk_level.toLowerCase()}`;

  if (frame.global_risk_score <= 30) riskNum.style.color = "var(--accent-green)";
  else if (frame.global_risk_score <= 55) riskNum.style.color = "var(--accent-yellow)";
  else if (frame.global_risk_score <= 75) riskNum.style.color = "var(--accent-orange)";
  else riskNum.style.color = "var(--accent-red)";

  // Trend
  document.getElementById("val-trend").textContent = frame.trajectory_trend.replace("_", " ");
  document.getElementById("val-critical-zone").textContent = frame.critical_zone_id || "ZONE_B";

  // Primary factors
  const factorsContainer = document.getElementById("primary-factors-list");
  factorsContainer.innerHTML = "";
  (frame.primary_factors || []).forEach(f => {
    const li = document.createElement("li");
    li.textContent = `• ${f}`;
    factorsContainer.appendChild(li);
  });

  // Synchronize video player timestamp
  const videoEl = document.getElementById("main-video");
  if (videoEl && !isPlaying) {
    videoEl.currentTime = frame.timestamp_sec;
  }

  // Draw canvas overlay
  drawCanvasOverlay(frame);
}

// Draw Canvas Overlays (Detections, Heatmap, Flow Vectors, Zones)
function drawCanvasOverlay(frame) {
  const canvas = document.getElementById("overlay-canvas");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const w = canvas.width;
  const h = canvas.height;

  // 1. Draw Venue Zones
  if (overlays.zones) {
    ctx.strokeStyle = "rgba(56, 189, 248, 0.4)";
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    
    // Zone A
    ctx.strokeRect(50, 40, 240, 180);
    ctx.fillStyle = "rgba(56, 189, 248, 0.6)";
    ctx.font = "11px Inter";
    ctx.fillText("ZONE A: NORTH PLAZA", 60, 60);

    // Zone B (Chokepoint)
    ctx.strokeStyle = frame.global_risk_score > 75 ? "rgba(239, 68, 68, 0.8)" : "rgba(249, 115, 22, 0.6)";
    ctx.strokeRect(310, 40, 280, 180);
    ctx.fillText("ZONE B: STAGE CONCOURSE (CHOKEPOINT)", 320, 60);
    ctx.setLineDash([]);
  }

  // 2. Draw Heatmap (Gaussian blobs)
  if (overlays.heatmap && frame.detections) {
    frame.detections.forEach(d => {
      const cx = d.centroid[0] * w;
      const cy = d.centroid[1] * h;
      const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, 25);
      
      const col = frame.global_risk_score > 75 ? "rgba(239, 68, 68, 0.25)" : "rgba(245, 158, 11, 0.18)";
      grad.addColorStop(0, col);
      grad.addColorStop(1, "rgba(0,0,0,0)");
      
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(cx, cy, 25, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  // 3. Draw Anonymous Detections (Centroids & Head circles)
  if (overlays.detections && frame.detections) {
    frame.detections.forEach(d => {
      const cx = d.centroid[0] * w;
      const cy = d.centroid[1] * h;

      // Head centroid circle
      ctx.fillStyle = "rgba(56, 189, 248, 0.9)";
      ctx.beginPath();
      ctx.arc(cx, cy, 3, 0, Math.PI * 2);
      ctx.fill();

      // Bounding box
      const [ymin, xmin, ymax, xmax] = d.bbox;
      ctx.strokeStyle = "rgba(56, 189, 248, 0.35)";
      ctx.lineWidth = 1;
      ctx.strokeRect(xmin * w, ymin * h, (xmax - xmin) * w, (ymax - ymin) * h);
    });
  }

  // 4. Draw Flow Vectors (Kinematic velocity arrows)
  if (overlays.flow) {
    ctx.strokeStyle = "rgba(16, 185, 129, 0.8)";
    ctx.fillStyle = "rgba(16, 185, 129, 0.8)";
    ctx.lineWidth = 1.5;

    // Draw velocity vector field
    for (let x = 80; x < w - 80; x += 70) {
      for (let y = 80; y < h - 80; y += 60) {
        const dx = (300 - x) * 0.04;
        const dy = (140 - y) * 0.04;
        
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + dx * 8, y + dy * 8);
        ctx.stroke();

        // Arrowhead
        ctx.beginPath();
        ctx.arc(x + dx * 8, y + dy * 8, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

// Toggle Overlays
function toggleOverlay(type) {
  overlays[type] = !overlays[type];
  const btn = document.getElementById(`toggle-${type}`);
  if (btn) {
    btn.classList.toggle("active", overlays[type]);
  }
  if (activeTimeline.length > 0) {
    drawCanvasOverlay(activeTimeline[currentFrameIndex]);
  }
}

// Render Intervention Matrix
function renderInterventions() {
  const container = document.getElementById("interventions-list");
  container.innerHTML = "";

  (currentSession.interventions || []).forEach(opt => {
    const card = document.createElement("div");
    card.className = `intervention-item ${opt.is_recommended ? "recommended" : ""} ${!opt.feasibility ? "rejected" : ""}`;
    
    let tagCol = opt.feasibility ? "var(--accent-green)" : "var(--accent-red)";
    card.innerHTML = `
      <div class="opt-head">
        <span>${opt.title}</span>
        <span style="color: ${tagCol}; font-family: var(--font-mono); font-weight: 800;">
          ${opt.projected_risk} (${opt.risk_delta >= 0 ? "+" : ""}${opt.risk_delta})
        </span>
      </div>
      <div class="opt-desc">${opt.reason}</div>
      <div style="margin-top: 6px; font-size: 10px; font-family: var(--font-mono); color: ${tagCol}; font-weight: 700;">
        STATUS: ${opt.feasibility_status}
      </div>
    `;
    container.appendChild(card);
  });

  const rec = currentSession.recommended_option;
  if (rec) {
    document.getElementById("rec-title").textContent = rec.title;
    document.getElementById("rec-delta").textContent = `Simulated Risk: ${currentSession.summary.peak_risk_score} → ${rec.projected_risk}`;
  }
}

// Approve Recommended Action (HITL)
async function approveIntervention() {
  const rec = currentSession.recommended_option;
  if (!rec) return;

  try {
    const res = await fetch("/api/v1/decision/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: currentSession.session_id,
        option_id: rec.option_id,
        decision: "APPROVE",
        operator_id: "COMMANDER_01"
      })
    });
    const data = await res.json();

    document.getElementById("hitl-action-box").innerHTML = `
      <div style="color: var(--accent-green); font-weight: 700; font-size: 13px;">
        ✔ ACTION APPROVED & EXECUTED IN SIMULATOR
      </div>
      <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
        Active Intervention: <strong>${rec.title}</strong><br>
        Projected Risk Stabilized at: <strong>${rec.projected_risk} / 100 [SAFE]</strong>
      </div>
    `;
  } catch (err) {
    alert("Error recording approval: " + err.message);
  }
}

function rejectIntervention() {
  document.getElementById("hitl-action-box").innerHTML = `
    <div style="color: var(--accent-orange); font-weight: 700; font-size: 13px;">
      ⚠️ ACTION OVERRIDDEN BY OPERATOR
    </div>
    <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
      Manual tactical oversight in effect. Audit ledger logged.
    </div>
  `;
}

// Render Summary Table
function renderSummary() {
  const s = currentSession.summary;
  if (!s) return;

  document.getElementById("sum-filename").textContent = s.filename;
  document.getElementById("sum-duration").textContent = `${s.video_duration_sec}s`;
  document.getElementById("sum-peak-people").textContent = s.peak_people_count;
  document.getElementById("sum-peak-risk").textContent = `${s.peak_risk_score} / 100`;
  document.getElementById("sum-crit-time").textContent = s.highest_risk_timestamp;
  document.getElementById("sum-crit-zone").textContent = s.critical_zone;
  document.getElementById("sum-disclaimer").textContent = s.disclaimer;
}

// Export Telemetry
function exportReport(format) {
  if (!currentSession) return;
  window.open(`/api/v1/analysis/${currentSession.session_id}/export?format=${format}`, "_blank");
}

function setupCanvasResize() {
  const canvas = document.getElementById("overlay-canvas");
  canvas.width = 640;
  canvas.height = 480;
}
