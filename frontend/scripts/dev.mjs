import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve } from "node:path";

const frontend = resolve(import.meta.dirname, "..");
const project = resolve(frontend, "..");
const backend = resolve(project, "backend");
const gpuPython = resolve(project, ".venv-yolo-training", "Scripts", "python.exe");
const localPython = process.env.LOCALAPPDATA ? resolve(process.env.LOCALAPPDATA, "Python", "bin", "python.exe") : "";
const python = process.env.CROWD_SHIELD_PYTHON || (existsSync(gpuPython) ? gpuPython : (localPython && existsSync(localPython) ? localPython : "python"));
const vite = resolve(frontend, "node_modules", "vite", "bin", "vite.js");
const env = { ...process.env, PYTHONPATH: backend, YOLO_CONFIG_DIR: resolve(backend, ".runtime"), MPLCONFIGDIR: resolve(backend, ".runtime", "matplotlib") };

async function responds(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(1500) });
    return response.ok;
  } catch {
    return false;
  }
}

async function main() {
  const frontendAlive = await responds("http://127.0.0.1:5173/");
  const proxiedApiAlive = await responds("http://127.0.0.1:5173/api/health");
  if (frontendAlive && proxiedApiAlive) {
    console.log("CROWD-SHIELD is already running at http://localhost:5173");
    return;
  }
  if (frontendAlive) throw new Error("Port 5173 is occupied by another frontend. Stop that process or choose another port.");

  const children = [];
  if (!(await responds("http://127.0.0.1:8010/api/health"))) {
    children.push(spawn(python, ["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8010"], { cwd: backend, env, stdio: "inherit" }));
  } else {
    console.log("Reusing the existing CROWD-SHIELD API on port 8010.");
  }
  children.push(spawn(process.execPath, [vite], { cwd: frontend, env, stdio: "inherit" }));

  let exiting = false;
  const stop = (code = 0) => {
    if (exiting) return;
    exiting = true;
    for (const child of children) if (!child.killed) child.kill();
    setTimeout(() => { process.exitCode = code; }, 250);
  };
  for (const child of children) {
    child.on("error", (error) => { console.error(`CROWD-SHIELD development service failed: ${error.message}`); stop(1); });
    child.on("exit", (code) => { if (!exiting && code) stop(code); });
  }
  process.on("SIGINT", () => stop());
  process.on("SIGTERM", () => stop());
}

await main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
