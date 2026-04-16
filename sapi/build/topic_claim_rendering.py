"""Topic claim-annotation parsing and sentence-level evidence rendering."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
import re
from typing import Any


def extract_claim_annotations(body: str) -> tuple[str, list[list[str]]]:
    annotation_pattern = re.compile(r"\[\[claims:([^\]]+)\]\]")
    annotation_groups = [parse_claim_ids(match.group(1)) for match in annotation_pattern.finditer(body)]
    clean_body = re.sub(r"\s{2,}", " ", annotation_pattern.sub("", body)).strip()
    return clean_body, [group for group in annotation_groups if group]


def sentence_claim_bindings(body: str) -> list[tuple[str, list[str]]]:
    annotation_pattern = re.compile(r"\[\[claims:([^\]]+)\]\]")
    matches = list(annotation_pattern.finditer(body))
    if not matches:
        return [(sentence, []) for sentence in split_sentences(body)]

    bindings: list[tuple[str, list[str]]] = []
    cursor = 0
    for match in matches:
        chunk = body[cursor : match.start()]
        claim_ids = parse_claim_ids(match.group(1))
        chunk_sentences = split_sentences(chunk)
        if chunk_sentences:
            for sentence in chunk_sentences[:-1]:
                bindings.append((sentence, []))
            bindings.append((chunk_sentences[-1], claim_ids))
        cursor = match.end()

    tail_sentences = split_sentences(body[cursor:])
    bindings.extend((sentence, []) for sentence in tail_sentences)
    if bindings:
        return bindings

    plain_text = re.sub(r"\s{2,}", " ", annotation_pattern.sub("", body)).strip()
    return [(plain_text, [])] if plain_text else []


def parse_claim_ids(raw_claim_ids: str) -> list[str]:
    return [token.strip() for token in raw_claim_ids.split(",") if token.strip()]


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    sentence_pattern = re.compile(r"[^.!?]+(?:[.!?]+[\"')\]]*)?(?:\s+|$)")
    sentences = [match.group(0).strip() for match in sentence_pattern.finditer(normalized) if match.group(0).strip()]
    return sentences if sentences else [normalized]


def render_sentence_claim_body(
    *,
    sentence_bindings: list[tuple[str, list[str]]],
    section_index: int,
    site_presentation_mode: str,
    claim_option_title_by_id: dict[str, str],
) -> str:
    rendered_sentences: list[str] = []
    for sentence_index, (sentence, claim_ids) in enumerate(sentence_bindings, start=1):
        rendered = render_sentence_claim_binding(
            sentence=sentence,
            claim_ids=claim_ids,
            section_index=section_index,
            sentence_index=sentence_index,
            site_presentation_mode=site_presentation_mode,
            claim_option_title_by_id=claim_option_title_by_id,
        )
        if rendered:
            rendered_sentences.append(rendered)
    return " ".join(rendered_sentences)


def render_sentence_claim_binding(
    *,
    sentence: str,
    claim_ids: list[str],
    section_index: int,
    sentence_index: int,
    site_presentation_mode: str,
    claim_option_title_by_id: dict[str, str],
) -> str:
    if not sentence:
        return ""
    sentence_html = escape(sentence)
    if not claim_ids:
        return sentence_html
    if len(claim_ids) == 1:
        claim_id = claim_ids[0]
        href = f"../claims/{claim_id}.html"
        debug_attrs = (
            f" data-claim-id=\"{escape(claim_id)}\" data-claim-href=\"{escape(href)}\""
            if site_presentation_mode == "debug"
            else ""
        )
        return (
            f"<a class=\"sentence-claim-link\" href=\"{escape(href)}\"{debug_attrs}>"
            + sentence_html
            + "</a>"
        )

    details_id = f"sentence-claim-picker-s{section_index}-t{sentence_index}"
    option_rows: list[str] = []
    for claim_id in claim_ids:
        href = f"../claims/{claim_id}.html"
        label = (
            escape(claim_id)
            if site_presentation_mode == "debug"
            else escape(claim_option_title(claim_id=claim_id, claim_option_title_by_id=claim_option_title_by_id))
        )
        debug_attrs = (
            f" data-claim-id=\"{escape(claim_id)}\" data-claim-href=\"{escape(href)}\""
            if site_presentation_mode == "debug"
            else ""
        )
        option_rows.append(
            f"<a class=\"sentence-claim-option\" href=\"{escape(href)}\"{debug_attrs}>{label}</a>"
        )
    return (
        f"<span id=\"{details_id}\" class=\"sentence-claim-picker\">"
        f"<a href=\"#\" class=\"sentence-claim-summary\" role=\"button\" aria-expanded=\"false\" "
        f"aria-controls=\"{details_id}-card\">{sentence_html}</a>"
        f"<span id=\"{details_id}-card\" class=\"sentence-claim-card\">"
        "<span class=\"sentence-claim-card-title\">Select evidence claim</span>"
        "<span class=\"sentence-claim-options\">"
        + "".join(option_rows)
        + "</span></span></span>"
    )


def render_sentence_claim_picker_script() -> str:
    return (
        "<script>\n"
        "(function(){\n"
        "  var pickers=Array.prototype.slice.call(document.querySelectorAll('.sentence-claim-picker'));\n"
        "  if(!pickers.length){return;}\n"
        "  function cardFor(picker){\n"
        "    if(!picker){return null;}\n"
        "    return picker.querySelector('.sentence-claim-card');\n"
        "  }\n"
        "  function clearPosition(picker){\n"
        "    if(!picker){return;}\n"
        "    picker.removeAttribute('data-align');\n"
        "    var card=cardFor(picker);\n"
        "    if(card){card.style.transform='';}\n"
        "  }\n"
        "  function positionCard(picker){\n"
        "    if(!picker||!picker.hasAttribute('data-open')){return;}\n"
        "    var card=cardFor(picker);\n"
        "    if(!card){return;}\n"
        "    clearPosition(picker);\n"
        "    var viewportWidth=window.innerWidth||document.documentElement.clientWidth||0;\n"
        "    var gutter=12;\n"
        "    var availableWidth=Math.max(260,viewportWidth-(gutter*2));\n"
        "    var targetWidth=Math.min(860,availableWidth);\n"
        "    card.style.maxWidth=targetWidth+'px';\n"
        "    var rect=card.getBoundingClientRect();\n"
        "    if(rect.right>viewportWidth-gutter){\n"
        "      picker.setAttribute('data-align','right');\n"
        "      rect=card.getBoundingClientRect();\n"
        "    }\n"
        "    var shiftX=0;\n"
        "    if(rect.right>viewportWidth-gutter){shiftX=viewportWidth-gutter-rect.right;}\n"
        "    if(rect.left<gutter){shiftX=shiftX+(gutter-rect.left);}\n"
        "    if(shiftX!==0){card.style.transform='translateX('+shiftX+'px)';}\n"
        "  }\n"
        "  function setOpen(picker,open){\n"
        "    if(!picker){return;}\n"
        "    if(open){\n"
        "      picker.setAttribute('data-open','true');\n"
        "      positionCard(picker);\n"
        "    }\n"
        "    else{\n"
        "      picker.removeAttribute('data-open');\n"
        "      clearPosition(picker);\n"
        "    }\n"
        "    var trigger=picker.querySelector('.sentence-claim-summary');\n"
        "    if(trigger){trigger.setAttribute('aria-expanded',open?'true':'false');}\n"
        "  }\n"
        "  function closeAll(exceptPicker){\n"
        "    pickers.forEach(function(picker){\n"
        "      if(exceptPicker&&picker===exceptPicker){return;}\n"
        "      setOpen(picker,false);\n"
        "    });\n"
        "  }\n"
        "  function eventWithinPicker(event){\n"
        "    var target=event&&event.target;\n"
        "    if(!target){return false;}\n"
        "    if(target.closest){return !!target.closest('.sentence-claim-picker');}\n"
        "    if(target.parentElement&&target.parentElement.closest){\n"
        "      return !!target.parentElement.closest('.sentence-claim-picker');\n"
        "    }\n"
        "    return false;\n"
        "  }\n"
        "  pickers.forEach(function(picker){\n"
        "    var trigger=picker.querySelector('.sentence-claim-summary');\n"
        "    if(!trigger){return;}\n"
        "    trigger.addEventListener('click',function(event){\n"
        "      event.preventDefault();\n"
        "      event.stopPropagation();\n"
        "      var alreadyOpen=picker.hasAttribute('data-open');\n"
        "      closeAll(picker);\n"
        "      setOpen(picker,!alreadyOpen);\n"
        "    });\n"
        "    trigger.addEventListener('keydown',function(event){\n"
        "      if(event.key!=='Enter'&&event.key!==' '){return;}\n"
        "      event.preventDefault();\n"
        "      event.stopPropagation();\n"
        "      var alreadyOpen=picker.hasAttribute('data-open');\n"
        "      closeAll(picker);\n"
        "      setOpen(picker,!alreadyOpen);\n"
        "    });\n"
        "  });\n"
        "  window.addEventListener('resize',function(){\n"
        "    pickers.forEach(function(picker){\n"
        "      if(picker.hasAttribute('data-open')){positionCard(picker);}\n"
        "    });\n"
        "  });\n"
        "  document.addEventListener('click',function(event){\n"
        "    if(eventWithinPicker(event)){return;}\n"
        "    closeAll(null);\n"
        "  });\n"
        "  document.addEventListener('keydown',function(event){\n"
        "    if(event.key==='Escape'){closeAll(null);}\n"
        "  });\n"
        "})();\n"
        "</script>\n"
    )


def load_claim_option_titles(*, space_root: Path) -> dict[str, str]:
    claim_records = _load_claim_records(space_root=space_root)
    titles: dict[str, str] = {}
    for claim_id, claim_record in claim_records.items():
        raw_short_title = str(claim_record.get("short_title") or "")
        title = short_claim_option_label(
            raw_short_title,
            fallback_text=_claim_text(claim_id=claim_id, claim_record=claim_record),
        )
        if title and title != claim_id:
            titles[claim_id] = title
    return titles


def claim_option_title(*, claim_id: str, claim_option_title_by_id: dict[str, str]) -> str:
    title = claim_option_title_by_id.get(claim_id)
    if title:
        return title
    return claim_id


def short_claim_option_label(text: str, *, fallback_text: str | None = None) -> str:
    raw_value = " ".join(text.split()).strip(" .,:;")
    if raw_value:
        return raw_value
    if fallback_text:
        fallback_value = " ".join(fallback_text.split()).strip(" .,:;")
        if fallback_value:
            return fallback_value
    return ""


def truncate_text_for_ui(text: str, *, max_length: int) -> str:
    value = text.strip()
    if len(value) <= max_length:
        return value
    if max_length <= 3:
        return value[:max_length]
    truncated = value[: max_length - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated + "..."


def _load_claim_records(*, space_root: Path) -> dict[str, dict[str, Any]]:
    claims_dir = space_root / "claims"
    if not claims_dir.is_dir():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for claim_path in sorted(claims_dir.glob("claim-*.json")):
        try:
            payload = json.loads(claim_path.read_text())
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        claim_id = str(payload.get("claim_id") or "").strip()
        if not claim_id:
            continue
        records[claim_id] = payload
    return records


def _claim_text(*, claim_id: str, claim_record: dict[str, Any]) -> str:
    text = str(claim_record.get("text") or "").strip()
    return text if text else claim_id
