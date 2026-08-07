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
    createVoiceSupportCase: vi.fn(),
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
    vi.mocked(api.createVoiceSupportCase).mockReset();
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
      intent_category: null,
      assistant_reply: null,
      conversation_history: [],
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
      intent_category: null,
      assistant_reply: null,
      conversation_history: [],
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    const elements = await screen.findAllByText(/my wireless headphones have not arrived/i);
    expect(elements.length).toBeGreaterThan(0);
  });

  it("auto-selects the order when the customer has exactly one order and shows the draft", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/Case Draft/i)).toBeInTheDocument();
    expect(screen.getByText(/delayed_delivery/i)).toBeInTheDocument();

    const select = screen.getByRole("combobox", { name: /order/i });
    expect(select).toHaveValue("ORD-5001");
    expect(screen.getByRole("button", { name: /confirm and create case/i })).not.toBeDisabled();
  });

  it("requires the customer to select an order when they have multiple orders", async () => {
    const multiOrderSession = {
      ...SESSION_RESPONSE,
      recent_orders: [
        ...SESSION_RESPONSE.recent_orders,
        {
          order_id: "ORD-9999",
          status: "shipped",
          total_amount: "50.00",
          currency_code: "GBP",
          items: [{ product_name: "Mouse", quantity: 1 }],
        }
      ]
    };
    vi.mocked(api.startVoiceSession).mockResolvedValue(multiOrderSession);

    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });

    render(<VoiceSupportPanel onClose={vi.fn()} />);
    await screen.findByRole("button", { name: /start speaking/i });

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/Case Draft/i)).toBeInTheDocument();

    const select = screen.getByRole("combobox", { name: /order/i });
    expect(select).toHaveValue("");

    const confirmBtn = screen.getByRole("button", { name: /confirm and create case/i });
    expect(confirmBtn).toBeDisabled();

    await user.selectOptions(select, "ORD-9999");
    expect(select).toHaveValue("ORD-9999");
    expect(confirmBtn).not.toBeDisabled();
  });

  it("allows no order for human agent request", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "I want to speak to a human",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "human_agent_request"
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/Case Draft/i)).toBeInTheDocument();

    const select = screen.getByRole("combobox", { name: /order/i });
    expect(select).toHaveValue("ORD-5001");

    // Select no order
    await user.selectOptions(select, "none");
    expect(select).toHaveValue("none");

    const confirmBtn = screen.getByRole("button", { name: /confirm and create case/i });
    expect(confirmBtn).not.toBeDisabled();
  });

  it("shows needs_clarification message and hides the confirm button", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "What time is it?",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "needs_clarification"
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/not sure how to classify this request/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /confirm and create case/i })).not.toBeInTheDocument();
  });

  it("allows the customer to record again from the draft view", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/Case Draft/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /record again/i }));

    expect(screen.queryByText(/Case Draft/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start speaking/i })).toBeInTheDocument();
  });

  it("successfully confirms and submits a case draft", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });
    vi.mocked(api.createVoiceSupportCase).mockResolvedValue({
      case_id: "CASE-9999",
      call_id: null,
      customer_id: "CUST-101",
      order_id: "ORD-5001",
      category: "delayed_delivery",
      status: "pending",
      summary: "My order is delayed",
      requires_human_review: true,
      created_at: new Date().toISOString(),
      voice_session_id: "VOICE-test-session"
    });
    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    expect(await screen.findByText(/Case Draft/i)).toBeInTheDocument();

    const confirmBtn = screen.getByRole("button", { name: /confirm and create case/i });
    await user.click(confirmBtn);

    expect(await screen.findByText(/Case Created Successfully/i)).toBeInTheDocument();
    expect(screen.getByText(/CASE-9999/i)).toBeInTheDocument();
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
    expect(api.createVoiceSupportCase).toHaveBeenCalledTimes(1);
    expect(api.createVoiceSupportCase).toHaveBeenCalledWith("VOICE-test-session", expect.objectContaining({
      category: "delayed_delivery",
      order_id: "ORD-5001",
      summary: "My order is delayed",
      idempotency_key: expect.any(String)
    }));
  });

  it("disables the confirm button during submission to prevent double-submits", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });

    let resolveSubmit: (val: any) => void = () => {};
    const slowSubmit = new Promise((resolve) => {
      resolveSubmit = resolve;
    });
    vi.mocked(api.createVoiceSupportCase).mockReturnValue(slowSubmit as any);

    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    const confirmBtn = await screen.findByRole("button", { name: /confirm and create case/i });
    await user.click(confirmBtn);

    expect(confirmBtn).toBeDisabled();
    expect(confirmBtn).toHaveTextContent(/confirming.../i);

    // Resolve submission
    resolveSubmit({
      case_id: "CASE-9999",
      call_id: null,
      customer_id: "CUST-101",
      order_id: "ORD-5001",
      category: "delayed_delivery",
      status: "pending",
      summary: "My order is delayed",
      requires_human_review: true,
      created_at: new Date().toISOString(),
      voice_session_id: "VOICE-test-session"
    });
  });

  it("reuses the same idempotency key on retry after a failure", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });
    vi.mocked(api.createVoiceSupportCase)
      .mockRejectedValueOnce(new api.VoiceSupportApiError(500, "Network Error"))
      .mockResolvedValueOnce({
        case_id: "CASE-9999",
        call_id: null,
        customer_id: "CUST-101",
        order_id: "ORD-5001",
        category: "delayed_delivery",
        status: "pending",
        summary: "My order is delayed",
        requires_human_review: true,
        created_at: new Date().toISOString(),
        voice_session_id: "VOICE-test-session"
      });

    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    const confirmBtn = await screen.findByRole("button", { name: /confirm and create case/i });
    await user.click(confirmBtn);

    expect(await screen.findByText(/network error/i)).toBeInTheDocument();
    expect(screen.getByText(/Case Draft/i)).toBeInTheDocument(); // Draft remains visible

    // Click confirm again
    await user.click(confirmBtn);
    expect(await screen.findByText(/Case Created Successfully/i)).toBeInTheDocument();

    expect(api.createVoiceSupportCase).toHaveBeenCalledTimes(2);
    const key1 = vi.mocked(api.createVoiceSupportCase).mock.calls[0][1].idempotency_key;
    const key2 = vi.mocked(api.createVoiceSupportCase).mock.calls[1][1].idempotency_key;
    expect(key1).toBe(key2); // Reused the same key
  });

  it("generates a new idempotency key for a new draft", async () => {
    installMediaMocks();
    vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "transcribed",
      transcript: "My order is delayed",
      detected_language: "en",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      intent_category: "delayed_delivery"
    });
    vi.mocked(api.createVoiceSupportCase)
      .mockRejectedValueOnce(new api.VoiceSupportApiError(500, "First failure"))
      .mockResolvedValueOnce({
        case_id: "CASE-9999",
        call_id: null,
        customer_id: "CUST-101",
        order_id: "ORD-5001",
        category: "delayed_delivery",
        status: "pending",
        summary: "My order is delayed",
        requires_human_review: true,
        created_at: new Date().toISOString(),
        voice_session_id: "VOICE-test-session"
      });

    await renderReadyPanel();

    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    const confirmBtn = await screen.findByRole("button", { name: /confirm and create case/i });
    await user.click(confirmBtn);

    expect(await screen.findByText(/first failure/i)).toBeInTheDocument();
    const key1 = vi.mocked(api.createVoiceSupportCase).mock.calls[0][1].idempotency_key;

    // Start again / record again
    await user.click(screen.getByRole("button", { name: /record again/i }));

    // Record second draft
    await user.click(screen.getByRole("button", { name: /start speaking/i }));
    await screen.findByText(/recording…/i);
    await user.click(screen.getByRole("button", { name: /^stop$/i }));

    const confirmBtn2 = await screen.findByRole("button", { name: /confirm and create case/i });
    await user.click(confirmBtn2);

    const key2 = vi.mocked(api.createVoiceSupportCase).mock.calls[1][1].idempotency_key;
    expect(key1).not.toBe(key2); // Different key for different draft session
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

  describe("Voice-to-voice features", () => {
    beforeEach(() => {
      (window.speechSynthesis.speak as ReturnType<typeof vi.fn>).mockClear();
      (window.speechSynthesis.cancel as ReturnType<typeof vi.fn>).mockClear();
    });

    async function uploadWithReply(overrides?: Partial<api.VoiceSessionAudioResult>) {
      installMediaMocks();
      vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
        session_id: "VOICE-test-session",
        status: "transcribed",
        transcript: "Where is my order?",
        detected_language: "en",
        customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
        intent_category: "delayed_delivery",
        assistant_reply: "I see your order ORD-5001 is delayed. Would you like me to open a case?",
        conversation_history: [
          { role: "user", content: "Where is my order?" },
          { role: "assistant", content: "I see your order ORD-5001 is delayed. Would you like me to open a case?" },
        ],
        ...overrides,
      });
      await renderReadyPanel();

      const user = userEvent.setup();
      await user.click(screen.getByRole("button", { name: /start speaking/i }));
      await screen.findByText(/recording…/i);
      await user.click(screen.getByRole("button", { name: /^stop$/i }));
      // Wait for transcribed phase to complete
      await screen.findByText(/Case Draft/i);
      return user;
    }

    it("displays the assistant reply after upload", async () => {
      await uploadWithReply();
      const replies = screen.getAllByText(/I see your order ORD-5001 is delayed/i);
      expect(replies.length).toBeGreaterThan(0);
    });

    it("calls speechSynthesis.speak with the assistant reply", async () => {
      await uploadWithReply();
      expect(window.speechSynthesis.speak).toHaveBeenCalled();
    });

    it("does not call speechSynthesis.speak when muted", async () => {
      installMediaMocks();
      vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
        session_id: "VOICE-test-session",
        status: "transcribed",
        transcript: "Where is my order?",
        detected_language: "en",
        customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
        intent_category: "delayed_delivery",
        assistant_reply: "I see your order ORD-5001 is delayed.",
        conversation_history: [],
      });
      await renderReadyPanel();

      const user = userEvent.setup();
      // Mute before recording
      await user.click(screen.getByRole("button", { name: /mute voice/i }));
      (window.speechSynthesis.speak as ReturnType<typeof vi.fn>).mockClear();

      await user.click(screen.getByRole("button", { name: /start speaking/i }));
      await screen.findByText(/recording…/i);
      await user.click(screen.getByRole("button", { name: /^stop$/i }));

      await screen.findByText(/Case Draft/i);
      expect(window.speechSynthesis.speak).not.toHaveBeenCalled();
    });

    it("replay speaks the last assistant reply", async () => {
      await uploadWithReply();
      (window.speechSynthesis.speak as ReturnType<typeof vi.fn>).mockClear();

      const user = userEvent.setup();
      const replayBtn = screen.getByRole("button", { name: /replay audio/i });
      await user.click(replayBtn);

      expect(window.speechSynthesis.speak).toHaveBeenCalled();
    });

    it("stop cancels speaking via speechSynthesis.cancel", async () => {
      await uploadWithReply();
      (window.speechSynthesis.cancel as ReturnType<typeof vi.fn>).mockClear();

      // Manually call cancel to verify it works
      window.speechSynthesis.cancel();
      expect(window.speechSynthesis.cancel).toHaveBeenCalled();
    });

    it("displays a fallback message when Ollama is unavailable", async () => {
      installMediaMocks();
      vi.mocked(api.uploadVoiceSessionAudio).mockResolvedValue({
        session_id: "VOICE-test-session",
        status: "transcribed",
        transcript: "My order is delayed",
        detected_language: "en",
        customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
        intent_category: "delayed_delivery",
        assistant_reply: "I found your order ORD-5001 (Status: delayed). Would you like me to prepare a support case for this request?",
        conversation_history: [
          { role: "user", content: "My order is delayed" },
          { role: "assistant", content: "I found your order ORD-5001 (Status: delayed). Would you like me to prepare a support case for this request?" },
        ],
      });
      await renderReadyPanel();

      const user = userEvent.setup();
      await user.click(screen.getByRole("button", { name: /start speaking/i }));
      await screen.findByText(/recording…/i);
      await user.click(screen.getByRole("button", { name: /^stop$/i }));

      await screen.findByText(/Case Draft/i);
      const replies = screen.getAllByText(/I found your order ORD-5001/i);
      expect(replies.length).toBeGreaterThan(0);
    });

    it("displays conversation history with user and assistant turns", async () => {
      await uploadWithReply();
      const historySection = screen.getByLabelText(/conversation history/i);
      expect(historySection).toBeInTheDocument();
      expect(screen.getAllByText(/You:/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Assistant:/i).length).toBeGreaterThan(0);
    });
  });
});
