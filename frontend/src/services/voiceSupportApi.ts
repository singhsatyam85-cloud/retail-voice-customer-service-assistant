// Thin client for the in-app voice-support backend. Never sends
// customer_id in a request body -- identity comes only from the
// Authorization header, which stands in for the retailer app's real
// session/auth once this component is embedded there.

export interface CustomerSummary {
  customer_id: string;
  full_name: string;
}

export interface RecentOrderItem {
  product_name: string;
  quantity: number;
}

export interface RecentOrder {
  order_id: string;
  status: string;
  total_amount: string;
  currency_code: string;
  items: RecentOrderItem[];
}

export interface VoiceSessionStart {
  session_id: string;
  status: string;
  customer: CustomerSummary;
  recent_orders: RecentOrder[];
  created_at: string;
}

export interface VoiceSessionAudioResult {
  session_id: string;
  status: string;
  transcript: string | null;
  detected_language: string | null;
  customer: CustomerSummary;
}

export class VoiceSupportApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "VoiceSupportApiError";
  }
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const DEMO_AUTH_TOKEN: string = import.meta.env.VITE_DEMO_AUTH_TOKEN ?? "";

function authHeaders(): HeadersInit {
  return { Authorization: `Bearer ${DEMO_AUTH_TOKEN}` };
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // Response body was not JSON -- fall back to a generic message.
  }
  return `Request failed with status ${response.status}.`;
}

export async function startVoiceSession(): Promise<VoiceSessionStart> {
  const response = await fetch(`${API_BASE_URL}/api/v1/voice-support/sessions`, {
    method: "POST",
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw new VoiceSupportApiError(response.status, await readErrorMessage(response));
  }

  return (await response.json()) as VoiceSessionStart;
}

export async function uploadVoiceSessionAudio(
  sessionId: string,
  audioBlob: Blob,
): Promise<VoiceSessionAudioResult> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "voice-support.webm");

  const response = await fetch(`${API_BASE_URL}/api/v1/voice-support/sessions/${sessionId}/audio`, {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });

  if (!response.ok) {
    throw new VoiceSupportApiError(response.status, await readErrorMessage(response));
  }

  return (await response.json()) as VoiceSessionAudioResult;
}
