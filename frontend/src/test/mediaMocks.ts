import { vi } from "vitest";

export class FakeMediaRecorder {
  static instances: FakeMediaRecorder[] = [];

  state: "inactive" | "recording" = "inactive";
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: (() => void) | null = null;
  stream: MediaStream;

  constructor(stream: MediaStream) {
    this.stream = stream;
    FakeMediaRecorder.instances.push(this);
  }

  start(): void {
    this.state = "recording";
  }

  stop(): void {
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob(["fake-audio"], { type: "audio/webm" }) });
    this.onstop?.();
  }
}

export function createFakeTrack(): MediaStreamTrack {
  return { stop: vi.fn(), kind: "audio" } as unknown as MediaStreamTrack;
}

/** Installs a fake MediaRecorder + getUserMedia on window/navigator for one test. */
export function installMediaMocks(): {
  getUserMedia: ReturnType<typeof vi.fn>;
  track: MediaStreamTrack;
} {
  FakeMediaRecorder.instances = [];
  const track = createFakeTrack();
  const stream = { getTracks: () => [track] } as unknown as MediaStream;
  const getUserMedia = vi.fn().mockResolvedValue(stream);

  Object.defineProperty(window, "MediaRecorder", {
    value: FakeMediaRecorder,
    writable: true,
    configurable: true,
  });
  Object.defineProperty(navigator, "mediaDevices", {
    value: { getUserMedia },
    writable: true,
    configurable: true,
  });

  return { getUserMedia, track };
}

export function removeMediaRecorderSupport(): void {
  Object.defineProperty(window, "MediaRecorder", {
    value: undefined,
    writable: true,
    configurable: true,
  });
}
