import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { VoiceOrbDNA } from "./VoiceOrbDNA";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="mock-canvas">{children}</div>
  ),
  useFrame: () => {},
}));

describe("VoiceOrbDNA", () => {
  it("renders correctly with different states", () => {
    const { rerender } = render(<VoiceOrbDNA state="idle" />);
    expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();

    rerender(<VoiceOrbDNA state="listening" />);
    expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();

    rerender(<VoiceOrbDNA state="speaking" />);
    expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();

    rerender(<VoiceOrbDNA state="processing" />);
    expect(screen.getByTestId("mock-canvas")).toBeInTheDocument();
  });
});
