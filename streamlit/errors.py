"""Turn Python errors into short, everyday language for the dashboard."""

from json import JSONDecodeError

from pydantic import ValidationError

from src.tools.ingest_file import FileTypeError, MissingHeadersError


class UserFacingError(Exception):
    """An error that already has a plain-language message."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def humanize_error(exc: BaseException) -> str:
    """
    Convert a technical exception into a sentence an Acme user can act on.

    We never show stack traces or library names in the popup.
    """
    if isinstance(exc, UserFacingError):
        return exc.message

    name = type(exc).__name__
    raw = str(exc) or ""
    lowered = raw.lower()

    if isinstance(exc, FileTypeError) or "unsupported file" in lowered:
        return (
            "Acme does not accept this file type. Please upload a PDF, Word document, "
            "spreadsheet, text file, JSON, XML, or a ZIP that contains one of those."
        )

    if isinstance(exc, MissingHeadersError):
        return (
            "This spreadsheet is missing column titles at the top. "
            "Add a header row and send it through Acme again."
        )

    if isinstance(exc, FileNotFoundError):
        return "Acme could not find the uploaded file. Please upload it again."

    if isinstance(exc, PermissionError):
        return "Acme does not have permission to open this file. Try saving a copy and uploading that."

    if isinstance(exc, JSONDecodeError) or "json" in name.lower():
        return "Acme could not read this invoice because the file is not formatted correctly."

    if isinstance(exc, UnicodeDecodeError):
        return "Acme could not read the text in this file. Try exporting it as UTF-8 and upload again."

    if isinstance(exc, ValidationError) or "outputstate" in lowered:
        return "This invoice is missing details Acme needs to finish processing."

    if "already exists" in lowered:
        return (
            "This invoice number is already in Acme's database. "
            "It needs a different ID before it can be saved properly."
        )

    if isinstance(exc, TimeoutError) or "timeout" in lowered:
        return "Acme's review took too long to finish. Please try again in a moment."

    if any(token in lowered for token in ("api key", "apikey", "authentication", "unauthorized", "401")):
        return "Acme's review service is not set up on this computer. Please contact an Acme administrator."

    if any(token in lowered for token in ("rate limit", "429", "quota")):
        return "Acme's review service is busy right now. Please wait a minute and try again."

    if any(
        token in name.lower() or token in lowered
        for token in ("connection", "connect", "network", "dns", "refused")
    ):
        return "Acme could not reach the review service. Check your internet connection and try again."

    if isinstance(exc, ValueError) and "invoice" in lowered:
        return "Something in this invoice does not look valid to Acme. Please check the file and try again."

    if isinstance(exc, OSError):
        return "Acme could not read this file from disk. Please upload it again."

    return (
        "Acme could not finish processing this invoice. "
        "Please try again, or upload a different file."
    )
