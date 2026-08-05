import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import LibrarianApp from "./LibrarianApp";

const issue = {
  id: "lib-review-1",
  issue_type: "checksum_mismatch",
  priority: "critical",
  title: "Knowledge checksum mismatch: Response style",
  summary: "An active approved record cannot be integrity-verified.",
  reason: "The file checksum differs from the approved record metadata.",
  evidence: ["Recorded SHA-256 differs from the local file."],
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
  methodology: "Transparent five-dimension store score; not the owner.",
  limitation: "The Librarian is read-only and never changes knowledge.",
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
  it("shows transparent health and a read-only review queue", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    render(<LibrarianApp />);

    expect(await screen.findByText("82%")).toBeInTheDocument();
    expect(screen.getByText(issue.title)).toBeInTheDocument();
    expect(screen.getByText("No automatic changes")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Librarian" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("link", { name: "Review" })).toHaveAttribute(
      "href",
      issue.review_url,
    );
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("opens source confidence and immutable evidence without a write request", async () => {
    const fetchMock = successfulFetch();
    vi.stubGlobal("fetch", fetchMock);

    render(<LibrarianApp />);
    fireEvent.click(await screen.findByRole("button", { name: "View evidence" }));

    const dialog = await screen.findByRole("dialog", {
      name: "Selected Librarian item",
    });
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText(/revision 2 · 100% source confidence/)).toBeInTheDocument();
    expect(screen.getByText("I prefer concise responses.")).toBeInTheDocument();
    expect(screen.getByText(/Updated · Owner saved revision 2/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Close" })).toHaveFocus();
    expect(screen.getByRole("link", { name: "Open existing review workflow" }))
      .toHaveAttribute("href", issue.review_url);
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
    fireEvent.click(screen.getByRole("button", { name: "Refresh analysis" }));

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("503"));
    expect(screen.getByText(issue.title)).toBeInTheDocument();
  });
});
