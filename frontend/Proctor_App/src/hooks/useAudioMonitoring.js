import { useState, useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook to manage persistent microphone access during the test.
 */
export const useAudioMonitoring = () => {
  const [isAudioActive, setIsAudioActive] = useState(false);
  const [audioError, setAudioError] = useState(null);
  const streamRef = useRef(null);

  const startAudio = useCallback(async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });

      streamRef.current = stream;
      setIsAudioActive(true);
      setAudioError(null);
      console.log("Microphone monitoring activated successfully.");

      // Ensure the stream stays active even if not attached to a UI element
      // This prevents some browsers from putting the track to sleep
      stream.getAudioTracks().forEach(track => {
        track.enabled = true;
      });

      return { success: true, stream };
    } catch (err) {
      const msg = "Microphone access denied. Please enable your mic to continue.";
      setAudioError(msg);
      setIsAudioActive(false);
      console.error("Audio Monitoring Error:", err);
      return { success: false, error: msg };
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
      setIsAudioActive(false);
      console.log("Microphone monitoring stopped.");
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => stopAudio();
  }, [stopAudio]);

  return {
    isAudioActive,
    audioError,
    startAudio,
    stopAudio
  };
};