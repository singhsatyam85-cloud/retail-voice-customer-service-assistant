import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";
import React from "react";

vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "mock-canvas" }, children),
  useFrame: () => {},
}));
