import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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

    expect(await screen.findByText("Not supported")).toBeInTheDocument();
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
        return response({ scanned: 0, added: 0, updated: 0, duplicates: 0 });
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
      return response([]);
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);

    fireEvent.change(
      await screen.findByRole("searchbox", {
        name: "Search files and extracted text",
      }),
      { target: { value: "invoice 90210" } },
    );
    fireEvent.change(screen.getByLabelText("Intake status"), {
      target: { value: "duplicate" },
    });

    await vi.waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([input]) => {
          const url = input.toString();
          return url.includes("q=invoice+90210") && url.includes("status=duplicate");
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
});
