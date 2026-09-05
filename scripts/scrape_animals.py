#!/usr/bin/env python3
"""Scrape Sons of the Forest animals ({{Animal ...}} infobox, Category:Fauna).
Output: src/data/animals.json
"""
import json
import re
import time

from shared import (
    OUT_DIR, get_wikitext, infobox_field, category_members, best_summary, clean_html,
)

OUT = OUT_DIR / "animals.json"
LANG_SUFFIX = re.compile(r"/[a-z]{2}(-[a-z]+)?$", re.I)


def clean_html(val: str) -> str:
    return re.sub(r"<[^>]+>", "", val).strip()


def main() -> None:
    members = category_members("Category:Fauna")
    titles = [
        m["title"]
        for m in members
        if m["ns"] == 0 and not LANG_SUFFIX.search(m["title"]) and m["title"] != "Fauna"
    ]
    print(f"{len(titles)} animal pages")

    animals = []
    for i, title in enumerate(titles):
        wt = get_wikitext(title)
        time.sleep(0.3)
        if not wt or "{{Animal" not in wt:
            print(f"[{i+1}/{len(titles)}] SKIP {title}")
            continue
        a = {
            "alias": infobox_field(wt, "alias"),
            "group": infobox_field(wt, "type"),
            "attitude": infobox_field(wt, "attitude"),
            "location": clean_html(infobox_field(wt, "location")),
            "season": infobox_field(wt, "season"),
            "loot": clean_html(infobox_field(wt, "loot")),
        }
        a["summary"] = clean_html(best_summary(wt))
        a["name"] = title
        a["slug"] = title.replace(" ", "_")
        animals.append(a)
        print(f"[{i+1}/{len(titles)}] {title} ok")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(animals, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(animals)} animals")


if __name__ == "__main__":
    main()
