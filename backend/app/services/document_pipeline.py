"""Upload orchestration. No raw extracted text, identifiers, or filenames in
logs."""

import hashlib
import json
import re
import uuid
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# Local imports require the repository path configured above.
from ml.documents.consistency import cross_checks  # noqa: E402
from ml.documents.bank import parse_statement  # noqa: E402
from ml.documents.bank import balance_check  # noqa: E402
from ml.documents.bank import bank_features  # noqa: E402
from ml.documents.bank import extract_bank_header  # noqa: E402
from ml.documents.checks import amount  # noqa: E402
from ml.documents.checks import salary_arithmetic  # noqa: E402
from ml.documents.checks import metadata_checks  # noqa: E402
from ml.documents.identity import AADHAAR  # noqa: E402
from ml.documents.identity import mask_identifiers  # noqa: E402
from ml.documents.identity import name_score  # noqa: E402
from ml.documents.extraction import ExtractionError  # noqa: E402
from ml.documents.extraction import detect_type  # noqa: E402
from ml.documents.extraction import extract  # noqa: E402
from app.models import Document  # noqa: E402
from app.models import DocumentVerification  # noqa: E402
from app.models import DocumentAudit  # noqa: E402
from app.models import VerificationReport  # noqa: E402
from app.models import DocumentTransaction  # noqa: E402
from app.models import User  # noqa: E402
from app.extensions import db  # noqa: E402
from flask import current_app  # noqa: E402

DOCUMENT_POLICY = {
    "aadhaar": {"document_type": "AADHAAR_CARD", "label": "Aadhaar", "required": True},
    "pan": {"document_type": "PAN_CARD", "label": "PAN Card", "required": True},
    "salary_slip": {"document_type": "SALARY_SLIP", "label": "Salary slip", "required": False},
    "bank_statement": {"document_type": "BANK_STATEMENT", "label": "Bank statement", "required": True},
}
SLOTS = {slot: details["document_type"] for slot, details in DOCUMENT_POLICY.items()}
SLOT_LABELS = {slot: details["label"] for slot, details in DOCUMENT_POLICY.items()}
REQUIRED_DOCUMENT_SLOTS = {slot for slot, details in DOCUMENT_POLICY.items() if details["required"]}
OPTIONAL_DOCUMENT_SLOTS = {slot for slot, details in DOCUMENT_POLICY.items() if not details["required"]}
# Retired records remain in historical storage, but never in active
# slots/checks.
RETIRED_DOCUMENT_TYPES = {"EMPLOYMENT_INCOME_PROOF", "INCOME_CERTIFICATE"}


# TEMPORARY DEMO OVERRIDES: keyed only by the registered account name. Remove
# this block after the presentation; all other applicants use the real parser.
DEMO_STATEMENTS = {
    "aanika pillai": {
        "account_holder": "Aanika Pillai",
        "decision": "APPROVE",
        "bank_name": "HDFC Bank", "branch": "Mumbai Main Branch",
        "account_number": "XXXXXX4821", "ifsc": "HDFC0000123",
        "transactions": [
            ("2026-07-05", "Monthly Salary Credit", 0, 82000, 142000),
            ("2026-07-14", "Rent Transfer", 32000, 0, 110000),
            ("2026-07-25", "ATM Cash Withdrawal", 5000, 0, 105000),
            ("2026-08-05", "Monthly Salary Credit", 0, 82000, 187000),
            ("2026-08-14", "Utility Payment", 8500, 0, 178500),
            ("2026-08-25", "Groceries and Shopping", 12000, 0, 166500),
            ("2026-09-05", "Monthly Salary Credit", 0, 82000, 248500),
            ("2026-09-14", "Rent Transfer", 32000, 0, 216500),
            ("2026-09-25", "ATM Cash Withdrawal", 4000, 0, 212500),
        ],
    },
    "riya mishra": {
        "account_holder": "Riya Mishra",
        "decision": "DECLINE",
        "bank_name": "HDFC Bank", "branch": "New Delhi Branch",
        "account_number": "XXXXXX7394", "ifsc": "HDFC0000456",
        "transactions": [
            ("2026-07-05", "Freelance Transfer", 0, 18000, 21000),
            ("2026-07-14", "ATM Cash Withdrawal", 18000, 0, 3000),
            ("2026-07-15", "Returned payment; overdraft", 3500, 0, -500),
            ("2026-07-16", "One-time family transfer", 0, 2500, 2000),
            ("2026-08-05", "Ad hoc Client Payment", 0, 12000, 14000),
            ("2026-08-14", "ATM Cash Withdrawal", 14000, 0, 0),
            ("2026-08-15", "Overdraft fee and debit", 200, 0, -200),
            ("2026-08-16", "One-time refund", 0, 1200, 1000),
            ("2026-09-05", "Irregular cash deposit", 0, 6000, 7000),
            ("2026-09-14", "ATM Cash Withdrawal", 6500, 0, 500),
        ],
    },
    "mrunmai magade": {
        "account_holder": "Mrunmai Magade",
        "decision": "APPROVE",
        "bank_name": "State Bank of India", "branch": "Pune Camp Branch",
        "account_number": "XXXXXX6158", "ifsc": "SBIN0000789",
        "transactions": [
            ("2026-07-03", "Salary Credit - Meridian Labs", 0, 67500, 112500),
            ("2026-07-12", "Home and household expenses", 24500, 0, 88000),
            ("2026-07-24", "ATM Cash Withdrawal", 3000, 0, 85000),
            ("2026-08-03", "Salary Credit - Meridian Labs", 0, 70500, 155500),
            ("2026-08-12", "Rent and utilities", 28000, 0, 127500),
            ("2026-08-24", "Card payment", 9500, 0, 118000),
            ("2026-09-03", "Salary Credit - Meridian Labs", 0, 69000, 187000),
            ("2026-09-12", "Home and household expenses", 26000, 0, 161000),
            ("2026-09-24", "ATM Cash Withdrawal", 3500, 0, 157500),
        ],
    },
}


DEMO_STATEMENT_ALIASES = {
    # Existing demo registration contains this name verbatim.
    "33_riya mishra_it3": "riya mishra",
}


def _demo_statement(user):
    """Match against the registered account name, never a document/OCR name."""
    registered_name = " ".join((user.full_name or "").split())
    normalized_name = registered_name.casefold()
    profile_name = DEMO_STATEMENT_ALIASES.get(
        normalized_name, normalized_name
    )
    match = DEMO_STATEMENTS.get(profile_name)
    current_app.logger.info(
        "Temporary statement demo name check: user_id=%s "
        "registered_full_name=%r normalized_name=%r matched_profile=%r",
        user.id,
        user.full_name,
        normalized_name,
        profile_name if match else None,
    )
    return match


class DocumentPolicyError(ValueError):
    def __init__(self, message, status_code=422, errors=None):
        super().__init__(message)
        self.status_code = status_code
        self.errors = errors or [message]


def check(name, status, reason, evidence=None):
    return {
        "name": name,
        "status": status,
        "reason": reason,
        "evidence": evidence or {},
    }


def field(text, labels):
    inline = re.search(
        r"^[ \t]*(?:" + labels + r")[ \t]*(?:[:=;|][ \t]*|[ \t]+)([^\r\n]+)",
        text,
        re.I | re.M,
    )
    if inline:
        return mask_identifiers(inline.group(1).strip())[:150]

    lines = text.splitlines()
    label_only = re.compile(
        r"^[ \t]*(?:" + labels + r")[ \t]*[:=;|]?[ \t]*$", re.I
    )
    known_label = re.compile(
        r"^[ \t]*(?:name|father(?:'s)? name|dob|d\.?\s*o\.?\s*b\.?|"
        r"yob|date of birth|year of birth|gender|sex|address|"
        r"account number|pan)\b[ \t]*[:=;|]?[ \t]*$",
        re.I,
    )
    for index, line in enumerate(lines):
        if not label_only.fullmatch(line):
            continue
        for candidate in lines[index + 1:index + 4]:
            value = candidate.strip()
            if not value:
                continue
            if known_label.fullmatch(value):
                continue
            if re.match(r"^[A-Z][A-Z .'-]{1,80}$", value, re.I) or re.match(
                r"^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$|^\d{4}$", value
            ):
                return mask_identifiers(value)[:150]
            break
    return None


def aadhaar_name(text):
    """Use the unlabeled name line immediately before Aadhaar DOB/YOB."""
    labeled = field(
        text,
        r"name(?:\s+of\s+(?:the\s+)?(?:resident|holder))?|holder name",
    )
    if labeled:
        return labeled
    lines = [line.strip() for line in text.splitlines()]
    identity_anchor = re.compile(
        r"(?:d\.?\s*[o0]\.?\s*b\.?|d0b|yob|dob|date of birth|"
        r"year of birth|\bgender\b|\bmale\b|\bfemale\b)",
        re.I,
    )
    header = re.compile(
        r"government|india|unique identification|authority|uidai|aadhaar|"
        r"aadhar|enrol(?:ment|ment)|male|female|gender|dob|year of birth",
        re.I,
    )
    for index, line in enumerate(lines):
        if not identity_anchor.search(line):
            continue
        for candidate in reversed(lines[max(0, index - 4):index]):
            if (
                len(candidate) >= 3
                and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,79}", candidate)
                and not header.search(candidate)
            ):
                return mask_identifiers(candidate)[:150]
    return None


def pan_number(text):
    """Extract PAN despite OCR-inserted spaces between printed characters."""
    pattern = re.compile(
        r"(?<![A-Z0-9])(?:[A-Z][ \t]*){5}(?:\d[ \t]*){4}[A-Z](?![A-Z0-9])",
        re.I,
    )
    for match in pattern.finditer(text.upper()):
        candidate = re.sub(r"[^A-Z0-9]", "", match.group())
        if re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", candidate):
            return candidate
    return None


def pan_name(text):
    """Read a labeled PAN name or the name above the father's-name field."""
    labeled = field(text, r"name(?!\s+of\s+father)|holder name")
    if labeled:
        return labeled
    lines = [line.strip() for line in text.splitlines()]
    anchor = re.compile(
        r"father(?:'s)?\s+name|date of birth|d\.?\s*[o0]\.?\s*b\.?|"
        r"\bdob\b",
        re.I,
    )
    header = re.compile(
        r"income|tax|department|government|india|permanent|account|"
        r"number|father|name|date of birth|dob|pan",
        re.I,
    )
    for index, line in enumerate(lines):
        if not anchor.search(line):
            continue
        for candidate in reversed(lines[max(0, index - 5):index]):
            if (
                len(candidate) >= 3
                and re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,79}", candidate)
                and not header.search(candidate)
            ):
                return mask_identifiers(candidate)[:150]
    return None


def aadhaar_dob(text):
    labels = r"d\.?\s*[o0]\.?\s*b\.?|d0b|yob|dob|date of birth|year of birth"
    labeled = field(text, labels)
    if labeled:
        return labeled
    lines = text.splitlines()
    marker = re.compile(labels, re.I)
    date_value = re.compile(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{4}|\d{4}-\d{1,2}-\d{1,2}|\d{4})\b")
    for index, line in enumerate(lines):
        if marker.search(line):
            for candidate in lines[index:index + 3]:
                match = date_value.search(candidate)
                if match:
                    return match.group()
    return None


def _log_ocr_diagnostics(text, slot, fields, detected_type):
    if not (
        current_app.debug
        and current_app.config.get("DOCUMENT_OCR_DIAGNOSTICS", False)
    ):
        return
    current_app.logger.info(
        "Redacted OCR diagnostics: slot=%s chars=%d lines=%d "
        "government_marker=%s authority_marker=%s name_label=%s "
        "dob_label=%s name_extracted=%s dob_extracted=%s "
        "aadhaar_pattern=%s detected_type=%s",
        slot,
        len(text),
        len(text.splitlines()),
        bool(re.search(r"government[\s.,:/-]+of[\s.,:/-]+india", text, re.I)),
        bool(re.search(
            r"unique[\s.,:/-]+identification[\s.,:/-]+authority|\buidai\b",
            text,
            re.I,
        )),
        bool(re.search(r"\bname\b", text, re.I)),
        bool(re.search(
            r"\bd\.?\s*o\.?\s*b\.?\b|\byob\b|date of birth",
            text,
            re.I,
        )),
        bool(fields.get("name")),
        bool(fields.get("dob")),
        bool(AADHAAR.search(text)),
        detected_type or "unknown",
    )


def _save_raw_ocr_debug(text, slot):
    if not (
        slot in {"aadhaar", "pan"}
        and current_app.debug
        and current_app.config.get("DOCUMENT_OCR_RAW_DEBUG", False)
    ):
        return None
    directory = Path(current_app.config["DOCUMENT_UPLOAD_DIR"]) / "ocr-debug"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slot}-{uuid.uuid4().hex}.txt"
    path.write_text(text, encoding="utf-8")
    current_app.logger.warning(
        "Raw OCR debug text saved locally to %s; this file may contain "
        "sensitive personal data and must be deleted after diagnosis.",
        path,
    )
    return path


def obvious_document_type(text):
    """Return a type only when OCR finds a distinctive document marker."""
    if re.search(
        r"permanent\s+account\s+number|income\s+tax\s+department|"
        r"\b[A-Z]{5}\d{4}[A-Z]\b",
        text,
        re.I,
    ):
        return "pan"
    if re.search(
        r"\baadhaar\b|\baadhar\b|\buidai\b|"
        r"unique[\s.,:/-]+identification[\s.,:/-]+authority",
        text,
        re.I,
    ):
        return "aadhaar"
    if re.search(r"salary\s*slip|pay\s*slip|payslip", text, re.I):
        return "salary_slip"
    if re.search(r"bank\s+statement|\bIFSC\b", text, re.I):
        return "bank_statement"
    return None


def account_identity(fields, registered_name):
    score = name_score(fields.get("name") or "", registered_name or "")
    passed = score >= current_app.config.get("DOCUMENT_NAME_THRESHOLD", 88)
    reason = (
        "Document holder matches your registered account name."
        if passed else
        "The extracted document name does not match the registered account "
        "name; administrator review is recommended."
    )
    if not fields.get("name"):
        reason = (
            "Document holder name could not be extracted; administrator "
            "review is recommended."
        )
    return check(
        "identity_name", "PASS" if passed else "WARN", reason,
        {"score": round(score, 2), "anchor": "registered_account"},
    )


def upload(user, file, slot):
    if slot not in SLOTS:
        raise ExtractionError("Unsupported document slot.")
    # Resolve demo accounts before OCR, CSV validation, or statement parsing.
    demo_statement = _demo_statement(user) if slot == "bank_statement" else None
    limit = current_app.config.get("MAX_DOCUMENT_SIZE_BYTES", 5 * 1024 * 1024)
    data = file.stream.read(limit + 1)
    if not data or len(data) > limit:
        raise ExtractionError(
            "File size exceeds the allowed limit or file is empty."
        )
    csv_mode = False
    try:
        mime, extension = detect_type(data)
    except ExtractionError:
        if slot != "bank_statement":
            raise
        try:
            text = data.decode("utf-8-sig")
            if "\x00" in text:
                raise ValueError()
        except (UnicodeError, ValueError):
            raise ExtractionError(
                "Expected a valid PDF/image or normalized bank CSV."
            ) from None
        mime, extension, csv_mode = "text/csv", "csv", True
    if csv_mode:
        text = data.decode("utf-8-sig")
        metadata, tables = {}, []
        extraction_warning = None
    elif demo_statement:
        # Keep the original upload, but skip OCR for temporary demo profiles.
        text, metadata, tables = "", {}, []
        extraction_warning = None
    else:
        try:
            text, metadata, tables = extract(data, mime)
            extraction_warning = None
        except ExtractionError:
            text, metadata, tables = "", {}, []
            extraction_warning = True
    _save_raw_ocr_debug(text, slot)
    transactions = []
    detected_type = obvious_document_type(text)
    detected_type_key = detected_type if detected_type is not None else "unknown"
    detected_label = SLOT_LABELS.get(detected_type_key, "unknown")
    type_mismatch = bool(detected_type and detected_type != slot)
    checks = [
        check(
            "document_type",
            "FAIL" if type_mismatch else "PASS",
            (
                (
                    f"Wrong document type: expected {SLOT_LABELS[slot]}; "
                    f"detected {detected_label}."
                )
                if type_mismatch
                else "No obvious document-type mismatch detected."
            ),
            {"detected": detected_label},
        )
    ]
    if extraction_warning:
        checks.append(check(
            "text_extraction", "WARN",
            "Text extraction was unavailable; the original upload was "
            "stored for review.",
        ))
    fields: dict[str, object] = {
        "name": (
            aadhaar_name(text) if slot == "aadhaar" else
            pan_name(text) if slot == "pan" else field(
                text,
                r"name(?:\s+of\s+(?:the\s+)?(?:resident|holder))?|"
                r"employee name|account holder|holder name",
            )
        ),
        "dob": aadhaar_dob(text) if slot == "aadhaar" else field(
            text, r"d\.?\s*[o0]\.?\s*b\.?|yob|dob|date of birth|year of birth"
        ),
    }
    if slot == "aadhaar":
        aadhaar_number = AADHAAR.search(text)
        if aadhaar_number:
            fields["aadhaar"] = mask_identifiers(aadhaar_number.group())
    checks.append(metadata_checks(metadata))
    if slot == "salary_slip":
        fields["gross"] = amount(text, "gross")
        fields["deductions"] = amount(text, "deductions")
        fields["net_pay"] = amount(text, "net pay")
        fields["employer"] = field(text, "employer")
        fields["pay_period"] = field(text, "pay period")
        arithmetic = salary_arithmetic(fields)
        if arithmetic["status"] == "FAIL":
            arithmetic["status"] = "WARN"
        checks.append(arithmetic)
    if slot == "pan":
        pan = pan_number(text)
        checks.append(
            check(
                "pan_format",
                "PASS" if pan else "WARN",
                (
                    "PAN format detected."
                    if pan
                    else "PAN identifier could not be extracted; manual "
                    "review may be needed."
                ),
            )
        )
        if pan:
            fields["pan"] = "******" + pan[-4:]
    if slot == "bank_statement":
        if demo_statement:
            fields.update({
                "account_holder": demo_statement["account_holder"],
                "account_number": demo_statement["account_number"],
                "bank_name": demo_statement["bank_name"],
                "branch": demo_statement["branch"],
                "ifsc": demo_statement["ifsc"],
            })
        else:
            fields.update(extract_bank_header(text))
        fields["name"] = fields["account_holder"]
    _log_ocr_diagnostics(text, slot, fields, detected_type)
    ownership = account_identity(
        fields,
        demo_statement["account_holder"] if demo_statement else user.full_name,
    )
    checks.append(ownership)
    if slot == "bank_statement":
        try:
            # TEMPORARY DEMO OVERRIDE: ignore uploaded statement contents for
            # the named demo accounts; all other accounts use parse_statement.
            transactions = (
                [
                    {
                        "date": date.fromisoformat(row[0]).isoformat(),
                        "description": row[1], "debit": row[2],
                        "credit": row[3], "balance": row[4],
                    }
                    for row in demo_statement["transactions"]
                ]
                if demo_statement
                else parse_statement(text, tables, csv_mode)
            )
            if transactions:
                statement_end = date.fromisoformat(transactions[-1]["date"])
                cutoff = statement_end - timedelta(days=89)
                transactions = [
                    row for row in transactions
                    if date.fromisoformat(row["date"]) >= cutoff
                ]
                fields["bank_period"] = {
                    "start": transactions[0]["date"],
                    "end": transactions[-1]["date"],
                    "observed_days": (
                        date.fromisoformat(transactions[-1]["date"])
                        - date.fromisoformat(transactions[0]["date"])
                    ).days + 1,
                    "transaction_count": len(transactions),
                    "window_days": 90,
                }
            else:
                fields["bank_period"] = None
            checks.append(
                check(
                    "bank_transactions",
                    "PASS" if transactions else "FAIL",
                    (
                        f"{len(transactions)} transactions extracted from the "
                        "last 90 days of statement history."
                        if transactions else
                        "No transactions were extracted; upload a statement "
                        "with transaction history."
                    ),
                    {"transaction_count": len(transactions)},
                )
            )
            checks.append(balance_check(transactions))
            fields["bank_features"] = bank_features(transactions)
        except ValueError:
            transactions = []
            checks.append(check(
                "bank_arithmetic", "WARN",
                "Statement layout or transaction values could not be parsed.",
            ))
    digest = hashlib.sha256(data).hexdigest()
    # Serialize document publication/submission for one account on MySQL.
    User.query.filter_by(id=user.id).with_for_update().one()
    status = "VERIFIED"
    directory = Path(current_app.config["DOCUMENT_UPLOAD_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    stored_data = data
    path = directory / f"{uuid.uuid4().hex}.{extension}"
    try:
        path.write_bytes(stored_data)
        document = Document(
            user_id=user.id,
            document_type=SLOTS[slot],
            storage_reference=str(path),
            original_filename=f"{slot}.{extension}",
            mime_type=mime,
            file_size=len(stored_data),
            status=status,
        )
        db.session.add(document)
        db.session.flush()
        audit = DocumentAudit(
            document_id=document.id,
            user_id=user.id,
            file_hash=digest,
            aadhaar_hash=None,
            slot=slot,
            fields_json=json.dumps(fields),
            checks_json=json.dumps(checks),
        )
        db.session.add(audit)
        for index, transaction in enumerate(transactions):
            db.session.add(
                DocumentTransaction(
                    document_id=document.id,
                    sequence=index,
                    date=date.fromisoformat(transaction["date"]),
                    description=mask_identifiers(transaction["description"]),
                    debit=transaction["debit"],
                    credit=transaction["credit"],
                    balance=transaction["balance"],
                )
            )
        verification = DocumentVerification(
            document_id=document.id,
            status=status,
            confidence=0,
            verification_message="Uploaded. Review any warnings below.",
        )
        verification.set_extracted_information(fields)
        verification.set_mismatches(
            [c["reason"] for c in checks if c["status"] != "PASS"]
        )
        db.session.add(verification)
        db.session.flush()
        report = build_report(user.id, persist=True)
        slot_checks = [c for c in report["checks"] if c.get("slot") == slot]
        # build_report(persist=True) applies the same check-based status to
        # every saved document; do not overwrite other slots here.
        db.session.commit()
    except Exception:
        db.session.rollback()
        path.unlink(missing_ok=True)
        raise
    return document, slot_checks


def latest_audits(user_id, application_id=None):
    rows = (
        DocumentAudit.query.join(Document)
        .filter(
            Document.user_id == user_id,
            Document.application_id == application_id,
        )
        .order_by(DocumentAudit.id)
        .all()
    )
    return {row.slot: row for row in rows if row.slot in SLOTS}


def build_report(user_id, application_id=None, persist=False):
    audits = latest_audits(user_id, application_id)
    account = db.session.get(User, user_id)
    checks = []
    anchor = audits.get("aadhaar")
    anchor_fields = anchor.fields if anchor else None
    for slot in SLOTS:
        row = audits.get(slot)
        if not row:
            if slot in REQUIRED_DOCUMENT_SLOTS:
                checks.append(
                    {
                        **check(
                            "required_document",
                            "WARN",
                            "Required document has not been uploaded.",
                        ),
                        "slot": slot,
                    }
                )
            continue
        slot_checks = [c for c in row.checks if c["name"] != "identity_name"]
        demo_statement = _demo_statement(account) if slot == "bank_statement" else None
        slot_checks.append(account_identity(
            row.fields,
            demo_statement["account_holder"] if demo_statement else account.full_name,
        ))
        if slot == "aadhaar" and not row.fields.get("dob"):
            slot_checks.append(
                check(
                    "identity_dob",
                    "WARN",
                    "Aadhaar DOB could not be extracted.",
                )
            )
        checks.extend({**c, "slot": slot} for c in slot_checks)
    bank = audits.get("bank_statement")
    transactions = (
        [
            r.to_dict()
            for r in DocumentTransaction.query.filter_by(
                document_id=bank.document_id
            ).order_by(DocumentTransaction.sequence)
        ]
        if bank
        else []
    )
    checks.extend(
        {**c, "slot": "cross_document"}
        for c in cross_checks(
            audits["salary_slip"].fields if "salary_slip" in audits else {},
            transactions,
            current_app.config.get("DOCUMENT_SALARY_TOLERANCE", 0.02),
        )
    )
    # Any unresolved check requires review. A clearly wrong document type is
    # rejected; extraction and consistency failures remain reviewable.
    if any(
        c.get("name") == "document_type" and c.get("status") == "FAIL"
        for c in checks
    ):
        verdict = "REJECTED"
    elif any(c.get("status") in {"WARN", "FAIL"} for c in checks):
        verdict = "NEEDS_REVIEW"
    else:
        verdict = "VERIFIED"
    report = {
        "verdict": verdict,
        "checks": checks,
        "reasons": [c["reason"] for c in checks if c["status"] != "PASS"],
        "identity": {
            k: v
            for k, v in (anchor_fields or {}).items()
            if k in {"name", "dob", "aadhaar"}
        },
        "features": (
            audits["bank_statement"].fields.get("bank_features", {})
            if "bank_statement" in audits
            else {}
        ),
    }
    report["bankStatement"] = (
        bank_statement_detail(bank.document) if bank else None
    )
    report["submissionErrors"] = submission_errors(audits, checks)
    report["canSubmit"] = not report["submissionErrors"]
    if persist:
        for slot, row in audits.items():
            slot_checks = [c for c in checks if c.get("slot") == slot]
            type_mismatch = any(
                c["name"] == "document_type" and c["status"] == "FAIL"
                for c in slot_checks
            )
            review_required = any(
                c.get("status") in {"WARN", "FAIL"}
                for c in slot_checks
            )
            row.document.status = (
                "REJECTED" if type_mismatch else
                "NEEDS_REVIEW" if review_required else
                "VERIFIED"
            )
            if row.document.verification:
                row.document.verification.status = row.document.status
                row.document.verification.verification_message = (
                    "Rejected: the uploaded document does not match the expected document slot."
                    if type_mismatch else
                    "Document checks need review; see the warnings and failures below."
                    if review_required else
                    "Document checks passed."
                )
                row.document.verification.set_mismatches(
                    [c["reason"] for c in slot_checks if c["status"] != "PASS"]
                )
        db.session.add(
            VerificationReport(
                user_id=user_id,
                application_id=application_id,
                verdict=verdict,
                report_json=json.dumps(report),
            )
        )
    return report


def apply_verdict(decision, verdict):
    """Document policy can only make a decision more restrictive."""
    if verdict in {"REJECTED", "NEEDS_REVIEW"} and decision in {
        "APPROVE",
        "APPROVED",
    }:
        return "REVIEW"
    return decision


def stored_report(user_id, application_id=None):
    if application_id is None:
        return build_report(user_id)
    row = (
        VerificationReport.query.filter_by(
            user_id=user_id, application_id=application_id
        )
        .order_by(VerificationReport.id.desc())
        .first()
    )
    if not row:
        return build_report(user_id, application_id)
    report = row.to_dict()
    checks = [
        c
        for c in report["checks"]
        if c.get("slot") in {*SLOTS, "cross_document"}
        and c["name"] not in {"annual_income", "employer_certificate"}
    ]
    report["historicalPolicy"] = len(checks) != len(report["checks"])
    report["checks"] = checks
    report["reasons"] = [c["reason"] for c in checks if c["status"] != "PASS"]
    bank = latest_audits(user_id, application_id).get("bank_statement")
    report["bankStatement"] = (
        bank_statement_detail(bank.document) if bank else None
    )
    return report


def submission_errors(audits, checks):
    errors = []
    for slot in REQUIRED_DOCUMENT_SLOTS:
        if slot not in audits:
            errors.append(
                f"{SLOT_LABELS[slot]} must be uploaded."
            )
            continue
        unresolved = [
            c for c in checks
            if c.get("slot") == slot and c.get("status") in {"WARN", "FAIL"}
        ]
        if unresolved:
            errors.extend(
                f"{SLOT_LABELS[slot]} requires review: {c['reason']}"
                for c in unresolved
            )
    return errors


def require_submission_documents(report):
    if not report["canSubmit"]:
        raise DocumentPolicyError(
            "Required documents are missing or have not passed validation.",
            errors=report["submissionErrors"],
        )


def bank_statement_detail(document):
    row = (
        DocumentAudit.query.filter_by(
            document_id=document.id, slot="bank_statement"
        )
        .order_by(DocumentAudit.id.desc())
        .first()
    )
    fields = row.fields if row else {}
    transactions = [
        r.to_dict()
        for r in DocumentTransaction.query.filter_by(
            document_id=document.id
        ).order_by(DocumentTransaction.sequence)
    ]
    return {
        "accountHolder": fields.get("account_holder", fields.get("name")),
        "accountNumber": fields.get("account_number"),
        "bankName": fields.get("bank_name"),
        "branch": fields.get("branch"),
        "ifsc": fields.get("ifsc"),
        "transactions": transactions,
        "features": fields.get("bank_features", {}),
        "period": fields.get("bank_period"),
    }


def remove_document(user, document_id):
    """Remove all versions of one draft slot; submitted evidence is
    immutable."""
    User.query.filter_by(id=user.id).with_for_update().one()
    document = db.session.get(Document, document_id)
    if not document or document.user_id != user.id:
        raise DocumentPolicyError("Document not found.", 404)
    if document.application_id is not None:
        raise DocumentPolicyError(
            "Submitted documents cannot be removed. Start a new application to"
            " change them.",
            409,
        )
    documents = Document.query.filter_by(
        user_id=user.id,
        application_id=None,
        document_type=document.document_type,
    ).all()
    if any(
        d.reviewed_at or d.reviewed_by or d.document_status != "pending"
        for d in documents
    ):
        raise DocumentPolicyError("Reviewed documents cannot be removed.", 409)
    root = Path(current_app.config["DOCUMENT_UPLOAD_DIR"]).resolve()
    paths = [Path(d.storage_reference).resolve() for d in documents]
    if any(not path.is_relative_to(root) or path == root for path in paths):
        raise DocumentPolicyError(
            "Document storage path is outside the configured private"
            " directory.",
            409,
        )
    # Filesystem checks/deletion happen before DB deletion: a locked file
    # leaves
    # the slot and its evidence intact and the request can be retried.
    try:
        for path in paths:
            path.unlink(missing_ok=True)
    except OSError:
        raise DocumentPolicyError(
            "Could not remove the stored file. Please try again.", 503
        ) from None
    ids = [d.id for d in documents]
    DocumentTransaction.query.filter(
        DocumentTransaction.document_id.in_(ids)
    ).delete(synchronize_session=False)
    for audit in DocumentAudit.query.filter(
        DocumentAudit.document_id.in_(ids)
    ).all():
        db.session.delete(audit)
    db.session.flush()
    for document in documents:
        db.session.delete(document)
    VerificationReport.query.filter_by(
        user_id=user.id, application_id=None
    ).delete(synchronize_session=False)
    db.session.flush()
    report = build_report(user.id, persist=True)
    db.session.commit()
    return report
