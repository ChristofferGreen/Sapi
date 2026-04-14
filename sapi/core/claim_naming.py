"""Claim statement and label normalization helpers."""

from __future__ import annotations

import re

_SPACE_RE = re.compile(r"\s+")
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-'’][A-Za-z0-9]+)*")
_REPORTING_PREFIX_RE = (
    re.compile(
        r"^(?:(?:the|this)\s+)?"
        r"(?:paper|article|study|source|text|manuscript|authors?|researchers?|work)\s+"
        r"(?:(?:also|further|then|specifically)\s+)*"
        r"(?:claims?|argues?|suggests?|shows?|states?|proposes?|finds?|presents?|reports?|"
        r"describes?|outlines?|concludes?|gives?|provides?|identifies?|develops?|defends?)\s+"
        r"(?:that\s+)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:it|this)\s+"
        r"(?:(?:also|further|then|specifically)\s+)*"
        r"(?:claims?|argues?|suggests?|shows?|states?|proposes?|finds?|presents?|reports?|"
        r"describes?|outlines?|concludes?|gives?|provides?|identifies?|develops?|defends?)\s+"
        r"(?:that\s+)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"^(?:(?:the|this)\s+)?(?:introduction|section|analysis)\s+"
        r"(?:identifies?|argues?|states?|shows?)\s+(?:that\s+)?",
        re.IGNORECASE,
    ),
)
_RELATION_TOKENS: set[str] = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "has",
    "have",
    "had",
    "implies",
    "imply",
    "requires",
    "require",
    "constrains",
    "constrain",
    "reveals",
    "reveal",
    "shows",
    "show",
    "proves",
    "prove",
    "supports",
    "support",
    "contradicts",
    "contradict",
    "precludes",
    "preclude",
    "determines",
    "determine",
    "exists",
    "exist",
    "fixes",
    "fix",
    "can",
    "cannot",
    "must",
    "should",
}
_VERBISH_TOKENS: set[str] = {
    "argue",
    "argues",
    "claim",
    "claims",
    "conclude",
    "concludes",
    "constrain",
    "constrains",
    "contradict",
    "contradicts",
    "defend",
    "defends",
    "derive",
    "derives",
    "develop",
    "develops",
    "determine",
    "determines",
    "exist",
    "exists",
    "find",
    "finds",
    "give",
    "gives",
    "identify",
    "identifies",
    "imply",
    "implies",
    "indicate",
    "indicates",
    "predict",
    "predicts",
    "present",
    "presents",
    "propose",
    "proposes",
    "provide",
    "provides",
    "report",
    "reports",
    "require",
    "requires",
    "reveal",
    "reveals",
    "show",
    "shows",
    "speculate",
    "speculates",
    "support",
    "supports",
    "use",
    "uses",
    "yield",
    "yields",
}
_META_PREFIX_TOKENS = {
    "article",
    "authors",
    "introduction",
    "paper",
    "researchers",
    "section",
    "source",
    "study",
    "text",
    "work",
}
_SUBJECT_TRIM_TOKENS = {
    "a",
    "an",
    "another",
    "core",
    "first",
    "main",
    "other",
    "second",
    "that",
    "the",
    "third",
    "this",
}
_CONNECTIVE_TOKENS = {
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}
_CLAIM_HEADWORDS = {
    "argument",
    "assumption",
    "claim",
    "conclusion",
    "constraint",
    "finding",
    "model",
    "proof",
    "proposition",
    "result",
    "theorem",
}


def normalize_claim_statement_text(value: str) -> str:
    normalized = _SPACE_RE.sub(" ", value).strip()
    if not normalized:
        return ""
    stripped = _strip_reporting_prefixes(normalized)
    stripped = re.sub(r"^that\s+", "", stripped, flags=re.IGNORECASE).strip(" .,:;")
    stripped = _rewrite_assumption_statement(stripped)
    stripped = _rewrite_colon_statement(stripped)
    stripped = _rewrite_deriving_statement(stripped)
    stripped = _ensure_propositional_statement(stripped)
    stripped = stripped.strip(" .,:;")
    if not stripped:
        stripped = normalized.strip(" .,:;")
    return _sentence_case(stripped)


def _ensure_propositional_statement(value: str) -> str:
    tokens = _WORD_RE.findall(value)
    if not tokens:
        return value
    lowered_tokens = [token.lower() for token in tokens]
    has_relation = any(token in _RELATION_TOKENS for token in lowered_tokens)
    has_verbish = any(token in _VERBISH_TOKENS for token in lowered_tokens)
    if has_relation or has_verbish:
        return value
    if len(tokens) > 9:
        return value
    last_token = lowered_tokens[-1]
    if last_token not in (_CLAIM_HEADWORDS | {"version"}):
        return value
    return " ".join(tokens) + " exists"


def resolve_claim_short_title(*, raw_short_title: object, claim_text: str) -> str:
    title_candidate = (
        normalize_claim_statement_text(str(raw_short_title))
        if isinstance(raw_short_title, str)
        else ""
    )
    fallback_statement = normalize_claim_statement_text(claim_text)
    title = _derive_short_title(title_candidate or fallback_statement)
    if not title and title_candidate and fallback_statement:
        title = _derive_short_title(fallback_statement)
    return title or "Claim is true"


def shorten_claim_label(*, value: str, fallback_text: str | None = None) -> str:
    return resolve_claim_short_title(
        raw_short_title=value,
        claim_text=fallback_text or value,
    )


def _strip_reporting_prefixes(value: str) -> str:
    current = value.strip()
    for _ in range(3):
        next_value = current
        for pattern in _REPORTING_PREFIX_RE:
            candidate = pattern.sub("", next_value).strip()
            if candidate != next_value:
                next_value = candidate
        if next_value == current:
            break
        current = next_value
    return current


def _rewrite_assumption_statement(value: str) -> str:
    match = re.match(
        r"^(?:a|an|the)?\s*"
        r"(?:(?:one|two|three|first|second|third)\s+)?"
        r"(?:(?:core|main|other|another)\s+)?"
        r"assumption\s+is\s+(?:that\s+)?(.+)$",
        value,
        flags=re.IGNORECASE,
    )
    if match is None:
        return value
    subject = match.group(1).strip()
    subject = subject.split(":", 1)[0].strip()
    subject = re.sub(r"[,:;]", " ", subject)
    subject = _SPACE_RE.sub(" ", subject).strip()
    verb_match = re.match(
        r"^(?P<head>.+?)\s+(?:has|have|is|are|can|cannot|must|should)\b.*$",
        subject,
        flags=re.IGNORECASE,
    )
    if verb_match is not None:
        subject = verb_match.group("head").strip()
    subject = re.sub(r"^(?:a|an|the)\s+", "", subject, flags=re.IGNORECASE).strip()
    if not subject:
        return value
    return f"{subject} is assumed"


def _rewrite_colon_statement(value: str) -> str:
    match = re.match(r"^(?P<head>[^:]{3,160}):\s*(?P<tail>.+)$", value)
    if match is None:
        return value
    head = match.group("head").strip()
    tail = match.group("tail").strip()
    head_tokens = [token.lower() for token in _WORD_RE.findall(head)]
    if not any(token in _CLAIM_HEADWORDS for token in head_tokens):
        return value
    head = re.sub(r"^(?:a|an|the)\s+", "", head, flags=re.IGNORECASE).strip()
    if not head or not tail:
        return value
    return f"{head} shows {tail}"


def _rewrite_deriving_statement(value: str) -> str:
    match = re.match(r"^(?P<head>.+?),\s*deriving\s+(?P<tail>.+)$", value, flags=re.IGNORECASE)
    if match is None:
        return value
    head = match.group("head").strip()
    tail = match.group("tail").strip()
    head = re.sub(r"^(?:a|an|the)\s+", "", head, flags=re.IGNORECASE).strip()
    if not head or not tail:
        return value
    return f"{head} derives {tail}"


def _derive_short_title(statement: str) -> str:
    value = _SPACE_RE.sub(" ", statement).strip(" .,:;")
    if not value:
        return ""
    lower_bound_title = _derive_lower_bound_title(value)
    if lower_bound_title:
        return lower_bound_title
    tokens = _WORD_RE.findall(value)
    if not tokens:
        return ""
    tokens = _drop_meta_prefix(tokens)
    if not tokens:
        return ""
    relation_index = _find_relation_index(tokens)
    if relation_index <= 0:
        relation_index = _find_verbish_index(tokens)
    if relation_index > 0:
        subject_tokens = _subject_tokens(tokens[:relation_index])
        relation_token = _normalize_relation_token(tokens[relation_index], subject_tokens=subject_tokens)
        predicate_tokens = _predicate_tokens(tokens[relation_index + 1 :])
    else:
        subject_tokens = _subject_tokens(tokens)
        relation_token = "is"
        filtered_tokens = [
            token
            for token in tokens
            if token.lower() not in _CONNECTIVE_TOKENS and token.lower() not in _META_PREFIX_TOKENS
        ]
        remaining_tokens = list(filtered_tokens)
        for subject_token in subject_tokens:
            if remaining_tokens and remaining_tokens[0].lower() == subject_token.lower():
                remaining_tokens.pop(0)
        predicate_tokens = _predicate_tokens(remaining_tokens)
    if not subject_tokens:
        subject_tokens = _subject_tokens(tokens[:2]) or tokens[:1]
    if relation_token not in {"exist", "exists"} and not predicate_tokens:
        predicate_tokens = _predicate_tokens(tokens)
    if relation_token not in {"exist", "exists"} and not predicate_tokens:
        predicate_tokens = ["true"]
    words = (
        subject_tokens[:3] + [relation_token]
        if relation_token in {"exist", "exists"} and not predicate_tokens
        else subject_tokens[:3] + [relation_token] + predicate_tokens[:3]
    )
    words = _fit_word_budget(words=words, fallback_tokens=tokens)
    if not words:
        return ""
    label = " ".join(words)
    return _sentence_case(label)


def _derive_lower_bound_title(statement: str) -> str:
    match = re.search(
        r"\blower bound on\s+(?:the\s+)?(?P<subject>[a-z0-9'’\-\s]+)",
        statement,
        flags=re.IGNORECASE,
    )
    if match is None:
        return ""
    subject_tokens = _WORD_RE.findall(match.group("subject"))
    subject = _subject_tokens(subject_tokens)
    if not subject:
        return ""
    title = " ".join(subject[:2] + ["has", "lower", "bound"])
    return _sentence_case(title)


def _drop_meta_prefix(tokens: list[str]) -> list[str]:
    trimmed = list(tokens)
    while trimmed and trimmed[0].lower() in _META_PREFIX_TOKENS:
        trimmed.pop(0)
    while trimmed and trimmed[0].lower() in {"also", "further", "specifically", "then"}:
        trimmed.pop(0)
    return trimmed


def _find_relation_index(tokens: list[str]) -> int:
    for index, token in enumerate(tokens):
        if index == 0:
            continue
        if token.lower() in _RELATION_TOKENS:
            return index
    return -1


def _find_verbish_index(tokens: list[str]) -> int:
    for index, token in enumerate(tokens):
        if index == 0:
            continue
        if token.lower() in _VERBISH_TOKENS:
            return index
    return -1


def _subject_tokens(tokens: list[str]) -> list[str]:
    cleaned = [token for token in tokens if token]
    while cleaned and cleaned[0].lower() in _SUBJECT_TRIM_TOKENS:
        cleaned.pop(0)
    filtered: list[str] = []
    for token in cleaned:
        lower = token.lower()
        if filtered and lower in {"about", "between", "for", "of", "over", "under", "with", "within"}:
            break
        if filtered and lower in {"either"}:
            break
        if lower in _CONNECTIVE_TOKENS:
            continue
        if lower in _META_PREFIX_TOKENS:
            continue
        filtered.append(token)
    if not filtered:
        filtered = cleaned
    return filtered[:3]


def _predicate_tokens(tokens: list[str]) -> list[str]:
    cleaned = [token for token in tokens if token]
    while cleaned and cleaned[0].lower() in _CONNECTIVE_TOKENS:
        cleaned.pop(0)
    filtered: list[str] = []
    for token in cleaned:
        lower = token.lower()
        if lower in {"also", "further", "specifically", "then", "that"}:
            continue
        filtered.append(token)
    if not filtered:
        filtered = cleaned
    return filtered[:3]


def _normalize_relation_token(token: str, *, subject_tokens: list[str]) -> str:
    lowered = token.lower()
    if lowered in {"was", "be"}:
        return "is"
    if lowered == "were":
        return "are"
    if lowered == "had":
        return "has"
    if lowered == "implies" and subject_tokens:
        last_subject = subject_tokens[-1].lower()
        if last_subject.endswith("s") and not last_subject.endswith("ss"):
            return "imply"
    return lowered


def _fit_word_budget(*, words: list[str], fallback_tokens: list[str]) -> list[str]:
    normalized = list(words)
    if len(normalized) > 7:
        normalized = normalized[:7]
    if len(normalized) < 3:
        for token in fallback_tokens:
            if len(normalized) >= 3:
                break
            lowered = token.lower()
            if lowered in _CONNECTIVE_TOKENS:
                continue
            normalized.append(token)
    if len(normalized) < 3:
        normalized = (normalized + ["is", "true"])[:3]
    if len(normalized) > 7:
        normalized = normalized[:7]
    return normalized


def _sentence_case(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return stripped[:1].upper() + stripped[1:]
