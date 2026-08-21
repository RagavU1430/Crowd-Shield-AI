import { useRef, useState } from "react";
import { uploadVideo } from "../../services/api";
import type { VideoUploadResponse } from "../../types/api";

const ALLOWED_EXTENSIONS = [".mp4", ".webm", ".mov"];
const MAX_FILE_SIZE = 1024 * 1024 * 1024;

type Props = {
  onUpload: (response: VideoUploadResponse) => void;
  onRemove: () => void;
};

export const VideoUploader = ({ onUpload, onRemove }: Props) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const selectFile = (file?: File) => {
    if (!file) return;
    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setError("Unsupported video format. Please upload MP4, WebM, or MOV.");
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError("File too large. Maximum size: 1GB.");
      setSelectedFile(null);
      return;
    }
    setError(null);
    setProgress(0);
    setSelectedFile(file);
  };

  const submit = async () => {
    if (!selectedFile) {
      setError("Please select a video file.");
      return;
    }
    setIsUploading(true);
    setError(null);
    const formData = new FormData();
    formData.append("file", selectedFile);
    try {
      const response = await uploadVideo(formData, setProgress);
      onUpload(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const clear = () => {
    setSelectedFile(null);
    setError(null);
    setProgress(0);
    if (inputRef.current) inputRef.current.value = "";
    onRemove();
  };

  return (
    <section className="upload-card" aria-labelledby="upload-title">
      <div className="upload-heading"><div><p className="eyebrow">START ANALYSIS</p><h2 id="upload-title">Upload crowd footage</h2></div><span className="secure-badge">LOCAL · SECURE</span></div>
      <div
        className={`drop-zone${isDragging ? " is-dragging" : ""}`}
        onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setIsDragging(false);
          selectFile(event.dataTransfer.files[0]);
        }}
      >
        <div className="upload-icon" aria-hidden="true">↑</div>
        <h3>Drop your video here</h3>
        <p>or browse a file from your computer</p>
        <button type="button" onClick={() => inputRef.current?.click()}>Browse video</button>
        <input
          ref={inputRef}
          className="visually-hidden"
          type="file"
          accept="video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov"
          onChange={(event) => selectFile(event.target.files?.[0])}
        />
        <small>MP4, WebM, MOV · maximum 100 MB</small>
      </div>
      {selectedFile && <div className="selected-file-card"><span className="file-symbol">▶</span><div><strong>{selectedFile.name}</strong><small>{(selectedFile.size / 1048576).toFixed(1)} MB · Ready to validate</small></div><span className="ready-check">✓</span></div>}
      {isUploading && (
        <div className="progress-wrap" aria-live="polite">
          <progress max="100" value={progress} />
          <span>Uploading {progress}%</span>
        </div>
      )}
      {error && <p className="error-message" role="alert"><b>Upload issue:</b> {error}</p>}
      <div className="button-row">
        <button type="button" className="analyze-button" onClick={submit} disabled={!selectedFile || isUploading}>{isUploading ? "Uploading…" : "Upload & prepare analysis"}<span>→</span></button>
        {selectedFile && <button type="button" className="secondary" onClick={clear} disabled={isUploading}>Remove</button>}
      </div>
      <div className="upload-footer"><span>Anonymous detection</span><span>Local processing</span><span>Human-in-the-loop</span></div>
    </section>
  );
};
