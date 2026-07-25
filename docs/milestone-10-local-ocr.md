# Milestone 10 — Bounded local OCR

## Purpose

Nova 0.10.0 completes the first Understanding milestone by extracting text from
supported images and scanned PDFs locally. OCR is optional and remains
read-only: it cannot approve, rename, move, delete, or share a file.

## Supported inputs

- PNG
- JPEG and JPG
- TIFF and TIF
- BMP
- PDF files whose ordinary text layer is empty

PDF text extraction still uses `pypdf` first. Nova does not spend OCR resources
on a PDF that already exposes readable text.

## Local processing

The Docker backend includes Tesseract with English language data and Poppler.
Image files are sent directly to Tesseract. Scanned PDF pages are rendered with
`pdftoppm` into a private temporary directory and processed in numeric page
order. Temporary page images are removed after the operation.

No OCR input, rendered page, or extracted text is uploaded to a service.

## Resource and process bounds

- The existing source-file limit applies before OCR starts.
- The existing extracted-text limit applies to OCR output.
- Scanned PDFs have a configurable maximum page count.
- PDF renders have a maximum dimension and total temporary-byte limit.
- One complete OCR operation has a configurable timeout.
- Commands use fixed argument lists and never invoke a command shell.
- Process stderr and internal paths are not exposed through the public API.

Nova reports structured codes including `ocr_unavailable`, `ocr_timeout`,
`ocr_page_limit`, `ocr_render_failed`, `ocr_render_too_large`, and
`ocr_process_error`.

## Upgrade behavior

When OCR first becomes available, Nova reconsiders unchanged images previously
marked unsupported and PDFs previously recorded as empty after `pypdf`
extraction. Once OCR has produced a terminal result, ordinary scan caching
resumes so background scans do not repeat expensive work.
