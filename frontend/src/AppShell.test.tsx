import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AppShell from "./AppShell";

describe("AppShell", () => {
  it("shows every existing workspace and identifies the active one", () => {
    render(
      <AppShell activeWorkspace="focus" contentClassName="focus-shell">
        <h1>Focus content</h1>
      </AppShell>,
    );

    const expectedWorkspaces = [
      ["Chat", "/chat.html"],
      ["Focus", "/focus.html"],
      ["Record", "/archive.html"],
      ["Librarian", "/librarian.html"],
      ["Intake", "/"],
    ];

    for (const [name, href] of expectedWorkspaces) {
      expect(screen.getByRole("link", { name })).toHaveAttribute("href", href);
    }
    expect(screen.getByRole("link", { name: "Focus" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getByRole("heading", { name: "Focus content" })).toBeInTheDocument();
  });

  it("opens and closes responsive navigation without changing workspace content", () => {
    render(
      <AppShell activeWorkspace="chat" contentClassName="chat-shell">
        <p>Conversation</p>
      </AppShell>,
    );

    const openButton = screen.getByRole("button", { name: "Open workspace navigation" });
    const navigation = screen.getByLabelText("Workspace navigation");

    fireEvent.click(openButton);
    expect(openButton).toHaveAttribute("aria-expanded", "true");
    expect(navigation).toHaveClass("open");

    fireEvent.keyDown(window, { key: "Escape" });
    expect(openButton).toHaveAttribute("aria-expanded", "false");
    expect(navigation).not.toHaveClass("open");
    expect(screen.getByText("Conversation")).toBeInTheDocument();
  });
});
