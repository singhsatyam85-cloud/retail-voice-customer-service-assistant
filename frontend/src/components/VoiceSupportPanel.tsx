import { useEffect, useRef, useState } from "react";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import {
  startVoiceSession,
  uploadVoiceSessionAudio,
  VoiceSupportApiError,
  type RecentOrder,
} from "../services/voiceSupportApi";
import "./VoiceSupportPanel.css";

type PanelPhase =
  | "opening"
  | "ready"
  | "requesting-microphone"
  | "recording"
  | "stopping"
  | "uploading"
  | "transcribed"
  | "permission-denied"
  | "unsupported-browser"
  | "backend-error";

type ErrorContext = "session" | "upload" | null;

interface VoiceSupportPanelProps {
  onClose: () => void;
}

function describeError(error: unknown): string {
  if (error instanceof VoiceSupportApiError) {
    return error.message;
  }
  return "We could not reach AI Voice Support. Please try again.";
}

export function VoiceSupportPanel({ onClose }: VoiceSupportPanelProps) {
  const [phase, setPhase] = useState<PanelPhase>("opening");
  const [firstName, setFirstName] = useState("");
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [transcript, setTranscript] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorContext, setErrorContext] = useState<ErrorContext>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [retryToken, setRetryToken] = useState(0);

  const recorder = useVoiceRecorder();
  const timerRef = useRef<number | null>(null);

  // Start (or restart, on retry) the voice-support session.
  useEffect(() => {
    let cancelled = false;
    setPhase("opening");
    setErrorMessage(null);
    setErrorContext(null);

    startVoiceSession()
      .then((session) => {
        if (cancelled) return;
        setFirstName(session.customer.full_name.split(" ")[0] || session.customer.full_name);
        setRecentOrders(session.recent_orders);
        setSessionId(session.session_id);
        setPhase("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setErrorMessage(describeError(error));
        setErrorContext("session");
        setPhase("backend-error");
      });

    return () => {
      cancelled = true;
    };
  }, [retryToken]);

  // Recording timer, only while actively recording.
  useEffect(() => {
    if (phase !== "recording") {
      return;
    }
    setElapsedSeconds(0);
    const intervalId = window.setInterval(() => {
      setElapsedSeconds((seconds) => seconds + 1);
    }, 1000);
    timerRef.current = intervalId;
    return () => {
      window.clearInterval(intervalId);
    };
  }, [phase]);

  // Reflect recorder-hook status into the panel's own phase.
  useEffect(() => {
    if (recorder.status === "recording") {
      setPhase("recording");
    } else if (recorder.status === "permission-denied") {
      setErrorMessage(recorder.errorMessage);
      setPhase("permission-denied");
    } else if (recorder.status === "unsupported") {
      setErrorMessage(recorder.errorMessage);
      setPhase("unsupported-browser");
    }
  }, [recorder.status, recorder.errorMessage]);

  // Release the microphone if the panel unmounts mid-recording.
  useEffect(() => {
    return () => {
      void recorder.stopRecording();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleStartSpeaking() {
    setErrorMessage(null);
    setPhase("requesting-microphone");
    await recorder.startRecording();
  }

  async function handleStop() {
    if (!sessionId) return;
    setPhase("stopping");
    const blob = await recorder.stopRecording();

    if (!blob || blob.size === 0) {
      setErrorMessage("No audio was captured. Please try again.");
      setPhase("ready");
      return;
    }

    setPhase("uploading");
    try {
      const result = await uploadVoiceSessionAudio(sessionId, blob);
      setTranscript(result.transcript);
      setPhase("transcribed");
    } catch (error) {
      setErrorMessage(describeError(error));
      setErrorContext("upload");
      setPhase("backend-error");
    }
  }

  function handleRecordAgain() {
    setTranscript(null);
    setErrorMessage(null);
    setPhase("ready");
  }

  function handleRetry() {
    setErrorMessage(null);
    if (errorContext === "session") {
      setRetryToken((token) => token + 1);
    } else {
      setErrorContext(null);
      setPhase("ready");
    }
  }

  const showOrders = phase !== "opening" && phase !== "backend-error";

  return (
    <div className="voice-support-panel" role="dialog" aria-modal="true" aria-label="AI Voice Support">
      <div className="voice-support-panel__header">
        <h2>AI Voice Support</h2>
        <button
          type="button"
          className="voice-support-panel__close"
          aria-label="Close AI Voice Support"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      <div className="voice-support-panel__body">
        {phase === "opening" && <p role="status">Starting your support session…</p>}

        {showOrders && firstName && (
          <p className="voice-support-panel__greeting">Hi {firstName}, how can we help?</p>
        )}

        {showOrders && recentOrders.length > 0 && (
          <ul className="voice-support-panel__orders">
            {recentOrders.map((order) => (
              <li key={order.order_id}>
                {order.order_id} — {order.status} ({order.currency_code} {order.total_amount})
              </li>
            ))}
          </ul>
        )}

        {showOrders && recentOrders.length === 0 && (
          <p className="voice-support-panel__no-orders">You have no recent orders.</p>
        )}

        {(phase === "ready" || phase === "requesting-microphone") && (
          <button
            type="button"
            className="voice-support-panel__action"
            onClick={handleStartSpeaking}
            disabled={phase === "requesting-microphone"}
          >
            Start speaking
          </button>
        )}

        {phase === "requesting-microphone" && <p role="status">Requesting microphone access…</p>}

        {phase === "recording" && (
          <div className="voice-support-panel__recording" role="status">
            <span className="voice-support-panel__recording-dot" aria-hidden="true" />
            <span>Recording… {elapsedSeconds}s</span>
            <button type="button" className="voice-support-panel__action" onClick={handleStop}>
              Stop
            </button>
          </div>
        )}

        {phase === "stopping" && <p role="status">Stopping recording…</p>}
        {phase === "uploading" && <p role="status">Uploading your recording…</p>}

        {phase === "transcribed" && (
          <div className="voice-support-panel__transcript">
            <h3>Transcript</h3>
            <p>{transcript}</p>
            <div className="voice-support-panel__transcript-actions">
              <button type="button" onClick={handleRecordAgain}>
                Record again
              </button>
              <button type="button" onClick={onClose}>
                Keep transcript and close
              </button>
            </div>
          </div>
        )}

        {phase === "permission-denied" && (
          <div className="voice-support-panel__error" role="alert">
            <p>{errorMessage ?? "Microphone permission was denied."}</p>
            <p>Please allow microphone access in your browser settings, then try again.</p>
            <button type="button" onClick={handleRecordAgain}>
              Try again
            </button>
          </div>
        )}

        {phase === "unsupported-browser" && (
          <div className="voice-support-panel__error" role="alert">
            <p>{errorMessage ?? "This browser does not support in-browser voice recording."}</p>
            <p>Please try a recent version of Chrome, Edge, Firefox, or Safari.</p>
          </div>
        )}

        {phase === "backend-error" && (
          <div className="voice-support-panel__error" role="alert">
            <p>{errorMessage ?? "Something went wrong. Please try again."}</p>
            <button type="button" onClick={handleRetry}>
              Retry
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
