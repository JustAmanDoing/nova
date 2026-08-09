import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import LibrarianApp from "./LibrarianApp";

const issue = {
  id: "lib-review-1",
  issue_type: "checksum_mismatch",
  priority: "critical",
  title: "Saved file changed unexpectedly: Response style",
  summary: "Nova cannot safely use this saved item right now.",
  reason: "The file no longer matches the version you approved.",
  evidence: ["Problem: File changed."],
  confidence: 1,
  record_ids: ["record-1"],
  source_titles: ["Response style"],
  suggested_action: "Review the source before changing anything.",
  review_url: "/chat.html?record=record-1",
};

const health = {
  generated_at: "2026-08-05T10:00:00Z",
  health_score: 82,
  dimensions: {
    coverage: 80,
    freshness: 90,
    retrieval: 100,
    integrity: 50,
    consistency: 90,
  },
  counts: {
    duplicates: 0,
    conflicts: 0,
    stale: 1,
    missing_coverage: 2,
    missing_files: 0,
    checksum_failures: 1,
    broken_references: 0,
  },
  active_record_count: 2,
  retired_record_count: 1,
  verified_source_count: 1,
  average_source_confidence: 1,
  methodology: "Five simple checks of Nova's saved information; not the owner.",
  limitation: "The Librarian only shows suggestions and never changes information.",
};

const review = {
  generated_at: "2026-08-05T10:00:00Z",
  total: 1,
  issues: [issue],
  limitation: "Review items are recomputed.",
};

const detail = {
  generated_at: "2026-08-05T10:00:00Z",
  issue,
  sources: [
    {
      record_id: "record-1",
      candidate_id: "candidate-1",
      kind: "preference",
      title: "Response style",
      content: "I prefer concise responses.",
      status: "active",
      revision: 2,
      updated_at: "2026-08-05T09:00:00Z",
      relative_path: "Preferences/response.md",
      sha256: "a".repeat(64),
      verification_status: "checksum_mismatch",
      candidate_confidence: 1,
      explicit_request: true,
      source_reason: "The owner explicitly asked NOVA to remember this.",
      conversation_id: "conversation-1",
      source_message_id: "message-1",
    },
  ],
  revisions: [
    {
      record_id: "record-1",
      revision: 2,
      status: "active",
      created_at: "2026-08-05T09:00:00Z",
      relative_path: "Preferences/response.md",
      sha256: "a".repeat(64),
    },
  ],
  events: [
    {
      sequence: 2,
      record_id: "record-1",
      event_type: "updated",
      detail: "Owner saved revision 2.",
      created_at: "2026-08-05T09:00:00Z",
    },
  ],
  limitation: "Evidence only.",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function successfulFetch() {
  return vi.fn((input: RequestInfo | URL, _init?: RequestInit) => {
    void _init;
    const url = String(input);
    if (url.endsWith("/librarian/health")) return Promise.resolve(jsonResponse(health));
    if (url.endsWith("/librarian/review")) return Promise.resolve(jsonResponse(review));
    if (url.endsWith(`/librarian/item/${issue.id}`)) {
      return Promise.resolve(jsonResponse(detail));
    }
    return Promise.resolve(jsonResponse({ detail: "not found" }, 404));
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("LibrarianApp", () => {
  it("shows health and suggestions in plain language", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    render(<LibrarianApp />);

    expect(await screen.findByText("82%")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Check what Nova remembers." }))
      .toBeInTheDocument();
    expect(screen.getByText(issue.title)).toBeInTheDocument();
    expect(screen.getByText("Nothing changes unless you choose")).toBeInTheDocument();
    expect(screen.getByText("Files match")).toBeInTheDocument();
    expect(screen.getByText("100% sure")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Librarian" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Open" })).toHaveAttribute(
      "href",
      issue.review_url,
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("opens plain-language details without a write request", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    render(<LibrarianApp />);
    fireEvent.click(await screen.findByRole("button", { name: "Why this is here" }));

    const dialog = await screen.findByRole("dialog", {
      name: "Suggestion details",
    });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText(/Saved as preference · version 2 · 100% sure/))
      .toBeInTheDocument();
    expect(screen.getAllByText("File changed")).toHaveLength(2);
    expect(screen.getByText("I prefer concise responses.")).toBeInTheDocument();
    expect(screen.getByText(/Updated · Owner saved revision 2/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();
    expect(screen.getByRole("link", { name: "Open review in Chat" }))
      .toHaveAttribute("href", issue.review_url);
    expect(screen.queryByText(/integrity-verified|immutable|SHA-256|deterministic/i))
      .not.toBeInTheDocument();
    expect(fetchMock.mock.calls.every(([, init]) => !init?.method)).toBe(true);
  });

  it("keeps the last analysis visible when refresh fails", async () => {
    const fetchMock = successfulFetch();
    fetchMock
      .mockImplementationOnce(() => Promise.resolve(jsonResponse(health)))
      .mockImplementationOnce(() => Promise.resolve(jsonResponse(review)))
      .mockImplementationOnce(() =>
        Promise.resolve(jsonResponse({ detail: "temporarily unavailable" }, 503)),
      )
      .mockImplementationOnce(() => Promise.resolve(jsonResponse(review)));
    vi.stubGlobal("fetch", fetchMock);

    render(<LibrarianApp />);
    expect(await screen.findByText(issue.title)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Check again" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("503"));
    expect(screen.getByText(issue.title)).toBeInTheDocument();
  });
});
