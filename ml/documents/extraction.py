"""Bounded extraction. Raw text stays in memory and is never persisted."""

from io import BytesIO
import math
import os
import re
import shutil
from pathlib import Path


class ExtractionError(ValueError):
    pass


def detect_type(data):
    import filetype

    kind = filetype.guess(data)
    if kind is None or kind.mime not in {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }:
        raise ExtractionError(
            "Only PDF, JPG, and PNG files with valid content are supported."
        )
    return kind.mime, kind.extension


def _estimate_skew(image):
    """Estimate small text-line rotation using a row projection profile."""
    import numpy as np
    from PIL import Image

    sample = image.copy()
    sample.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
    source = np.asarray(sample, dtype=np.uint8)
    if np.count_nonzero(source < 170) < 100:
        return 0.0

    def score(angle):
        rotated = sample.rotate(
            angle,
            resample=Image.Resampling.BILINEAR,
            expand=False,
            fillcolor=255,
        )
        rows = (np.asarray(rotated, dtype=np.uint8) < 170).sum(axis=1)
        return float(rows.var())

    zero_score = score(0)
    candidates = [step / 2 for step in range(-10, 11)]
    best = max(candidates, key=score)
    best_score = score(best)
    if best == 0 or best_score < zero_score * 1.015:
        return 0.0

    refine = [best + step / 10 for step in range(-5, 6)]
    best = max(refine, key=score)
    return best if abs(best) >= 0.3 else 0.0


def _preprocess_image(image):
    """Normalize photographed or scanned pages before Tesseract."""
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    normalized = ImageOps.exif_transpose(image).convert("L")
    normalized = ImageOps.autocontrast(normalized, cutoff=1)
    normalized = ImageEnhance.Contrast(normalized).enhance(1.35)
    angle = _estimate_skew(normalized)
    if angle:
        normalized = normalized.rotate(
            angle,
            resample=Image.Resampling.BICUBIC,
            expand=True,
            fillcolor=255,
        )

    width, height = normalized.size
    scale = min(
        2.5,
        1800 / max(width, height),
        math.sqrt(20_000_000 / (width * height)),
    )
    if scale > 1.05:
        normalized = normalized.resize(
            (round(width * scale), round(height * scale)),
            Image.Resampling.LANCZOS,
        )
    return normalized.filter(
        ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=3)
    )


def _ocr(image):
    import pytesseract

    # Prefer an explicit path, then PATH, then common Windows install paths.
    # This avoids requiring a machine-wide PATH edit for a standard install.
    configured = os.environ.get("TESSERACT_CMD", "").strip()
    if configured and Path(configured).is_dir():
        configured = str(
            Path(configured) / ("tesseract.exe" if os.name == "nt" else "tesseract")
        )
    discovered = shutil.which("tesseract")
    if not discovered and os.name == "nt":
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        candidates = (
            Path(program_files) / "Tesseract-OCR" / "tesseract.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "Tesseract-OCR" / "tesseract.exe",
        )
        discovered = next((str(path) for path in candidates if path.is_file()), None)
    pytesseract.pytesseract.tesseract_cmd = configured or discovered or "tesseract"
    if image.width * image.height > 20_000_000:
        raise ExtractionError("OCR image exceeds the 20 megapixel limit.")
    try:
        prepared = _preprocess_image(image)
        if prepared.width * prepared.height > 20_000_000:
            raise ExtractionError("OCR image exceeds the 20 megapixel limit.")
        primary = pytesseract.image_to_string(
            prepared, config="--oem 3 --psm 6", timeout=20
        )
        # Identity cards have sparse, separated labels; PSM 11 often recovers
        # those lines when the default block layout drops them. Run the second
        # pass only when OCR sees identity-card markers or very little text.
        identity_marker = re.search(
            r"permanent\s+account\s+number|income\s+tax\s+department|"
            r"unique\s+identification|\buidai\b|\baadhaar\b|\baadhar\b",
            primary,
            re.I,
        )
        identity_fields = bool(
            re.search(r"\bname\b", primary, re.I)
            and re.search(
                r"\b(?:d\.?\s*[o0]\.?\s*b\.?|dob|yob|date of birth)\b",
                primary,
                re.I,
            )
        )
        identifier_hint = bool(re.search(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", primary))
        identity_candidate = bool(identity_marker or identity_fields or identifier_hint)
        if not identity_candidate and len(primary.strip()) >= 160:
            return primary
        secondary = pytesseract.image_to_string(
            prepared, config="--oem 3 --psm 11", timeout=20
        )
        candidates = (primary, secondary)
        identity_text = re.compile(
            r"permanent\s+account\s+number|income\s+tax\s+department|"
            r"unique\s+identification|\buidai\b|\baadhaar\b|\baadhar\b",
            re.I,
        )
        if (
            any(identity_text.search(candidate) for candidate in candidates)
            and not re.search(r"\d{4}[ -]?\d{4}[ -]?\d{4}", "\n".join(candidates))
        ):
            # Aadhaar numbers sit near the lower edge of many card layouts and
            # can be too small when OCR runs over a full-page scan. OCR a
            # magnified lower band as a separate candidate; extraction still
            # validates the resulting 12-digit value before reporting it.
            from PIL import Image

            top = prepared.height // 3
            focused = prepared.crop((0, top, prepared.width, prepared.height))
            scale = min(
                2.0,
                math.sqrt(20_000_000 / (focused.width * focused.height)),
            )
            if scale > 1.05:
                focused = focused.resize(
                    (round(focused.width * scale), round(focused.height * scale)),
                    Image.Resampling.LANCZOS,
                )
            focused_text = pytesseract.image_to_string(
                focused, config="--oem 3 --psm 11", timeout=20
            )
            candidates += (focused_text,)
        if (
            identity_candidate
            or any(identity_text.search(candidate) for candidate in candidates)
        ):
            # Keep the better-structured pass first and retain the other pass
            # for fields that Tesseract may have missed in its first layout.
            ordered = sorted(
                candidates,
                key=lambda candidate: (_ocr_quality(candidate), len(candidate.strip())),
                reverse=True,
            )
            return "\n".join(candidate for candidate in ordered if candidate.strip())
        return max(
            candidates,
            key=lambda candidate: (_ocr_quality(candidate), len(candidate.strip())),
        )
    except pytesseract.TesseractNotFoundError:
        raise ExtractionError(
            "OCR requires Tesseract. Install Tesseract and add it to PATH."
        ) from None
    except RuntimeError:
        raise ExtractionError(
            "OCR timed out; upload a smaller, clearer document."
        ) from None


def _ocr_quality(text):
    """Prefer OCR output that preserves useful identity-card fields."""
    score = min(sum(char.isalnum() for char in text), 60)
    if re.search(r"\bname\b", text, re.I):
        score += 30
    if re.search(r"\b(?:d\.?\s*o\.?\s*b\.?|dob|yob|date of birth)\b", text, re.I):
        score += 30
    if re.search(
        r"\b(?:income tax department|permanent account number|uidai|aadhaar)\b",
        text,
        re.I,
    ):
        score += 20
    if re.search(r"(?:[A-Z][ \t]*){5}(?:\d[ \t]*){4}[A-Z]", text, re.I):
        score += 130
    if re.search(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", text):
        score += 130
    return score


def _scanned_pdf_page(data, index):
    """Render with bundled PDFium; no separate Poppler installation needed."""
    import pypdfium2

    with pypdfium2.PdfDocument(data) as document:
        page = document[index]
        try:
            width, height = page.get_size()
            scale = min(
                300 / 72,
                math.sqrt(20_000_000 / (width * height)),
            )
            bitmap = page.render(scale=scale)
            try:
                return bitmap.to_pil().copy()
            finally:
                bitmap.close()
        finally:
            page.close()


def extract(data, mime):
    try:
        if mime == "application/pdf":
            import pdfplumber

            with pdfplumber.open(BytesIO(data)) as pdf:
                if len(pdf.pages) > 20:
                    raise ExtractionError("PDF exceeds the 20-page limit.")
                metadata = {
                    k: str(v)
                    for k, v in (pdf.metadata or {}).items()
                    if k in {"Producer", "Creator", "CreationDate", "ModDate"}
                }
                texts, tables = [], []
                for index, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    # Scanned PDFs often contain an incomplete OCR text layer
                    # alongside the actual page image. A non-empty text layer
                    # is not evidence that identity fields were extracted.
                    # Re-OCR image-backed pages when the layer is short or
                    # lacks identity markers, then keep both sources so a
                    # partial text layer cannot hide fields visible on-page.
                    identity_markers = re.compile(
                        r"aadhaar|aadhar|uidai|unique\s+identification|"
                        r"permanent\s+account\s+number|income\s+tax\s+department|"
                        r"\b(?:name|address|gender|dob|yob)\b|"
                        r"\d{4}[ -]?\d{4}[ -]?\d{4}",
                        re.I,
                    )
                    needs_ocr = len(text.strip()) < 25 or (
                        bool(page.images)
                        and (
                            len(text.strip()) < 1000
                            or not identity_markers.search(text)
                        )
                    )
                    if needs_ocr:
                        with _scanned_pdf_page(data, index) as image:
                            try:
                                rendered_text = _ocr(image)
                            except ExtractionError:
                                if len(text.strip()) < 25:
                                    raise
                            else:
                                if rendered_text.strip():
                                    text = "\n".join(
                                        part
                                        for part in (text.strip(), rendered_text.strip())
                                        if part
                                    )
                    texts.append(text)
                    tables.extend(page.extract_tables() or [])
                return "\n".join(texts), metadata, tables
        from PIL import Image

        with Image.open(BytesIO(data)) as img:
            if img.width * img.height > 20_000_000:
                raise ExtractionError("Image exceeds the 20 megapixel limit.")
            img.load()
            text = _ocr(img)
            if sum(char.isalnum() for char in text) < 12:
                raise ExtractionError(
                    "OCR found too little readable text. Upload a sharp, "
                    "higher-resolution image showing the full document."
                )
            return text, {}, []
    except ExtractionError:
        raise
    except Exception:
        raise ExtractionError(
            "Document cannot be read. Use an unencrypted, valid PDF or clear"
            " image."
        ) from None
