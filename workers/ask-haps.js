// Ask Haps — Cloudflare Worker (v1)
// POST /api/ask  {"q": "something outdoors this Saturday"}
// → {"answer": "...", "picks": [{title, when, where, price, link, tagline}]}
// Secrets: ANTHROPIC_API_KEY (wrangler secret put / dashboard → Settings → Variables).

const SITE = "https://haps.club";
const MODEL = "claude-haiku-4-5";
const ALLOWED_ORIGINS = ["https://haps.club", "https://www.haps.club"];
const MAX_Q = 300;
const RATE = { perMin: 6, perDay: 40 }; // per IP, best-effort per isolate
const hits = new Map();

export default {
  async fetch(req, env, ctx) {
    const origin = req.headers.get("Origin") || "";
    const cors = {
      "Access-Control-Allow-Origin": ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
      "Vary": "Origin",
    };
    if (req.method === "OPTIONS") return new Response(null, { headers: cors });
    if (req.method !== "POST") return json({ error: "POST only" }, 405, cors);

    const ip = req.headers.get("CF-Connecting-IP") || "anon";
    if (!allow(ip)) return json({ error: "Easy there — try again in a minute." }, 429, cors);

    let q = "";
    try { q = String((await req.json()).q || "").trim().slice(0, MAX_Q); } catch {}
    if (q.length < 3) return json({ error: "Ask something like “outdoor plans this Saturday”." }, 400, cors);

    const items = await loadItems(ctx);
    const now = new Date();
    const today = now.toLocaleDateString("en-US", { timeZone: "America/Los_Angeles", weekday: "long", year: "numeric", month: "long", day: "numeric" });

    const catalog = items.map((e, i) =>
      `[${i}] ${e.title} | ${when(e)} | ${e.where || e.area || ""} | ${e.price || ""} | ${e.cat || ""} ${e.tags || ""} | ${e.tagline || ""}`
    ).join("\n");

    const system =
`You are "Ask Haps", the search box on haps.club — a curated guide to what's good in Los Angeles.
Today is ${today} (Los Angeles time). Resolve "this Saturday", "tonight", "this weekend" against today.
Answer ONLY from the catalog below. Never invent events, venues, prices or times. If nothing fits, say so briefly and suggest the closest thing in the catalog.
Voice: warm, quick, a friend who knows the city. 1–3 short sentences. Always write "Los Angeles", never "LA".
Return ONLY JSON: {"answer": string, "ids": [up to 5 catalog numbers, best first]}.

CATALOG:
${catalog}`;

    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: { "x-api-key": env.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json" },
      body: JSON.stringify({ model: MODEL, max_tokens: 400, system, messages: [{ role: "user", content: q }] }),
    });
    if (!r.ok) return json({ error: "Search is taking a breather. Try again shortly." }, 502, cors);

    const text = ((await r.json()).content || []).map(c => c.text || "").join("");
    let out = { answer: "", ids: [] };
    try { out = JSON.parse(text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1)); } catch { out.answer = text; }

    const picks = (out.ids || [])
      .filter(i => Number.isInteger(i) && items[i]).slice(0, 5)
      .map(i => { const e = items[i]; return { title: e.title, when: when(e), where: e.where || "", price: e.price || "", link: e.link || "", tagline: e.tagline || "" }; });

    return json({ answer: String(out.answer || "").slice(0, 600), picks }, 200, cors);
  },
};

// Pull live site data (events + inbox picks), cached 10 min at the edge. Drops anything already over.
async function loadItems(ctx) {
  const get = async (path) => {
    try {
      const r = await fetch(SITE + path, { cf: { cacheTtl: 600, cacheEverything: true } });
      return r.ok ? await r.json() : null;
    } catch { return null; }
  };
  const [ev, pk] = await Promise.all([get("/data/events.json"), get("/data/picks.json")]);
  const nowStamp = laStamp(new Date());
  const seen = new Set();
  return [...(ev?.featured || []), ...(ev?.events || []), ...(pk?.picks || [])]
    .filter(e => e && e.title && (!e.ends || e.ends >= nowStamp))
    .filter(e => { const k = e.title.toLowerCase(); if (seen.has(k)) return false; seen.add(k); return true; })
    .slice(0, 250);
}

function when(e) {
  const fmt = s => {
    if (!s || s.length < 8) return "";
    const d = new Date(`${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}T${s.length >= 13 ? s.slice(9,11)+":"+s.slice(11,13) : "12:00"}:00`);
    const day = d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
    return s.length >= 13 && s.slice(9,13) !== "0000" ? `${day} ${d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}` : day;
  };
  if (e.starts && e.ends && e.starts.slice(0,8) !== e.ends.slice(0,8)) return `${fmt(e.starts)} → ${fmt(e.ends)}`;
  if (e.starts) return fmt(e.starts);
  if (e.month) return `${e.month} ${e.day || ""}`.trim();
  return "Ongoing";
}

function laStamp(d) {
  const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/Los_Angeles", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(d).map(x => [x.type, x.value]));
  return `${p.year}${p.month}${p.day}T${p.hour === "24" ? "00" : p.hour}${p.minute}00`;
}

function allow(ip) {
  const t = Date.now(), h = hits.get(ip) || { m: [], d: [] };
  h.m = h.m.filter(x => t - x < 60e3); h.d = h.d.filter(x => t - x < 864e5);
  if (h.m.length >= RATE.perMin || h.d.length >= RATE.perDay) return false;
  h.m.push(t); h.d.push(t); hits.set(ip, h);
  return true;
}

function json(obj, status, headers) {
  return new Response(JSON.stringify(obj), { status, headers: { ...headers, "Content-Type": "application/json" } });
}
