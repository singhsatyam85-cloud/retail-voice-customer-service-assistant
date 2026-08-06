import { useState } from "react";
import { VoiceSupportPanel } from "./VoiceSupportPanel";
import "./VoiceSupportButton.css";

/**
 * Embeddable floating support button. Designed to be dropped into an
 * existing retailer app (see docs/04-in-app-voice-support-foundation.md)
 * -- it renders itself and its panel, and expects nothing from the host
 * page beyond being mounted somewhere in the tree.
 */
export function VoiceSupportButton() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        className="voice-support-button"
        aria-label="Open AI Voice Support"
        aria-haspopup="dialog"
        aria-expanded={isOpen}
        onClick={() => setIsOpen(true)}
      >
        <svg
          className="voice-support-button__icon"
          viewBox="0 0 24 24"
          aria-hidden="true"
          focusable="false"
        >
          <path
            fill="currentColor"
            d="M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-2.08A7 7 0 0 0 19 12h-2Z"
          />
        </svg>
        AI Voice Support
      </button>
      {isOpen && <VoiceSupportPanel onClose={() => setIsOpen(false)} />}
    </>
  );
}
