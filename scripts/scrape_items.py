#!/usr/bin/env python3
"""Scrape Sons of the Forest items from sonsoftheforest.wiki.gg.

Category:Items (filter /pl /es translation pages), parse {{Basic item}} infobox
+ Overview/Usage prose. Output: src/data/items.json
"""
import json
import re
import time

import requests

from shared import (
    API, OUT_DIR, session, get_wikitext, strip_templates, clean_ws, section_text,
    infobox_field, category_members,
)

OUT = OUT_DIR / "items.json"
LANG_SUFFIX = re.compile(r"/(pl|es|de|fr|ru|zh)$")


def main() -> None:
    members = category_members("Category:Items")
    titles = [
        m["title"]
        for m in members
        if m["ns"] == 0 and not LANG_SUFFIX.search(m["title"])
    ]
    print(f"{len(titles)} item pages after lang filter")

    items, skipped = [], []
    for i, title in enumerate(titles):
        wt = get_wikitext(title)
        time.sleep(0.3)
        if not wt or "{{Basic item" not in wt and "{{Item" not in wt:
            skipped.append(title)
            print(f"[{i+1}/{len(titles)}] SKIP {title}")
            continue
        slug = title.replace(" ", "_")
        item = {
            "name": title,
            "slug": slug,
            "alias": infobox_field(wt, "alias"),
            "obtained": infobox_field(wt, "obtained"),
            "type": infobox_field(wt, "type"),
            "gameId": infobox_field(wt, "id"),
            "stack": infobox_field(wt, "stack"),
            "consumable": infobox_field(wt, "consumable"),
            "equippable": infobox_field(wt, "equippable"),
            "location": infobox_field(wt, "location"),
            "uses": infobox_field(wt, "uses"),
            "summary": section_text(wt, "Overview") or section_text(wt, "Usage"),
        }
        items.append(item)
        print(f"[{i+1}/{len(titles)}] {title} ok")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(items)} items; skipped {len(skipped)}: {skipped[:10]}")


if __name__ == "__main__":
    main()
