#!/usr/bin/env python3
"""Scrape Sons of the Forest consumables ({{Consumable ...}} infobox).
Output: src/data/consumables.json
"""
import json
import re
import time

from shared import (
    OUT_DIR, get_wikitext, infobox_field, category_members, best_summary, clean_html,
)

OUT = OUT_DIR / "consumables.json"
LANG_SUFFIX = re.compile(r"/[a-z]{2}(-[a-z]+)?$", re.I)
META_PAGES = {
    "Consumables", "Healing items", "Energy items", "Energy ingredients",
    "Healing ingredients", "Food items", "Drink items", "Food", "Drinks",
    "Consumable ingredients",
}


def clean_html(val: str) -> str:
    return re.sub(r"<[^>]+>", "", val).strip()


def main() -> None:
    members = category_members("Category:Consumables")
    titles = [
        m["title"]
        for m in members
        if m["ns"] == 0 and not LANG_SUFFIX.search(m["title"]) and m["title"] not in META_PAGES
    ]
    print(f"{len(titles)} consumable pages")

    rows = []
    for i, title in enumerate(titles):
        wt = get_wikitext(title)
        time.sleep(0.3)
        if not wt or "{{Consumable" not in wt:
            print(f"[{i+1}/{len(titles)}] SKIP {title}")
            continue
        grp = infobox_field(wt, "type")
        # {{RL|Canned Food|2}} renders a superscript count — drop trailing digits
        grp = re.sub(r"\s+\d+$", "", grp)
        c = {
            "alias": infobox_field(wt, "alias"),
            "group": grp,
            "obtained": infobox_field(wt, "obtained"),
            "id": infobox_field(wt, "id"),
            "stack": infobox_field(wt, "stack"),
            "health": clean_html(infobox_field(wt, "health")),
            "stamina": clean_html(infobox_field(wt, "stamina")),
            "energy": clean_html(infobox_field(wt, "energy")),
            "hydration": clean_html(infobox_field(wt, "hydration")),
            "fullness": clean_html(infobox_field(wt, "fullness")),
            "effects": infobox_field(wt, "effects"),
            "spoil": infobox_field(wt, "spoil"),
            "storage": clean_html(infobox_field(wt, "storage")),
        }
        c["summary"] = clean_html(best_summary(wt))
        c["name"] = title
        c["slug"] = title.replace(" ", "_")
        rows.append(c)
        print(f"[{i+1}/{len(titles)}] {title} ok")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(rows)} consumables")


if __name__ == "__main__":
    main()
