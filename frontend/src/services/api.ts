import type { AnalysisJob, DetectionJob, VideoUploadResponse } from "../types/api";

const BASE_URL = (import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8010").replace(/\/$/, "");

async function messageFromResponse(response: Response, fallback: string) {
  const body = await response.json().catch(() => null);
  return body?.error?.message || body?.detail || fallback;
}

export function uploadVideo(
  formData: FormData,
  onProgress?: (percentage: number) => void,
): Promise<VideoUploadResponse> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", `${BASE_URL}/api/videos/upload`);
    request.responseType = "json";
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
    };
    request.onerror = () => reject(new Error("Unable to connect to the analysis server. Make sure the backend is running."));
    request.onload = () => {
      const body = request.response;
      if (request.status >= 200 && request.status < 300) resolve(body);
      else reject(new Error(body?.error?.message || body?.detail || "Upload failed"));
    };
    request.send(formData);
  });
}

export async function getAnalysisStatus(jobId: string): Promise<AnalysisJob> {
  const response = await fetch(`${BASE_URL}/api/analysis/${encodeURIComponent(jobId)}`);
  if (!response.ok) throw new Error(await messageFromResponse(response, "Backend unavailable"));
  return response.json();
}

export function videoUrl(videoId: string) {
  return `${BASE_URL}/uploads/${encodeURIComponent(videoId)}`;
}

export async function startPersonDetection(jobId: string, demoMode = false): Promise<DetectionJob> {
  const response = await fetch(`${BASE_URL}/api/analysis/${encodeURIComponent(jobId)}/detect?demo_mode=${demoMode}`, {
    method: "POST",
  });
  if (!response.ok) {
    if (response.status === 409) {
      return getPersonDetections(jobId);
    }
    throw new Error(await messageFromResponse(response, "Detection could not start"));
  }
  return response.json();
}

export async function approveIntervention(jobId: string, optionId: string) {
  const response = await fetch(`${BASE_URL}/api/analysis/${encodeURIComponent(jobId)}/interventions/${encodeURIComponent(optionId)}/approve`, { method: "POST" });
  if (!response.ok) throw new Error(await messageFromResponse(response, "Approval simulation failed"));
  return response.json();
}

export async function rejectIntervention(jobId: string) {
  const response = await fetch(`${BASE_URL}/api/analysis/${encodeURIComponent(jobId)}/interventions/reject`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ reason: "Operator rejected recommendation" }) });
  if (!response.ok) throw new Error(await messageFromResponse(response, "Rejection failed"));
  return response.json();
}

export async function getPersonDetections(jobId: string): Promise<DetectionJob> {
  const response = await fetch(`${BASE_URL}/api/analysis/${encodeURIComponent(jobId)}/detections`);
  if (!response.ok) {
    if (response.status === 502 || response.status === 503 || response.status === 504) {
      throw new Error("Server warming up, retrying...");
    }
    throw new Error(await messageFromResponse(response, "Detection status unavailable"));
  }
  return response.json();
}

export function assetUrl(path: string) {
  return `${BASE_URL}${path}`;
}
