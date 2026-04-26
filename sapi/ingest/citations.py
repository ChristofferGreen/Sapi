"""Reference extraction, normalization, local linking, and backfill helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


_DOI_RE = re.compile(r"(?:doi:\s*)?(10\.\d{4,9}/[-._;()/:a-z0-9]+)", re.IGNORECASE)
_ARXIV_RE = re.compile(r"(?:arxiv:\s*)?(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)
_URL_RE = re.compile(r"(https?://[^\s\]>\"')]+)", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
_SPACE_RE = re.compile(r"\s+")
_REFERENCE_XML_NOISE_RE = re.compile(r"(?:<rdf|rdf:|xmlns|xpacket)", re.IGNORECASE)
_BLOCKED_REFERENCE_URL_HOSTS: set[str] = {
    "ns.adobe.com",
    "www.w3.org",
}
_RELATED_LINK_TYPE_BY_HOST_SUFFIX: tuple[tuple[str, str, str], ...] = (
    ("wikipedia.org", "encyclopedia", "trusted"),
    ("doi.org", "canonical_paper", "trusted"),
    ("arxiv.org", "research_index", "trusted"),
    ("paperswithcode.com", "research_index", "contextual"),
    ("github.com", "repository", "contextual"),
    ("gitlab.com", "repository", "contextual"),
    ("reddit.com", "discussion_forum", "contextual"),
    ("stackexchange.com", "discussion_forum", "contextual"),
    ("stackoverflow.com", "discussion_forum", "contextual"),
    ("news.ycombinator.com", "discussion_forum", "contextual"),
    ("lobste.rs", "discussion_forum", "contextual"),
)

_REFERENCE_KEYS: tuple[str, ...] = (
    "title",
    "authors",
    "year",
    "doi",
    "arxiv",
    "url",
    "linked_source_ids",
)


@dataclass(frozen=True)
class ReferenceLinkingResult:
    source_id: str
    reference_count: int
    linked_source_ids: list[str]
    backfilled_source_ids: list[str]
    related_link_count: int


@dataclass(frozen=True)
class _SourceIndexEntry:
    source_id: str
    title_norm: str | None
    year: int | None
    doi: str | None
    arxiv: str | None
    url: str | None


def run_reference_extraction_and_link_backfill(
    *,
    space_root: Path,
    source_id: str,
) -> ReferenceLinkingResult:
    """Extract and normalize references for one source, then backfill links in older records."""
    records_dir = space_root / "sources" / "records"
    if not records_dir.is_dir():
        raise FileNotFoundError(f"Source records directory missing: {records_dir}")

    record_paths = sorted(records_dir.glob("source-*.json"))
    if not record_paths:
        raise FileNotFoundError(f"No source records found in {records_dir}")

    source_records: dict[str, dict[str, Any]] = {}
    source_record_paths: dict[str, Path] = {}
    for path in record_paths:
        payload = json.loads(path.read_text())
        if not isinstance(payload, dict):
            raise ValueError(f"Source record must be a JSON object: {path}")
        record_source_id = payload.get("source_id")
        if not isinstance(record_source_id, str) or not record_source_id.strip():
            raise ValueError(f"Source record missing non-empty source_id: {path}")
        source_records[record_source_id] = payload
        source_record_paths[record_source_id] = path

    if source_id not in source_records:
        raise FileNotFoundError(f"Source record not found for source_id={source_id}")

    source_index = _build_source_index(source_records)

    current_record = source_records[source_id]
    references = _extract_references_from_record(current_record=current_record, space_root=space_root)
    references_with_links = _link_references(
        references=references,
        source_index=source_index,
        current_source_id=source_id,
    )
    current_record["references"] = references_with_links
    current_record["linked_source_ids"] = _collect_linked_source_ids(references_with_links)
    related_links, related_link_enrichment = _build_external_related_links(current_record)
    current_record["external_related_links"] = related_links
    current_record["related_link_enrichment"] = related_link_enrichment
    current_path = source_record_paths[source_id]
    current_path.write_text(json.dumps(current_record, indent=2, sort_keys=True) + "\n")

    backfilled_source_ids: list[str] = []
    for older_source_id in sorted(source_records.keys()):
        if older_source_id == source_id:
            continue
        older_record = source_records[older_source_id]
        raw_existing = older_record.get("references")
        if not isinstance(raw_existing, list) or not raw_existing:
            continue
        normalized_existing = _normalize_existing_references(raw_existing)
        relinked = _link_references(
            references=normalized_existing,
            source_index=source_index,
            current_source_id=older_source_id,
        )
        old_linked = older_record.get("linked_source_ids")
        new_linked = _collect_linked_source_ids(relinked)
        relinked_record = dict(older_record)
        relinked_record["references"] = relinked
        relinked_record["linked_source_ids"] = new_linked
        related_links, related_link_enrichment = _build_external_related_links(relinked_record)
        if (
            relinked != normalized_existing
            or new_linked != old_linked
            or related_links != older_record.get("external_related_links")
            or related_link_enrichment != older_record.get("related_link_enrichment")
        ):
            older_record["references"] = relinked
            older_record["linked_source_ids"] = new_linked
            older_record["external_related_links"] = related_links
            older_record["related_link_enrichment"] = related_link_enrichment
            older_path = source_record_paths[older_source_id]
            older_path.write_text(json.dumps(older_record, indent=2, sort_keys=True) + "\n")
            backfilled_source_ids.append(older_source_id)

    return ReferenceLinkingResult(
        source_id=source_id,
        reference_count=len(references_with_links),
        linked_source_ids=_collect_linked_source_ids(references_with_links),
        backfilled_source_ids=backfilled_source_ids,
        related_link_count=len(related_links),
    )


def extract_normalized_references_from_text(text: str) -> list[dict[str, Any]]:
    """Extract deterministic structured reference rows from raw source text."""
    rows: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if len(line) < 8:
            continue
        doi = _extract_doi(line)
        arxiv = _extract_arxiv(line)
        urls = _extract_urls(line)
        if doi is None and arxiv is None and not urls:
            continue

        year = _extract_year(line)
        row_urls = urls or [None]
        for url in row_urls:
            title = _extract_title(line=line, doi=doi, arxiv=arxiv, url=url, year=year)
            if _is_metadata_reference_noise(
                line=line,
                title=title,
                url=url,
            ):
                continue
            rows.append(
                {
                    "title": title,
                    "authors": [],
                    "year": year,
                    "doi": doi,
                    "arxiv": arxiv,
                    "url": url,
                    "linked_source_ids": [],
                }
            )
    return _dedupe_and_sort_references(rows)


def _extract_references_from_record(*, current_record: dict[str, Any], space_root: Path) -> list[dict[str, Any]]:
    decoded_text = _read_source_text_for_analysis(current_record=current_record, space_root=space_root)
    if not decoded_text.strip():
        return []
    return extract_normalized_references_from_text(decoded_text)


def _read_source_text_for_analysis(*, current_record: dict[str, Any], space_root: Path) -> str:
    artifacts = current_record.get("artifacts")
    if not isinstance(artifacts, dict):
        return ""
    analysis_policy = current_record.get("analysis_policy")
    quality_status = ""
    if isinstance(analysis_policy, dict):
        quality_status = _normalize_optional_string(analysis_policy.get("quality_status")) or ""
    source_markdown_rel = artifacts.get("source_markdown")
    if isinstance(source_markdown_rel, str) and source_markdown_rel.strip() and quality_status != "unusable":
        source_markdown_path = (space_root / source_markdown_rel).resolve()
        if source_markdown_path.is_file():
            markdown_text = source_markdown_path.read_text()
            if markdown_text.strip():
                return markdown_text
    source_file_rel = artifacts.get("source_file")
    if isinstance(source_file_rel, str) and source_file_rel.strip():
        source_file_path = (space_root / source_file_rel).resolve()
        if source_file_path.is_file():
            raw_bytes = source_file_path.read_bytes()
            decoded_text = raw_bytes.decode("utf-8", errors="ignore")
            if decoded_text.strip():
                return decoded_text
    return ""


def _build_external_related_links(record: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_candidates: list[dict[str, Any]] = []
    warnings: list[str] = []
    sources_used: set[str] = set()

    canonical_identifier = _normalize_optional_string(record.get("canonical_identifier"))
    doi = _doi_from_identifier(canonical_identifier)
    if doi is not None:
        sources_used.add("canonical_identifier")
        raw_candidates.append(
            _make_related_link_candidate(
                title="DOI landing page",
                url=f"https://doi.org/{doi}",
                rationale="Canonical identifier for the ingested source.",
                provenance_origin="canonical_identifier",
                source_field="canonical_identifier",
                confidence="high",
            )
        )
    arxiv = _arxiv_from_identifier(canonical_identifier)
    if arxiv is not None:
        sources_used.add("canonical_identifier")
        raw_candidates.append(
            _make_related_link_candidate(
                title="arXiv abstract",
                url=f"https://arxiv.org/abs/{arxiv}",
                rationale="Canonical arXiv identifier for the ingested source.",
                provenance_origin="canonical_identifier",
                source_field="canonical_identifier",
                confidence="high",
            )
        )

    source_locator = _normalize_url(record.get("source_locator"))
    if source_locator is not None:
        sources_used.add("source_locator")
        raw_candidates.append(
            _make_related_link_candidate(
                title="Original source link",
                url=source_locator,
                rationale="Original network location captured during ingest.",
                provenance_origin="source_locator",
                source_field="source_locator",
                confidence="high",
                allow_unknown_domain=True,
            )
        )

    references = record.get("references")
    if isinstance(references, list):
        for index, reference in enumerate(references):
            if not isinstance(reference, dict):
                continue
            reference_url = _normalize_url(reference.get("url"))
            if reference_url is not None:
                sources_used.add("references")
                raw_candidates.append(
                    _make_related_link_candidate(
                        title=_normalize_optional_string(reference.get("title")) or "Referenced external link",
                        url=reference_url,
                        rationale="Captured from normalized source references.",
                        provenance_origin="reference_url",
                        source_field=f"references[{index}].url",
                        confidence="medium",
                    )
                )
            reference_doi = _normalize_doi(reference.get("doi"))
            if reference_doi is not None:
                sources_used.add("references")
                raw_candidates.append(
                    _make_related_link_candidate(
                        title=_normalize_optional_string(reference.get("title")) or "Referenced DOI",
                        url=f"https://doi.org/{reference_doi}",
                        rationale="Derived from a DOI found in the source references.",
                        provenance_origin="reference_doi",
                        source_field=f"references[{index}].doi",
                        confidence="medium",
                    )
                )
            reference_arxiv = _normalize_arxiv(reference.get("arxiv"))
            if reference_arxiv is not None:
                sources_used.add("references")
                raw_candidates.append(
                    _make_related_link_candidate(
                        title=_normalize_optional_string(reference.get("title")) or "Referenced arXiv entry",
                        url=f"https://arxiv.org/abs/{reference_arxiv}",
                        rationale="Derived from an arXiv identifier found in the source references.",
                        provenance_origin="reference_arxiv",
                        source_field=f"references[{index}].arxiv",
                        confidence="medium",
                    )
                )

    curated_links = _dedupe_and_sort_related_links(raw_candidates=raw_candidates, warnings=warnings)
    if curated_links:
        return curated_links, {
            "status": "enriched",
            "warnings": warnings,
            "sources": sorted(sources_used),
            "skip_reason": None,
        }
    return [], {
        "status": "skipped",
        "warnings": warnings,
        "sources": sorted(sources_used),
        "skip_reason": "no_curated_links_found",
    }


def _make_related_link_candidate(
    *,
    title: str,
    url: str,
    rationale: str,
    provenance_origin: str,
    source_field: str,
    confidence: str,
    allow_unknown_domain: bool = False,
) -> dict[str, Any]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    link_type, quality_status = _classify_related_link_host(domain, allow_unknown_domain=allow_unknown_domain)
    return {
        "title": title,
        "url": url,
        "domain": domain,
        "link_type": link_type,
        "rationale": rationale,
        "provenance": {
            "origin": provenance_origin,
            "source_field": source_field,
        },
        "confidence": confidence,
        "quality_status": quality_status,
    }
    

def _classify_related_link_host(domain: str, *, allow_unknown_domain: bool) -> tuple[str | None, str | None]:
    normalized_domain = domain.strip().lower()
    for suffix, link_type, quality_status in _RELATED_LINK_TYPE_BY_HOST_SUFFIX:
        if normalized_domain == suffix or normalized_domain.endswith(f".{suffix}"):
            return link_type, quality_status
    if allow_unknown_domain and normalized_domain:
        return "primary_source", "contextual"
    return None, None


def _dedupe_and_sort_related_links(*, raw_candidates: list[dict[str, Any]], warnings: list[str]) -> list[dict[str, Any]]:
    by_url: dict[str, dict[str, Any]] = {}
    skipped_candidates = 0
    for candidate in raw_candidates:
        url = _normalize_url(candidate.get("url"))
        title = _normalize_optional_string(candidate.get("title"))
        domain = _normalize_optional_string(candidate.get("domain"))
        link_type = _normalize_optional_string(candidate.get("link_type"))
        quality_status = _normalize_optional_string(candidate.get("quality_status"))
        if url is None or title is None or domain is None or link_type is None or quality_status is None:
            skipped_candidates += 1
            continue
        shaped = {
            "title": title,
            "url": url,
            "domain": domain,
            "link_type": link_type,
            "rationale": _normalize_optional_string(candidate.get("rationale")),
            "provenance": candidate.get("provenance") if isinstance(candidate.get("provenance"), dict) else {},
            "confidence": _normalize_optional_string(candidate.get("confidence")) or "medium",
            "quality_status": quality_status,
        }
        if url in by_url:
            current = by_url[url]
            current_quality_rank = _related_link_quality_rank(str(current.get("quality_status") or ""))
            new_quality_rank = _related_link_quality_rank(quality_status)
            if new_quality_rank < current_quality_rank:
                by_url[url] = shaped
                continue
            if (
                new_quality_rank == current_quality_rank
                and str(shaped.get("title") or "") < str(current.get("title") or "")
            ):
                by_url[url] = shaped
            continue
        by_url[url] = shaped
    if skipped_candidates:
        warnings.append(f"Skipped {skipped_candidates} unsupported external-link candidate(s).")
    return sorted(by_url.values(), key=_related_link_sort_key)


def _related_link_sort_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        _related_link_quality_rank(str(row.get("quality_status") or "")),
        _related_link_type_rank(str(row.get("link_type") or "")),
        str(row.get("title") or "").lower(),
        str(row.get("url") or ""),
    )


def _related_link_quality_rank(value: str) -> int:
    if value == "trusted":
        return 0
    if value == "contextual":
        return 1
    return 2


def _related_link_type_rank(value: str) -> int:
    ranks = {
        "canonical_paper": 0,
        "primary_source": 1,
        "research_index": 2,
        "encyclopedia": 3,
        "repository": 4,
        "discussion_forum": 5,
    }
    return ranks.get(value, 99)


def _normalize_existing_references(raw_references: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw in raw_references:
        if not isinstance(raw, dict):
            continue
        normalized.append(
            {
                "title": _normalize_optional_string(raw.get("title")),
                "authors": _normalize_authors(raw.get("authors")),
                "year": _normalize_year(raw.get("year")),
                "doi": _normalize_doi(raw.get("doi")),
                "arxiv": _normalize_arxiv(raw.get("arxiv")),
                "url": _normalize_url(raw.get("url")),
                "linked_source_ids": [],
            }
        )
    return _dedupe_and_sort_references(normalized)


def _link_references(
    *,
    references: list[dict[str, Any]],
    source_index: list[_SourceIndexEntry],
    current_source_id: str,
) -> list[dict[str, Any]]:
    linked_rows: list[dict[str, Any]] = []
    for row in references:
        matches: set[str] = set()
        for entry in source_index:
            if entry.source_id == current_source_id:
                continue
            if _reference_matches_source(reference=row, source=entry):
                matches.add(entry.source_id)
        linked_row = dict(row)
        linked_row["linked_source_ids"] = sorted(matches)
        linked_rows.append(_shape_reference_row(linked_row))
    return _dedupe_and_sort_references(linked_rows)


def _reference_matches_source(*, reference: dict[str, Any], source: _SourceIndexEntry) -> bool:
    reference_doi = _normalize_doi(reference.get("doi"))
    if reference_doi is not None and source.doi is not None and reference_doi == source.doi:
        return True

    reference_arxiv = _normalize_arxiv(reference.get("arxiv"))
    if reference_arxiv is not None and source.arxiv is not None and reference_arxiv == source.arxiv:
        return True

    reference_url = _normalize_url(reference.get("url"))
    if reference_url is not None and source.url is not None and reference_url == source.url:
        return True

    reference_title_norm = _normalize_title(reference.get("title"))
    reference_year = _normalize_year(reference.get("year"))
    if reference_title_norm is None or source.title_norm is None:
        return False
    if reference_title_norm != source.title_norm:
        return False
    if reference_year is None or source.year is None:
        return True
    return reference_year == source.year


def _build_source_index(source_records: dict[str, dict[str, Any]]) -> list[_SourceIndexEntry]:
    entries: list[_SourceIndexEntry] = []
    for source_id in sorted(source_records.keys()):
        record = source_records[source_id]
        title_norm = _normalize_title(record.get("title"))
        year = _extract_year_from_record(record)

        canonical_identifier = _normalize_optional_string(record.get("canonical_identifier"))
        doi = _doi_from_identifier(canonical_identifier)
        arxiv = _arxiv_from_identifier(canonical_identifier)
        url = _url_from_identifier(canonical_identifier)

        if url is None:
            url = _normalize_url(record.get("source_locator"))
        entries.append(
            _SourceIndexEntry(
                source_id=source_id,
                title_norm=title_norm,
                year=year,
                doi=doi,
                arxiv=arxiv,
                url=url,
            )
        )
    return entries


def _extract_year_from_record(record: dict[str, Any]) -> int | None:
    raw_date = _normalize_optional_string(record.get("date"))
    if raw_date is None:
        return None
    match = _YEAR_RE.search(raw_date)
    if match is None:
        return None
    return int(match.group(1))


def _doi_from_identifier(identifier: str | None) -> str | None:
    if identifier is None:
        return None
    lowered = identifier.lower()
    if lowered.startswith("doi:"):
        return _normalize_doi(lowered[4:])
    if lowered.startswith("https://doi.org/") or lowered.startswith("http://doi.org/"):
        parts = identifier.split("doi.org/", 1)
        return _normalize_doi(parts[1] if len(parts) == 2 else identifier)
    return _normalize_doi(identifier)


def _arxiv_from_identifier(identifier: str | None) -> str | None:
    if identifier is None:
        return None
    lowered = identifier.lower()
    if lowered.startswith("arxiv:"):
        return _normalize_arxiv(identifier[6:])
    if "arxiv.org/abs/" in lowered:
        parts = lowered.split("arxiv.org/abs/", 1)
        if len(parts) == 2:
            return _normalize_arxiv(parts[1])
    return _normalize_arxiv(identifier)


def _url_from_identifier(identifier: str | None) -> str | None:
    if identifier is None:
        return None
    return _normalize_url(identifier)


def _extract_doi(line: str) -> str | None:
    match = _DOI_RE.search(line)
    if match is None:
        return None
    return _normalize_doi(match.group(1))


def _extract_arxiv(line: str) -> str | None:
    match = _ARXIV_RE.search(line)
    if match is None:
        return None
    return _normalize_arxiv(match.group(1))


def _extract_url(line: str) -> str | None:
    urls = _extract_urls(line)
    if not urls:
        return None
    return urls[0]


def _extract_urls(line: str) -> list[str]:
    urls: list[str] = []
    for match in _URL_RE.finditer(line):
        url = _normalize_url(match.group(1))
        if url is not None:
            urls.append(url)
    return urls


def _extract_year(line: str) -> int | None:
    match = _YEAR_RE.search(line)
    if match is None:
        return None
    return int(match.group(1))


def _extract_title(
    *,
    line: str,
    doi: str | None,
    arxiv: str | None,
    url: str | None,
    year: int | None,
) -> str | None:
    text = line
    if doi is not None:
        text = re.sub(re.escape(doi), " ", text, flags=re.IGNORECASE)
        text = re.sub(r"doi:\s*", " ", text, flags=re.IGNORECASE)
    if arxiv is not None:
        text = re.sub(re.escape(arxiv), " ", text, flags=re.IGNORECASE)
        text = re.sub(r"arxiv:\s*", " ", text, flags=re.IGNORECASE)
    if url is not None:
        text = re.sub(re.escape(url), " ", text, flags=re.IGNORECASE)
    if year is not None:
        text = text.replace(str(year), " ")
    text = re.sub(r"[\[\](),;<>=\"']", " ", text)
    text = _SPACE_RE.sub(" ", text).strip(" .:-")
    if not text:
        return None
    return text[:200]


def _is_metadata_reference_noise(
    *,
    line: str,
    title: str | None,
    url: str | None,
) -> bool:
    lowered_line = line.lower()
    if _REFERENCE_XML_NOISE_RE.search(lowered_line):
        return True

    if isinstance(title, str) and _REFERENCE_XML_NOISE_RE.search(title.lower()):
        return True

    normalized_url = _normalize_url(url)
    if normalized_url is None:
        return False
    parsed = urlparse(normalized_url)
    host = parsed.netloc.lower()
    return host in _BLOCKED_REFERENCE_URL_HOSTS


def _shape_reference_row(row: dict[str, Any]) -> dict[str, Any]:
    shaped: dict[str, Any] = {}
    for key in _REFERENCE_KEYS:
        if key == "title":
            shaped[key] = _normalize_optional_string(row.get(key))
        elif key == "authors":
            shaped[key] = _normalize_authors(row.get(key))
        elif key == "year":
            shaped[key] = _normalize_year(row.get(key))
        elif key == "doi":
            shaped[key] = _normalize_doi(row.get(key))
        elif key == "arxiv":
            shaped[key] = _normalize_arxiv(row.get(key))
        elif key == "url":
            shaped[key] = _normalize_url(row.get(key))
        elif key == "linked_source_ids":
            shaped[key] = _normalize_linked_source_ids(row.get(key))
    return shaped


def _dedupe_and_sort_references(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, dict[str, Any]] = {}
    for raw_row in rows:
        row = _shape_reference_row(raw_row)
        dedupe_key = _reference_dedupe_key(row)
        if dedupe_key in by_key:
            by_key[dedupe_key] = _merge_reference_rows(by_key[dedupe_key], row)
        else:
            by_key[dedupe_key] = row
    sorted_rows = sorted(by_key.values(), key=_reference_sort_key)
    return sorted_rows


def _merge_reference_rows(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    for key in ("title", "year", "doi", "arxiv", "url"):
        if merged.get(key) is None and right.get(key) is not None:
            merged[key] = right[key]
    if not merged.get("authors") and right.get("authors"):
        merged["authors"] = list(right["authors"])
    merged_links = set(_normalize_linked_source_ids(merged.get("linked_source_ids")))
    merged_links.update(_normalize_linked_source_ids(right.get("linked_source_ids")))
    merged["linked_source_ids"] = sorted(merged_links)
    return _shape_reference_row(merged)


def _reference_dedupe_key(row: dict[str, Any]) -> str:
    doi = row.get("doi")
    if isinstance(doi, str) and doi:
        return f"doi:{doi}"
    arxiv = row.get("arxiv")
    if isinstance(arxiv, str) and arxiv:
        return f"arxiv:{arxiv}"
    url = row.get("url")
    if isinstance(url, str) and url:
        return f"url:{url}"
    title = row.get("title")
    year = row.get("year")
    return f"title:{_normalize_title(title) or ''}|year:{year or ''}"


def _reference_sort_key(row: dict[str, Any]) -> tuple[str, str, str, str, int]:
    doi = row.get("doi") or ""
    arxiv = row.get("arxiv") or ""
    url = row.get("url") or ""
    title = row.get("title") or ""
    year = row.get("year") if isinstance(row.get("year"), int) else -1
    return (str(doi), str(arxiv), str(url), str(title), int(year))


def _collect_linked_source_ids(references: list[dict[str, Any]]) -> list[str]:
    linked: set[str] = set()
    for reference in references:
        linked.update(_normalize_linked_source_ids(reference.get("linked_source_ids")))
    return sorted(linked)


def _normalize_title(raw: Any) -> str | None:
    text = _normalize_optional_string(raw)
    if text is None:
        return None
    return _SPACE_RE.sub(" ", text.lower()).strip()


def _normalize_optional_string(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        return None
    stripped = raw.strip()
    return stripped or None


def _normalize_authors(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        authors: list[str] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                authors.append(item.strip())
        return sorted(set(authors))
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def _normalize_year(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        if 1800 <= raw <= 2100:
            return raw
        return None
    if isinstance(raw, str):
        match = _YEAR_RE.search(raw)
        if match is None:
            return None
        return int(match.group(1))
    return None


def _normalize_doi(raw: Any) -> str | None:
    value = _normalize_optional_string(raw)
    if value is None:
        return None
    lowered = value.lower()
    if lowered.startswith("doi:"):
        lowered = lowered[4:].strip()
    lowered = lowered.rstrip(".,);]")
    match = _DOI_RE.search(lowered)
    if match is None:
        return None
    return match.group(1).lower()


def _normalize_arxiv(raw: Any) -> str | None:
    value = _normalize_optional_string(raw)
    if value is None:
        return None
    lowered = value.lower().strip()
    if lowered.startswith("arxiv:"):
        lowered = lowered[6:].strip()
    if "arxiv.org/abs/" in lowered:
        lowered = lowered.split("arxiv.org/abs/", 1)[1].strip()
    lowered = lowered.rstrip(".,);]")
    match = _ARXIV_RE.search(lowered)
    if match is None:
        return None
    return match.group(1).lower()


def _normalize_url(raw: Any) -> str | None:
    value = _normalize_optional_string(raw)
    if value is None:
        return None
    lowered = value.rstrip(".,);]").strip()
    parsed = urlparse(lowered)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    path = path.rstrip("/")
    normalized = f"{parsed.scheme.lower()}://{netloc}{path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    return normalized


def _normalize_linked_source_ids(raw: Any) -> list[str]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    normalized: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            normalized.append(item.strip())
    return sorted(set(normalized))
