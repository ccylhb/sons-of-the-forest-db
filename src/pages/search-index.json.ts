import type { APIRoute } from "astro";
import animals_data from "../data/animals.json";
import consumables_data from "../data/consumables.json";
import enemies_data from "../data/enemies.json";
import items_data from "../data/items.json";
import weapons_data from "../data/weapons.json";

const tools: Array<{ t: string; u: string; k: string; i?: string }> = [{"t": "Weapon Damage Rankings", "u": "/rankings/", "k": "Tool"}, {"t": "Food Planner", "u": "/calculator/", "k": "Tool"}];

const items: Array<{ t: string; u: string; k: string; i?: string }> = [
  ...animals_data.map((x: any) => { const n = x.name || x.title; if (!n || !x.slug) return null; if (n.includes("/") || String(x.slug).includes("/")) return null; return { t: n, u: `/animals/${x.slug}/`, k: "Creatures", i: x.icon || "" }; }).filter(Boolean) as Array<{t:string;u:string;k:string;i:string}>,
  ...consumables_data.map((x: any) => { const n = x.name || x.title; if (!n || !x.slug) return null; if (n.includes("/") || String(x.slug).includes("/")) return null; return { t: n, u: `/consumables/${x.slug}/`, k: "Consumables", i: x.icon || "" }; }).filter(Boolean) as Array<{t:string;u:string;k:string;i:string}>,
  ...enemies_data.map((x: any) => { const n = x.name || x.title; if (!n || !x.slug) return null; if (n.includes("/") || String(x.slug).includes("/")) return null; return { t: n, u: `/enemies/${x.slug}/`, k: "Creatures", i: x.icon || "" }; }).filter(Boolean) as Array<{t:string;u:string;k:string;i:string}>,
  ...items_data.map((x: any) => { const n = x.name || x.title; if (!n || !x.slug) return null; if (n.includes("/") || String(x.slug).includes("/")) return null; return { t: n, u: `/items/${x.slug}/`, k: "Items", i: x.icon || "" }; }).filter(Boolean) as Array<{t:string;u:string;k:string;i:string}>,
  ...weapons_data.map((x: any) => { const n = x.name || x.title; if (!n || !x.slug) return null; if (n.includes("/") || String(x.slug).includes("/")) return null; return { t: n, u: `/weapons/${x.slug}/`, k: "Weapons", i: x.icon || "" }; }).filter(Boolean) as Array<{t:string;u:string;k:string;i:string}>,
];

export const GET: APIRoute = () =>
  new Response(JSON.stringify({ tools, items }), {
    headers: { "Content-Type": "application/json" },
  });
