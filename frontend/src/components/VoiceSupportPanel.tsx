import { useEffect, useRef, useState } from "react";
import { useVoiceRecorder } from "../hooks/useVoiceRecorder";
import {
  startVoiceSession,
  uploadVoiceSessionAudio,
  VoiceSupportApiError,
  createVoiceSupportCase,
  type RecentOrder,
  type SupportCase,
  type ConversationTurn,
} from "../services/voiceSupportApi";
import { VoiceOrbDNA } from "./VoiceOrbDNA";
import "./VoiceSupportPanel.css";

type PanelPhase =
  | "opening"
  | "ready"
  | "requesting-microphone"
  | "recording"
  | "stopping"
  | "uploading"
  | "transcribed"
  | "submitting"
  | "submitted"
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
  const [intentCategory, setIntentCategory] = useState<string | null>(null);
  const [assistantReply, setAssistantReply] = useState<string | null>(null);
  const [conversationHistory, setConversationHistory] = useState<ConversationTurn[]>([]);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [errorContext, setErrorContext] = useState<ErrorContext>(null);
  const [idempotencyKey, setIdempotencyKey] = useState<string | null>(null);
  const [createdCase, setCreatedCase] = useState<SupportCase | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [retryToken, setRetryToken] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const recorder = useVoiceRecorder();
  const timerRef = useRef<number | null>(null);

  // SpeechSynthesis helpers
  function speakText(text: string) {
    if (typeof window === "undefined" || !("speechSynthesis" in window) || isMuted || !text) {
      return;
    }
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    } catch {
      setIsSpeaking(false);
    }
  }

  function handleReplaySpeech() {
    if (assistantReply) {
      speakText(assistantReply);
    }
  }

  function handleStopSpeech() {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }

  function handleToggleMute() {
    setIsMuted((prev) => {
      const next = !prev;
      if (next && typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      }
      return next;
    });
  }

  // Cleanup speech on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

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
        setTranscript(null);
        setIntentCategory(null);
        setAssistantReply(null);
        setConversationHistory([]);
        setSelectedOrderId(null);
        setIdempotencyKey(null);
        setSubmissionError(null);
        setCreatedCase(null);
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
    handleStopSpeech();
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
      setIntentCategory(result.intent_category);
      setAssistantReply(result.assistant_reply || null);
      if (result.conversation_history) {
        setConversationHistory(result.conversation_history);
      }

      if (result.suggested_order_id && result.intent_category !== "needs_clarification") {
        setSelectedOrderId(result.suggested_order_id);
      } else if (recentOrders.length === 1 && result.intent_category !== "needs_clarification") {
        setSelectedOrderId(recentOrders[0].order_id);
      } else {
        setSelectedOrderId(null);
      }

      if (result.intent_category !== "needs_clarification") {
        setIdempotencyKey(self.crypto.randomUUID());
      }
      setPhase("transcribed");

      if (result.assistant_reply && !isMuted) {
        speakText(result.assistant_reply);
      }
    } catch (error) {
      setErrorMessage(describeError(error));
      setErrorContext("upload");
      setPhase("backend-error");
    }
  }

  function handleRecordAgain() {
    handleStopSpeech();
    setTranscript(null);
    setIntentCategory(null);
    setAssistantReply(null);
    setSelectedOrderId(null);
    setIdempotencyKey(null);
    setSubmissionError(null);
    setCreatedCase(null);
    setErrorMessage(null);
    setPhase("ready");
  }

  async function handleConfirmCase() {
    if (!sessionId || !intentCategory || !idempotencyKey) return;

    handleStopSpeech();
    const isHumanAgent = intentCategory === "human_agent_request";
    const orderId = selectedOrderId === "none" ? null : selectedOrderId;

    if (!isHumanAgent && !orderId) {
      setSubmissionError("An order must be selected for this request.");
      return;
    }

    setIsSubmitting(true);
    setSubmissionError(null);

    try {
      const caseResult = await createVoiceSupportCase(sessionId, {
        category: intentCategory,
        order_id: orderId,
        summary: transcript || assistantReply || "",
        idempotency_key: idempotencyKey,
      });
      setCreatedCase(caseResult);
      setPhase("submitted");
    } catch (error: unknown) {
      setSubmissionError(describeError(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleRetry() {
    handleStopSpeech();
    setErrorMessage(null);
    if (errorContext === "session") {
      setRetryToken((token) => token + 1);
    } else {
      setErrorContext(null);
      setPhase("ready");
    }
  }

  const showOrders = phase !== "opening" && phase !== "backend-error";

  let orbState: "idle" | "listening" | "speaking" | "processing" = "idle";
  if (phase === "recording") {
    orbState = "listening";
  } else if (phase === "uploading" || phase === "stopping" || phase === "submitting" || phase === "requesting-microphone") {
    orbState = "processing";
  } else if (isSpeaking || phase === "transcribed" || phase === "submitted") {
    orbState = "speaking";
  }

  return (
    <div className="voice-support-panel" role="dialog" aria-modal="true" aria-label="AI Voice Support">
      <div className="voice-support-panel__header">
        <h2>AI Voice Support</h2>
        <button
          type="button"
          className="voice-support-panel__close"
          aria-label="Close AI Voice Support"
          onClick={() => {
            handleStopSpeech();
            onClose();
          }}
        >
          Close
        </button>
      </div>

      <div className="voice-support-panel__body">
        {phase === "opening" && <p role="status">Starting your support session…</p>}

        {showOrders && <VoiceOrbDNA state={orbState} />}

        {showOrders && (
          <div className="voice-support-panel__audio-controls">
            <button type="button" onClick={handleToggleMute}>
              {isMuted ? "Unmute Voice" : "Mute Voice"}
            </button>
            {assistantReply && (
              <>
                <button type="button" onClick={handleReplaySpeech} disabled={isSpeaking}>
                  Replay Audio
                </button>
                {isSpeaking && (
                  <button type="button" onClick={handleStopSpeech}>
                    Stop Audio
                  </button>
                )}
              </>
            )}
          </div>
        )}

        {showOrders && firstName && (
          <p className="voice-support-panel__greeting">Hi {firstName}, how can we help?</p>
        )}

        {showOrders && conversationHistory.length > 0 && (
          <div className="voice-support-panel__history" aria-label="Conversation History">
            {conversationHistory.map((turn, i) => (
              <div key={i} className={`voice-support-panel__turn voice-support-panel__turn--${turn.role}`}>
                <strong>{turn.role === "user" ? "You" : "Assistant"}:</strong> {turn.content}
              </div>
            ))}
          </div>
        )}

        {showOrders && recentOrders.length > 0 && conversationHistory.length === 0 && (
          <ul className="voice-support-panel__orders">
            {recentOrders.map((order) => (
              <li key={order.order_id}>
                {order.order_id} — {order.status} ({order.currency_code} {order.total_amount})
              </li>
            ))}
          </ul>
        )}

        {showOrders && recentOrders.length === 0 && conversationHistory.length === 0 && (
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
        {phase === "uploading" && <p role="status">Processing conversation with local AI…</p>}

        {phase === "transcribed" && (
          <div className="voice-support-panel__transcript">
            {assistantReply && (
              <div className="voice-support-panel__reply">
                <strong>Assistant:</strong> {assistantReply}
              </div>
            )}

            <h3>Your Input</h3>
            <p>{transcript}</p>

            {intentCategory === "needs_clarification" ? (
              <div className="voice-support-panel__draft">
                <p>We're not sure how to classify this request. Please provide more details or ask to speak to an agent.</p>
              </div>
            ) : (
              <div className="voice-support-panel__draft">
                <h3>Case Draft</h3>
                <p><strong>Category:</strong> {intentCategory}</p>
                <p><strong>Summary:</strong> {transcript}</p>

                <div className="voice-support-panel__order-selection">
                  <label htmlFor="order-select"><strong>Order:</strong></label>
                  <select
                    id="order-select"
                    value={selectedOrderId || ""}
                    onChange={(e) => setSelectedOrderId(e.target.value)}
                  >
                    <option value="">-- Select an order --</option>
                    {recentOrders.map(o => (
                      <option key={o.order_id} value={o.order_id}>{o.order_id}</option>
                    ))}
                    {intentCategory === "human_agent_request" && (
                      <option value="none">No order (General question)</option>
                    )}
                  </select>
                </div>

                <p className="voice-support-panel__notice">
                  <em>Note: Returns, refunds, and cancellations are subject to human review.</em>
                </p>
              </div>
            )}

            {submissionError && (
              <div className="voice-support-panel__error" role="alert">
                <p>{submissionError}</p>
              </div>
            )}

            <div className="voice-support-panel__transcript-actions">
              <button type="button" onClick={handleRecordAgain} disabled={isSubmitting}>
                Record again
              </button>
              {intentCategory !== "needs_clarification" && (
                <button
                  type="button"
                  disabled={isSubmitting || (!selectedOrderId && intentCategory !== "human_agent_request")}
                  onClick={handleConfirmCase}
                >
                  {isSubmitting ? "Confirming..." : "Confirm and Create Case"}
                </button>
              )}
              <button type="button" onClick={onClose} disabled={isSubmitting}>
                Cancel
              </button>
            </div>
          </div>
        )}

        {phase === "submitted" && createdCase && (
          <div className="voice-support-panel__submitted">
            <h3>Case Created Successfully</h3>
            <p><strong>Case ID:</strong> {createdCase.case_id}</p>
            <p><strong>Status:</strong> {createdCase.status}</p>
            <p><strong>Category:</strong> {createdCase.category}</p>
            {createdCase.order_id && createdCase.order_id !== "none" && (
              <p><strong>Order ID:</strong> {createdCase.order_id}</p>
            )}
            <p><strong>Summary:</strong> {createdCase.summary}</p>
            <p className="voice-support-panel__notice">
              <em>Note: Returns, refunds, and cancellations are subject to human review.</em>
            </p>
            <button
              type="button"
              className="voice-support-panel__action"
              onClick={() => {
                handleStopSpeech();
                onClose();
              }}
            >
              Close
            </button>
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
