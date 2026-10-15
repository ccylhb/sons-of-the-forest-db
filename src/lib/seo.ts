/**
 * SERP snippet builders for TimberDB (Sons of the Forest).
 *
 * The old snippets were keyword-stuffing prefixes plus a blind 100-char
 * slice of the wiki summary:
 *
 *   "Sons of the Forest Crafted Club: damage (standard/charged/downward),
 *    speed, range, how to get it and combat tips. The Crafted Club is a
 *    basic melee weapon in Sons of th"
 *
 * The prefix lists field NAMES without values (zero information) and the
 * slice cuts mid-sentence. This file replaces both with answer-first
 * sentences built from the fields that are actually populated.
 *
 * Data quirks handled here (all observed in the scrape):
 *  - wiki template residue: "|map =", "|attachment =", "|ammo =", and
 *    alias fields that are a raw infobox dump ("|obtained = Collecting")
 *  - loot strings with no separators: "Meat x1Animal Hides x2Head Trophy x1"
 *  - <br>-separated multi-values (season, spawn, attacks, effects bullets)
 *  - enemy health as "180 (Normal)"
 */

const SENTINELS = new Set(["", "none", "null", "n/a", "na", "-", "—", "?", "tbd", "no", "yes"]);

/** Wiki-template residue like "|map =" or a raw infobox dump "|obtained = X". */
const isTemplateJunk = (s: string): boolean => /^\s*\|/.test(s) || /^\s*\|[^=]*=\s*$/.test(s);

/** Strip <br>, bullets, wiki links and collapse whitespace. */
export const clean = (v: unknown): string =>
  String(v ?? "")
    .replace(/<br\s*\/?>/gi, ", ")
    .replace(/<\/?[a-z][^>]*>/gi, " ")
    .replace(/•/g, " ")
    .replace(/\[\[[^\]]*\|([^\]]*)\]\]/g, "$1")
    .replace(/\[\[([^\]]*)\]\]/g, "$1")
    .replace(/\s+/g, " ")
    .replace(/\s*,\s*/g, ", ")
    .trim();

/** clean() + drop sentinels and template residue. */
export const sane = (v: unknown): string => {
  const s = clean(v);
  if (SENTINELS.has(s.toLowerCase())) return "";
  if (isTemplateJunk(s)) return "";
  return s;
};

/**
 * "Meat x1Animal Hides x2Head Trophy x1" -> "Meat x1, Animal Hides x2, Head Trophy x1".
 * The wiki scrape concatenates loot rows without separators; the "xN + Capital"
 * boundary is the only reliable split point.
 */
export const splitLoot = (v: unknown): string => {
  const s = sane(v);
  if (!s) return "";
  return s
    .replace(/(x\d+)(?=[A-Z])/g, "$1, ")
    .replace(/([a-z])([A-Z])/g, "$1, $2") // FeathersHead -> Feathers, Head（有空格的不受影响）
    .replace(/\s*,\s*/g, ", ")
    .replace(/,\s*$/, "")
    .trim();
};

/** Strip a leading "<Name>," / "<Name> " from a summary so it doesn't repeat the title. */
export const stripLeadName = (sum: string, name: string): string => {
  if (!sum || !name) return sum;
  if (sum.startsWith(name + ",")) return sum.slice(name.length + 1).trim();
  if (sum.startsWith(name + " ")) return sum.slice(name.length + 1).trim();
  return sum;
};

/** Small preposition map so "in Surface" doesn't happen. */
const LOC_PREP: Record<string, string> = {
  surface: "on the surface",
  cave: "in caves",
  caves: "in caves",
  forest: "in the forest",
  lake: "at the lakes",
  lakes: "at the lakes",
  winter: "in winter",
};

const wherePhrase = (loc: string): string => {
  const key = loc.trim().toLowerCase();
  return LOC_PREP[key] || `in ${key}`;
};

/** Lower-case a category word for mid-sentence use: "Melee" -> "melee". */
export const lower = (v: unknown): string => sane(v).toLowerCase();

/** First sentence of a wiki summary (fallback when stats are too thin). */
export const firstSentence = (v: unknown): string => {
  const s = sane(v);
  if (!s) return "";
  const m = s.match(/^(.{20,200}?[.!?])(\s|$)/);
  return (m ? m[1] : s.slice(0, 140)).trim();
};

/** Numeric prefix of a value: "180 (Normal)" -> "180", "2%" -> "2". */
export const num = (v: unknown): string => {
  const s = sane(v);
  if (!s) return "";
  const m = s.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  return m ? m[0] : "";
};

/** Hard-clip to the SERP budget without cutting mid-word. */
export const clip = (s: string, n = 158): string => {
  const t = s.replace(/\s+/g, " ").trim();
  if (t.length <= n) return t;
  const cut = t.slice(0, n - 1);
  const sp = cut.lastIndexOf(" ");
  return (sp > n * 0.6 ? cut.slice(0, sp) : cut).replace(/[,;:\s]+$/, "") + "…";
};

/* ------------------------------------------------------------- weapons -- */

export const weaponDesc = (w: any): string => {
  const name = sane(w?.name) || "This weapon";
  const type = lower(w?.type);
  const std = num(w?.damageStandard);
  const chg = num(w?.damageCharged);
  const dwn = num(w?.damageDownward);
  const speed = lower(w?.speed);
  const dist = lower(w?.distance);
  const block = sane(w?.block);
  const loc = sane(w?.location);

  let s = `${name} — `;
  s += type ? `Sons of the Forest ${type} weapon` : "Sons of the Forest weapon";
  const dmgBits: string[] = [];
  if (std) dmgBits.push(`${std} standard`);
  if (chg && chg !== std) dmgBits.push(`${chg} charged`);
  if (dwn && dwn !== std) dmgBits.push(`${dwn} downward`);
  if (dmgBits.length) s += `: ${dmgBits.join(" / ")} damage`;
  const statBits: string[] = [];
  if (speed) statBits.push(speed);
  if (dist) statBits.push(`${dist} range`);
  if (block && block.toLowerCase() !== "none") statBits.push(`${lower(block)} blocking`);
  if (statBits.length) s += `, ${statBits.join(", ")}`;
  s += ".";
  if (w?.solafite) s += " Solafite plating ready.";
  if (loc) s += ` Location: ${loc}.`;
  if (s.length < 70) {
    const sum = firstSentence(w?.summary);
    if (sum) s += ` ${sum}`;
  }
  return clip(s);
};

export const weaponTitle = (w: any): string => {
  const name = sane(w?.name) || "Weapon";
  const std = num(w?.damageStandard);
  const tail = std ? ` (${std} dmg)` : "";
  return `${name} – Sons of the Forest Weapon${tail}`;
};

/* ------------------------------------------------------------- animals -- */

export const animalDesc = (a: any): string => {
  const name = sane(a?.name) || "This animal";
  const group = lower(a?.group);
  const attitude = lower(a?.attitude);
  const loc = sane(a?.location);
  const season = sane(a?.season);
  const loot = splitLoot(a?.loot);

  let s = `${name} — `;
  const head: string[] = [];
  if (attitude) head.push(attitude);
  if (group) head.push(group);
  s += head.length ? `${head.join(" ")} ` : "";
  s += "animal";
  if (loc) s += ` ${wherePhrase(loc)}`;
  if (season) s += `, active ${season.trim().toLowerCase() === "all" ? "year-round" : `in ${season.toLowerCase()}`}`;
  s += ".";
  if (loot) s += ` Drops: ${loot.toLowerCase()}.`;
  if (s.length < 70) {
    const sum = firstSentence(a?.summary);
    if (sum) s += ` ${sum}`;
  }
  return clip(s);
};

export const animalTitle = (a: any): string => {
  const name = sane(a?.name) || "Animal";
  const attitude = sane(a?.attitude);
  const tail = attitude ? ` (${attitude})` : "";
  return `${name} – Sons of the Forest Animal${tail}`;
};

/* --------------------------------------------------------- consumables -- */

const STAT_LABELS: Array<[string, string]> = [
  ["health", "health"],
  ["stamina", "stamina"],
  ["energy", "energy"],
  ["hydration", "hydration"],
  ["fullness", "fullness"],
];

export const consumableDesc = (c: any): string => {
  const name = sane(c?.name) || "This consumable";
  const group = lower(c?.group);
  const obtained = lower(c?.obtained);
  const stack = num(c?.stack);
  const spoil = sane(c?.spoil);

  let s = `${name} — `;
  s += group || "consumable";
  if (obtained) s += ` (${obtained})`;
  const stats: string[] = [];
  for (const [k, label] of STAT_LABELS) {
    const v = num(c?.[k]);
    if (v) stats.push(`+${v}% ${label}`);
  }
  if (stats.length) s += `: ${stats.join(", ")}`;
  s += ".";
  const effects = sane(c?.effects);
  if (effects) s += ` Effects: ${effects.toLowerCase()}.`;
  const bits: string[] = [];
  if (stack) bits.push(`stacks to ${stack}`);
  if (spoil && spoil.toLowerCase() === "no") bits.push("does not spoil");
  else if (spoil && spoil.toLowerCase() === "yes") bits.push("spoils over time");
  if (bits.length) {
    const joined = bits.join(", ");
    s += ` ${joined.charAt(0).toUpperCase()}${joined.slice(1)}.`;
  }
  if (s.length < 70) {
    const sum = firstSentence(c?.summary);
    if (sum) s += ` ${sum}`;
  }
  return clip(s);
};

export const consumableTitle = (c: any): string => {
  const name = sane(c?.name) || "Consumable";
  const group = sane(c?.group);
  const tail = group ? ` (${group})` : "";
  return `${name} – Sons of the Forest Consumable${tail}`;
};

/* ------------------------------------------------------------- enemies -- */

export const enemyDesc = (e: any): string => {
  const name = sane(e?.name) || "This enemy";
  const group = lower(e?.group);
  const spawn = sane(e?.spawn);
  const hp = num(e?.health);
  const speed = lower(e?.speed);
  const weakness = sane(e?.weakness);
  const drops = sane(e?.drops);
  const attacks = sane(e?.weapon);

  let s = `${name} — `;
  s += group && group !== "groups" ? `${group} ` : "";
  s += "enemy";
  if (spawn) s += ` (spawns: ${spawn.toLowerCase()})`;
  s += ".";
  const bits: string[] = [];
  if (hp) bits.push(`${hp} HP`);
  if (speed) bits.push(`${speed} speed`);
  if (weakness) bits.push(`weak to ${weakness.toLowerCase()}`);
  if (bits.length) s += ` ${bits.join(", ")}.`;
  if (attacks) s += ` Attacks: ${attacks.toLowerCase()}.`;
  if (drops) s += ` Drops: ${drops.toLowerCase()}.`;
  if (s.length < 70) {
    const sum = stripLeadName(firstSentence(e?.summary), name);
    if (sum) s += ` ${sum.charAt(0).toUpperCase()}${sum.slice(1)}`;
  }
  return clip(s);
};

export const enemyTitle = (e: any): string => {
  const name = sane(e?.name) || "Enemy";
  const group = sane(e?.group);
  const tail = group ? ` (${group})` : "";
  return `${name} – Sons of the Forest Enemy${tail}`;
};

/* --------------------------------------------------------------- items -- */

export const itemDesc = (i: any): string => {
  const name = sane(i?.name) || "This item";
  const type = sane(i?.type);
  const obtained = lower(i?.obtained);
  const stack = num(i?.stack);
  const equippable = sane(i?.equippable);
  const uses = sane(i?.uses);
  const loc = sane(i?.location);

  let s = `${name} — `;
  const genericType = type && /^other items?$/i.test(type);
  s += type && !genericType ? `Sons of the Forest item (${type.toLowerCase()})` : "Sons of the Forest item";
  const bits: string[] = [];
  if (stack) bits.push(`stacks to ${stack}`);
  if (equippable && equippable.toLowerCase() === "yes") bits.push("equippable");
  if (obtained) bits.push(`obtained by ${obtained}`);
  if (bits.length) s += `: ${bits.join(", ")}`;
  s += ".";
  if (loc) s += ` Found in ${loc}.`;
  if (uses) s += ` Uses: ${lower(uses)}.`;
  if (s.length < 70) {
    const sum = stripLeadName(firstSentence(i?.summary), name);
    if (sum) s += ` ${sum.charAt(0).toUpperCase()}${sum.slice(1)}`;
  }
  return clip(s);
};

export const itemTitle = (i: any): string => {
  const name = sane(i?.name) || "Item";
  const type = sane(i?.type);
  const tail = type ? ` (${type})` : "";
  return `${name} – Sons of the Forest Item${tail}`;
};
