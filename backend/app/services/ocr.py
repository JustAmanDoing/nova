import shutil
import subprocess
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol


class OcrError(RuntimeError):
    def __init__(
        self,
        public_message: str,
        code: str,
        *,
        retryable: bool,
    ) -> None:
        super().__init__(public_message)
        self.public_message = public_message
        self.code = code
        self.retryable = retryable


class OcrEngine(Protocol):
    def extract_image(self, path: Path, max_output_bytes: int) -> str: ...

    def extract_pdf(
        self,
        path: Path,
        page_count: int,
        max_output_bytes: int,
    ) -> str: ...


@dataclass(frozen=True)
class LocalOcrService:
    max_pages: int = 10
    timeout_seconds: float = 60.0
    max_render_dimension: int = 2400
    max_rendered_bytes: int = 50_000_000
    language: str = "eng"

    def extract_image(self, path: Path, max_output_bytes: int) -> str:
        tesseract = self._require_tool("tesseract")
        output = self._run(
            [
                tesseract,
                str(path),
                "stdout",
                "-l",
                self.language,
                "--psm",
                "3",
            ],
            self.timeout_seconds,
            "Local image OCR timed out.",
        )
        self._check_output_size(output, max_output_bytes)
        return output.decode("utf-8", errors="replace")

    def extract_pdf(
        self,
        path: Path,
        page_count: int,
        max_output_bytes: int,
    ) -> str:
        if page_count > self.max_pages:
            raise OcrError(
                f"Scanned-PDF OCR is limited to {self.max_pages} pages.",
                "ocr_page_limit",
                retryable=False,
            )
        pdftoppm = self._require_tool("pdftoppm")
        tesseract = self._require_tool("tesseract")
        deadline = time.monotonic() + self.timeout_seconds
        with TemporaryDirectory(prefix="nova-ocr-") as temporary:
            output_prefix = Path(temporary) / "page"
            self._run(
                [
                    pdftoppm,
                    "-f",
                    "1",
                    "-l",
                    str(page_count),
                    "-scale-to",
                    str(self.max_render_dimension),
                    "-png",
                    str(path),
                    str(output_prefix),
                ],
                self._remaining(deadline),
                "Scanned-PDF rendering timed out.",
            )
            pages = sorted(Path(temporary).glob("page-*.png"), key=_page_number)
            if not pages:
                raise OcrError(
                    "The scanned PDF could not be rendered for local OCR.",
                    "ocr_render_failed",
                    retryable=True,
                )
            rendered_bytes = sum(page.stat().st_size for page in pages)
            if rendered_bytes > self.max_rendered_bytes:
                raise OcrError(
                    "Rendered PDF pages exceeded Nova's local OCR safety limit.",
                    "ocr_render_too_large",
                    retryable=False,
                )

            text_parts: list[str] = []
            output_bytes = 0
            for page in pages:
                output = self._run(
                    [
                        tesseract,
                        str(page),
                        "stdout",
                        "-l",
                        self.language,
                        "--psm",
                        "3",
                    ],
                    self._remaining(deadline),
                    "Scanned-PDF OCR timed out.",
                )
                output_bytes += len(output)
                if output_bytes > max_output_bytes:
                    raise OcrError(
                        "OCR text exceeded Nova's configured extraction limit.",
                        "extracted_text_too_large",
                        retryable=False,
                    )
                text_parts.append(output.decode("utf-8", errors="replace"))
            return "\n\n".join(text_parts)

    @staticmethod
    def _require_tool(name: str) -> str:
        executable = shutil.which(name)
        if executable is None:
            raise OcrError(
                (
                    "Local OCR is unavailable because a required tool is not "
                    f"installed: {name}."
                ),
                "ocr_unavailable",
                retryable=True,
            )
        return executable

    @staticmethod
    def _run(
        command: Sequence[str],
        timeout: float,
        timeout_message: str,
    ) -> bytes:
        if timeout <= 0:
            raise OcrError(timeout_message, "ocr_timeout", retryable=True)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                check=False,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise OcrError(
                timeout_message,
                "ocr_timeout",
                retryable=True,
            ) from error
        except OSError as error:
            raise OcrError(
                "Nova could not start the local OCR process.",
                "ocr_process_error",
                retryable=True,
            ) from error
        if result.returncode != 0:
            raise OcrError(
                "The local OCR process could not read this document.",
                "ocr_process_error",
                retryable=True,
            )
        return result.stdout

    @staticmethod
    def _remaining(deadline: float) -> float:
        return deadline - time.monotonic()

    @staticmethod
    def _check_output_size(output: bytes, max_output_bytes: int) -> None:
        if len(output) > max_output_bytes:
            raise OcrError(
                "OCR text exceeded Nova's configured extraction limit.",
                "extracted_text_too_large",
                retryable=False,
            )


def _page_number(path: Path) -> int:
    try:
        return int(path.stem.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 0
