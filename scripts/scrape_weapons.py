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

# --- wiki 魔术字展开 ---------------------------------------------------------
# strip_templates() 整段删 [[...]] 之外还会把 {{PAGENAME}} 等魔术字删空，
# 正文出现 "The is a basic in that ..." 残句。必须在清洗前展开成真实文本。
_MAGIC_TITLE = re.compile(r"\{\{\s*(?:SUB|BASE|FULL)?PAGENAME(?:E)?\s*\}\}", re.I)
_MAGIC_GAME = re.compile(r"\{\{\s*(?:Gamename|Game|SITENAME|Sitename)\s*\}\}", re.I)
_MAGIC_DROP = re.compile(
    r"\{\{\s*(?:DISPLAYTITLE|DEFAULTSORT|#(?:expr|var|if|ifeq|ifexist|switch|tag|invoke|time|pos|len|replace|sub|explode|titleparts)[^}]*)\}\}",
    re.I,
)


def expand_magic(wt: str | None, title: str) -> str | None:
    """把 {{PAGENAME}} 换成条目名，丢弃解析器函数等元魔术字。"""
    if not wt:
        return wt
    wt = _MAGIC_TITLE.sub(lambda _m: title, wt)
    wt = _MAGIC_GAME.sub("Sons of the Forest", wt)
    wt = _MAGIC_DROP.sub("", wt)
    return wt


# --- wiki.gg 工具模板展开 -----------------------------------------------------
# wiki.gg 的 {{BT|X}} / {{WTL|n}} / {{Caves|n}} / {{Bunkers|n}} 用 #switch 把
# 一个数字参数翻译成可读标签（{{WTL|3}} -> "Attachment"，{{Caves|3}} -> "Shovel
# Cave"）。strip_templates() 的「丢弃纯数字参数」规则会把这些标签一并丢掉，
# 留下 "The is found in the and ." 这类残句。必须在清洗前把语义还原出来。
_WTL = {"1": "Melee", "2": "Ranged", "3": "Attachment", "4": "Explosives"}
_CAVES = {"1": "Rebreather Cave", "2": "Rope Gun Cave", "3": "Shovel Cave",
          "4": "Ancient Armor Cave", "5": "Pickaxe Cave", "6": "Artifact Cave",
          "7": "Hell Cave"}
_BUNKERS = {"1": "Food and Dining Bunker", "2": "Entertainment Bunker",
            "3": "Residential Bunker", "4": "Luxury Bunker", "5": "Maintenance A",
            "6": "Maintenance B", "7": "Maintenance C"}

_UTIL_TPL = re.compile(r"\{\{\s*(BT|WTL|Caves|Bunkers)\s*\|([^{}]*?)\}\}", re.I)


def expand_util_templates(wt: str | None) -> str | None:
    """把 wiki.gg 工具模板还原成它渲染后的可读文字。"""
    if not wt:
        return wt

    def _sub(m):
        name = m.group(1).strip().lower()
        parts = [p.strip() for p in m.group(2).split("|")]
        if name == "bt":                       # {{BT|X}} -> X
            return parts[0] if parts else ""
        if name == "wtl":                      # {{WTL|n}} / {{WTL|n|label}}
            if len(parts) >= 2 and parts[1]:
                return parts[1]
            return _WTL.get(parts[0] if parts else "", "Weapon")
        mp = _CAVES if name == "caves" else _BUNKERS
        if len(parts) >= 3 and parts[2]:       # {{{3|...}}} 显式标签优先
            return parts[2]
        key = parts[0] if parts else ""
        return mp.get(key, ("Cave " if name == "caves" else "Bunker ") + key)

    return _UTIL_TPL.sub(_sub, wt)


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
                return expand_util_templates(expand_magic(d["parse"]["wikitext"]["*"], title))
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
    # iteratively collapse innermost {{...}}: keep positional args as text
    # ({{Item|Skull}} -> Skull) so material/type words survive instead of
    # leaving "crafted using , , and the Utility Knife".
    while "{{" in text:
        def repl(m):
            parts = m.group(1).split("|")
            # 只保留可读的位置参数；纯数字/符号参数是模板编号，保留会变成
            # "a basic 1 melee weapon" 这类数字垃圾。
            args = [p.strip() for p in parts[1:]
                    if p.strip() and not re.fullmatch(r"[\d\s.,%+\-]+", p.strip())]
            return " ".join(args)

        new = re.sub(r"\{\{([^{}]*)\}\}", repl, text)
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
