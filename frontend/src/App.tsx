import { useEffect, useState } from "react";

import { getHealth, type HealthResponse } from "./lib/api";

type ServiceState =
  | { kind: "loading" }
  | { kind: "online"; health: HealthResponse }
  | { kind: "offline"; message: string };

function App() {
  const [service, setService] = useState<ServiceState>({ kind: "loading" });

  useEffect(() => {
    const controller = new AbortController();

    getHealth(controller.signal)
      .then((health) => setService({ kind: "online", health }))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const message = error instanceof Error ? error.message : "Unknown error";
        setService({ kind: "offline", message });
      });

    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <nav className="nav" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          Nova
        </a>
        <span className="phase">Foundation · 0.1.0</span>
      </nav>

      <section className="hero">
        <p className="eyebrow">Local-first · Explainable · User-controlled</p>
        <h1>Make better AI architecture decisions.</h1>
        <p className="lede">
          Nova will turn system requirements into clear, comparable designs—while
          keeping the evidence, trade-offs, and final decision visible.
        </p>

        <div className="status-card" aria-live="polite">
          <div>
            <p className="status-label">System status</p>
            <Status state={service} />
          </div>
          <a href={`${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/docs`}>
            Open API docs
          </a>
        </div>
      </section>

      <section className="principles" aria-labelledby="principles-title">
        <div>
          <p className="section-number">01</p>
          <h2 id="principles-title">A small core with room to grow.</h2>
        </div>
        <div className="principle-grid">
          <article>
            <h3>Compare</h3>
            <p>Place multiple system designs against the same requirements.</p>
          </article>
          <article>
            <h3>Explain</h3>
            <p>Trace every recommendation back to evidence and constraints.</p>
          </article>
          <article>
            <h3>Decide</h3>
            <p>Keep approvals and meaningful trade-offs in human hands.</p>
          </article>
        </div>
      </section>
    </main>
  );
}

function Status({ state }: { state: ServiceState }) {
  if (state.kind === "loading") {
    return <p className="status pending"><span />Checking Nova API…</p>;
  }

  if (state.kind === "offline") {
    return (
      <p className="status offline" title={state.message}>
        <span />API unavailable
      </p>
    );
  }

  return (
    <p className="status online">
      <span />{state.health.service} online · {state.health.environment}
    </p>
  );
}

export default App;

