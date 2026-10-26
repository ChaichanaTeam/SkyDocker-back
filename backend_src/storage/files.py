from dataclasses import dataclass

from fastapi import UploadFile

from .constants import MAX_DOCUMENT_SIZE


# Type is detected by content, the file name and Content-Type are client-controlled
_SIGNATURES = (
    (b"%PDF-", "application/pdf", "pdf"),
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
)


class DocumentTooLarge(ValueError):
    pass


class UnsupportedDocument(ValueError):
    pass


@dataclass(frozen=True)
class Document:
    body: bytes
    content_type: str
    ext: str


async def read_document(upload: UploadFile) -> Document:
    body = await upload.read(MAX_DOCUMENT_SIZE + 1)

    if len(body) > MAX_DOCUMENT_SIZE:
        raise DocumentTooLarge(f"File is larger than {MAX_DOCUMENT_SIZE // (1024 * 1024)} MB")

    for signature, content_type, ext in _SIGNATURES:
        if body.startswith(signature):
            return Document(body=body, content_type=content_type, ext=ext)

    raise UnsupportedDocument("Only PDF, JPEG and PNG files are accepted")
