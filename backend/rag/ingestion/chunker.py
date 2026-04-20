"""Split extracted 3GPP spec text into overlapping chunks with metadata."""

from typing import Generator


CHUNK_SIZE = 800      # characters
CHUNK_OVERLAP = 150   # characters


def chunk_text(text: str, metadata: dict) -> Generator[dict, None, None]:
    """
    Yield chunks with metadata.
    Tries to split on paragraph boundaries first, falls back to fixed-size.
    """
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    current_chunk = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        if current_len + para_len > CHUNK_SIZE and current_chunk:
            chunk_text = "\n".join(current_chunk)
            yield {"text": chunk_text, "metadata": metadata.copy()}

            # Keep overlap: retain last paragraph(s) up to CHUNK_OVERLAP chars
            overlap = []
            overlap_len = 0
            for p in reversed(current_chunk):
                if overlap_len + len(p) <= CHUNK_OVERLAP:
                    overlap.insert(0, p)
                    overlap_len += len(p)
                else:
                    break
            current_chunk = overlap
            current_len = overlap_len

        current_chunk.append(para)
        current_len += para_len

    if current_chunk:
        yield {"text": "\n".join(current_chunk), "metadata": metadata.copy()}
