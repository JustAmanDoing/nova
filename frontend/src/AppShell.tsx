import { useCallback, useEffect, useState, type ReactNode } from "react";

import "./app-shell.css";

export type WorkspaceId = "chat" | "focus" | "record" | "librarian" | "intake";

const workspaces: Array<{
  id: WorkspaceId;
  label: string;
  description: string;
  href: string;
  mark: string;
}> = [
  { id: "chat", label: "Chat", description: "Talk with Nova", href: "/chat.html", mark: "C" },
  { id: "focus", label: "Focus", description: "Projects and actions", href: "/focus.html", mark: "F" },
  { id: "record", label: "Record", description: "Project history", href: "/archive.html", mark: "R" },
  { id: "librarian", label: "Librarian", description: "Knowledge quality", href: "/librarian.html", mark: "L" },
  { id: "intake", label: "Intake", description: "Review incoming files", href: "/", mark: "I" },
];

export default function AppShell({
  activeWorkspace,
  children,
  contentClassName,
  mobileHeaderAction,
  mobileNavigationContent,
  navigationOpen: controlledNavigationOpen,
  onNavigationOpenChange,
  status,
}: {
  activeWorkspace: WorkspaceId;
  children: ReactNode;
  contentClassName: string;
  mobileHeaderAction?: ReactNode;
  mobileNavigationContent?: ReactNode;
  navigationOpen?: boolean;
  onNavigationOpenChange?: (open: boolean) => void;
  status?: ReactNode;
}) {
  const [internalNavigationOpen, setInternalNavigationOpen] = useState(false);
  const navigationOpen = controlledNavigationOpen ?? internalNavigationOpen;
  const activeLabel = workspaces.find((workspace) => workspace.id === activeWorkspace)?.label;

  const setNavigationOpen = useCallback((open: boolean) => {
    if (controlledNavigationOpen === undefined) setInternalNavigationOpen(open);
    onNavigationOpenChange?.(open);
  }, [controlledNavigationOpen, onNavigationOpenChange]);

  useEffect(() => {
    if (!navigationOpen) return;

    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setNavigationOpen(false);
    }

    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [navigationOpen, setNavigationOpen]);

  return (
    <div className={`app-shell app-shell-${activeWorkspace}`}>
      <header className="app-shell-mobile-header">
        <button
          type="button"
          className="app-shell-menu-button"
          aria-label="Open workspace navigation"
          aria-expanded={navigationOpen}
          aria-controls="app-shell-navigation"
          onClick={() => setNavigationOpen(true)}
        >
          <span aria-hidden="true">☰</span>
        </button>
        <a className="app-shell-mobile-brand" href="/chat.html">
          <span className="brand-mark" aria-hidden="true">N</span>
          <span>Nova</span>
        </a>
        {mobileHeaderAction ?? (
          <span className="app-shell-current-workspace">{activeLabel}</span>
        )}
      </header>

      {navigationOpen ? (
        <button
          type="button"
          className="app-shell-backdrop"
          aria-label="Close workspace navigation"
          onClick={() => setNavigationOpen(false)}
        />
      ) : null}

      <aside
        id="app-shell-navigation"
        className={`app-shell-sidebar ${navigationOpen ? "open" : ""}`}
        aria-label="Workspace navigation"
      >
        <div className="app-shell-sidebar-heading">
          <a className="brand" href="/chat.html">
            <span className="brand-mark" aria-hidden="true">N</span>
            <span>Nova</span>
          </a>
          <button
            type="button"
            className="app-shell-close-button"
            aria-label="Close workspace navigation"
            onClick={() => setNavigationOpen(false)}
          >
            ×
          </button>
        </div>

        <nav className="app-shell-workspaces" aria-label="Primary navigation">
          <p>Workspaces</p>
          {workspaces.map((workspace) => (
            <a
              key={workspace.id}
              className={workspace.id === activeWorkspace ? "active" : ""}
              href={workspace.href}
              aria-current={workspace.id === activeWorkspace ? "page" : undefined}
              onClick={() => setNavigationOpen(false)}
            >
              <span className="app-shell-workspace-mark" aria-hidden="true">
                {workspace.mark}
              </span>
              <span>
                <strong>{workspace.label}</strong>
                <small aria-hidden="true">{workspace.description}</small>
              </span>
            </a>
          ))}
        </nav>

        {navigationOpen && mobileNavigationContent ? (
          <div className="app-shell-mobile-extension">
            {mobileNavigationContent}
          </div>
        ) : null}

        <div className="app-shell-status">
          {status}
          <p>Private by default</p>
          <span>Workspace data stays local and private unless you explicitly choose otherwise.</span>
        </div>
      </aside>

      <main className={`app-shell-content ${contentClassName}`}>{children}</main>
    </div>
  );
}
