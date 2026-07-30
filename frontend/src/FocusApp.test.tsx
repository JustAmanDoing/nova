import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import FocusApp from "./FocusApp";

const overview = {
  generated_at: "2026-07-30T09:00:00Z",
  projects: [
    {
      id: "project-1",
      kind: "project",
      title: "Build NOVA",
      content: "My active project is building NOVA.",
      revision: 2,
      updated_at: "2026-07-29T09:00:00Z",
      review_due_at: "2026-10-27T09:00:00Z",
      review_state: "current",
    },
  ],
  goals: [
    {
      id: "goal-1",
      kind: "goal",
      title: "Daily-use prototype",
      content: "My current goal is a reliable daily-use prototype.",
      revision: 1,
      updated_at: "2026-01-01T09:00:00Z",
      review_due_at: "2026-04-01T09:00:00Z",
      review_state: "review_due",
    },
  ],
  excluded_unverified_count: 0,
  warning: null,
  limitation:
    "This view displays active owner-approved, integrity-verified project and goal knowledge. NOVA does not infer progress, priority, dates, deadlines, or next actions.",
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

describe("FocusApp", () => {
  it("shows verified projects and goals without inferred planning data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(jsonResponse(overview))),
    );

    render(<FocusApp />);

    expect(await screen.findByText("Build NOVA")).toBeInTheDocument();
    expect(screen.getByText("Daily-use prototype")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getByText("Review due")).toBeInTheDocument();
    expect(screen.getByText("Revision 2")).toBeInTheDocument();
    expect(
      screen.getByText(/does not invent priorities, progress, deadlines/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/50% complete/i)).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "Review approved record" })[0],
    ).toHaveAttribute("href", "/chat.html?record=project-1");
  });

  it("offers guided chat for truthful empty sections without saving", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          jsonResponse({
            ...overview,
            projects: [],
            goals: [],
          }),
        ),
      ),
    );

    render(<FocusApp />);

    expect(
      await screen.findByText("No verified active project has been approved yet."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("No verified current goal has been approved yet."),
    ).toBeInTheDocument();
    const addLinks = screen.getAllByRole("link", { name: "Add through chat" });
    expect(addLinks[0]).toHaveAttribute(
      "href",
      "/chat.html?knowledge=active-projects",
    );
    expect(addLinks[1]).toHaveAttribute(
      "href",
      "/chat.html?knowledge=current-goals",
    );
    expect(
      screen.getAllByText("Nothing is saved until you approve the review card."),
    ).toHaveLength(2);
  });

  it("surfaces a safe integrity warning without showing excluded content", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          jsonResponse({
            ...overview,
            projects: [],
            excluded_unverified_count: 1,
            warning:
              "NOVA excluded 1 planning record because the approved local file could not be verified.",
          }),
        ),
      ),
    );

    render(<FocusApp />);

    expect(
      await screen.findByText(/excluded 1 planning record/),
    ).toBeInTheDocument();
    expect(screen.queryByText("Build NOVA")).not.toBeInTheDocument();
    expect(screen.getByText("1 safely excluded")).toBeInTheDocument();
  });

  it("keeps the view read-only and reports a failed refresh", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(overview))
      .mockResolvedValueOnce(jsonResponse({ detail: "Unavailable" }, 503));
    vi.stubGlobal("fetch", fetchMock);

    render(<FocusApp />);
    await screen.findByText("Build NOVA");
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Existing knowledge was not changed.",
      ),
    );
    expect(screen.getByText("Build NOVA")).toBeInTheDocument();
  });

  it("does not describe an unavailable initial view as empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(jsonResponse({ detail: "Unavailable" }, 503)),
      ),
    );

    render(<FocusApp />);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Existing knowledge was not changed.",
    );
    expect(
      screen.getAllByText(
        "Unable to verify this section right now. No knowledge was changed.",
      ),
    ).toHaveLength(2);
    expect(screen.getByText("Verification unavailable")).toBeInTheDocument();
    expect(
      screen.queryByText("No verified active project has been approved yet."),
    ).not.toBeInTheDocument();
  });
});
