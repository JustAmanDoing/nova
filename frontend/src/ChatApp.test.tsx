import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ChatApp", () => {
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
        return Promise.resolve(jsonResponse([]));
      }),
    );

    render(<ChatApp />);

    expect(await screen.findByText("Local AI ready")).toBeInTheDocument();
    expect(screen.getByRole("combobox")).toHaveValue("qwen3:8b");
    expect(screen.getByText("Ready when you are.")).toBeInTheDocument();
    expect(
      screen.getByText(/A suggestion is never permanent/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Knowledge capture is local and approval-only/),
    ).toBeInTheDocument();
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
        if (url.includes("/knowledge/candidates")) {
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
                    },
                    {
                      id: "assistant-1",
                      conversation_id: conversation.id,
                      role: "assistant",
                      content: "Hello from Nova.",
                      model: "qwen3:8b",
                      created_at: "2026-07-28T09:01:01Z",
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

    const composer = await screen.findByRole("textbox", { name: "Message Nova" });
    fireEvent.change(composer, { target: { value: "Hello Nova" } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText("2 messages")).toBeInTheDocument();
    expect(screen.getByText("Hello from Nova.")).toBeInTheDocument();
    expect(screen.getByText("Hello Nova")).toBeInTheDocument();
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
        if (url.includes("/knowledge/candidates")) {
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
        if (url.includes("/knowledge/candidates")) {
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
    expect(screen.getByRole("textbox", { name: "Message Nova" })).toBeDisabled();
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
        if (url.endsWith("/knowledge/candidates?status=pending")) {
          return Promise.resolve(jsonResponse(reviewed ? [] : [candidate]));
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
});
