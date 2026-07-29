import {
  type FormEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createKnowledgeSnapshot,
  createChatConversation,
  getChatConversation,
  getChatConversations,
  getChatModels,
  getKnowledgeCandidates,
  getKnowledgeQuality,
  getKnowledgeRecords,
  reviewKnowledgeCandidate,
  streamChatMessage,
  updateKnowledgeRecord,
  type ChatConversationSummary,
  type ChatKnowledgeSource,
  type ChatMessage,
  type ChatModel,
  type ChatStreamEvent,
  type KnowledgeCandidate,
  type KnowledgeKind,
  type KnowledgeQualityReport,
  type KnowledgeRecord,
  type KnowledgeRecordLifecycleRequest,
  type KnowledgeRequirementQuality,
} from "./lib/api";

type DraftMessage = Pick<
  ChatMessage,
  "id" | "role" | "content" | "model" | "knowledge_checked" | "sources"
>;

const KNOWLEDGE_PROMPT_STARTERS: Record<string, string> = {
  "preferred-name": "Remember that my name is ",
  "response-style": "Remember that I prefer responses that ",
  "current-goals": "Remember that my current goal is ",
  "active-projects": "Remember that my active project is ",
  "timezone-location": "Remember that my timezone or general location is ",
  "work-context": "Remember that my work context or schedule is ",
  "technology-environment":
    "Remember that my main technology environment is ",
  "household-context":
    "Remember that the household context useful for planning is ",
  "vehicle-context": "Remember that my vehicle context is ",
  "home-responsibilities":
    "Remember that my current home responsibility is ",
  "financial-goals": "Remember that my high-level financial goal is ",
  "health-preferences":
    "Remember that my health or dietary preference is ",
  "emergency-plan":
    "Remember that my emergency plan or contact process is ",
};

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
  const [knowledgeCandidates, setKnowledgeCandidates] = useState<
    KnowledgeCandidate[]
  >([]);
  const [knowledgeRecords, setKnowledgeRecords] = useState<KnowledgeRecord[]>([]);
  const [knowledgeQuality, setKnowledgeQuality] =
    useState<KnowledgeQualityReport | null>(null);
  const [knowledgeQualityError, setKnowledgeQualityError] =
    useState<string | null>(null);
  const [snapshotting, setSnapshotting] = useState(false);
  const [reviewRequest, setReviewRequest] = useState<{
    recordId: string;
    requestId: number;
  } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const draftIdRef = useRef(0);
  const reviewRequestIdRef = useRef(0);
  const transcriptRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  const refreshConversations = useCallback(async () => {
    const records = await getChatConversations();
    setConversations(records);
    return records;
  }, []);

  const refreshKnowledgeCandidates = useCallback(async () => {
    const records = await getKnowledgeCandidates("pending");
    setKnowledgeCandidates(records);
    return records;
  }, []);

  const refreshKnowledgeRecords = useCallback(async () => {
    const records = await getKnowledgeRecords();
    setKnowledgeRecords(records);
    return records;
  }, []);

  const refreshKnowledgeQuality = useCallback(async () => {
    try {
      const report = await getKnowledgeQuality();
      setKnowledgeQuality(report);
      setKnowledgeQualityError(null);
      return report;
    } catch (error: unknown) {
      setKnowledgeQualityError(errorMessage(error));
      return null;
    }
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
      getKnowledgeCandidates("pending", controller.signal),
      getKnowledgeRecords(controller.signal),
      getKnowledgeQuality(controller.signal),
    ])
      .then(
        async ([
          modelResult,
          conversationResult,
          knowledgeResult,
          recordResult,
          qualityResult,
        ]) => {
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
        if (knowledgeResult.status === "fulfilled") {
          setKnowledgeCandidates(knowledgeResult.value);
        } else {
          failures.push(errorMessage(knowledgeResult.reason));
        }
        if (recordResult.status === "fulfilled") {
          setKnowledgeRecords(recordResult.value);
        } else {
          failures.push(errorMessage(recordResult.reason));
        }
        if (qualityResult.status === "fulfilled") {
          setKnowledgeQuality(qualityResult.value);
          setKnowledgeQualityError(null);
        } else {
          setKnowledgeQualityError(errorMessage(qualityResult.reason));
        }
        setNotice(failures[0] ?? null);
        },
      )
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
    let knowledgeWarning: string | null = null;
    draftIdRef.current += 1;
    const userId = `draft-user-${draftIdRef.current}`;
    const assistantId = `draft-assistant-${draftIdRef.current}`;
    try {
      conversationId = await ensureConversation();
      setMessages((current) => [
        ...current,
        {
          id: userId,
          role: "user",
          content,
          model: selectedModel,
          knowledge_checked: false,
          sources: [],
        },
        {
          id: assistantId,
          role: "assistant",
          content: "",
          model: selectedModel,
          knowledge_checked: false,
          sources: [],
        },
      ]);
      await streamChatMessage(
        conversationId,
        selectedModel,
        content,
        (streamEvent) => {
          if (streamEvent.type === "knowledge_warning") {
            knowledgeWarning = streamEvent.message;
            return;
          }
          handleStreamEvent(streamEvent, assistantId);
        },
        controller.signal,
      );
      await Promise.all([
        openConversation(conversationId),
        refreshConversations(),
        refreshKnowledgeCandidates(),
        refreshKnowledgeRecords(),
        refreshKnowledgeQuality(),
      ]);
      if (knowledgeWarning) setNotice(knowledgeWarning);
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
            refreshKnowledgeCandidates(),
            refreshKnowledgeRecords(),
            refreshKnowledgeQuality(),
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
    if (event.type === "knowledge") {
      setMessages((current) =>
        current.map((message) =>
          message.id === assistantId
            ? {
                ...message,
                knowledge_checked: event.checked,
                sources: event.sources,
              }
            : message,
        ),
      );
    }
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

  async function handleKnowledgeReview(
    candidateId: string,
    review: {
      action: "approve" | "reject";
      kind?: KnowledgeKind;
      title?: string;
      content?: string;
      duplicate_confirmation?: string;
    },
  ) {
    try {
      const reviewed = await reviewKnowledgeCandidate(candidateId, review);
      await Promise.all([
        refreshKnowledgeCandidates(),
        refreshKnowledgeRecords(),
        refreshKnowledgeQuality(),
      ]);
      setNotice(
        reviewed.status === "approved"
          ? `Saved locally to ${reviewed.record_path}.`
          : "Not saved. The proposal was rejected.",
      );
    } catch (error: unknown) {
      setNotice(errorMessage(error));
    }
  }

  async function handleKnowledgeLifecycle(
    recordId: string,
    lifecycle: KnowledgeRecordLifecycleRequest,
  ) {
    try {
      const record = await updateKnowledgeRecord(recordId, lifecycle);
      await Promise.all([
        refreshKnowledgeRecords(),
        refreshKnowledgeQuality(),
      ]);
      setReviewRequest(null);
      setNotice(
        record.status === "retired"
          ? `Retired ${record.title}. Its files and history were retained.`
          : `Updated ${record.title} to revision ${record.revision}.`,
      );
    } catch (error: unknown) {
      setNotice(errorMessage(error));
    }
  }

  function handlePrepareKnowledge(requirement: KnowledgeRequirementQuality) {
    setDraft(
      KNOWLEDGE_PROMPT_STARTERS[requirement.id] ??
        `Remember that ${requirement.title.toLowerCase()} is `,
    );
    setNotice(
      `Prepared an editable prompt for ${requirement.title}. ` +
        "Nothing has been sent or saved.",
    );
    window.requestAnimationFrame(() => composerRef.current?.focus());
  }

  function handleReviewKnowledge(requirement: KnowledgeRequirementQuality) {
    const recordId = requirement.matched_record_ids[0];
    if (!recordId) {
      setNotice(
        `NOVA could not find the approved record for ${requirement.title}. ` +
          "No change was made.",
      );
      return;
    }
    reviewRequestIdRef.current += 1;
    setReviewRequest({
      recordId,
      requestId: reviewRequestIdRef.current,
    });
    setNotice(
      `Opened the approved record for ${requirement.title}. ` +
        "Review it before choosing whether to save a new revision.",
    );
  }

  async function handleKnowledgeSnapshot() {
    setSnapshotting(true);
    try {
      const snapshot = await createKnowledgeSnapshot();
      setNotice(
        `Verified knowledge snapshot created: ${snapshot.filename} ` +
          `(${snapshot.file_count} files, SHA-256 ${snapshot.sha256.slice(0, 12)}…).`,
      );
    } catch (error: unknown) {
      setNotice(errorMessage(error));
    } finally {
      setSnapshotting(false);
    }
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
            Chat history and approved knowledge stay local. A suggestion is never
            permanent until you choose Approve &amp; save.
          </p>
        </aside>

        <section className="chat-stage" aria-labelledby="chat-title">
          <header className="chat-heading">
            <div>
              <p className="eyebrow">Milestone 59 · Guided Onboarding</p>
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
                  Nova can use owner-approved local knowledge and show the exact
                  record it considered. Say “Remember that…” to prepare a review
                  card. Nova never silently saves personal facts.
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
                    {message.role === "assistant" && message.knowledge_checked ? (
                      <KnowledgeSources sources={message.sources} />
                    ) : null}
                  </div>
                </article>
              ))
            )}
          </div>

          {knowledgeCandidates.length ? (
            <section className="knowledge-review" aria-labelledby="knowledge-title">
              <div className="knowledge-review-heading">
                <div>
                  <p className="section-number">Owner approval required</p>
                  <h3 id="knowledge-title">Memory review</h3>
                </div>
                <span>{knowledgeCandidates.length} pending</span>
              </div>
              <div className="knowledge-candidate-list">
                {knowledgeCandidates.map((candidate) => (
                  <KnowledgeCandidateCard
                    key={candidate.id}
                    candidate={candidate}
                    onReview={handleKnowledgeReview}
                  />
                ))}
              </div>
            </section>
          ) : null}

          <KnowledgeHealth
            report={knowledgeQuality}
            error={knowledgeQualityError}
            actionsDisabled={generating}
            onPrepare={handlePrepareKnowledge}
            onReview={handleReviewKnowledge}
          />

          <section className="knowledge-library" aria-labelledby="library-title">
            <div className="knowledge-review-heading">
              <div>
                <p className="section-number">Owner-controlled records</p>
                <h3 id="library-title">Knowledge library</h3>
              </div>
              <div className="knowledge-library-tools">
                <span>
                  {knowledgeRecords.filter((record) => record.status === "active").length}
                  {" active"}
                </span>
                <button
                  type="button"
                  onClick={() => void handleKnowledgeSnapshot()}
                  disabled={snapshotting}
                >
                  {snapshotting ? "Verifying…" : "Create verified snapshot"}
                </button>
              </div>
            </div>
            {knowledgeRecords.length ? (
              <div className="knowledge-record-list">
                {knowledgeRecords.map((record) => (
                  <KnowledgeRecordCard
                    key={record.id}
                    record={record}
                    onLifecycle={handleKnowledgeLifecycle}
                    reviewRequestId={
                      reviewRequest?.recordId === record.id
                        ? reviewRequest.requestId
                        : null
                    }
                  />
                ))}
              </div>
            ) : (
              <p className="knowledge-library-empty">
                No approved records yet. Use “Remember that…” to prepare one.
              </p>
            )}
          </section>

          {notice ? <p className="chat-notice" role="status">{notice}</p> : null}

          <form className="chat-composer" onSubmit={handleSend}>
            <label className="sr-only" htmlFor="chat-message">Message Nova</label>
            <textarea
              ref={composerRef}
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
            Retrieval uses active, approved local records only. Updates create
            immutable revisions; retirement never deletes a knowledge file.
            Tools, web access, autonomous actions, and general document search
            remain disabled.
          </p>
        </section>
      </div>
    </main>
  );
}

export default ChatApp;

function KnowledgeHealth({
  report,
  error,
  actionsDisabled,
  onPrepare,
  onReview,
}: {
  report: KnowledgeQualityReport | null;
  error: string | null;
  actionsDisabled: boolean;
  onPrepare: (requirement: KnowledgeRequirementQuality) => void;
  onReview: (requirement: KnowledgeRequirementQuality) => void;
}) {
  if (error) {
    return (
      <section className="knowledge-health" aria-labelledby="knowledge-health-title">
        <div className="knowledge-review-heading">
          <div>
            <p className="section-number">Read-only local report</p>
            <h3 id="knowledge-health-title">Knowledge health</h3>
          </div>
          <span>Unavailable</span>
        </div>
        <p className="knowledge-health-unavailable">
          The quality report is unavailable. Chat and approved knowledge remain
          usable. {error}
        </p>
      </section>
    );
  }

  if (!report) {
    return (
      <section className="knowledge-health" aria-labelledby="knowledge-health-title">
        <div className="knowledge-review-heading">
          <div>
            <p className="section-number">Read-only local report</p>
            <h3 id="knowledge-health-title">Knowledge health</h3>
          </div>
          <span>Checking…</span>
        </div>
      </section>
    );
  }

  const nextSuggestions = report.requirements
    .filter((requirement) => requirement.status !== "covered")
    .sort(
      (left, right) =>
        Number(right.core) - Number(left.core) ||
        right.priority - left.priority ||
        left.title.localeCompare(right.title),
    )
    .slice(0, 5);

  return (
    <section className="knowledge-health" aria-labelledby="knowledge-health-title">
      <div className="knowledge-review-heading">
        <div>
          <p className="section-number">Read-only local report</p>
          <h3 id="knowledge-health-title">Knowledge health</h3>
        </div>
        <span>{report.active_record_count} verified active</span>
      </div>
      <p className="knowledge-health-boundary">
        NOVA scores its published capability checklist, not you. Optional
        information never lowers core coverage.
      </p>
      <div className="knowledge-health-metrics">
        <article>
          <span>Core coverage</span>
          <strong>{report.completion_percent}%</strong>
          <small>
            {report.core_covered} of {report.core_total} checklist areas
          </small>
        </article>
        <article>
          <span>Freshness</span>
          <strong>{report.freshness_percent}%</strong>
          <small>
            {report.fresh_covered} of {report.covered_total} covered areas current
          </small>
        </article>
        <article>
          <span>Retrieval self-check</span>
          <strong>{report.retrieval_percent}%</strong>
          <small>
            {report.retrieval_passed} of {report.retrieval_checked} records found
          </small>
        </article>
      </div>
      <details className="knowledge-health-details">
        <summary>How this is measured</summary>
        <p>{report.methodology}</p>
        <p>{report.limitation}</p>
      </details>
      <div className="knowledge-gaps">
        <div>
          <h4>Suggested next additions</h4>
          <span>Highest-value gaps first</span>
        </div>
        {nextSuggestions.length ? (
          <ol>
            {nextSuggestions.map((requirement) => (
              <li key={requirement.id}>
                <div>
                  <strong>{requirement.title}</strong>
                  <span
                    className={`knowledge-gap-scope ${
                      requirement.core ? "core" : "optional"
                    }`}
                  >
                    {requirement.core ? "Core" : "Optional"}
                  </span>
                  <span className="knowledge-gap-status">
                    {requirement.status === "stale" ? "Review due" : "Missing"}
                  </span>
                </div>
                <p>{requirement.suggestion}</p>
                {requirement.status === "stale" &&
                requirement.matched_record_titles[0] ? (
                  <p className="knowledge-gap-record">
                    Approved record: {requirement.matched_record_titles[0]}
                  </p>
                ) : null}
                <span
                  className="knowledge-gap-priority"
                  aria-label={`Priority ${requirement.priority} of 5`}
                >
                  <span aria-hidden="true">
                    {"★".repeat(requirement.priority)}
                    {"☆".repeat(5 - requirement.priority)}
                  </span>
                </span>
                <button
                  type="button"
                  className="knowledge-gap-action"
                  aria-label={
                    requirement.status === "stale"
                      ? `Review ${requirement.title} record`
                      : `Add ${requirement.title} through chat`
                  }
                  disabled={
                    actionsDisabled ||
                    (requirement.status === "stale" &&
                      !requirement.matched_record_ids[0])
                  }
                  onClick={() =>
                    requirement.status === "stale"
                      ? onReview(requirement)
                      : onPrepare(requirement)
                  }
                >
                  {requirement.status === "stale"
                    ? "Review record"
                    : "Add through chat"}
                </button>
              </li>
            ))}
          </ol>
        ) : (
          <p className="knowledge-health-complete">
            Every published checklist item is covered and current.
          </p>
        )}
      </div>
    </section>
  );
}


function KnowledgeSources({ sources }: { sources: ChatKnowledgeSource[] }) {
  if (!sources.length) {
    return (
      <p className="knowledge-no-match">
        No approved knowledge matched this message.
      </p>
    );
  }
  return (
    <section className="knowledge-sources" aria-label="Approved knowledge sources">
      <span>Approved knowledge</span>
      <ul>
        {sources.map((source) => (
          <li key={source.record_id}>
            <code>[{source.citation_label}]</code>
            <div>
              <strong>{source.title}</strong>
              <small>{source.relative_path}</small>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

const KNOWLEDGE_KIND_LABELS: Record<KnowledgeKind, string> = {
  fact: "Fact",
  preference: "Preference",
  goal: "Goal",
  project: "Project",
  lesson: "Lesson",
  rule: "Rule",
  reference: "Reference",
};

function KnowledgeCandidateCard({
  candidate,
  onReview,
}: {
  candidate: KnowledgeCandidate;
  onReview: (
    candidateId: string,
    review: {
      action: "approve" | "reject";
      kind?: KnowledgeKind;
      title?: string;
      content?: string;
      duplicate_confirmation?: string;
    },
  ) => Promise<void>;
}) {
  const [kind, setKind] = useState<KnowledgeKind>(candidate.kind);
  const [title, setTitle] = useState(candidate.title);
  const [content, setContent] = useState(candidate.content);
  const [saving, setSaving] = useState(false);
  const [separateConfirmed, setSeparateConfirmed] = useState(false);

  async function review(action: "approve" | "reject") {
    setSaving(true);
    try {
      await onReview(
        candidate.id,
        action === "approve"
          ? {
              action,
              kind,
              title: title.trim(),
              content: content.trim(),
              duplicate_confirmation:
                separateConfirmed
                  ? "CREATE SEPARATE RECORD"
                  : undefined,
            }
          : { action },
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className="knowledge-candidate">
      <div className="knowledge-candidate-summary">
        <strong>
          {candidate.explicit_request
            ? "You asked Nova to remember this"
            : "Suggested"}
        </strong>
        <span>Nothing has been saved yet.</span>
      </div>
      <p>{candidate.reason}</p>
      {candidate.duplicate_record_id ? (
        <div className="duplicate-warning" role="alert">
          <strong>Possible duplicate</strong>
          <p>
            This closely matches “{candidate.duplicate_title}” at{" "}
            <code>{candidate.duplicate_path}</code>.
          </p>
          <label>
            <input
              type="checkbox"
              checked={separateConfirmed}
              onChange={(event) => setSeparateConfirmed(event.target.checked)}
              disabled={saving}
            />
            Keep both as separate records
          </label>
        </div>
      ) : (
        <label className="separate-record-option">
          <input
            type="checkbox"
            checked={separateConfirmed}
            onChange={(event) => setSeparateConfirmed(event.target.checked)}
            disabled={saving}
          />
          If my edits match another record, keep both separately
        </label>
      )}
      <div className="knowledge-fields">
        <label>
          <span>Type</span>
          <select
            value={kind}
            onChange={(event) => setKind(event.target.value as KnowledgeKind)}
            disabled={saving}
          >
            {Object.entries(KNOWLEDGE_KIND_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Title</span>
          <input
            value={title}
            maxLength={120}
            onChange={(event) => setTitle(event.target.value)}
            disabled={saving}
          />
        </label>
        <label className="knowledge-content">
          <span>Information to save</span>
          <textarea
            value={content}
            maxLength={4000}
            rows={3}
            onChange={(event) => setContent(event.target.value)}
            disabled={saving}
          />
        </label>
      </div>
      <div className="knowledge-actions">
        <button
          type="button"
          className="reject-knowledge"
          onClick={() => void review("reject")}
          disabled={saving}
        >
          Don&apos;t save
        </button>
        <button
          type="button"
          className="approve-knowledge"
          onClick={() => void review("approve")}
          disabled={
            saving ||
            !title.trim() ||
            !content.trim() ||
            Boolean(candidate.duplicate_record_id && !separateConfirmed)
          }
        >
          {saving ? "Saving…" : "Approve & save"}
        </button>
      </div>
    </article>
  );
}

function KnowledgeRecordCard({
  record,
  onLifecycle,
  reviewRequestId,
}: {
  record: KnowledgeRecord;
  onLifecycle: (
    recordId: string,
    lifecycle: KnowledgeRecordLifecycleRequest,
  ) => Promise<void>;
  reviewRequestId: number | null;
}) {
  const [kind, setKind] = useState<KnowledgeKind>(record.kind);
  const [title, setTitle] = useState(record.title);
  const [content, setContent] = useState(record.content);
  const [retireConfirmation, setRetireConfirmation] = useState("");
  const [separateConfirmed, setSeparateConfirmed] = useState(false);
  const [saving, setSaving] = useState(false);
  const detailsRef = useRef<HTMLDetailsElement | null>(null);
  const titleRef = useRef<HTMLInputElement | null>(null);
  const retirePhrase = `RETIRE ${record.id.slice(0, 8)}`;
  const changed =
    kind !== record.kind ||
    title.trim() !== record.title ||
    content.trim() !== record.content;

  useEffect(() => {
    if (reviewRequestId === null || !detailsRef.current) return;
    detailsRef.current.open = true;
    titleRef.current?.focus();
  }, [reviewRequestId]);

  async function applyLifecycle(lifecycle: KnowledgeRecordLifecycleRequest) {
    setSaving(true);
    try {
      await onLifecycle(record.id, lifecycle);
    } finally {
      setSaving(false);
    }
  }

  return (
    <details
      className={`knowledge-record ${record.status}`}
      ref={detailsRef}
    >
      <summary>
        <span>
          <strong>{record.title}</strong>
          <small>{record.relative_path}</small>
        </span>
        <span>
          {record.status === "active" ? "Active" : "Retired"} · revision{" "}
          {record.revision}
        </span>
      </summary>
      <div className="knowledge-record-body">
        {record.status === "active" ? (
          <>
            <div className="knowledge-fields">
              <label>
                <span>Type</span>
                <select
                  value={kind}
                  onChange={(event) =>
                    setKind(event.target.value as KnowledgeKind)
                  }
                  disabled={saving}
                >
                  {Object.entries(KNOWLEDGE_KIND_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              <label>
                <span>Title</span>
                <input
                  ref={titleRef}
                  value={title}
                  maxLength={120}
                  onChange={(event) => setTitle(event.target.value)}
                  disabled={saving}
                />
              </label>
              <label className="knowledge-content">
                <span>Approved information</span>
                <textarea
                  value={content}
                  maxLength={4000}
                  rows={3}
                  onChange={(event) => setContent(event.target.value)}
                  disabled={saving}
                />
              </label>
            </div>
            <label className="separate-record-option">
              <input
                type="checkbox"
                checked={separateConfirmed}
                onChange={(event) =>
                  setSeparateConfirmed(event.target.checked)
                }
                disabled={saving}
              />
              If this revision matches another record, keep both separately
            </label>
            <div className="knowledge-actions">
              <button
                type="button"
                className="approve-knowledge"
                disabled={
                  saving || !changed || !title.trim() || !content.trim()
                }
                onClick={() =>
                  void applyLifecycle({
                    action: "update",
                    kind,
                    title: title.trim(),
                    content: content.trim(),
                    duplicate_confirmation: separateConfirmed
                      ? "CREATE SEPARATE RECORD"
                      : undefined,
                  })
                }
              >
                {saving ? "Saving…" : "Save new revision"}
              </button>
            </div>
            <div className="retire-record">
              <p>
                Retirement removes this record from future retrieval without
                deleting its files or history. Type <code>{retirePhrase}</code>.
              </p>
              <div>
                <input
                  aria-label={`Retire confirmation for ${record.title}`}
                  value={retireConfirmation}
                  onChange={(event) => setRetireConfirmation(event.target.value)}
                  disabled={saving}
                  placeholder={retirePhrase}
                />
                <button
                  type="button"
                  className="reject-knowledge"
                  disabled={saving || retireConfirmation !== retirePhrase}
                  onClick={() =>
                    void applyLifecycle({
                      action: "retire",
                      confirmation: retireConfirmation,
                    })
                  }
                >
                  Retire record
                </button>
              </div>
            </div>
          </>
        ) : (
          <p>
            This record is excluded from retrieval. Its approved file and
            revision history remain available for recovery.
          </p>
        )}
      </div>
    </details>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Nova could not connect to the local model provider.";
}
