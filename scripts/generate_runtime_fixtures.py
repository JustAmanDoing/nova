"""Generate deterministic documents for Nova's isolated runtime acceptance check."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _write_pdf(path: Path, lines: list[str], *, font_size: int = 18) -> None:
    commands = ["BT", f"/F1 {font_size} Tf", "72 720 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append(f"0 -{font_size + 12} Td")
        commands.append(f"({_pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
        ),
        (
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"\nendstream"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{number} 0 obj\n".encode("ascii"))
        document.extend(body)
        document.extend(b"\nendobj\n")

    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    document.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(document)


def _write_docx(path: Path, lines: list[str]) -> None:
    paragraphs = "".join(
        f"<w:p><w:r><w:t>{xml_escape(line)}</w:t></w:r></w:p>"
        for line in lines
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<w:document xmlns:w='
        '"http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}</w:body>"
        "</w:document>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document_xml)


def generate(data_root: Path) -> None:
    intake = data_root / "intake"
    runtime_fixtures = data_root / "runtime-fixtures"
    intake.mkdir(parents=True, exist_ok=True)
    runtime_fixtures.mkdir(parents=True, exist_ok=True)

    (intake / "ci-smoke-invoice.txt").write_text(
        "\n".join(
            [
                "NOVA TEST DOCUMENT",
                "Document type: Invoice",
                "Invoice number: TXT-ACCEPT-001",
                "Invoice date: 25-07-2026",
                "Supplier: Nova Runtime Verification",
                "Total: $35.15 AUD",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (intake / "ci-project.md").write_text(
        "# Nova runtime project\n\n"
        "Acceptance reference MD-ACCEPT-204 confirms local Markdown extraction.\n",
        encoding="utf-8",
    )
    _write_docx(
        intake / "ci-brief.docx",
        [
            "Nova project brief",
            "Acceptance reference DOCX-ACCEPT-482",
        ],
    )
    _write_pdf(
        intake / "ci-report.pdf",
        [
            "NOVA RUNTIME PROJECT REPORT",
            "Reference PDF-ACCEPT-731",
            "Project: Nova",
        ],
    )
    _write_pdf(
        runtime_fixtures / "ci-image-source.pdf",
        [
            "NOVA OCR IMAGE",
            "Reference OCR-ACCEPT-417",
        ],
        font_size=30,
    )

    for number in range(1, 5):
        label = "PROBE" if number == 4 else str(number)
        (intake / f"ci-learning-{label.lower()}.txt").write_text(
            "\n".join(
                [
                    f"NOVA LEARNING INVOICE {label}",
                    "Document type: Invoice",
                    f"Invoice number: LEARN-ACCEPT-{number:03d}",
                    "Invoice date: 25-07-2026",
                    f"Supplier: Nova Learning Supplier {label}",
                    f"Total: ${number}0.00 AUD",
                ]
            )
            + "\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("data"),
        help="Host data directory mounted into Nova's production containers.",
    )
    arguments = parser.parse_args()
    generate(arguments.data_root.resolve())


if __name__ == "__main__":
    main()
