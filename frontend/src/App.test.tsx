import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.useRealTimers();
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

function healthyOperations() {
  return {
    status: "healthy",
    uptime_seconds: 45,
    database_size_bytes: 1_048_576,
    storage_free_bytes: 20 * 1_073_741_824,
    storage_total_bytes: 100 * 1_073_741_824,
    storage_free_percent: 20,
    last_scan_status: "ok",
    last_scan_completed_at: "2026-07-25T00:00:00Z",
    last_scan_duration_ms: 125,
    warnings: [],
  };
}

describe("App", () => {
  it("does not let an older refresh overwrite newer dashboard state", async () => {
    let summaryRequests = 0;
    let releaseInitialSummary = () => {};
    const initialSummaryResponse = new Promise((resolve) => {
      releaseInitialSummary = () =>
        resolve({
          ok: true,
          json: async () => ({
            files_observed: 1,
            understood: 1,
            ready_for_review: 0,
            exact_duplicates: 0,
          }),
        });
    });
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.48.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/scan")) {
        return response({
          scanned: 2,
          added: 0,
          updated: 0,
          removed: 0,
          duplicates: 0,
        });
      }
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        summaryRequests += 1;
        if (summaryRequests === 1) return initialSummaryResponse;
        return response({
          files_observed: 2,
          understood: 2,
          ready_for_review: 0,
          exact_duplicates: 0,
        });
      }
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await vi.waitFor(() => expect(summaryRequests).toBe(1));

    fireEvent.click(screen.getByRole("button", { name: "Scan now" }));
    await vi.waitFor(() => expect(summaryRequests).toBe(2));

    const observedMetric = screen.getByText("Files observed").closest("article");
    await vi.waitFor(() => expect(observedMetric).toHaveTextContent("2"));

    await act(async () => {
      releaseInitialSummary();
      await initialSummaryResponse;
      await Promise.resolve();
    });

    expect(observedMetric).toHaveTextContent("2");
  });

  it("refreshes backup history less often than live intake state", async () => {
    vi.useFakeTimers();
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.43.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
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
      await vi.advanceTimersByTimeAsync(250);
    });

    const countRequests = (suffix: string) =>
      fetchMock.mock.calls.filter(([input]) =>
        input.toString().endsWith(suffix),
      ).length;
    expect(countRequests("/backups")).toBe(1);
    const initialSummaryRequests = countRequests("/summary");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });

    expect(countRequests("/summary")).toBeGreaterThan(initialSummaryRequests);
    expect(countRequests("/backups")).toBe(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(55_000);
    });

    expect(countRequests("/backups")).toBe(2);
  });

  it("retries backup history promptly after a failed refresh", async () => {
    vi.useFakeTimers();
    let backupRequests = 0;
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.46.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/backups")) {
        backupRequests += 1;
        if (backupRequests === 1) {
          return Promise.reject(new Error("Backup inventory unavailable"));
        }
        return response([]);
      }
      if (url.endsWith("/actions/recovery")) return response([]);
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
      await vi.advanceTimersByTimeAsync(250);
    });
    expect(backupRequests).toBe(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(5_000);
    });

    expect(backupRequests).toBe(2);
  });

  it("keeps core dashboard state current when backup history fails", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.47.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/backups")) {
        return Promise.reject(new Error("Backup inventory unavailable"));
      }
      if (url.endsWith("/actions/recovery")) return response([]);
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 3,
          understood: 2,
          ready_for_review: 1,
          exact_duplicates: 0,
        });
      }
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    const observedMetric = screen.getByText("Files observed").closest("article");
    await vi.waitFor(() => expect(observedMetric).toHaveTextContent("3"));
    expect(
      screen.getByRole("alert", {
        name: "",
      }),
    ).toHaveTextContent("Backup history: Backup inventory unavailable");
  });

  it("updates intake files when operational status fails", async () => {
    const file = recommendedInvoice();
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.48.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/system/status")) {
        return Promise.reject(new Error("Operations unavailable"));
      }
      if (url.endsWith("/preferences")) return response([]);
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
      if (url.endsWith("/actions")) return response([]);
      if (url.endsWith("/summary")) {
        return response({
          files_observed: 1,
          understood: 1,
          ready_for_review: 1,
          exact_duplicates: 0,
        });
      }
      return response([file]);
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    expect(await screen.findByText(file.original_name)).toBeInTheDocument();
    expect(screen.getByText("1 result")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Operational status: Operations unavailable",
    );
  });

  it("shows the truthful empty state during an optional panel failure", async () => {
    const fetchMock = vi.fn((input: string | URL | Request) => {
      const url = input.toString();
      if (url.endsWith("/health")) {
        return response({
          status: "ok",
          service: "Nova API",
          version: "0.48.0",
          environment: "test",
          timestamp: "2026-07-25T09:00:00Z",
        });
      }
      if (url.endsWith("/preferences")) {
        return Promise.reject(new Error("Learning history unavailable"));
      }
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
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

    expect(await screen.findByText("Your intake is empty")).toBeInTheDocument();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Learning preferences: Learning history unavailable",
    );
  });

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
        if (url.endsWith("/system/status")) {
          return response(healthyOperations());
        }
        if (url.endsWith("/preferences")) return response([]);
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
    expect(screen.getByRole("status")).toHaveTextContent("Nova online");
    expect(await screen.findByText("invoice.txt")).toBeInTheDocument();
    expect(
      screen.getByRole("table", {
        name: "Nova intake files and processing status",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Intake MVP · 0.1.0")).toBeInTheDocument();
    expect(screen.getByText("Healthy")).toBeInTheDocument();
    expect(screen.getByText("20.0 GB free (20.0%)")).toBeInTheDocument();
    expect(screen.getByText("Latest scan 125 ms")).toBeInTheDocument();
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
        if (url.endsWith("/preferences")) return response([]);
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
    const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
      void init;
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
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
      const scanCall = fetchMock.mock.calls.find(([input]) =>
        input.toString().endsWith("/scan"),
      );
      expect(scanCall).toBeDefined();
      expect(new Headers(scanCall?.[1]?.headers).get("X-Nova-Intent")).toBe(
        "local-user-action",
      );
      const healthCall = fetchMock.mock.calls.find(([input]) =>
        input.toString().endsWith("/health"),
      );
      expect(new Headers(healthCall?.[1]?.headers).has("X-Nova-Intent")).toBe(
        false,
      );
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
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
    expect(
      screen.getByText(/Filename and title matches rank above content/i),
    ).toBeInTheDocument();
    expect(screen.getByText("0 results").closest(".search-summary")).toHaveAttribute(
      "aria-live",
      "polite",
    );
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
        if (input.toString().endsWith("/preferences")) return response([]);
        if (input.toString().endsWith("/backups")) return response([]);
        if (input.toString().endsWith("/actions/recovery")) return response([]);
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
        if (input.toString().endsWith("/preferences")) return response([]);
        if (input.toString().endsWith("/backups")) return response([]);
        if (input.toString().endsWith("/actions/recovery")) return response([]);
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
      if (url.endsWith("/preferences")) return response([]);
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
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
      if (url.endsWith("/preferences")) return response([]);
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
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
      if (url.endsWith("/backups")) return response([]);
      if (url.endsWith("/actions/recovery")) return response([]);
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

  it("shows and forgets a learned destination only after typed confirmation", async () => {
    let reset = false;
    const preference = {
      document_type: "plain_text",
      base_category: "Financial",
      candidate_destination: "Preferred",
      supporting_examples: 3,
      active_examples: 3,
      stored_examples: 3,
      preference_share: 1,
      eligible: true,
      revision: 3,
    };
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.13.0",
            environment: "test",
            timestamp: "2026-07-25T00:00:00Z",
          });
        }
        if (url.endsWith("/preferences/reset") && init?.method === "POST") {
          reset = true;
          return response({
            document_type: preference.document_type,
            base_category: preference.base_category,
            removed_examples: 3,
            reset_at: "2026-07-25T00:10:00Z",
            detail: "Stored examples removed.",
          });
        }
        if (url.endsWith("/preferences")) {
          return response(reset ? [] : [preference]);
        }
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "prompt").mockReturnValue(
      "FORGET plain_text / Financial",
    );
    render(<App />);

    expect(await screen.findByText("Active suggestion")).toBeInTheDocument();
    expect(screen.getByText("Preferred")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Forget examples" }),
    );

    expect(
      await screen.findByText("Forgot 3 stored learning examples."),
    ).toBeInTheDocument();
    const resetCall = fetchMock.mock.calls.find(([input]) =>
      input.toString().endsWith("/preferences/reset"),
    );
    expect(resetCall?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(resetCall?.[1]?.body))).toEqual({
      document_type: "plain_text",
      base_category: "Financial",
      confirmation: "FORGET plain_text / Financial",
    });
  });

  it("surfaces incomplete operation diagnostics without recovery controls", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.6.0",
            environment: "test",
            timestamp: "2026-07-25T00:00:00Z",
          });
        }
        if (url.endsWith("/backups")) return response([]);
        if (url.endsWith("/actions/recovery")) {
          return response([
            {
              operation_id: "interrupted-operation",
              kind: "move",
              state: "ready_to_retry",
              source_path: "invoice.txt",
              destination_path: "Financial/Invoices/invoice.txt",
              expected_sha256: "abcdef1234567890",
              source_sha256: "abcdef1234567890",
              destination_sha256: null,
              detail:
                "The verified source remains and the destination is empty.",
              started_at: "2026-07-25T00:00:00Z",
              assessed_at: "2026-07-25T00:10:00Z",
            },
          ]);
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
      }),
    );

    render(<App />);

    expect(await screen.findByText("Source safe")).toBeInTheDocument();
    expect(
      screen.getByText(
        "The verified source remains and the destination is empty.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Nova has not changed these files/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /recover/i })).toBeNull();
  });

  it("creates and exposes a verified local database backup", async () => {
    let created = false;
    const backup = {
      filename: "nova-20260725T090000.000000Z.db",
      size_bytes: 8192,
      sha256: "a".repeat(64),
      created_at: "2026-07-25T09:00:00Z",
      verified: true,
    };
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.7.0",
            environment: "test",
            timestamp: "2026-07-25T09:00:00Z",
          });
        }
        if (url.endsWith("/backups")) {
          if (init?.method === "POST") {
            created = true;
            return response(backup);
          }
          return response(created ? [backup] : []);
        }
        if (url.endsWith("/actions/recovery")) return response([]);
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
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.click(await screen.findByRole("button", { name: "Create backup" }));

    expect(
      await screen.findByText("nova-20260725T090000.000000Z.db"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Checksum recorded/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: `Download integrity-checked copy of ${backup.filename}`,
      }),
    ).toHaveAttribute(
      "href",
      "http://localhost:8000/api/v1/backups/nova-20260725T090000.000000Z.db",
    );
    expect(
      screen.getByRole("link", {
        name: `Download checksum for ${backup.filename}`,
      }),
    ).toHaveAttribute(
      "href",
      "http://localhost:8000/api/v1/backups/nova-20260725T090000.000000Z.db/checksum",
    );
    expect(
      fetchMock.mock.calls.some(
        ([input, init]) =>
          input.toString().endsWith("/backups") && init?.method === "POST",
      ),
    ).toBe(true);
  });

  it("reveals the complete retained backup history on request", async () => {
    const backups = Array.from({ length: 8 }, (_, index) => ({
      filename: `nova-20260725T0${9 - index}0000.000000Z.db`,
      size_bytes: 8192,
      sha256: `${index}`.repeat(64),
      created_at: `2026-07-25T0${9 - index}:00:00Z`,
      verified: true,
    }));
    vi.stubGlobal(
      "fetch",
      vi.fn((input: string | URL | Request) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.42.0",
            environment: "test",
            timestamp: "2026-07-25T09:00:00Z",
          });
        }
        if (url.endsWith("/backups")) return response(backups);
        if (url.endsWith("/actions/recovery")) return response([]);
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
      }),
    );

    render(<App />);

    const showAll = await screen.findByRole("button", {
      name: "Show all 8 backups",
    });
    expect(screen.getByText("8 backups retained")).toBeInTheDocument();
    expect(screen.getByText("64.0 KB total")).toBeInTheDocument();
    expect(screen.getByText("8 checksums recorded")).toBeInTheDocument();
    expect(showAll).toHaveAttribute("aria-expanded", "false");
    expect(screen.getByText(backups[4].filename)).toBeInTheDocument();
    expect(screen.queryByText(backups[5].filename)).toBeNull();

    fireEvent.click(showAll);

    expect(screen.getByText(backups[7].filename)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Show latest 5" }),
    ).toHaveAttribute("aria-expanded", "true");

    fireEvent.click(screen.getByRole("button", { name: "Show latest 5" }));

    expect(screen.queryByText(backups[5].filename)).toBeNull();
  });

  it("restores a verified backup only after exact typed confirmation", async () => {
    const backup = {
      filename: "nova-20260725T100000.000000Z.db",
      size_bytes: 8192,
      sha256: "a".repeat(64),
      created_at: "2026-07-25T10:00:00Z",
      verified: true,
    };
    const safetyBackup = {
      ...backup,
      filename: "nova-20260725T100500.000000Z.db",
      created_at: "2026-07-25T10:05:00Z",
    };
    const fetchMock = vi.fn(
      (input: string | URL | Request, init?: RequestInit) => {
        const url = input.toString();
        if (url.endsWith("/health")) {
          return response({
            status: "ok",
            service: "Nova API",
            version: "0.8.0",
            environment: "test",
            timestamp: "2026-07-25T10:00:00Z",
          });
        }
        if (
          url.endsWith(`/${backup.filename}/restore`) &&
          init?.method === "POST"
        ) {
          return response({
            restored_from: backup.filename,
            restored_from_sha256: backup.sha256,
            safety_backup: safetyBackup,
            restored_at: "2026-07-25T10:05:00Z",
            detail: "Restored verified backup.",
          });
        }
        if (url.endsWith("/backups")) return response([backup, safetyBackup]);
        if (url.endsWith("/actions/recovery")) return response([]);
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
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "prompt").mockReturnValue(`RESTORE ${backup.filename}`);
    render(<App />);

    fireEvent.click(
      await screen.findByRole("button", {
        name: `Restore ${backup.filename}`,
      }),
    );

    expect(
      await screen.findByText(
        `Restored ${backup.filename}. Safety snapshot: ${safetyBackup.filename}.`,
      ),
    ).toBeInTheDocument();
    const restoreCall = fetchMock.mock.calls.find(([input]) =>
      input.toString().endsWith(`/${backup.filename}/restore`),
    );
    expect(restoreCall?.[1]?.method).toBe("POST");
    expect(JSON.parse(String(restoreCall?.[1]?.body))).toEqual({
      confirmation: `RESTORE ${backup.filename}`,
    });
  });
});
