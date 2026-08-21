import { useEffect, useState } from "react";
import { getAnalysisStatus } from "../services/api";
import type { AnalysisJob } from "../types/api";

export function useAnalysisStatus(jobId: string, pollInterval: number = 1500) {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;

    async function fetchStatus() {
      setIsPolling(true);
      setError(null);
      try {
        const data = await getAnalysisStatus(jobId);
        if (!cancelled) setJob(data);
      } catch (err: any) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setIsPolling(false);
      }
    }

    fetchStatus();
    const interval = setInterval(() => {
      if (job?.status !== "COMPLETED" && job?.status !== "FAILED") fetchStatus();
    }, pollInterval);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [jobId, pollInterval, job?.status]);

  return { job, error, isPolling };
}
