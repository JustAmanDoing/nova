import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App", () => {
  it("shows the backend status when the health request succeeds", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: "ok",
          service: "Nova API",
          version: "0.1.0",
          environment: "test",
          timestamp: "2026-07-24T00:00:00Z",
        }),
      }),
    );

    render(<App />);

    expect(await screen.findByText("Nova API online · test")).toBeInTheDocument();
  });

  it("shows an unavailable state when the health request fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network error")));

    render(<App />);

    expect(await screen.findByText("API unavailable")).toBeInTheDocument();
  });
});

