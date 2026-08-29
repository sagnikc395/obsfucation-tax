from __future__ import annotations

import re


def _normalize(s: str) -> str:
    return s.strip().lower()


def extract_letter_answer(text: str) -> str | None:
    """Extract A/B/C/D from generated text. Returns uppercase letter or None."""
    if not text:
        return None
    # Look for patterns: "Answer: B", "(B)", "B", "option B"
    text = text.strip()
    # direct single letter
    if re.fullmatch(r"[A-Da-d]", text.strip()):
        return text.strip().upper()
    # search for common patterns
    patterns = [
        r"answer\s*[:\-]\s*([A-Da-d])\b",
        r"option\s*([A-Da-d])\b",
        r"\(([A-Da-d])\)",
        r"\b([A-Da-d])\b\s*[\.\)]",
        r"^\s*([A-Da-d])\s*$",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    # fallback: last occurrence of A-D standalone
    matches = re.findall(r"\b([A-Da-d])\b", text)
    if matches:
        return matches[-1].upper()
    return None


def extract_gsm8k_answer(text: str) -> str | None:
    """Extract final numeric answer. GSM8K gold often after ####, generations may have boxed."""
    if not text:
        return None
    # GSM8K gold format may contain "#### 42"
    m = re.search(r"####\s*(-?\d+(?:,\d+)*(?:\.\d+)?)", text)
    if m:
        return m.group(1).replace(",", "").strip()
    # Look for \boxed{42}
    m = re.search(r"\\boxed\{([^}]+)\}", text)
    if m:
        return m.group(1).replace(",", "").strip()
    # Last number in text
    nums = re.findall(r"-?\d+(?:,\d+)*(?:\.\d+)?", text.replace(",", ""))
    # Actually re-find without comma handling duplication; simpler:
    nums = re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))
    if nums:
        return nums[-1].strip()
    return None


def score_mmlu(parsed: str | None, gold: str) -> bool:
    if parsed is None:
        return False
    return _normalize(parsed) == _normalize(gold)


def score_gsm8k(parsed: str | None, gold: str) -> bool:
    if parsed is None:
        return False
    # normalize numeric: remove commas, strip
    p = parsed.replace(",", "").strip()
    g = gold.replace(",", "").strip()
    # handle #### in gold
    if "####" in g:
        g = g.split("####")[-1].strip()
    try:
        # numeric compare with tolerance
        return float(p) == float(g)
    except ValueError:
        return _normalize(p) == _normalize(g)


def score_example(parsed: str | None, gold: str, scoring: str) -> bool:
    if scoring == "exact_match_letter":
        return score_mmlu(parsed, gold)
    elif scoring == "numeric_exact":
        return score_gsm8k(parsed, gold)
    else:
        # default exact
        if parsed is None:
            return False
        return _normalize(parsed) == _normalize(gold)


def parse_answer(text: str, scoring: str) -> str | None:
    if scoring == "exact_match_letter":
        return extract_letter_answer(text)
    elif scoring == "numeric_exact":
        return extract_gsm8k_answer(text)
    else:
        return text.strip() if text else None
