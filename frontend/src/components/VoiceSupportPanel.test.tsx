import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "../services/voiceSupportApi";
import { installMediaMocks, removeMediaRecorderSupport } from "../test/mediaMocks";
import { VoiceSupportPanel } from "./VoiceSupportPanel";

vi.mock("../services/voiceSupportApi", async () => {
  const actual =
    await vi.importActual<typeof import("../services/voiceSupportApi")>(
      "../services/voiceSupportApi",
    );
  return {
    ...actual,
    startVoiceSession: vi.fn(),
    uploadVoiceSessionAudio: vi.fn(),
  };
});

const SESSION_RESPONSE = {
  session_id: "VOICE-test-session",
  status: "started",
  customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
  recent_orders: [
    {
      order_id: "ORD-5001",
      status: "delayed",
      total_amount: "24.99",
      currency_code: "GBP",
      items: [{ product_name: "Wireless Headphones", quantity: 1 }],
    },
  ],
  created_at: new Date().toISOString(),
};

async function renderReadyPanel() {
  vi.mocked(api.startVoiceSession).mockResolvedValue(SESSION_RESPONSE);
  render(<VoiceSupportPanel onClose={vi.fn()} />);
  await screen.findByRole("button", { name: /start speaking/i });
}

describe("VoiceSupportPanel", () => {
  beforeEach(() => {
    vi.mocked(api.startVoiceSession).mockReset();
    vi.mocked(api.uploadVoiceSessionAudio).mockReset();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("shows the customer's first name and their recent orders once the session starts", async () => {
    await renderReadyPanel();

    expect(screen.getByText(/hi test, how can we help/i)).toBeInTheDocument();
    expect(screen.getByText(/ORD-5001/)).toBeInTheDocument();
  });

  it("does not display the full demo auth token anywhere in the UI", async () => {
    vi.stubEnv("VITE_DEMO_AUTH_TOKEN", "demo-cust-101");
    await renderReadyPanel();

    expect(document.body.textContent).not.toContain("demo-cust-101");
  });

  it("shows a controlled message when the browser does not support recording", async () => {
    removeMediaRecorderSupport();
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));

    expect(
      await screen.findByText(/does not support in-browser (audio|voice) recording/i),
    ).toBeInTheDocument();
  });

  it("shows a controlled message when microphone permission is denied", async () => {
    const { getUserMedia } = installMediaMocks();
    getUserMedia.mockRejectedValue(new DOMException("denied", "NotAllowedError"));
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));

    expect(await screen.findByText(/microphone permission was denied/i)).toBeInTheDocument();
  });

  it("displays a recording indicator while recording", async () => {
    installMediaMocks();
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));

    expect(await screen.findByText(/recording…/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^stop$/i })).toBeInTheDocument();
  });

  it("releases the microphone track when recording is stopped", async () => {
    const { track } = installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My wireless headphones have not arrived.",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    await waitFor(() => expect(track.stop).toHaveBeenCalled());
  });

  it("displays the transcript after a successful upload", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My wireless headphones have not arrived.",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(
      await screen.findByText(/my wireless headphones have not arrived/i),
    ).toBeInTheDocument();
  });

  it("returns to a usable state when the customer retries after a session-start failure", async () => {
    vi.mocked(api.startVoiceSession)
      .mockRejectedValueOnce(new api.VoiceSupportApiError(503, "Service unavailable."))
      .mockResolvedValueOnce(SESSION_RESPONSE);

    const user = userEvent.setup();
    render(<VoiceSupportPanel onClose={vi.fn()} />);

    expect(await screen.findByRole("alert")).toHaveTextContent(/service unavailable/i);
    await user.click(screen.getByRole("button", { name: /retry/i }));

    expect(await screen.findByRole("button", { name: /start speaking/i })).toBeInTheDocument();
    expect(api.startVoiceSession).toHaveBeenCalledTimes(2);
  });
});
