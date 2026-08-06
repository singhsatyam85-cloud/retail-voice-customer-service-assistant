import { afterEach, describe, expect, it, vi } from "vitest";
import { startVoiceSession, uploadVoiceSessionAudio, VoiceSupportApiError } from "./voiceSupportApi";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("voiceSupportApi", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("starts a session with only an Authorization header and no request body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        session_id: "VOICE-abc",
        status: "started",
        customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
        recent_orders: [],
        created_at: new Date().toISOString(),
      }),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await startVoiceSession();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBeUndefined();
    const headers = init.headers as Record<string, string>;
    expect(headers.Authorization).toMatch(/^Bearer /);
    expect(JSON.stringify(init)).not.toContain("customer_id");
  });

  it("uploads audio as multipart form data with no customer_id field", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        session_id: "VOICE-abc",
        status: "transcribed",
        transcript: "hello",
        detected_language: "en",
        customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      }),
    );
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const blob = new Blob(["fake-audio"], { type: "audio/webm" });
    await uploadVoiceSessionAudio("VOICE-abc", blob);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/voice-support/sessions/VOICE-abc/audio");
    expect(init.body).toBeInstanceOf(FormData);

    const formData = init.body as FormData;
    expect(formData.get("customer_id")).toBeNull();
    expect(formData.get("audio")).not.toBeNull();
  });

  it("raises VoiceSupportApiError with the server's detail message on failure", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "Voice support session not found." }, 404));
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    await expect(
      uploadVoiceSessionAudio("VOICE-missing", new Blob(["x"])),
    ).rejects.toBeInstanceOf(VoiceSupportApiError);
  });
});
