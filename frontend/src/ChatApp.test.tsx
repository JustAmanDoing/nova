import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import ChatApp from "./ChatApp";

const conversation = {
  id: "conversation-1",
  title: "New conversation",
  model: null,
  created_at: "2026-07-28T09:00:00Z",
  updated_at: "2026-07-28T09:00:00Z",
  message_count: 0,
};

const knowledgeSource = {
  record_id: "record-1",
  citation_label: "K1",
  title: "Automated approval phrase",
  kind: "fact",
  content: "The automated approval phrase is amber lighthouse.",
  relative_path: "Facts/automated-approval-phrase.md",
  sha256: "a".repeat(64),
  score: 1,
};

const documentSource = {
  file_id: "file-1",
  citation_label: "D1",
  title: "Delivery note",
  original_name: "delivery.txt",
  relative_path: "delivery.txt",
  sha256: "d".repeat(64),
  document_type: "text",
  character_count: 31,
};

const conductorCapability = {
  id: "focus.next_actions",
  label: "Open next actions",
  description: "Show the owner's current open Next actions from Focus.",
  prompt: "Show my open next actions",
  source_title: "Focus",
  source_url: "/focus.html#next-actions",
};

const capabilitySource = {
  capability_id: "focus.next_actions",
  source_title: "Focus",
  source_url: "/focus.html#next-actions",
  generated_at: "2026-08-09T20:00:00Z",
  result_sha256: "c".repeat(64),
};

const knowledgeRecord = {
  id: "record-1",
  candidate_id: "candidate-1",
  kind: "fact",
  title: "Automated approval phrase",
  content: "The automated approval phrase is amber lighthouse.",
  relative_path: "Facts/automated-approval-phrase.md",
  sha256: "a".repeat(64),
  created_at: "2026-07-28T09:00:00Z",
  status: "active",
  revision: 1,
  updated_at: "2026-07-28T09:00:00Z",
  retired_at: null,
};

const knowledgeQualityReport = {
  generated_at: "2026-07-28T09:00:00Z",
  active_record_count: 1,
  retired_record_count: 0,
  core_covered: 1,
  core_total: 7,
  completion_percent: 16.7,
  fresh_covered: 1,
  covered_total: 1,
  freshness_percent: 100,
  retrieval_total_records: 1,
  retrieval_checked: 1,
  retrieval_passed: 1,
  retrieval_percent: 100,
  retrieval_check_limit: 100,
  requirements: [
    {
      id: "preferred-name",
      domain: "personal",
      title: "Preferred name",
      why: "Lets Nova address you consistently without guessing.",
      suggestion: "Tell Nova the name you want it to use.",
      prompt_starter: "Remember that the name I want you to use is ",
      examples: [
        {
          text: "A first name, such as Sam",
          draft: "Remember that the name I want you to use is Sam.",
        },
        {
          text: "A nickname, such as Sunny",
          draft: "Remember that the nickname I want you to use is Sunny.",
        },
      ],
      priority: 5,
      core: true,
      review_days: 365,
      status: "covered",
      last_reviewed: "2026-07-28T09:00:00Z",
      matched_record_ids: ["record-1"],
      matched_record_titles: ["Preferred name"],
    },
    {
      id: "current-goals",
      domain: "planning",
      title: "What you want to achieve",
      why: "Helps Nova focus on what matters to you.",
      suggestion: "Add something you want Nova to help you achieve.",
      prompt_starter: "Remember that something I want to achieve is ",
      examples: [
        {
          text: "Build a steady exercise habit",
          draft: "Remember that I want to build a steady exercise habit.",
        },
        {
          text: "Learn basic home maintenance skills",
          draft: "Remember that I want to learn basic home maintenance skills.",
        },
      ],
      priority: 5,
      core: true,
      review_days: 90,
      status: "missing",
      last_reviewed: null,
      matched_record_ids: [],
      matched_record_titles: [],
    },
    {
      id: "emergency-plan",
      domain: "safety",
      title: "Emergency contacts or plan",
      why: "Can make personal contingency planning easier to retrieve.",
      suggestion: "Optionally add a safe, non-secret emergency plan.",
      prompt_starter: "Remember that an emergency step I want to save is ",
      examples: [
        {
          text: "Keep a torch and radio with the emergency kit",
          draft: "Remember that my emergency kit should include a torch and radio.",
        },
        {
          text: "Use a familiar public place as a family meeting point",
          draft: "Remember that our emergency meeting point is a familiar public place.",
        },
      ],
      priority: 4,
      core: false,
      review_days: 180,
      status: "missing",
      last_reviewed: null,
      matched_record_ids: [],
      matched_record_titles: [],
    },
    {
      id: "active-projects",
      domain: "planning",
      title: "Projects you are working on",
      why: "Helps Nova suggest useful next steps.",
      suggestion: "Add a project you are working on.",
      prompt_starter: "Remember that a project I am working on is ",
      examples: [
        {
          text: "Organising family photos",
          draft: "Remember that a project I am working on is organising family photos.",
        },
        {
          text: "Planning a small garden",
          draft: "Remember that a project I am working on is planning a small garden.",
        },
      ],
      priority: 5,
      core: true,
      review_days: 90,
      status: "missing",
      last_reviewed: null,
      matched_record_ids: [],
      matched_record_titles: [],
    },
  ],
  retrieval_failures: [],
  methodology: "A transparent deterministic checklist.",
  limitation:
    "This report measures NOVA's approved local knowledge and does not measure or score the owner.",
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  Object.defineProperty(HTMLElement.prototype, "scrollTo", {
    configurable: true,
    value: vi.fn(),
  });
  vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
    callback(0);
    return 1;
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/chat.html");
});

describe("ChatApp", () => {
  it("opens a long conversation at the latest exchange and offers phone shortcuts", async () => {
    const messages = Array.from({ length: 79 }, (_, index) => ({
      id: `message-${index + 1}`,
      conversation_id: conversation.id,
      role: index % 2 === 0 ? "user" : "assistant",
      content: `Private test exchange ${index + 1}`,
      model: "qwen3:8b",
      created_at: `2026-07-28T09:${String(index).padStart(2, "0")}:00Z`,
      knowledge_checked: false,
      sources: [],
      document_sources: [],
    }));
    const longConversation = {
      ...conversation,
      model: "qwen3:8b",
      message_count: messages.length,
      archived_at: null,
      trashed_at: null,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.includes("/chat/conversations?status=")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith(`/chat/conversations/${conversation.id}`)) {
          return Promise.resolve(jsonResponse({ ...longConversation, messages }));
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([longConversation]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        return Promise.resolve(jsonResponse([]));
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Private test exchange 79")).toBeInTheDocument();
    expect(vi.mocked(HTMLElement.prototype.scrollTo)).toHaveBeenCalled();
    expect(screen.getAllByRole("button", { name: "New chat" })).toHaveLength(2);

    const historyToggle = screen.getByRole("button", { name: "Chats" });
    fireEvent.click(historyToggle);
    expect(historyToggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("complementary", { name: "Conversation history" }))
      .toHaveClass("mobile-open");
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    expect(historyToggle).toHaveAttribute("aria-expanded", "false");

    const transcript = document.querySelector<HTMLElement>(".chat-transcript");
    expect(transcript).not.toBeNull();
    Object.defineProperties(transcript as HTMLElement, {
      scrollHeight: { configurable: true, value: 90_000 },
      clientHeight: { configurable: true, value: 300 },
      scrollTop: { configurable: true, writable: true, value: 0 },
    });
    fireEvent.scroll(transcript as HTMLElement);
    const jump = screen.getByRole("button", { name: "Jump to latest" });
    fireEvent.click(jump);
    expect(vi.mocked(HTMLElement.prototype.scrollTo)).toHaveBeenLastCalledWith({
      top: 90_000,
      behavior: "smooth",
    });
  });

  it("shows the local-only boundary and available Ollama model", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/chat/documents")) {
          return Promise.resolve(
            jsonResponse([
              {
                ...documentSource,
                understood_at: "2026-07-28T09:00:00Z",
              },
            ]),
          );
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        return Promise.resolve(jsonResponse([]));
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Local AI ready")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Local model" })).toHaveValue(
      "qwen3:8b",
    );
    expect(
      screen.getByRole("combobox", { name: "Open conversation" }),
    ).toBeDisabled();
    expect(screen.getByText("Ready when you are.")).toBeInTheDocument();
    expect(
      screen.getByText(/A suggestion is never permanent/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Retrieval uses active, approved local records only/),
    ).toBeInTheDocument();
    const privacyDetails = screen
      .getByText("Privacy and knowledge controls")
      .closest("details");
    expect(privacyDetails).not.toHaveAttribute("open");
    const composer = screen.getByRole("textbox", { name: "Message Nova" });
    const knowledgeHealth = screen.getByRole("region", {
      name: "Knowledge health",
    });
    expect(
      composer.compareDocumentPosition(knowledgeHealth) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });

  it("creates a local conversation, streams a reply, and reloads saved history", async () => {
    let conversationCreated = false;
    let turnCompleted = false;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/chat/documents")) {
          return Promise.resolve(
            jsonResponse([
              {
                ...documentSource,
                understood_at: "2026-07-28T09:00:00Z",
              },
            ]),
          );
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.includes("/knowledge/candidates")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/conversations") && init?.method === "POST") {
          conversationCreated = true;
          return Promise.resolve(jsonResponse(conversation, 201));
        }
        if (
          url.endsWith("/chat/conversations/conversation-1/messages") &&
          init?.method === "POST"
        ) {
          expect(JSON.parse(String(init.body))).toMatchObject({
            document_id: documentSource.file_id,
          });
          turnCompleted = true;
          return Promise.resolve(
            new Response(
              [
                JSON.stringify({
                  type: "user",
                  message: {
                    id: "user-1",
                    conversation_id: conversation.id,
                    role: "user",
                    content: "Hello Nova",
                    model: "qwen3:8b",
                    created_at: "2026-07-28T09:01:00Z",
                  },
                }),
                JSON.stringify({
                  type: "knowledge",
                  checked: true,
                  sources: [knowledgeSource],
                }),
                JSON.stringify({
                  type: "document",
                  source: documentSource,
                }),
                JSON.stringify({ type: "delta", content: "Hello " }),
                JSON.stringify({ type: "delta", content: "from Nova." }),
                JSON.stringify({
                  type: "done",
                  message: {
                    id: "assistant-1",
                    conversation_id: conversation.id,
                    role: "assistant",
                    content: "Hello from Nova.",
                    model: "qwen3:8b",
                    created_at: "2026-07-28T09:01:01Z",
                    knowledge_checked: true,
                    sources: [knowledgeSource],
                    document_sources: [documentSource],
                  },
                }),
                "",
              ].join("\n"),
              {
                status: 200,
                headers: { "Content-Type": "application/x-ndjson" },
              },
            ),
          );
        }
        if (url.endsWith("/chat/conversations/conversation-1")) {
          return Promise.resolve(
            jsonResponse({
              ...conversation,
              model: "qwen3:8b",
              message_count: 2,
              messages: turnCompleted
                ? [
                    {
                      id: "user-1",
                      conversation_id: conversation.id,
                      role: "user",
                      content: "Hello Nova",
                      model: "qwen3:8b",
                      created_at: "2026-07-28T09:01:00Z",
                      knowledge_checked: false,
                      sources: [],
                      document_sources: [],
                    },
                    {
                      id: "assistant-1",
                      conversation_id: conversation.id,
                      role: "assistant",
                      content: "Hello from Nova.",
                      model: "qwen3:8b",
                      created_at: "2026-07-28T09:01:01Z",
                      knowledge_checked: true,
                      sources: [knowledgeSource],
                      document_sources: [documentSource],
                    },
                  ]
                : [],
            }),
          );
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(
            jsonResponse(
              conversationCreated
                ? [{ ...conversation, message_count: turnCompleted ? 2 : 0 }]
                : [],
            ),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const documentSelector = await screen.findByRole("combobox", {
      name: "Local document for this turn",
    });
    expect(
      await screen.findByRole("option", { name: documentSource.original_name }),
    ).toBeInTheDocument();
    fireEvent.change(documentSelector, {
      target: { value: documentSource.file_id },
    });
    await waitFor(() => {
      expect(documentSelector).toHaveValue(documentSource.file_id);
    });
    const composer = await screen.findByRole("textbox", { name: "Message Nova" });
    fireEvent.change(composer, { target: { value: "Hello Nova" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("2 messages")).toBeInTheDocument();
    expect(screen.getByText("Hello from Nova.")).toBeInTheDocument();
    expect(screen.getByText("Hello Nova")).toBeInTheDocument();
    expect(screen.getByText("Approved knowledge")).toBeInTheDocument();
    expect(screen.getByText("[K1]")).toBeInTheDocument();
    expect(screen.getByText("Automated approval phrase")).toBeInTheDocument();
    expect(screen.getByText("Selected local document")).toBeInTheDocument();
    expect(screen.getByText("Delivery note")).toBeInTheDocument();
    expect(screen.getByText("[D1]")).toBeInTheDocument();
    expect(
      screen.getByText("Facts/automated-approval-phrase.md"),
    ).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(
        ([input, init]) =>
          input.toString().endsWith(
            "/chat/conversations/conversation-1/messages",
          ) &&
          init?.method === "POST" &&
          new Headers(init.headers).get("X-Nova-Intent") ===
            "local-user-action",
      ),
    ).toBe(true);
  });

  it("stops generation and refreshes the saved local history", async () => {
    let conversationCreated = false;
    let userPersisted = false;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.includes("/knowledge/candidates")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/conversations") && init?.method === "POST") {
          conversationCreated = true;
          return Promise.resolve(jsonResponse(conversation, 201));
        }
        if (
          url.endsWith("/chat/conversations/conversation-1/messages") &&
          init?.method === "POST"
        ) {
          userPersisted = true;
          const signal = init.signal;
          const encoder = new TextEncoder();
          const body = new ReadableStream<Uint8Array>({
            start(controller) {
              controller.enqueue(
                encoder.encode(
                  `${JSON.stringify({
                    type: "user",
                    message: {
                      id: "user-stopped",
                      conversation_id: conversation.id,
                      role: "user",
                      content: "A deliberately long reply",
                      model: "qwen3:8b",
                      created_at: "2026-07-28T09:02:00Z",
                    },
                  })}\n`,
                ),
              );
              controller.enqueue(
                encoder.encode(
                  `${JSON.stringify({ type: "delta", content: "Partial" })}\n`,
                ),
              );
              signal?.addEventListener("abort", () => {
                controller.error(new DOMException("Stopped", "AbortError"));
              });
            },
          });
          return Promise.resolve(
            new Response(body, {
              status: 200,
              headers: { "Content-Type": "application/x-ndjson" },
            }),
          );
        }
        if (url.endsWith("/chat/conversations/conversation-1")) {
          return Promise.resolve(
            jsonResponse({
              ...conversation,
              model: "qwen3:8b",
              message_count: userPersisted ? 1 : 0,
              messages: userPersisted
                ? [
                    {
                      id: "user-stopped",
                      conversation_id: conversation.id,
                      role: "user",
                      content: "A deliberately long reply",
                      model: "qwen3:8b",
                      created_at: "2026-07-28T09:02:00Z",
                    },
                  ]
                : [],
            }),
          );
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(
            jsonResponse(
              conversationCreated
                ? [
                    {
                      ...conversation,
                      model: "qwen3:8b",
                      message_count: userPersisted ? 1 : 0,
                    },
                  ]
                : [],
            ),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const composer = await screen.findByRole("textbox", { name: "Message Nova" });
    fireEvent.change(composer, {
      target: { value: "A deliberately long reply" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    fireEvent.click(await screen.findByRole("button", { name: "Stop" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Generation stopped.",
    );
    expect(await screen.findByText("1 message")).toBeInTheDocument();
    expect(screen.getByText("A deliberately long reply")).toBeInTheDocument();
    expect(screen.queryByText("Partial")).toBeNull();
  });

  it("shows a truthful provider error instead of inventing availability", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse({ detail: "Ollama is unavailable." }, 503),
          );
        }
        if (url.endsWith("/chat/capabilities")) {
          return Promise.resolve(jsonResponse([conductorCapability]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.includes("/knowledge/candidates")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/documents")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/conversations/conversation-1")) {
          return Promise.resolve(
            jsonResponse({
              ...conversation,
              model: "qwen3:8b",
              message_count: 1,
              messages: [
                {
                  id: "saved-user",
                  conversation_id: conversation.id,
                  role: "user",
                  content: "Saved while local",
                  model: "qwen3:8b",
                  created_at: "2026-07-28T09:03:00Z",
                },
              ],
            }),
          );
        }
        return Promise.resolve(
          jsonResponse([{ ...conversation, message_count: 1 }]),
        );
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Local AI unavailable")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Nova API returned 503: Ollama is unavailable.",
    );
    expect(screen.getByText("Saved while local")).toBeInTheDocument();
    expect(screen.getByText("1 message")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Message Nova" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: "Open next actions" }),
    ).toBeEnabled();
  });

  it("runs a listed NOVA status request without an AI model and shows evidence", async () => {
    let turnCompleted = false;
    const savedMessages = [
      {
        id: "user-1",
        conversation_id: conversation.id,
        role: "user",
        content: conductorCapability.prompt,
        model: null,
        created_at: "2026-08-09T20:00:00Z",
        knowledge_checked: false,
        sources: [],
        document_sources: [],
        capability_sources: [],
      },
      {
        id: "assistant-1",
        conversation_id: conversation.id,
        role: "assistant",
        content: "Open next actions\n- Review Milestone 80 evidence",
        model: null,
        created_at: "2026-08-09T20:00:01Z",
        knowledge_checked: false,
        sources: [],
        document_sources: [],
        capability_sources: [capabilitySource],
      },
    ];
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(jsonResponse({ detail: "Ollama is unavailable." }, 503));
        }
        if (url.endsWith("/chat/capabilities")) {
          return Promise.resolve(jsonResponse([conductorCapability]));
        }
        if (url.endsWith("/chat/documents")) return Promise.resolve(jsonResponse([]));
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.includes("/knowledge/candidates")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (
          url.endsWith("/chat/conversations/conversation-1/messages") &&
          init?.method === "POST"
        ) {
          expect(JSON.parse(String(init.body))).toEqual({
            model: null,
            content: conductorCapability.prompt,
            document_id: null,
          });
          turnCompleted = true;
          return Promise.resolve(
            new Response(
              [
                JSON.stringify({ type: "user", message: savedMessages[0] }),
                JSON.stringify({ type: "capability", source: capabilitySource }),
                JSON.stringify({
                  type: "delta",
                  content: "Open next actions\n- Review Milestone 80 evidence",
                }),
                JSON.stringify({ type: "done", message: savedMessages[1] }),
                "",
              ].join("\n"),
              { headers: { "Content-Type": "application/x-ndjson" } },
            ),
          );
        }
        if (url.endsWith("/chat/conversations/conversation-1")) {
          return Promise.resolve(
            jsonResponse({
              ...conversation,
              title: turnCompleted ? conductorCapability.prompt : conversation.title,
              message_count: turnCompleted ? 2 : 0,
              messages: turnCompleted ? savedMessages : [],
            }),
          );
        }
        if (url.includes("/chat/conversations?status=")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(
            jsonResponse([
              {
                ...conversation,
                message_count: turnCompleted ? 2 : 0,
              },
            ]),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const starter = await screen.findByRole("button", {
      name: "Open next actions",
    });
    await waitFor(() => expect(starter).toBeEnabled());
    fireEvent.click(starter);
    expect(screen.getByRole("textbox", { name: "Message Nova" })).toHaveValue(
      conductorCapability.prompt,
    );
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await screen.findByRole("button", { name: "Stop" });
    await screen.findByRole("button", { name: "Send" });

    expect(
      screen.getByText(/Review Milestone 80 evidence/),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("NOVA capability evidence")).toHaveTextContent(
      "Evidence cccccccccccc…",
    );
    expect(screen.getByRole("link", { name: "Open Focus" })).toHaveAttribute(
      "href",
      "/focus.html#next-actions",
    );
  });

  it("requires explicit local approval before saving proposed knowledge", async () => {
    const candidate = {
      id: "candidate-1",
      conversation_id: "conversation-1",
      source_message_id: "user-1",
      kind: "preference",
      title: "Prefer short answers",
      content: "I prefer short answers",
      source_excerpt: "Remember that I prefer short answers",
      reason: "You explicitly asked Nova to remember this.",
      confidence: 1,
      explicit_request: true,
      status: "pending",
      created_at: "2026-07-28T10:00:00Z",
      reviewed_at: null,
      record_path: null,
    };
    let reviewed = false;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse(reviewed ? [] : [candidate]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (
          url.endsWith("/knowledge/candidates/candidate-1") &&
          init?.method === "PUT"
        ) {
          reviewed = true;
          return Promise.resolve(
            jsonResponse({
              ...candidate,
              title: "Preferred response style",
              content: "Use concise answers with recommendations.",
              status: "approved",
              reviewed_at: "2026-07-28T10:01:00Z",
              record_path: "Preferences/response-style.md",
            }),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    expect(await screen.findByText("Memory review")).toBeInTheDocument();
    expect(screen.getByText("Nothing has been saved yet.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Preferred response style" },
    });
    fireEvent.change(screen.getByLabelText("Information to save"), {
      target: { value: "Use concise answers with recommendations." },
    });
    fireEvent.click(screen.getByRole("button", { name: "Approve & save" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Saved locally to Preferences/response-style.md.",
    );
    expect(screen.queryByText("Memory review")).toBeNull();
    const reviewCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        input.toString().endsWith("/knowledge/candidates/candidate-1") &&
        init?.method === "PUT",
    );
    expect(reviewCall).toBeDefined();
    expect(new Headers(reviewCall?.[1]?.headers).get("X-Nova-Intent")).toBe(
      "local-user-action",
    );
    expect(JSON.parse(reviewCall?.[1]?.body as string)).toEqual({
      action: "approve",
      kind: "preference",
      title: "Preferred response style",
      content: "Use concise answers with recommendations.",
    });
  });

  it("removes a suggested addition after its approved record covers the gap", async () => {
    const candidate = {
      id: "candidate-response-style",
      conversation_id: "conversation-1",
      source_message_id: "user-1",
      kind: "preference",
      title: "Prefer responses that are concise",
      content: "I prefer responses that are concise and direct.",
      source_excerpt: "Remember that I prefer responses that are concise and direct.",
      reason: "You explicitly asked Nova to remember this.",
      confidence: 1,
      explicit_request: true,
      status: "pending",
      created_at: "2026-08-03T10:00:00Z",
      reviewed_at: null,
      record_path: null,
    };
    const missingResponseStyle = {
      id: "response-style",
      domain: "preferences",
      title: "How you like replies",
      why: "Helps Nova answer in the way you prefer.",
      suggestion: "Say whether you want short, detailed, or step-by-step replies.",
      priority: 4,
      core: true,
      review_days: 180,
      status: "missing",
      last_reviewed: null,
      matched_record_ids: [],
      matched_record_titles: [],
    };
    const coveredResponseStyle = {
      ...missingResponseStyle,
      status: "covered",
      last_reviewed: "2026-08-03T10:01:00Z",
      matched_record_ids: ["record-response-style"],
      matched_record_titles: [candidate.title],
    };
    let reviewed = false;
    let qualityRequests = 0;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) return Promise.resolve(jsonResponse([]));
        if (url.endsWith("/chat/documents")) return Promise.resolve(jsonResponse([]));
        if (url.includes("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse(reviewed ? [] : [candidate]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(
            jsonResponse(
              reviewed
                ? [
                    {
                      ...knowledgeRecord,
                      id: "record-response-style",
                      candidate_id: candidate.id,
                      kind: candidate.kind,
                      title: candidate.title,
                      content: candidate.content,
                    },
                  ]
                : [],
            ),
          );
        }
        if (url.endsWith("/knowledge/quality")) {
          qualityRequests += 1;
          return Promise.resolve(
            jsonResponse({
              ...knowledgeQualityReport,
              requirements: [
                reviewed ? coveredResponseStyle : missingResponseStyle,
              ],
            }),
          );
        }
        if (
          url.endsWith(`/knowledge/candidates/${candidate.id}`) &&
          init?.method === "PUT"
        ) {
          reviewed = true;
          return Promise.resolve(
            jsonResponse({
              ...candidate,
              status: "approved",
              reviewed_at: "2026-08-03T10:01:00Z",
              record_path: "Preferences/response-style.md",
            }),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    expect(
      await screen.findByRole("button", {
        name: "Add How you like replies through chat",
      }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Approve & save" }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", {
          name: "Add How you like replies through chat",
        }),
      ).toBeNull();
    });
    expect(qualityRequests).toBeGreaterThanOrEqual(2);
  });

  it("requires separate-record confirmation for a possible duplicate", async () => {
    const candidate = {
      id: "candidate-duplicate",
      conversation_id: "conversation-1",
      source_message_id: "user-1",
      kind: "fact",
      title: "Automated approval phrase copy",
      content: "The automated approval phrase is amber lighthouse.",
      source_excerpt: "Remember the automated approval phrase.",
      reason: "You explicitly asked Nova to remember this.",
      confidence: 1,
      explicit_request: true,
      status: "pending",
      created_at: "2026-07-28T10:00:00Z",
      reviewed_at: null,
      record_path: null,
      duplicate_record_id: knowledgeRecord.id,
      duplicate_title: knowledgeRecord.title,
      duplicate_path: knowledgeRecord.relative_path,
      duplicate_score: 1,
    };
    let reviewed = false;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) return Promise.resolve(jsonResponse([]));
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse(reviewed ? [] : [candidate]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([knowledgeRecord]));
        }
        if (
          url.endsWith("/knowledge/candidates/candidate-duplicate") &&
          init?.method === "PUT"
        ) {
          reviewed = true;
          return Promise.resolve(
            jsonResponse({
              ...candidate,
              status: "approved",
              reviewed_at: "2026-07-28T10:01:00Z",
              record_path: "Facts/automated-approval-phrase-copy.md",
            }),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    expect(await screen.findByText("Possible duplicate")).toBeInTheDocument();
    const approve = screen.getByRole("button", { name: "Approve & save" });
    expect(approve).toBeDisabled();
    fireEvent.click(
      screen.getByRole("checkbox", { name: "Keep both as separate records" }),
    );
    expect(approve).toBeEnabled();
    fireEvent.click(approve);

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Saved locally to Facts/automated-approval-phrase-copy.md.",
    );
    const reviewCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        input
          .toString()
          .endsWith("/knowledge/candidates/candidate-duplicate") &&
        init?.method === "PUT",
    );
    expect(JSON.parse(reviewCall?.[1]?.body as string)).toMatchObject({
      action: "approve",
      duplicate_confirmation: "CREATE SEPARATE RECORD",
    });
  });

  it("creates an immutable revision and a verified knowledge snapshot", async () => {
    let currentRecord = knowledgeRecord;
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) return Promise.resolve(jsonResponse([]));
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records") && !init?.method) {
          return Promise.resolve(jsonResponse([currentRecord]));
        }
        if (
          url.endsWith("/knowledge/records/record-1") &&
          init?.method === "PUT"
        ) {
          currentRecord = {
            ...knowledgeRecord,
            title: "Revised approval phrase",
            content: "The revised approval phrase is golden comet.",
            relative_path: "Facts/revised-approval-phrase-r2.md",
            sha256: "b".repeat(64),
            revision: 2,
            updated_at: "2026-07-28T10:30:00Z",
          };
          return Promise.resolve(jsonResponse(currentRecord));
        }
        if (
          url.endsWith("/knowledge/snapshots") &&
          init?.method === "POST"
        ) {
          return Promise.resolve(
            jsonResponse({
              filename: "nova-knowledge-20260728T103100Z.zip",
              size_bytes: 2048,
              sha256: "c".repeat(64),
              record_count: 1,
              file_count: 2,
              created_at: "2026-07-28T10:31:00Z",
            }),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    fireEvent.click(await screen.findByText("Automated approval phrase"));
    fireEvent.change(screen.getByLabelText("Approved information"), {
      target: { value: "The revised approval phrase is golden comet." },
    });
    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Revised approval phrase" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save new revision" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Updated Revised approval phrase to revision 2.",
    );
    const updateCall = fetchMock.mock.calls.find(
      ([input, init]) =>
        input.toString().endsWith("/knowledge/records/record-1") &&
        init?.method === "PUT",
    );
    expect(new Headers(updateCall?.[1]?.headers).get("X-Nova-Intent")).toBe(
      "local-user-action",
    );
    expect(JSON.parse(updateCall?.[1]?.body as string)).toMatchObject({
      action: "update",
      title: "Revised approval phrase",
      content: "The revised approval phrase is golden comet.",
    });

    fireEvent.click(
      screen.getByRole("button", { name: "Create verified snapshot" }),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Verified knowledge snapshot created",
    );
  });

  it("states clearly when no approved knowledge matches", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        if (url.includes("/knowledge/candidates")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/chat/conversations/conversation-1")) {
          return Promise.resolve(
            jsonResponse({
              ...conversation,
              model: "qwen3:8b",
              message_count: 2,
              messages: [
                {
                  id: "user-no-match",
                  conversation_id: conversation.id,
                  role: "user",
                  content: "What is my favourite fruit?",
                  model: "qwen3:8b",
                  created_at: "2026-07-28T11:00:00Z",
                  knowledge_checked: false,
                  sources: [],
                },
                {
                  id: "assistant-no-match",
                  conversation_id: conversation.id,
                  role: "assistant",
                  content: "I do not have approved knowledge for that.",
                  model: "qwen3:8b",
                  created_at: "2026-07-28T11:00:01Z",
                  knowledge_checked: true,
                  sources: [],
                },
              ],
            }),
          );
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(
            jsonResponse([{ ...conversation, message_count: 2 }]),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      }),
    );

    render(<ChatApp />);

    expect(
      await screen.findByText("No approved knowledge matched this message."),
    ).toBeInTheDocument();
  });

  it("shows transparent coverage, freshness, retrieval, and gap guidance", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) return Promise.resolve(jsonResponse([]));
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([knowledgeRecord]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        throw new Error(`Unexpected request: ${url}`);
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Knowledge health")).toBeInTheDocument();
    expect(screen.getByText("16.7%")).toBeInTheDocument();
    expect(screen.getAllByText("100%")).toHaveLength(2);
    expect(
      screen.getByText(/NOVA scores its published capability checklist, not you/),
    ).toBeInTheDocument();
    expect(screen.getByText("What you want to achieve")).toBeInTheDocument();
    expect(screen.getAllByText("Core").length).toBeGreaterThan(0);
    expect(screen.getByText("Emergency contacts or plan")).toBeInTheDocument();
    expect(screen.getByText("Optional")).toBeInTheDocument();
    expect(screen.getAllByText("Missing")).toHaveLength(3);
    expect(
      screen.getAllByLabelText("Priority 5 of 5")[0],
    ).toBeInTheDocument();
  });

  it("keeps chat usable when the quality report is unavailable", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/chat/conversations")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(
            jsonResponse({ detail: "Quality integrity check failed." }, 422),
          );
        }
        throw new Error(`Unexpected request: ${url}`);
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Local AI ready")).toBeInTheDocument();
    expect(screen.getByText("Knowledge health")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(
      screen.getByText(/Chat and approved knowledge remain usable/),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Message Nova" })).toBeEnabled();
  });

  it("prepares an editable missing-knowledge prompt without sending or saving", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/chat/models")) {
        return Promise.resolve(
          jsonResponse([
            {
              name: "qwen3:8b",
              size_bytes: 5_200_000_000,
              parameter_size: "8.2B",
              quantization_level: "Q4_K_M",
            },
          ]),
        );
      }
      if (url.endsWith("/chat/conversations")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/candidates?status=pending")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/records")) {
        return Promise.resolve(jsonResponse([knowledgeRecord]));
      }
      if (url.endsWith("/knowledge/quality")) {
        return Promise.resolve(jsonResponse(knowledgeQualityReport));
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const addButton = await screen.findByRole("button", {
      name: "Add What you want to achieve through chat",
    });
    expect(
      screen.getAllByText("Examples — you do not need to add these.").length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText("A first name, such as Sam")).not.toBeInTheDocument();
    const callsBeforeClick = fetchMock.mock.calls.length;
    fireEvent.click(addButton);

    const composer = screen.getByRole("textbox", { name: "Message Nova" });
    expect(composer).toHaveValue("Remember that something I want to achieve is ");
    expect(composer).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Nothing has been sent or saved.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeClick);

    fireEvent.click(screen.getByRole("button", { name: "Build a steady exercise habit" }));
    expect(composer).toHaveValue(
      "Remember that I want to build a steady exercise habit.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeClick);
  });

  it("preserves optional status while preparing an optional prompt", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/chat/models")) {
        return Promise.resolve(
          jsonResponse([
            {
              name: "qwen3:8b",
              size_bytes: 5_200_000_000,
              parameter_size: "8.2B",
              quantization_level: "Q4_K_M",
            },
          ]),
        );
      }
      if (url.endsWith("/chat/conversations")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/candidates?status=pending")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/records")) {
        return Promise.resolve(jsonResponse([knowledgeRecord]));
      }
      if (url.endsWith("/knowledge/quality")) {
        return Promise.resolve(jsonResponse(knowledgeQualityReport));
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const addButton = await screen.findByRole("button", {
      name: "Add Emergency contacts or plan through chat",
    });
    fireEvent.click(addButton);

    expect(screen.getByText("Optional")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Message Nova" })).toHaveValue(
      "Remember that an emergency step I want to save is ",
    );
  });

  it("opens the exact approved record when a review is due", async () => {
    const staleQualityReport = {
      ...knowledgeQualityReport,
      requirements: knowledgeQualityReport.requirements.map((requirement) =>
        requirement.id === "current-goals"
          ? {
              ...requirement,
              status: "stale",
              last_reviewed: "2025-01-01T00:00:00Z",
              matched_record_ids: [knowledgeRecord.id],
              matched_record_titles: [knowledgeRecord.title],
            }
          : requirement,
      ),
    };
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/chat/models")) {
        return Promise.resolve(
          jsonResponse([
            {
              name: "qwen3:8b",
              size_bytes: 5_200_000_000,
              parameter_size: "8.2B",
              quantization_level: "Q4_K_M",
            },
          ]),
        );
      }
      if (url.endsWith("/chat/conversations")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/candidates?status=pending")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/records")) {
        return Promise.resolve(jsonResponse([knowledgeRecord]));
      }
      if (url.endsWith("/knowledge/quality")) {
        return Promise.resolve(jsonResponse(staleQualityReport));
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    expect(
      await screen.findByText(
        `Approved record: ${knowledgeRecord.title}`,
      ),
    ).toBeInTheDocument();
    const callsBeforeClick = fetchMock.mock.calls.length;
    fireEvent.click(
      screen.getByRole("button", {
        name: "Review What you want to achieve record",
      }),
    );

    const titleInput = screen.getByDisplayValue(knowledgeRecord.title);
    expect(titleInput.closest("details")).toHaveAttribute("open");
    expect(titleInput).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Review it before choosing whether to save a new revision.",
    );
    expect(fetchMock).toHaveBeenCalledTimes(callsBeforeClick);
  });

  it("prepares a focus-page project prompt without sending or saving", async () => {
    window.history.replaceState(
      {},
      "",
      "/chat.html?knowledge=active-projects",
    );
    let writeRequested = false;
    const fetchMock = vi.fn((
      input: string | URL | Request,
      init?: RequestInit,
    ) => {
      if (init?.method === "POST") writeRequested = true;
      const url = input.toString();
      if (url.endsWith("/chat/models")) {
        return Promise.resolve(
          jsonResponse([
            {
              name: "qwen3:8b",
              size_bytes: 5_200_000_000,
              parameter_size: "8.2B",
              quantization_level: "Q4_K_M",
            },
          ]),
        );
      }
      if (url.endsWith("/knowledge/records")) {
        return Promise.resolve(jsonResponse([]));
      }
      if (url.endsWith("/knowledge/quality")) {
        return Promise.resolve(jsonResponse(knowledgeQualityReport));
      }
      return Promise.resolve(jsonResponse([]));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const composer = await screen.findByRole("textbox", {
      name: "Message Nova",
    });
    await waitFor(() =>
      expect(composer).toHaveValue("Remember that a project I am working on is "),
    );
    expect(composer).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Nothing has been sent or saved.",
    );
    expect(writeRequested).toBe(false);
  });

  it("treats a linked example as editable draft text and makes no write", async () => {
    const linkedDraft = "Remember that <untrusted example text> stays editable.";
    window.history.replaceState(
      {},
      "",
      `/chat.html?knowledge=active-projects&example=${encodeURIComponent(linkedDraft)}`,
    );
    let writeRequested = false;
    const fetchMock = vi.fn((
      input: string | URL | Request,
      init?: RequestInit,
    ) => {
      if (init?.method && init.method !== "GET") writeRequested = true;
      const url = input.toString();
      if (url.endsWith("/chat/models")) {
        return Promise.resolve(
          jsonResponse([
            {
              name: "qwen3:8b",
              size_bytes: 5_200_000_000,
              parameter_size: "8.2B",
              quantization_level: "Q4_K_M",
            },
          ]),
        );
      }
      if (url.endsWith("/knowledge/quality")) {
        return Promise.resolve(jsonResponse(knowledgeQualityReport));
      }
      return Promise.resolve(jsonResponse([]));
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<ChatApp />);

    const composer = await screen.findByRole("textbox", { name: "Message Nova" });
    await waitFor(() => expect(composer).toHaveValue(linkedDraft));
    expect(screen.queryByText("<untrusted example text>")).not.toBeInTheDocument();
    expect(writeRequested).toBe(false);
  });

  it("opens the exact approved record requested by the focus page", async () => {
    window.history.replaceState(
      {},
      "",
      `/chat.html?record=${knowledgeRecord.id}`,
    );
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/chat/models")) {
          return Promise.resolve(
            jsonResponse([
              {
                name: "qwen3:8b",
                size_bytes: 5_200_000_000,
                parameter_size: "8.2B",
                quantization_level: "Q4_K_M",
              },
            ]),
          );
        }
        if (url.endsWith("/knowledge/records")) {
          return Promise.resolve(jsonResponse([knowledgeRecord]));
        }
        if (url.endsWith("/knowledge/quality")) {
          return Promise.resolve(jsonResponse(knowledgeQualityReport));
        }
        return Promise.resolve(jsonResponse([]));
      }),
    );

    render(<ChatApp />);

    const titleInput = await screen.findByDisplayValue(knowledgeRecord.title);
    await waitFor(() =>
      expect(titleInput.closest("details")).toHaveAttribute("open"),
    );
    expect(titleInput).toHaveFocus();
    expect(screen.getByRole("status")).toHaveTextContent(
      `Opened ${knowledgeRecord.title}.`,
    );
  });
});
