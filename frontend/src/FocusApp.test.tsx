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

const openAction = {
  id: "action-1",
  title: "Run Milestone 68 acceptance",
  status: "open",
  project_record_id: "project-1",
  project_title: "Build NOVA",
  project_revision: 2,
  project_unavailable: false,
  created_at: "2026-07-31T09:00:00Z",
  updated_at: "2026-07-31T09:00:00Z",
  completed_at: null,
};

const nextActions = {
  generated_at: "2026-07-31T09:00:00Z",
  open: [openAction],
  completed: [],
  limitation:
    "Next actions are entered explicitly by the owner and ordered deterministically by creation time. NOVA does not infer priority, progress, dates, deadlines, reminders, or additional actions.",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubReads(
  planning: unknown = overview,
  actions: unknown = nextActions,
) {
  const mock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    return Promise.resolve(
      url.includes("/focus/actions")
        ? jsonResponse(actions)
        : jsonResponse(planning),
    );
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("FocusApp", () => {
  it("shows verified direction and explicit next actions without inferred data", async () => {
    stubReads();

    render(<FocusApp />);

    expect(await screen.findByText("Build NOVA")).toBeInTheDocument();
    expect(screen.getByText("Daily-use prototype")).toBeInTheDocument();
    expect(screen.getByText("Run Milestone 68 acceptance")).toBeInTheDocument();
    expect(screen.getByText("Current")).toBeInTheDocument();
    expect(screen.getByText("Review due")).toBeInTheDocument();
    expect(screen.getByText("Revision 2")).toBeInTheDocument();
    expect(screen.getByText("Project: Build NOVA · revision 2")).toBeInTheDocument();
    expect(
      screen.getByText(/does not invent priorities, progress, deadlines/),
    ).toBeInTheDocument();
    expect(screen.queryByText(/50% complete/i)).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "Review approved record" })[0],
    ).toHaveAttribute("href", "/chat.html?record=project-1");
  });

  it("offers guided chat for truthful empty planning sections", async () => {
    stubReads({ ...overview, projects: [], goals: [] }, {
      ...nextActions,
      open: [],
    });

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
      screen.getByText(
        "No open next actions. Add one only when it is genuinely useful.",
      ),
    ).toBeInTheDocument();
  });

  it("creates only the owner-entered action through the guarded local API", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/focus/actions") && init?.method === "POST") {
        return Promise.resolve(jsonResponse(openAction, 201));
      }
      return Promise.resolve(
        url.includes("/focus/actions")
          ? jsonResponse(nextActions)
          : jsonResponse(overview),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<FocusApp />);
    await screen.findByText("Run Milestone 68 acceptance");

    fireEvent.change(screen.getByLabelText("Next action"), {
      target: { value: "Prepare the owner test" },
    });
    fireEvent.change(screen.getByLabelText("Active project (optional)"), {
      target: { value: "project-1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add next action" }));

    expect(await screen.findByText("Next action added locally.")).toBeInTheDocument();
    const createCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        String(input).endsWith("/api/v1/focus/actions")
        && init?.method === "POST",
    );
    expect(createCall).toBeDefined();
    const init = createCall?.[1] as RequestInit;
    expect(new Headers(init.headers).get("X-Nova-Intent")).toBe(
      "local-user-action",
    );
    expect(JSON.parse(String(init.body))).toEqual({
      title: "Prepare the owner test",
      project_record_id: "project-1",
    });
    expect(
      fetchMock.mock.calls.filter(
        ([input, init]) =>
          String(input).endsWith("/api/v1/focus/actions") && !init?.method,
      ),
    ).toHaveLength(1);
  });

  it("completes an action explicitly and retains a truthful status message", async () => {
    const completed = {
      ...openAction,
      status: "completed",
      completed_at: "2026-07-31T09:10:00Z",
    };
    let actionReadCount = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/complete") && init?.method === "POST") {
        return Promise.resolve(jsonResponse(completed));
      }
      if (url.endsWith("/api/v1/focus/actions")) {
        actionReadCount += 1;
        return Promise.resolve(
          jsonResponse(
            actionReadCount === 1
              ? nextActions
              : { ...nextActions, open: [], completed: [completed] },
          ),
        );
      }
      return Promise.resolve(jsonResponse(overview));
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<FocusApp />);

    fireEvent.click(await screen.findByRole("button", { name: "Mark complete" }));

    expect(
      await screen.findByText(
        "Next action marked complete. Its history was retained.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Completed history (1)")).toBeInTheDocument();
    const completeCall = fetchMock.mock.calls.find(([input]) =>
      String(input).endsWith("/action-1/complete"),
    );
    expect(new Headers(completeCall?.[1]?.headers).get("X-Nova-Intent")).toBe(
      "local-user-action",
    );
    expect(actionReadCount).toBe(1);
  });

  it("reopens a completed action only after an explicit click", async () => {
    const completed = {
      ...openAction,
      status: "completed",
      completed_at: "2026-07-31T09:10:00Z",
    };
    let actionReadCount = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/reopen") && init?.method === "POST") {
        return Promise.resolve(jsonResponse(openAction));
      }
      if (url.endsWith("/api/v1/focus/actions")) {
        actionReadCount += 1;
        return Promise.resolve(
          jsonResponse(
            actionReadCount === 1
              ? { ...nextActions, open: [], completed: [completed] }
              : nextActions,
          ),
        );
      }
      return Promise.resolve(jsonResponse(overview));
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<FocusApp />);

    fireEvent.click(await screen.findByText("Completed history (1)"));
    fireEvent.click(screen.getByRole("button", { name: "Reopen" }));

    expect(await screen.findByText("Next action reopened.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mark complete" })).toBeInTheDocument();
    expect(actionReadCount).toBe(1);
  });

  it("preserves owner input and reports a failed create", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/v1/focus/actions") && init?.method === "POST") {
        return Promise.resolve(jsonResponse({ detail: "Local write failed" }, 503));
      }
      return Promise.resolve(
        url.includes("/focus/actions")
          ? jsonResponse(nextActions)
          : jsonResponse(overview),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<FocusApp />);
    await screen.findByText("Run Milestone 68 acceptance");

    const input = screen.getByLabelText("Next action");
    fireEvent.change(input, { target: { value: "Keep this exact action" } });
    fireEvent.click(screen.getByRole("button", { name: "Add next action" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Nova API returned 503: Local write failed",
    );
    expect(input).toHaveValue("Keep this exact action");
  });

  it("hides stale project content when an association is unavailable", async () => {
    stubReads(overview, {
      ...nextActions,
      open: [
        {
          ...openAction,
          project_title: null,
          project_revision: null,
          project_unavailable: true,
        },
      ],
    });

    render(<FocusApp />);

    expect(
      await screen.findByText(
        "Project association unavailable; stale content is hidden.",
      ),
    ).toBeInTheDocument();
  });

  it("surfaces a safe integrity warning without showing excluded content", async () => {
    stubReads({
      ...overview,
      projects: [],
      excluded_unverified_count: 1,
      warning:
        "NOVA excluded 1 planning record because the approved local file could not be verified.",
    });

    render(<FocusApp />);

    expect(
      await screen.findByText(/excluded 1 planning record/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Build NOVA" })).not.toBeInTheDocument();
  });

  it("preserves current data and reports failed refreshes independently", async () => {
    let reads = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      reads += 1;
      if (reads <= 2) {
        return Promise.resolve(
          String(input).includes("/focus/actions")
            ? jsonResponse(nextActions)
            : jsonResponse(overview),
        );
      }
      return Promise.resolve(jsonResponse({ detail: "Unavailable" }, 503));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<FocusApp />);
    await screen.findByText("Build NOVA");
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));

    await waitFor(() =>
      expect(screen.getAllByRole("alert")).toHaveLength(2),
    );
    expect(screen.getByText("Build NOVA")).toBeInTheDocument();
    expect(screen.getByText("Run Milestone 68 acceptance")).toBeInTheDocument();
  });

  it("does not describe unavailable initial views as empty", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(jsonResponse({ detail: "Unavailable" }, 503)),
      ),
    );

    render(<FocusApp />);

    expect(await screen.findAllByRole("alert")).toHaveLength(2);
    expect(
      screen.getAllByText(
        "Unable to verify this section right now. No knowledge was changed.",
      ),
    ).toHaveLength(2);
    expect(
      screen.getByText(
        "Unable to verify next actions right now. No actions were changed.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Verification unavailable")).toBeInTheDocument();
  });
});
