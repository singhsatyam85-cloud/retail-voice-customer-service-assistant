import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import * as api from "../services/voiceSupportApi";
import { VoiceSupportButton } from "./VoiceSupportButton";

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

describe("VoiceSupportButton", () => {
  beforeEach(() => {
    vi.mocked(api.startVoiceSession).mockReset();
  });

  it("renders the floating support button", () => {
    render(<VoiceSupportButton />);
    expect(screen.getByRole("button", { name: /ai voice support/i })).toBeInTheDocument();
  });

  it("opens the panel and starts a session when clicked", async () => {
    vi.mocked(api.startVoiceSession).mockResolvedValue({
      session_id: "VOICE-test-session",
      status: "started",
      customer: { customer_id: "CUST-101", full_name: "Test Customer One" },
      recent_orders: [],
      created_at: new Date().toISOString(),
    });

    const user = userEvent.setup();
    render(<VoiceSupportButton />);

    await user.click(screen.getByRole("button", { name: /open ai voice support/i }));

    expect(await screen.findByRole("dialog", { name: /ai voice support/i })).toBeInTheDocument();
    expect(api.startVoiceSession).toHaveBeenCalledTimes(1);
  });
});
