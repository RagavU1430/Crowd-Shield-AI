import { useState, useCallback } from 'react'
import { uploadVideo } from './services/api'
import { DashboardShell } from './components/dashboard/DashboardShell'
import { SyntheticDashboard } from './components/dashboard/SyntheticDashboard'
import './App.css'

function App() {
  const [mode, setMode] = useState('SYNTHETIC') // REAL | SYNTHETIC
  const [upload, setUpload] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState(null)

  const handleUpload = useCallback(async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setError(null)
    setUploadProgress(0)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const result = await uploadVideo(formData, setUploadProgress)
      setUpload(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setUploading(false)
    }
  }, [])

  const resetUpload = useCallback(() => {
    setUpload(null)
    setError(null)
    setUploadProgress(0)
  }, [])

  return (
    <div className="crowd-shield-app">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo-mark">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <circle cx="14" cy="14" r="12" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.5"/>
              <circle cx="14" cy="14" r="6" fill="currentColor" opacity="0.8"/>
              <path d="M14 2 L14 6 M14 22 L14 26 M2 14 L6 14 M22 14 L26 14" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
          </div>
          <div>
            <h1>CROWD-SHIELD</h1>
            <p className="subtitle">Context-Aware Predictive Crowd Safety</p>
          </div>
        </div>
        <div className="header-right">
          <span className="status-dot online" /> SYSTEM ONLINE
        </div>
      </header>

      {/* Mode Toggle */}
      <nav className="mode-toggle-bar">
        <span className="toggle-label">ANALYSIS MODE</span>
        <div className="mode-toggle">
          <button
            className={`mode-btn ${mode === 'REAL' ? 'active real' : ''}`}
            onClick={() => setMode('REAL')}
          >
            <span className="mode-icon">📹</span>
            REAL VIDEO
          </button>
          <button
            className={`mode-btn ${mode === 'SYNTHETIC' ? 'active synthetic' : ''}`}
            onClick={() => setMode('SYNTHETIC')}
          >
            <span className="mode-icon">📊</span>
            DATA FROM UPLOADED VIDEOS
          </button>
        </div>
      </nav>

      {/* Content */}
      <main className="app-main">
        {mode === 'SYNTHETIC' ? (
          <SyntheticDashboard />
        ) : (
          <>
            {upload ? (
              <DashboardShell upload={upload} onReset={resetUpload} />
            ) : (
              <section className="glass-panel upload-panel multi-upload">
                <div className="upload-header-copy">
                  <h2>PERCEPTION MEDIA UPLOAD</h2>
                  <p>Select a video or image for YOLO anonymous person detection and crowd safety risk analysis</p>
                </div>

                <div className="upload-zones-grid">
                  {/* Video Upload Area */}
                  <div className="upload-zone-card">
                    <div className="upload-icon">📹</div>
                    <h3>UPLOAD CROWD VIDEO</h3>
                    <p>Recorded video footage for timeline & optical flow analysis</p>
                    <span className="upload-note">MP4, WebM, MOV · Max 1GB</span>

                    <label className="upload-button primary-action">
                      {uploading ? `UPLOADING... ${uploadProgress}%` : 'SELECT VIDEO FILE'}
                      <input
                        type="file"
                        accept="video/mp4,video/webm,video/quicktime"
                        onChange={handleUpload}
                        disabled={uploading}
                        hidden
                      />
                    </label>
                  </div>

                  {/* Image Upload Area */}
                  <div className="upload-zone-card image-zone">
                    <div className="upload-icon">🖼️</div>
                    <h3>UPLOAD CROWD IMAGE</h3>
                    <p>Crowd photo for instant YOLO person detection & risk evaluation</p>
                    <span className="upload-note">JPG, PNG, WebP, BMP · Max 1GB</span>

                    <label className="upload-button primary-action image-action">
                      {uploading ? `UPLOADING... ${uploadProgress}%` : 'SELECT IMAGE FILE'}
                      <input
                        type="file"
                        accept="image/jpeg,image/png,image/webp,image/bmp"
                        onChange={handleUpload}
                        disabled={uploading}
                        hidden
                      />
                    </label>
                  </div>
                </div>

                {uploading && <progress max="100" value={uploadProgress} className="upload-progress-bar" />}
                {error && <p className="error-message" role="alert">{error}</p>}

                <div className="real-mode-info">
                  <p className="panel-title">YOLO PERCEPTION PIPELINE</p>
                  <div className="pipeline-steps">
                    <span>Uploaded Media (Video / Image)</span>
                    <span className="arrow">→</span>
                    <span>YOLOv8n Person Detection</span>
                    <span className="arrow">→</span>
                    <span>Centroid Coordinates</span>
                    <span className="arrow">→</span>
                    <span>Crowd Risk Engine</span>
                    <span className="arrow">→</span>
                    <span>What-If Interventions</span>
                  </div>
                </div>
              </section>
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Sense → Predict → Simulate → Recommend → Protect</p>
      </footer>
    </div>
  )
}

export default App
