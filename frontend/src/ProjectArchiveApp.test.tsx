import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import ProjectArchiveApp from "./ProjectArchiveApp";

const report = {
  generated_at: "2026-08-03T09:00:00Z",
  index_generated_at: "2026-08-03T08:59:00Z",
  current_release: "0.74.0",
  current_commit: "d00e35c66ebab1a0e9449f7cf0a4c55013f6e951",
  migration_summary: "Repository and runtime evidence are stored locally.",
  source_count: 1,
  verified_count: 1,
  changed_count: 0,
  missing_count: 0,
  invalid_count: 0,
  raw_chat_source_count: 0,
  sources: [
    {
      id: "status",
      label: "Current NOVA status",
      category: "current_status",
      authority: "verified_runtime",
      relative_path: "Current/NOVA-Current-Status.md",
      expected_sha256: "a".repeat(64),
      actual_sha256: "a".repeat(64),
      expected_size_bytes: 120,
      actual_size_bytes: 120,
      captured_at: "2026-08-03T08:59:00Z",
      verification_status: "verified",
      preview_available: true,
    },
  ],
  warnings: [],
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ProjectArchiveApp", () => {
  it("shows verified local coverage without claiming ChatGPT chats were imported", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(jsonResponse(report))));

    render(<ProjectArchiveApp />);

    expect(await screen.findByText("0.74.0")).toBeInTheDocument();
    expect(screen.getByText("Current NOVA status")).toBeInTheDocument();
    expect(
      screen.getByText(/No raw ChatGPT conversation has been supplied yet/),
    ).toBeInTheDocument();
    expect(screen.getByText("Verified")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Record" })).toHaveAttribute(
      "aria-current",
      "page",
    );
  });

  it("opens a verified local source as escaped plain text", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/sources/status")) {
        return Promise.resolve(
          jsonResponse({
            id: "status",
            label: "Current NOVA status",
            relative_path: "Current/NOVA-Current-Status.md",
            sha256: "a".repeat(64),
            content: "# NOVA\n<script>not executed</script>",
            truncated: false,
          }),
        );
      }
      return Promise.resolve(jsonResponse(report));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectArchiveApp />);
    fireEvent.click(await screen.findByRole("button", { name: "Open" }));

    const preview = await screen.findByRole("dialog", {
      name: "Selected archive document",
    });
    expect(preview).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();
    expect(await screen.findByText(/<script>not executed<\/script>/)).toBeInTheDocument();
    expect(document.querySelector("script:not([type])")).toBeNull();
  });

  it("keeps the last report visible when refresh fails", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(report))
      .mockResolvedValueOnce(jsonResponse({ detail: "unavailable" }, 503));
    vi.stubGlobal("fetch", fetchMock);

    render(<ProjectArchiveApp />);
    expect(await screen.findByText("Current NOVA status")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Refresh record" }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("503");
    });
    expect(screen.getByText("Current NOVA status")).toBeInTheDocument();
  });
});
