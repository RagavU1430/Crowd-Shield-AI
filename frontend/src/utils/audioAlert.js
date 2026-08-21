/**
 * Web Audio API Continuous Emergency Alert Engine for CROWD-SHIELD.
 * Loops a high-urgency emergency warning chime until explicitly muted or reported.
 */

let alertInterval = null;
let audioCtx = null;

export function startContinuousCriticalBeep() {
  // If already playing, don't create duplicate loops
  if (alertInterval) return;

  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    audioCtx = new AudioCtx();

    const playPulse = () => {
      if (!audioCtx || audioCtx.state === "closed") return;
      const now = audioCtx.currentTime;

      // Pulse 1: 880 Hz High Alert
      const osc1 = audioCtx.createOscillator();
      const gain1 = audioCtx.createGain();
      osc1.type = "sawtooth";
      osc1.frequency.setValueAtTime(880, now);
      gain1.gain.setValueAtTime(0.22, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.14);
      osc1.connect(gain1);
      gain1.connect(audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.14);

      // Pulse 2: 1046 Hz Urgent Chime
      const osc2 = audioCtx.createOscillator();
      const gain2 = audioCtx.createGain();
      osc2.type = "sawtooth";
      osc2.frequency.setValueAtTime(1046, now + 0.16);
      gain2.gain.setValueAtTime(0.28, now + 0.16);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.32);
      osc2.connect(gain2);
      gain2.connect(audioCtx.destination);
      osc2.start(now + 0.16);
      osc2.stop(now + 0.32);
    };

    playPulse();
    alertInterval = setInterval(playPulse, 450);
  } catch (e) {
    console.error("Audio Context Error:", e);
  }
}

export function stopContinuousCriticalBeep() {
  if (alertInterval) {
    clearInterval(alertInterval);
    alertInterval = null;
  }
  if (audioCtx) {
    try {
      audioCtx.close();
    } catch (e) {}
    audioCtx = null;
  }
}

export const playCriticalBeep = startContinuousCriticalBeep;
