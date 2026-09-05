#!/usr/bin/env python3
"""Scrape Sons of the Forest enemies (v2, tolerant).

Pages use one of: {{Enemy ...}} multi-line infobox, {{Mutant Template|...}}
inline infobox, or no infobox at all (group hubs like Cannibals/Mutants).
For hub pages we take the intro paragraph as summary.
Output: src/data/enemies.json
"""
import json
import re
import time

from shared import (
    OUT_DIR, get_wikitext, infobox_field, category_members, section_text, strip_templates, clean_ws,
)

OUT = OUT_DIR / "enemies.json"
LANG_SUFFIX = re.compile(r"/(pl|es|de|fr|ru|zh)$")


def mutant_field(wikitext: str, *names: str) -> str:
    """Field from {{Mutant Template|category=X|location(s)=Y|...}} (single line)."""
    for name in names:
        m = re.search(rf"\|\s*{re.escape(name)}\s*=([^|}}]*)", wikitext)
        if m:
            val = clean_ws(strip_templates(m.group(1)))
            if val:
                return val
    return ""


def intro_text(wikitext: str, limit: int = 600) -> str:
    """First prose paragraph before any == heading (after infobox/templates)."""
    body = re.split(r"\n==+ ", wikitext, maxsplit=1)[0]
    # drop templates and empty lines
    body = strip_templates(body)
    paras = [clean_ws(p) for p in body.split("\n") if len(clean_ws(p)) > 60]
    return (paras[0] if paras else "")[:limit]


def main() -> None:
    members = category_members("Category:Enemies")
    titles = [
        m["title"]
        for m in members
        if m["ns"] == 0 and not LANG_SUFFIX.search(m["title"])
    ]
    # drop the hub category page itself
    titles = [t for t in titles if t != "Enemies"]
    print(f"{len(titles)} enemy pages after lang filter")

    enemies = []
    for i, title in enumerate(titles):
        wt = get_wikitext(title)
        time.sleep(0.3)
        if not wt:
            print(f"[{i+1}/{len(titles)}] SKIP(no wt) {title}")
            continue
        if "{{Enemy" in wt:
            e = {
                "alias": infobox_field(wt, "alias"),
                "group": infobox_field(wt, "type"),
                "klass": infobox_field(wt, "class"),
                "health": infobox_field(wt, "health"),
                "speed": infobox_field(wt, "speed"),
                "weakness": infobox_field(wt, "weakness"),
                "drops": infobox_field(wt, "drops"),
                "spawn": infobox_field(wt, "spawn"),
                "weapon": infobox_field(wt, "weapon"),
            }
        elif "Mutant Template" in wt:
            e = {
                "alias": mutant_field(wt, "also_known_as"),
                "group": mutant_field(wt, "category"),
                "klass": "",
                "health": "",
                "speed": "",
                "weakness": "",
                "drops": "",
                "spawn": mutant_field(wt, "location(s)", "locations"),
                "weapon": mutant_field(wt, "attacks"),
            }
        else:
            # hub page (Cannibals, Mutants, Puffies, ...)
            g = "Cannibals" if "cannibal" in title.lower() else ("Mutants" if "mutant" in title.lower() or "puffy" in title.lower() else "Groups")
            e = {
                "alias": "", "group": g, "klass": "", "health": "", "speed": "",
                "weakness": "", "drops": "", "spawn": "", "weapon": "",
            }
        e["summary"] = section_text(wt, "Appearance") or section_text(wt, "Gameplay") \
            or section_text(wt, "Overview") or intro_text(wt)
        if not e["summary"] and not any(v for k, v in e.items() if k != "summary"):
            print(f"[{i+1}/{len(titles)}] SKIP(empty) {title}")
            continue
        e["name"] = title
        e["slug"] = title.replace(" ", "_")
        enemies.append(e)
        print(f"[{i+1}/{len(titles)}] {title} ok ({len(e['summary'])} chars summary)")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(enemies, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(enemies)} enemies")


if __name__ == "__main__":
    main()
