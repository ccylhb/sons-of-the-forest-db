#!/usr/bin/env python3
"""Scrape Sons of the Forest weapons from sonsoftheforest.wiki.gg.

Strategy (verified 2026-09-05):
- The [[Weapons]] page renders {{WeaponTable|All}} via Lua -> one big HTML table
  with ALL weapons and their combat stats (type/distance/speed/damage x3/amount/id/solafite).
- Each weapon page has a {{Weapon ...}} infobox with obtained/location/block/ammo/etc.
  and prose sections (Overview/Usage) that we clean into a summary.
Output: src/data/weapons.json
"""
import json
import re
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

API = "https://sonsoftheforest.wiki.gg/api.php"
PROXY = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
OUT = "../src/data/weapons.json"
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
            if "parse" in d:
                return d["parse"]["wikitext"]["*"]
            return None
        except Exception as e:
            print(f"  retry {title}: {e}")
            time.sleep(2 * (attempt + 1))
    return None


def strip_templates(text: str) -> str:
    """Remove nested {{...}} and [[...]] wiki markup, keep readable text."""
    # remove ref/comment blocks
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    # iteratively remove innermost {{...}}
    while "{{" in text:
        new = re.sub(r"\{\{[^{}]*\}\}", "", text)
        if new == text:
            break
        text = new
    # [[link|label]] -> label ; [[link]] -> link
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    # bold/italics
    text = text.replace("'''", "").replace("''", "")
    return text


def clean_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def section_text(wikitext: str, heading: str) -> str:
    """Extract prose after == heading == until next == heading."""
    m = re.search(rf"==+\s*{re.escape(heading)}\s*==+\n(.*?)(?=\n==|\Z)", wikitext, flags=re.S)
    if not m:
        return ""
    return clean_ws(strip_templates(m.group(1)))[:600]


def infobox_field(wikitext: str, field: str) -> str:
    m = re.search(rf"\|\s*{field}\s*=\s*(.*)", wikitext)
    if not m:
        return ""
    val = m.group(1).split("\n")[0]
    val = strip_templates(val)
    return clean_ws(val)


def parse_weapon_table() -> list[dict]:
    """Fetch Weapons page rendered HTML and parse the weapon-table rows."""
    r = session.get(API, params={"action": "parse", "page": "Weapons", "prop": "text", "format": "json"}, timeout=60)
    html = r.json()["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr:has(td.weapon-table__item)")
    weapons = []
    seen = set()
    for tr in rows:
        def cell(cls: str) -> str:
            td = tr.find("td", class_=f"weapon-table__{cls}")
            return td.get_text(strip=True) if td else ""
        link = tr.select_one("td.weapon-table__item a[href^='/wiki/']")
        if not link:
            continue
        name = link.get_text(strip=True)
        slug = urllib.parse.unquote(link["href"].removeprefix("/wiki/"))
        if slug in seen:
            continue
        seen.add(slug)
        weapons.append({
            "name": name,
            "slug": slug,
            "type": cell("type"),
            "distance": cell("distance"),
            "speed": cell("speed"),
            "damageStandard": cell("standard"),
            "damageCharged": cell("charge"),
            "damageDownward": cell("downward"),
            "amount": cell("amount"),
            "gameId": cell("id"),
            "solafite": cell("solafite") != "",
        })
    return weapons


def main() -> None:
    weapons = parse_weapon_table()
    print(f"parsed {len(weapons)} unique weapons from table")
    for i, w in enumerate(weapons):
        wt = get_wikitext(w["slug"])
        if not wt:
            print(f"[{i+1}/{len(weapons)}] NO WIKITEXT: {w['slug']}")
            time.sleep(0.3)
            continue
        w["obtained"] = infobox_field(wt, "obtained")
        w["location"] = infobox_field(wt, "location")
        w["block"] = infobox_field(wt, "block")
        w["ammo"] = infobox_field(wt, "ammo")
        w["capacity"] = infobox_field(wt, "capacity")
        w["added"] = infobox_field(wt, "added")
        w["alias"] = infobox_field(wt, "alias")
        w["summary"] = section_text(wt, "Overview") or section_text(wt, "Usage")
        print(f"[{i+1}/{len(weapons)}] {w['name']} ok (summary {len(w['summary'])} chars)")
        time.sleep(0.35)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(weapons, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(weapons)} weapons")


if __name__ == "__main__":
    main()
