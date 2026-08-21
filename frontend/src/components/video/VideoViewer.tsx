import { useState, useRef, useEffect } from "react";

type ZoneData = {
  zone_id: string;
  count?: number;
  relative_density?: number;
  risk_score?: number;
};

type VideoViewerProps = {
  src: string;
  onPlayPause?: () => void;
  onSeek?: (timestamp: number) => void;
  onTimeUpdate?: (timestamp: number) => void;
  heatmapLevel?: number | null;
  flowAngle?: number | null;
  zones?: ZoneData[] | null;
};

const getHeatColor = (density: number) => {
  if (density >= 75) return "rgba(239, 68, 68, 0.85)";   // Critical Red
  if (density >= 55) return "rgba(249, 115, 22, 0.75)";   // High Orange
  if (density >= 30) return "rgba(245, 158, 11, 0.65)";   // Watch Yellow
  return "rgba(16, 185, 129, 0.45)";                     // Safe Green
};

const formatTime = (secs: number) => {
  if (!secs || isNaN(secs) || secs < 0) return "0:00";
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
};

export const VideoViewer = ({
  src,
  onPlayPause,
  onSeek,
  onTimeUpdate,
  heatmapLevel,
  flowAngle,
  zones,
}: VideoViewerProps) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [timestamp, setTimestamp] = useState(0);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    if (!videoRef.current) return;
    const video = videoRef.current;

    video.src = src;
    video.autoplay = true;
    video.muted = true;

    video.onloadedmetadata = () => {
      setDuration(video.duration || 0);
    };

    video.onplay = () => {
      setTimestamp(video.currentTime);
      if (video.duration) setDuration(video.duration);
    };

    video.ontimeupdate = () => {
      setTimestamp(video.currentTime);
      if (video.duration) setDuration(video.duration);
    };

    return () => {
      video.src = "";
    };
  }, [src]);

  const togglePlayPause = () => {
    if (!videoRef.current) return;
    const video = videoRef.current;
    if (video.paused) {
      video.play();
    } else {
      video.pause();
    }
    onPlayPause?.();
  };

  const isImageSrc = /\.(jpg|jpeg|png|webp|bmp)(\?.*)?$/i.test(src);

  return (
    <div className="video-player-box">
      {isImageSrc ? (
        <img src={src} alt="Analyzed crowd media" className="analyzed-media-display" />
      ) : (
        <video
          ref={videoRef}
          controls
          muted
          onTimeUpdate={() => {
            const current = videoRef.current?.currentTime ?? 0;
            setTimestamp(current);
            onTimeUpdate?.(current);
          }}
          onClick={togglePlayPause}
          onSeeked={() => onSeek?.(videoRef.current?.currentTime ?? 0)}
        >
          <source src={src} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      )}

      {!isImageSrc && (
        <span className="timestamp video-duration-badge">
          {formatTime(timestamp)} / {formatTime(duration)}
        </span>
      )}

      {/* Thermal Heatmap Overlay */}
      {heatmapLevel != null && (
        <div className="heatmap-overlay">
          {/* Global Density Glow */}
          <div
            className="heatmap-global-glow"
            style={{
              background: `radial-gradient(circle at 50% 50%, ${getHeatColor(
                heatmapLevel
              )} 0%, rgba(245, 158, 11, 0.35) 45%, rgba(16, 185, 129, 0.15) 80%, transparent 100%)`,
              opacity: Math.max(0.45, Math.min(0.85, 0.3 + heatmapLevel / 100)),
            }}
          />

          {/* Zone-by-Zone Heat Spot Overlay (2x2 Grid) */}
          {zones && zones.length > 0 && (
            <div className="heatmap-zone-grid">
              {zones.map((z) => {
                const density = z.relative_density ?? z.risk_score ?? heatmapLevel;
                const color = getHeatColor(density);
                return (
                  <div
                    key={z.zone_id}
                    className={`zone-heat-spot ${density >= 75 ? "critical-pulse" : ""}`}
                    style={{
                      background: `radial-gradient(circle at 50% 50%, ${color} 0%, transparent 80%)`,
                    }}
                  >
                    <span className="zone-heat-badge">
                      {z.zone_id}: {density.toFixed(0)}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Directional Flow Overlay */}
      {flowAngle != null && (
        <div className="flow-overlay">
          {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
            <span
              key={i}
              className="flow-arrow"
              style={{ transform: `rotate(${flowAngle}deg)` }}
            >
              ➔
            </span>
          ))}
        </div>
      )}

      <canvas id="overlay-canvas" className="video-canvas-overlay" />
    </div>
  );
};
