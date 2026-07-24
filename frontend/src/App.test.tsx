import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function response(body: unknown) {
  return Promise.resolve({
    ok: true,
    json: async () => body,
  });
}

function recommendedInvoice() {
  return {
    id: "invoice-file",
    relative_path: "invoice.txt",
    original_name: "invoice.txt",
    extension: ".txt",
    size_bytes: 256,
    modified_at: "2026-07-24T00:00:00Z",
    observed_at: "2026-07-24T00:00:00Z",
    sha256: "abcdef1234567890",
    status: "observed",
    duplicate_of: null,
    understanding: {
      status: "ready",
      document_type: "plain_text",
      title: "Office invoice",
      text_preview: "Invoice number INV-001",
      word_count: 4,
      character_count: 22,
      evidence: "Extracted locally from plain text content.",
      error: null,
      error_code: null,
      extraction_method: "utf-8",
      retryable: false,
      understood_at: "2026-07-24T00:00:01Z",
    },
    recommendation: {
      outcome: "suggested",
      category: "Financial",
      suggested_filename:
        "24-07-2026_Financial_Invoice_Example-Office_v01.txt",
      destination: "Financial/Invoices",
      confidence: 0.96,
      reasons: [
        "Matched invoice signals: invoice, invoice number, supplier:, total:.",
        "Applied the approved Financial filing category.",
        "No file will change until a later approval step.",
      ],
      generated_at: "2026-07-24T00:00:02Z",
    },
    approval: null,
  };
}

function approvedInvoice() {
  return {
    ...recommendedInvoice(),
    approval: {
      status: "approved",
      category: "Financial",
      suggested_filename:
        "24-07-2026_Financial_Invoice_Example-Office_v01.txt",
      destination: "Financial/Invoices",
      recommendation_generated_at: "2026-07-24T00:00:02Z",
      reviewed_at: "2026-07-25T00:00:00Z",
    },
  };
}

describe("App", () => {
  it("shows observed files and duplicate totals", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.1.0",
            environment: "test",
            timestamp: "2026-07-24T00:00:00Z",
          });
        }
        if (url.endsWith("/actions")) return response([]);
        if (url.endsWith("/summary")) {
          return response({
            files_observed: 1,
            understood: 1,
            ready_for_review: 0,
            exact_duplicates: 1,
          });
        }
        return response([
          {
            id: "file-1",
            relative_path: "invoice.txt",
            original_name: "invoice.txt",
            extension: ".txt",
            size_bytes: 1200,
            modified_at: "2026-07-24T00:00:00Z",
            observed_at: "2026-07-24T00:00:00Z",
            sha256: "abcdef1234567890",
            status: "duplicate",
            duplicate_of: "file-0",
            understanding: {
              status: "ready",
              document_type: "plain_text",
              title: "Office supply invoice",
              text_preview: "Invoice TEST-2026-001 from Example Office Supplies",
              word_count: 6,
              character_count: 52,
              evidence: "Extracted locally from plain text content.",
              error: null,
              understood_at: "2026-07-24T00:00:01Z",
            },
            recommendation: {
              outcome: "insufficient_evidence",
              category: null,
              suggested_filename: null,
              destination: null,
              confidence: 0,
              reasons: [
                "Exact duplicates are not recommended for filing independently.",
              ],
              generated_at: "2026-07-24T00:00:02Z",
            },
          },
        ]);
      }),
    );

    render(<App />);

    expect(await screen.findByText("Nova online")).toBeInTheDocument();
    expect(await screen.findByText("invoice.txt")).toBeInTheDocument();
    expect(screen.getAllByText("Duplicate")).toHaveLength(2);
    expect(screen.getAllByText("Understood")).toHaveLength(3);
    expect(screen.getByText("Office supply invoice")).toBeInTheDocument();
    expect(
      screen.getByText(/Invoice TEST-2026-001 from Example Office Supplies/),
    ).toBeInTheDocument();
    expect(screen.getByText(/1\.2 KB/)).toBeInTheDocument();
    expect(screen.getByText("No recommendation")).toBeInTheDocument();
    expect(
      screen.getByText(/Exact duplicates are not recommended/),
    ).toBeInTheDocument();
  });

  it("shows a clear status for unsupported formats", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.2.0",
            environment: "test",
            timestamp: "2026-07-24T00:00:00Z",
          });
        }
        if (url.endsWith("/actions")) return response([]);
        if (url.endsWith("/summary")) {
          return response({
            files_observed: 1,
            understood: 0,
            ready_for_review: 0,
            exact_duplicates: 0,
          });
        }
        return response([
          {
            id: "file-2",
            relative_path: "scan.pdf",
            original_name: "scan.pdf",
            extension: ".pdf",
            size_bytes: 512,
            modified_at: "2026-07-24T00:00:00Z",
            observed_at: "2026-07-24T00:00:00Z",
            sha256: "1234567890abcdef",
            status: "observed",
            duplicate_of: null,
            understanding: {
              status: "unsupported",
              document_type: null,
              title: null,
              text_preview: null,
              word_count: null,
              character_count: null,
              evidence: ".pdf files are not supported yet.",
              error: null,
              understood_at: "2026-07-24T00:00:01Z",
            },
          },
        ]);
      }),
    );

    render(<App />);

    expect(await screen.findByText("scan.pdf")).toBeInTheDocument();
    expect(screen.getAllByText("Not supported")).toHaveLength(2);
    expect(screen.getByText("Format not supported yet")).toBeInTheDocument();
    expect(screen.getByText(".pdf files are not supported yet.")).toBeInTheDocument();
  });

  it("requests a scan when the user selects Scan now", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.1.0",
          environment: "test",
          timestamp: "2026-07-24T00:00:00Z",
        });
      }
      if (url.endsWith("/scan")) {
        return response({
          scanned: 0,
          added: 0,
          updated: 0,
          removed: 0,
          duplicates: 0,
        });
      }
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 0,
          understood: 0,
          ready_for_review: 0,
          exact_duplicates: 0,
        });
      }
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    fireEvent.click(await screen.findByRole("button", { name: "Scan now" }));

    await vi.waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) => input.toString().endsWith("/scan")),
      ).toBe(true);
    });
  });

  it("searches extracted content and applies status filters", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.2.0",
          environment: "test",
          timestamp: "2026-07-24T00:00:00Z",
        });
      }
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 0,
          understood: 0,
          ready_for_review: 0,
          exact_duplicates: 0,
        });
      }
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    await act(async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    });

    fireEvent.change(
      await screen.findByRole("searchbox", {
        name: "Search files, extracted text, and recommendations",
      }),
      { target: { value: "invoice 90210" } },
    );
    fireEvent.change(screen.getByLabelText("Intake status"), {
      target: { value: "duplicate" },
    });
    fireEvent.change(screen.getByLabelText("Review status"), {
      target: { value: "approved" },
    });

    await act(async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    });
    await vi.waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) => {
          const url = input.toString();
          return (
            url.includes("q=invoice+90210") &&
            url.includes("status=duplicate") &&
            url.includes("approval_status=approved")
          );
        }),
      ).toBe(true);
    });
  });

  it("surfaces structured extraction diagnostics", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        if (input.toString().endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.2.0",
            environment: "test",
            timestamp: "2026-07-24T00:00:00Z",
          });
        }
        if (input.toString().endsWith("/actions")) return response([]);
        if (input.toString().endsWith("/summary")) {
          return response({
            files_observed: 1,
            understood: 0,
            ready_for_review: 0,
            exact_duplicates: 0,
          });
        }
        return response([
          {
            id: "failed-file",
            relative_path: "invalid.txt",
            original_name: "invalid.txt",
            extension: ".txt",
            size_bytes: 3,
            modified_at: "2026-07-24T00:00:00Z",
            observed_at: "2026-07-24T00:00:00Z",
            sha256: "abcdef1234567890",
            status: "observed",
            duplicate_of: null,
            understanding: {
              status: "failed",
              document_type: "plain_text",
              title: null,
              text_preview: null,
              word_count: null,
              character_count: null,
              evidence: "Nova attempted local UTF-8 text extraction.",
              error: "The file could not be decoded as UTF-8 text.",
              error_code: "invalid_utf8",
              extraction_method: "utf-8",
              retryable: false,
              understood_at: "2026-07-24T00:00:01Z",
            },
          },
        ]);
      }),
    );

    render(<App />);
    expect(await screen.findByText(/invalid_utf8/)).toBeInTheDocument();
    expect(screen.getByText(/Extractor: utf-8/)).toBeInTheDocument();
  });

  it("shows explainable review controls before execution", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        if (input.toString().endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.3.0",
            environment: "test",
            timestamp: "2026-07-25T00:00:00Z",
          });
        }
        if (input.toString().endsWith("/actions")) return response([]);
        if (input.toString().endsWith("/summary")) {
          return response({
            files_observed: 1,
            understood: 1,
            ready_for_review: 1,
            exact_duplicates: 0,
          });
        }
        return response([
          {
            id: "invoice-file",
            relative_path: "invoice.txt",
            original_name: "invoice.txt",
            extension: ".txt",
            size_bytes: 256,
            modified_at: "2026-07-24T00:00:00Z",
            observed_at: "2026-07-24T00:00:00Z",
            sha256: "abcdef1234567890",
            status: "observed",
            duplicate_of: null,
            understanding: {
              status: "ready",
              document_type: "plain_text",
              title: "Office invoice",
              text_preview: "Invoice number INV-001",
              word_count: 4,
              character_count: 22,
              evidence: "Extracted locally from plain text content.",
              error: null,
              error_code: null,
              extraction_method: "utf-8",
              retryable: false,
              understood_at: "2026-07-24T00:00:01Z",
            },
            recommendation: {
              outcome: "suggested",
              category: "Financial",
              suggested_filename:
                "24-07-2026_Financial_Invoice_Example-Office_v01.txt",
              destination: "Financial/Invoices",
              confidence: 0.96,
              reasons: [
                "Matched invoice signals: invoice, invoice number, supplier:, total:.",
                "Applied the approved Financial filing category.",
                "No file will change until a later approval step.",
              ],
              generated_at: "2026-07-24T00:00:02Z",
            },
          },
        ]);
      }),
    );

    render(<App />);

    expect(await screen.findByText("Financial · 96%")).toBeInTheDocument();
    expect(
      screen.getByText(
        "24-07-2026_Financial_Invoice_Example-Office_v01.txt",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Destination: Financial/Invoices")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Edit" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ignore" })).toBeInTheDocument();
    expect(
      screen.getByText(
        "No file action will run until approval and explicit execution.",
      ),
    ).toBeInTheDocument();
  });

  it("saves edited review fields through the approval API", async () => {
    const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.4.0",
          environment: "test",
          timestamp: "2026-07-25T00:00:00Z",
        });
      }
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 1,
          understood: 1,
          ready_for_review: 1,
          exact_duplicates: 0,
        });
      }
      if (url.endsWith("/approval") && init?.method === "PUT") {
        return response({
          status: "pending",
          category: "Financial",
          suggested_filename: "24-07-2026_Financial_Invoice_Office_v02.txt",
          destination: "Financial/Invoices/2026",
          recommendation_generated_at: "2026-07-24T00:00:02Z",
          reviewed_at: "2026-07-25T00:00:00Z",
        });
      }
      return response([recommendedInvoice()]);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    fireEvent.change(screen.getByLabelText("Suggested filename"), {
      target: {
        value: "24-07-2026_Financial_Invoice_Office_v02.txt",
      },
    });
    fireEvent.change(screen.getByLabelText("Recommendation destination"), {
      target: { value: "Financial/Invoices/2026" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save edits" }));

    await vi.waitFor(() => {
      const reviewCall = fetchMock.mock.calls.find(([input]) =>
        input.toString().endsWith("/approval"),
      );
      expect(reviewCall).toBeDefined();
      expect(JSON.parse(String(reviewCall?.[1]?.body))).toEqual({
        action: "edit",
        category: "Financial",
        suggested_filename: "24-07-2026_Financial_Invoice_Office_v02.txt",
        destination: "Financial/Invoices/2026",
      });
    });
  });

  it("executes only from an approved recommendation", async () => {
    const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.5.0",
          environment: "test",
          timestamp: "2026-07-25T00:00:00Z",
        });
      }
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 1,
          understood: 1,
          ready_for_review: 0,
          exact_duplicates: 0,
        });
      }
      if (url.endsWith("/execute") && init?.method === "POST") {
        return response({
          operation_id: "move-operation",
          file_id: "invoice-file",
          kind: "move",
          status: "succeeded",
          source_path: "invoice.txt",
          destination_path:
            "Financial/Invoices/24-07-2026_Financial_Invoice_Example-Office_v01.txt",
          sha256: "abcdef1234567890",
          related_operation_id: null,
          detail: "Moved and verified.",
          created_at: "2026-07-25T00:00:00Z",
          can_undo: true,
        });
      }
      return response([approvedInvoice()]);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Move file" }));

    await vi.waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          ([input, init]) =>
            input.toString().endsWith("/execute") && init?.method === "POST",
        ),
      ).toBe(true);
    });
  });

  it("shows append-only action history and requests guarded undo", async () => {
    const moveAction = {
      operation_id: "move-operation",
      file_id: "invoice-file",
      kind: "move",
      status: "succeeded",
      source_path: "invoice.txt",
      destination_path:
        "Financial/Invoices/24-07-2026_Financial_Invoice_Example-Office_v01.txt",
      sha256: "abcdef1234567890",
      related_operation_id: null,
      detail: "Moved and verified.",
      created_at: "2026-07-25T00:00:00Z",
      can_undo: true,
    };
    const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.5.0",
          environment: "test",
          timestamp: "2026-07-25T00:00:00Z",
        });
      }
      if (url.endsWith("/actions/move-operation/undo") && init?.method === "POST") {
        return response({
          ...moveAction,
          operation_id: "undo-operation",
          kind: "undo",
          source_path: moveAction.destination_path,
          destination_path: moveAction.source_path,
          related_operation_id: moveAction.operation_id,
          can_undo: false,
        });
      }
      if (url.endsWith("/actions")) return response([moveAction]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 0,
          understood: 0,
          ready_for_review: 0,
          exact_duplicates: 0,
        });
      }
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<App />);

    expect(await screen.findByText("Moved and verified.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Undo move" }));

    await vi.waitFor(() => {
      expect(
        fetchMock.mock.calls.some(
          ([input, init]) =>
            input.toString().endsWith("/actions/move-operation/undo") &&
            init?.method === "POST",
        ),
      ).toBe(true);
    });
  });
});
