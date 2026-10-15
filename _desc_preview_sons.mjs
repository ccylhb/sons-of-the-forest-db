// 预演 TimberDB C1 描述改造：直接 import 真实 src/lib/seo.ts，与页面实现零漂移。
// 判据：<60 字符 / >158 字符 / "?" 泄漏 / 脏模式（模板残留、无分隔 loot）/ 唯一性 / title 检查。
import { pathToFileURL } from "node:url";
import { readFileSync } from "node:fs";

const REPO = "C:/Users/梁会斌/Documents/Codex/sons-of-the-forest-db";
const mod = await import(pathToFileURL(`${REPO}/src/lib/seo.ts`).href);
const { weaponDesc, apparelUnused, animalDesc, consumableDesc, enemyDesc, itemDesc } = mod;
const { weaponTitle, animalTitle, consumableTitle, enemyTitle, itemTitle } = mod;

const read = (p) => JSON.parse(readFileSync(p, "utf8"));
const data = [
  ["weapons", `${REPO}/src/data/weapons.json`, weaponDesc, weaponTitle],
  ["animals", `${REPO}/src/data/animals.json`, animalDesc, animalTitle],
  ["consumables", `${REPO}/src/data/consumables.json`, consumableDesc, consumableTitle],
  ["enemies", `${REPO}/src/data/enemies.json`, enemyDesc, enemyTitle],
  ["items", `${REPO}/src/data/items.json`, itemDesc, itemTitle],
];

const DIRTY = [
  /\?\s*[%,]/, /\?\s*(damage|range|armor|health|stamina|dmg)/i,
  /\|/, // wiki 模板残留
  /\bNone\b/, /\bundefined\b/, /\bNaN\b/, /,\s*\./, /\s{2,}/, /—\s*\./, /^\s*[,.;:]/,
  /[a-z]\d[A-Z]/, // 无分隔 loot 残留（Meat x1Animal）
  /<br/i, /•/,
];

const all = [];
let grand = 0;
for (const [name, path, fn, tfn] of data) {
  const rows = read(path);
  const out = rows.map((x) => ({ title: x.name, slug: x.slug, desc: fn(x), ptitle: tfn(x) }));
  const lens = out.map((o) => o.desc.length);
  const short = out.filter((o) => o.desc.length < 60);
  const long = out.filter((o) => o.desc.length > 158);
  const q = out.filter((o) => o.desc.includes("?"));
  const dirty = out.filter((o) => DIRTY.some((r) => r.test(o.desc)));
  const tq = out.filter((o) => o.ptitle.includes("?")).length;
  const tlong = out.filter((o) => o.ptitle.length > 80).length;
  const dupMap = new Map();
  for (const o of out) dupMap.set(o.desc, (dupMap.get(o.desc) || 0) + 1);
  const dups = [...dupMap.entries()].filter(([, c]) => c > 1);
  console.log(
    `${name.padEnd(12)} n=${String(rows.length).padStart(3)}  ` +
      `len min=${Math.min(...lens)} avg=${Math.round(lens.reduce((a, b) => a + b, 0) / lens.length)} max=${Math.max(...lens)}  ` +
      `<60=${short.length}  >158=${long.length}  "?"=${q.length}  脏=${dirty.length}  唯一=${out.length - dups.reduce((a, [, c]) => a + c - 1, 0)}/${out.length}  title?=${tq} title>80=${tlong}`,
  );
  for (const o of short.slice(0, 4)) console.log(`    <60 ${o.title}: ${o.desc}`);
  for (const o of q.slice(0, 4)) console.log(`    "?" ${o.title}: ${o.desc}`);
  for (const o of dirty.slice(0, 4)) console.log(`    脏  ${o.title}: ${o.desc}`);
  for (const o of out.filter((o) => o.ptitle.length > 80).slice(0, 3)) console.log(`    title长 ${o.ptitle}`);
  if (dups.length) for (const [d, c] of dups.slice(0, 3)) console.log(`    重复×${c}: ${d.slice(0, 90)}`);
  all.push(...out);
  grand += out.length;
}
console.log(`\n合计 ${grand} 条`);

console.log("\n================ 每类前 3 条 ================");
for (const [name, path, fn] of data) {
  const rows = read(path);
  console.log(`\n--- ${name} ---`);
  for (const x of rows.slice(0, 3)) console.log(`  ${fn(x)}`);
}
console.log("\n--- 原印 ? / 模板残留的代表条目 ---");
const wp = read(`${REPO}/src/data/weapons.json`);
for (const x of wp.filter((y) => String(y.location || "").startsWith("|")).slice(0, 3)) console.log(`  ${weaponDesc(x)}`);
const an = read(`${REPO}/src/data/animals.json`);
for (const x of an.filter((y) => /x\d+[A-Z]/.test(y.loot || "")).slice(0, 3)) console.log(`  ${animalDesc(x)}`);
const en = read(`${REPO}/src/data/enemies.json`);
for (const x of en.filter((y) => !y.health && !y.speed).slice(0, 3)) console.log(`  ${enemyDesc(x)}`);
const it = read(`${REPO}/src/data/items.json`);
for (const x of it.filter((y) => !y.summary).slice(0, 3)) console.log(`  ${itemDesc(x)}`);
