import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createChatConversation,
  getChatConversation,
  getChatConversations,
  getChatModels,
  streamChatMessage,
  type ChatConversationSummary,
  type ChatMessage,
  type ChatModel,
  type ChatStreamEvent,
} from "./lib/api";

type DraftMessage = Pick<ChatMessage, "id" | "role" | "content" | "model">;

function ChatApp() {
  const [models, setModels] = useState<ChatModel[]>([]);
  const [selectedModel, setSelectedModel] = useState("");
  const [conversations, setConversations] = useState<ChatConversationSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<DraftMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const draftIdRef = useRef(0);
  const transcriptRef = useRef<HTMLDivElement | null>(null);

  const refreshConversations = useCallback(async () => {
    const records = await getChatConversations();
    setConversations(records);
    return records;
  }, []);

  const openConversation = useCallback(async (conversationId: string) => {
    const conversation = await getChatConversation(conversationId);
    setSelectedId(conversation.id);
    setMessages(conversation.messages);
    if (conversation.model) setSelectedModel(conversation.model);
    setNotice(null);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    Promise.allSettled([
      getChatModels(controller.signal),
      getChatConversations(controller.signal),
    ])
      .then(async ([modelResult, conversationResult]) => {
        if (controller.signal.aborted) return;
        const failures: string[] = [];
        if (modelResult.status === "fulfilled") {
          setModels(modelResult.value);
          setSelectedModel(modelResult.value[0]?.name ?? "");
        } else {
          failures.push(errorMessage(modelResult.reason));
        }
        if (conversationResult.status === "fulfilled") {
          setConversations(conversationResult.value);
          if (conversationResult.value[0]) {
            try {
              await openConversation(conversationResult.value[0].id);
            } catch (error: unknown) {
              failures.push(errorMessage(error));
            }
          }
        } else {
          failures.push(errorMessage(conversationResult.reason));
        }
        setNotice(failures[0] ?? null);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setNotice(errorMessage(error));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [openConversation]);

  useEffect(() => {
    transcriptRef.current?.scrollTo({
      top: transcriptRef.current.scrollHeight,
      behavior: generating ? "auto" : "smooth",
    });
  }, [messages, generating]);

  async function handleNewConversation() {
    if (generating) return;
    try {
      const conversation = await createChatConversation();
      setConversations((current) => [conversation, ...current]);
      setSelectedId(conversation.id);
      setMessages([]);
      setNotice(null);
    } catch (error: unknown) {
      setNotice(error instanceof Error ? error.message : "Unable to start a chat.");
    }
  }

  async function ensureConversation(): Promise<string> {
    if (selectedId) return selectedId;
    const conversation = await createChatConversation();
    setConversations((current) => [conversation, ...current]);
    setSelectedId(conversation.id);
    return conversation.id;
  }

  async function handleSend(event: FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || !selectedModel || generating) return;
    setDraft("");
    setNotice(null);
    setGenerating(true);
    const controller = new AbortController();
    abortRef.current = controller;
    let conversationId: string | null = null;
    draftIdRef.current += 1;
    const userId = `draft-user-${draftIdRef.current}`;
    const assistantId = `draft-assistant-${draftIdRef.current}`;
    try {
      conversationId = await ensureConversation();
      setMessages((current) => [
        ...current,
        { id: userId, role: "user", content, model: selectedModel },
        { id: assistantId, role: "assistant", content: "", model: selectedModel },
      ]);
      await streamChatMessage(
        conversationId,
        selectedModel,
        content,
        (streamEvent) => handleStreamEvent(streamEvent, assistantId),
        controller.signal,
      );
      await Promise.all([
        openConversation(conversationId),
        refreshConversations(),
      ]);
    } catch (error: unknown) {
      const stopped = error instanceof DOMException && error.name === "AbortError";
      if (!stopped) {
        setMessages((current) =>
          current.filter((message) => message.id !== assistantId),
        );
      }
      if (conversationId) {
        try {
          await Promise.all([
            openConversation(conversationId),
            refreshConversations(),
          ]);
        } catch {
          // Keep the original stop or provider failure as the actionable notice.
        }
      }
      setNotice(
        stopped
          ? "Generation stopped."
          : error instanceof Error
            ? error.message
            : "Nova could not complete the reply.",
      );
    } finally {
      abortRef.current = null;
      setGenerating(false);
    }
  }

  function handleStreamEvent(event: ChatStreamEvent, assistantId: string) {
    if (event.type === "delta") {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? { ...message, content: message.content + event.content }
            : message,
        ),
      );
    }
    if (event.type === "error") throw new Error(event.message);
  }

  function stopGeneration() {
    abortRef.current?.abort();
  }

  return (
    <main className="chat-shell">
      <nav className="nav chat-nav" aria-label="Primary navigation">
        <a className="brand" href="/">
          <span className="brand-mark" aria-hidden="true">N</span>
          Nova
        </a>
        <div className="chat-nav-links">
          <a className="chat-nav-link active" href="/chat.html" aria-current="page">
            Chat
          </a>
          <a className="chat-nav-link" href="/">Intake</a>
        </div>
        <span className={`chat-provider ${models.length ? "online" : "offline"}`}>
          <span aria-hidden="true" />
          {models.length ? "Local AI ready" : "Local AI unavailable"}
        </span>
      </nav>

      <div className="chat-layout">
        <aside className="conversation-sidebar" aria-label="Conversation history">
          <div className="sidebar-heading">
            <div>
              <p className="section-number">Local history</p>
              <h1>Conversations</h1>
            </div>
            <button
              type="button"
              className="new-chat-button"
              onClick={handleNewConversation}
              disabled={generating}
            >
              New
            </button>
          </div>
          <div className="conversation-list">
            {conversations.length ? (
              conversations.map((conversation) => (
                <button
                  type="button"
                  key={conversation.id}
                  className={conversation.id === selectedId ? "selected" : ""}
                  onClick={() => void openConversation(conversation.id)}
                  disabled={generating}
                >
                  <strong>{conversation.title}</strong>
                  <span>
                    {conversation.message_count} message
                    {conversation.message_count === 1 ? "" : "s"}
                  </span>
                </button>
              ))
            ) : (
              <p className="conversation-empty">
                Your conversations stay on this PC.
              </p>
            )}
          </div>
          <p className="privacy-note">
            Chat history is local. Nothing from a conversation becomes permanent
            personal knowledge in this prototype.
          </p>
        </aside>

        <section className="chat-stage" aria-labelledby="chat-title">
          <header className="chat-heading">
            <div>
              <p className="eyebrow">Milestone 54 · Local Chat Core</p>
              <h2 id="chat-title">Talk with Nova.</h2>
            </div>
            <label>
              <span>Local model</span>
              <select
                value={selectedModel}
                onChange={(event) => setSelectedModel(event.target.value)}
                disabled={generating || models.length === 0}
              >
                {models.map((model) => (
                  <option key={model.name} value={model.name}>
                    {model.name}
                    {model.parameter_size ? ` · ${model.parameter_size}` : ""}
                  </option>
                ))}
              </select>
            </label>
          </header>

          <div
            className="chat-transcript"
            ref={transcriptRef}
            aria-live="polite"
            aria-busy={generating}
          >
            {loading ? (
              <div className="chat-welcome">
                <span className="nova-orb" aria-hidden="true">N</span>
                <p>Connecting to your local AI…</p>
              </div>
            ) : messages.length === 0 ? (
              <div className="chat-welcome">
                <span className="nova-orb" aria-hidden="true">N</span>
                <h3>Ready when you are.</h3>
                <p>
                  This prototype talks to Ollama on your PC. It can converse and
                  keep local chat history, but it cannot act on files or silently
                  save personal facts.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <article className={`chat-message ${message.role}`} key={message.id}>
                  <span>{message.role === "user" ? "You" : "N"}</span>
                  <div>
                    <strong>{message.role === "user" ? "You" : "Nova"}</strong>
                    <p>
                      {message.content ||
                        (message.role === "assistant" && generating
                          ? "Thinking…"
                          : "")}
                    </p>
                  </div>
                </article>
              ))
            )}
          </div>

          {notice ? <p className="chat-notice" role="status">{notice}</p> : null}

          <form className="chat-composer" onSubmit={handleSend}>
            <label className="sr-only" htmlFor="chat-message">Message Nova</label>
            <textarea
              id="chat-message"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder={
                models.length
                  ? "Message Nova…"
                  : "Start Ollama to chat with Nova"
              }
              rows={2}
              disabled={models.length === 0 || generating}
            />
            {generating ? (
              <button type="button" className="stop-button" onClick={stopGeneration}>
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!draft.trim() || !selectedModel}
              >
                Send
              </button>
            )}
          </form>
          <p className="chat-boundary">
            Nova prepares answers only. Tools, web access, RAG, and permanent
            memory are disabled in this milestone.
          </p>
        </section>
      </div>
    </main>
  );
}

export default ChatApp;

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Nova could not connect to the local model provider.";
}
