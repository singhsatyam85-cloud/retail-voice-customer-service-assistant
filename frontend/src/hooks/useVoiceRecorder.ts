import { useCallback, useRef, useState } from "react";

export type RecorderStatus =
  | "idle"
  | "requesting-permission"
  | "recording"
  | "stopping"
  | "permission-denied"
  | "unsupported";

interface UseVoiceRecorderResult {
  status: RecorderStatus;
  errorMessage: string | null;
  isSupported: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
}

function isRecordingSupported(): boolean {
  return (
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof window !== "undefined" &&
    typeof window.MediaRecorder === "function"
  );
}

export function useVoiceRecorder(): UseVoiceRecorderResult {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const releaseStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    if (!isRecordingSupported()) {
      setStatus("unsupported");
      setErrorMessage("This browser does not support in-browser audio recording.");
      return;
    }

    setStatus("requesting-permission");
    setErrorMessage(null);

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setStatus("permission-denied");
      setErrorMessage("Microphone permission was denied.");
      return;
    }

    streamRef.current = stream;
    chunksRef.current = [];

    const recorder = new MediaRecorder(stream);
    recorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    recorder.onerror = () => {
      setErrorMessage("Recording failed unexpectedly.");
      setStatus("unsupported");
      releaseStream();
    };

    mediaRecorderRef.current = recorder;
    recorder.start();
    setStatus("recording");
  }, [releaseStream]);

  const stopRecording = useCallback((): Promise<Blob | null> => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      releaseStream();
      setStatus("idle");
      return Promise.resolve(null);
    }

    setStatus("stopping");

    return new Promise((resolve) => {
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        chunksRef.current = [];
        releaseStream();
        setStatus("idle");
        resolve(blob);
      };
      recorder.stop();
    });
  }, [releaseStream]);

  return {
    status,
    errorMessage,
    isSupported: isRecordingSupported(),
    startRecording,
    stopRecording,
  };
}
