"""
Signature-based file carving.

For each known signature, scan the raw byte buffer for every occurrence
of its header. For each header found, search forward for the matching
footer within max_size bytes:
  - Footer found -> clean extraction, header through footer (inclusive).
  - No footer found within the window -> truncated extraction, cut off
    at max_size, flagged so the confidence scorer can mark it as a guess
    rather than a confirmed-complete file.

This does not attempt fragmented/non-contiguous file reconstruction —
that's flagged as a known, documented limitation (see docs/phase4.md),
consistent with treating it as a research-grade stretch goal rather than
promising something not actually solved.
"""
from dataclasses import dataclass

from src.signatures import SIGNATURES, FileSignature


@dataclass
class CarvedFile:
    signature_name: str
    extension: str
    offset: int
    size: int
    data: bytes
    footer_found: bool  # False = truncated/guessed cutoff, not a confirmed-complete file


def carve(buffer: bytes) -> list[CarvedFile]:
    """Scan the full buffer against every known signature. Returns one
    CarvedFile per header match found, in the order signatures are
    checked (not necessarily byte-offset order across different types)."""
    results: list[CarvedFile] = []

    for sig in SIGNATURES:
        results.extend(_carve_for_signature(buffer, sig))

    return results


def _carve_for_signature(buffer: bytes, sig: FileSignature) -> list[CarvedFile]:
    found: list[CarvedFile] = []
    search_start = 0

    while True:
        header_pos = buffer.find(sig.header, search_start)
        if header_pos == -1:
            break

        window_end = min(len(buffer), header_pos + sig.max_size)
        window = buffer[header_pos:window_end]

        if sig.footer is not None:
            footer_pos_in_window = window.find(sig.footer, len(sig.header))
        else:
            footer_pos_in_window = -1

        if footer_pos_in_window != -1:
            end = header_pos + footer_pos_in_window + len(sig.footer) + sig.footer_trailing_fixed_bytes
            end = min(end, len(buffer))  # never read past the actual buffer
            footer_found = True
        else:
            end = window_end
            footer_found = False

        data = buffer[header_pos:end]
        found.append(CarvedFile(
            signature_name=sig.name,
            extension=sig.extension,
            offset=header_pos,
            size=len(data),
            data=data,
            footer_found=footer_found,
        ))

        # Continue searching after this match to avoid re-finding the
        # same header, and to avoid re-scanning the (potentially huge)
        # window we just consumed.
        search_start = end if end > header_pos else header_pos + 1

    return found
