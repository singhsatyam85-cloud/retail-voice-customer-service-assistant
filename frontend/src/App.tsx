import { VoiceSupportButton } from "./components/VoiceSupportButton";
import "./App.css";

/**
 * Stand-in for an existing retailer page. The only thing this task adds
 * to a real e-commerce app is <VoiceSupportButton /> -- everything else
 * here just gives it somewhere realistic to float above.
 */
function App() {
  return (
    <div className="demo-page">
      <header className="demo-page__header">
        <span className="demo-page__brand">Northbridge Retail</span>
        <nav aria-label="Account">
          <span className="demo-page__account">My Account</span>
        </nav>
      </header>

      <main className="demo-page__main">
        <h1>Your recent orders</h1>
        <p className="demo-page__hint">
          This page stands in for an existing, already-authenticated retailer
          application. The floating <strong>AI Voice Support</strong> button in
          the corner is the only new component this task adds.
        </p>
      </main>

      <VoiceSupportButton />
    </div>
  );
}

export default App;
