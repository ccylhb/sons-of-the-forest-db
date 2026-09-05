#!/usr/bin/env python3
"""Shared helpers for SotF wiki scrapers."""
import re
import time
from pathlib import Path

import requests

API = "https://sonsoftheforest.wiki.gg/api.php"
PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "data"
HEADERS = {"User-Agent": "TimberDB scraper (site build, contact via github)"}

session = requests.Session()
session.proxies.update(PROXY)
session.headers.update(HEADERS)


def get_wikitext(title: str) -> str | None:
    for attempt in range(3):
        try:
            r = session.get(
                API,
                params={"action": "parse", "page": title, "prop": "wikitext", "format": "json"},
                timeout=30,
            )
            d = r.json()
            return d["parse"]["wikitext"]["*"] if "parse" in d else None
        except Exception as e:
            print(f"  retry {title}: {e}")
            time.sleep(2 * (attempt + 1))
    return None


def category_members(title: str) -> list[dict]:
    for attempt in range(3):
        try:
            r = session.get(
                API,
                params={"action": "query", "list": "categorymembers", "cmtitle": title,
                        "cmlimit": "500", "format": "json"},
                timeout=30,
            )
            return r.json()["query"]["categorymembers"]
        except Exception as e:
            print(f"  retry members {title}: {e}")
            time.sleep(2 * (attempt + 1))
    return []


def strip_templates(text: str) -> str:
    """Remove nested {{...}} templates. Templates WITH args are replaced by
    their positional args joined by space ({{Col|No}} -> No), so infobox data
    like type/consumable survives. Nameless templates ({{gamename}}) vanish."""
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    while "{{" in text:
        def repl(m: "re.Match[str]") -> str:
            parts = m.group(1).split("|")
            args = [p.strip() for p in parts[1:] if p.strip()]
            return " ".join(args)
        new = re.sub(r"\{\{([^{}]*)\}\}", repl, text)
        if new == text:
            break
        text = new
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    return text.replace("'''", "").replace("''", "")


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def section_text(wikitext: str, heading: str, limit: int = 600) -> str:
    m = re.search(rf"==+\s*{re.escape(heading)}\s*==+\n(.*?)(?=\n==|\Z)", wikitext, flags=re.S)
    if not m:
        return ""
    return clean_ws(strip_templates(m.group(1)))[:limit]


def infobox_field(wikitext: str, field: str) -> str:
    # [ \t]* (not \s*) after "=" so the match never crosses a newline into the next field
    m = re.search(rf"^\|\s*{field}[ \t]*=[ \t]*(.*)", wikitext, flags=re.M)
    if not m:
        return ""
    val = m.group(1).split("\n")[0]
    return clean_ws(strip_templates(val))
