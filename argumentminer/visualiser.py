"""Render argument graphs as HTML or plain-text trees.

The HTML page is self-contained: layout, pan and zoom, and the detail panel
are plain JavaScript embedded beside the graph JSON, with no external
requests. It used to pull D3 from a CDN, which meant a saved report drew
nothing without network access - on a plane, behind a proxy, or simply once
that CDN version stopped being served. A report you cannot open later is not
a report.
"""

from __future__ import annotations

import json
from html import escape as _escape
from pathlib import Path

from argumentminer.graph import ArgumentGraph, RelationType


def _js_json(payload) -> str:
    """Serialise for embedding inside a <script> block.

    An HTML parser looks for the literal "</script" before any JavaScript runs,
    so a document containing that text would close the block early and the rest
    of the analysed text would be parsed as markup. json.dumps does not escape
    the slash, so it has to be escaped here. The ampersand and angle brackets
    are escaped for the same reason in the HTML-comment case.
    """
    return (
        json.dumps(payload)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_text_tree(graph: ArgumentGraph) -> str:
    """Print the argument graph as an indented text tree."""
    lines = []
    visited = set()

    def _walk(node_id: str, indent: int = 0):
        if node_id in visited:
            return
        visited.add(node_id)
        node = graph.get_node(node_id)
        if node is None:
            return
        prefix = "  " * indent
        label  = f"[{node.segment.type.upper()}]"
        lines.append(f"{prefix}{label} {node.segment.text[:80]}")
        for child in graph.children_of(node_id):
            edge = next((e for e in graph.edges
                         if e.source_id == child.id and e.target_id == node_id), None)
            rel  = f" ({edge.relation})" if edge else ""
            lines.append(f"{prefix}  |{rel}")
            _walk(child.id, indent + 2)

    for root in graph.roots():
        _walk(root.id)
    return "\n".join(lines)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    --bg:#0b0c0e; --panel:#111318; --soft:#1a1d22; --border:#262a30;
    --text:#e8e9ea; --dim:#9aa0a8; --faint:#6f757e;
    --claim:#4f8ef7; --premise:#f7a54f; --conclusion:#4ff7a5; --background:#8b949e;
    --support:#3fb950; --attack:#f85149;
    --mono:ui-monospace,"JetBrains Mono","Cascadia Mono",Consolas,monospace;
  }
  *{box-sizing:border-box;margin:0}
  body{background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif;
       height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{padding:10px 16px;border-bottom:1px solid var(--border);display:flex;gap:14px;
         align-items:center;flex-wrap:wrap}
  header h1{font-size:15px;font-weight:600;white-space:nowrap}
  .stat{color:var(--dim);font-size:12px;white-space:nowrap}
  .stat b{color:var(--text)}
  .stat i{font-style:normal;display:inline-block;width:8px;height:8px;border-radius:50%;
          margin-right:5px;vertical-align:middle}
  .offline{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--faint)}
  main{flex:1;display:flex;min-height:0}
  #wrap{flex:1;position:relative;min-width:0}
  canvas{position:absolute;inset:0;cursor:grab}
  .legend{position:absolute;left:12px;bottom:12px;background:rgba(17,19,24,.92);
          border:1px solid var(--border);border-radius:8px;padding:9px 13px;
          font-size:12px;color:var(--dim);display:flex;flex-direction:column;gap:4px}
  .legend b{font-weight:400;color:var(--text)}
  .ln{display:inline-block;width:14px;height:2px;margin-right:6px;vertical-align:middle}
  aside{width:340px;flex:none;border-left:1px solid var(--border);background:var(--panel);
        overflow-y:auto;padding:16px}
  aside h2{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);
           margin-bottom:8px}
  .type{font-family:var(--mono);font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
        padding:3px 9px;border-radius:10px;display:inline-block}
  .quote{font-size:14px;line-height:1.65;margin:12px 0;color:var(--text);
         border-left:2px solid var(--border);padding-left:12px;white-space:pre-wrap;
         overflow-wrap:anywhere}
  .meta{display:grid;grid-template-columns:auto 1fr;gap:5px 14px;font-family:var(--mono);
        font-size:11.5px;color:var(--dim);margin-top:14px}
  .meta span:nth-child(even){color:var(--text);overflow-wrap:anywhere}
  .rel{display:flex;flex-direction:column;gap:6px;margin-top:6px}
  .rel div{background:var(--soft);border-radius:6px;padding:9px 11px;font-size:12.5px;
           cursor:pointer;overflow-wrap:anywhere}
  .rel div:hover{outline:1px solid var(--border)}
  .rel small{font-family:var(--mono);font-size:10.5px;display:block;margin-bottom:3px}
  .hint{color:var(--faint);font-size:12.5px;line-height:1.6}
  .fal{background:var(--soft);border-left:2px solid var(--premise);border-radius:0 6px 6px 0;
       padding:10px 12px;margin-bottom:8px}
  .fal b{font-size:12.5px;color:var(--premise);font-weight:600}
  .fal p{font-size:12px;color:var(--dim);margin-top:3px;line-height:1.5}
  .fal q{font-size:12px;color:var(--text);display:block;margin-top:5px;font-style:italic;
         overflow-wrap:anywhere}
  hr{border:0;border-top:1px solid var(--border);margin:18px 0}
</style>
</head>
<body>
<header>
  <h1>__TITLE__</h1>
  <span class="stat"><i style="background:#4f8ef7"></i><b id="n-claim">0</b> claims</span>
  <span class="stat"><i style="background:#f7a54f"></i><b id="n-premise">0</b> premises</span>
  <span class="stat"><i style="background:#4ff7a5"></i><b id="n-conclusion">0</b> conclusions</span>
  <span class="stat"><i style="background:#8b949e"></i><b id="n-background">0</b> background</span>
  <span class="offline">self-contained &middot; no network needed</span>
</header>
<main>
  <div id="wrap">
    <canvas id="c"></canvas>
    <div class="legend">
      <div><span class="ln" style="background:#3fb950"></span><b>supports</b></div>
      <div><span class="ln" style="background:#f85149"></span><b>attacks</b></div>
      <div style="color:#6f757e;margin-top:2px">drag to pan, scroll to zoom, click a node</div>
    </div>
  </div>
  <aside id="panel"></aside>
</main>
<script id="data" type="application/json">__DATA__</script>
<script id="fallacies" type="application/json">__FALLACIES__</script>
<script>
"use strict";
const DATA = JSON.parse(document.getElementById("data").textContent);
const FALLACIES = JSON.parse(document.getElementById("fallacies").textContent);
const COLOUR = {claim:"#4f8ef7", premise:"#f7a54f", conclusion:"#4ff7a5", background:"#8b949e"};
const REL = {support:"#3fb950", attack:"#f85149", neutral:"#6f757e"};

for (const t of ["claim","premise","conclusion","background"]) {
  document.getElementById("n-" + t).textContent =
    DATA.nodes.filter(n => n.type === t).length;
}

const idx = new Map(DATA.nodes.map((n, i) => [n.id, i]));
const nodes = DATA.nodes.map((n, i) => {
  // Seed from a hash of the id so the same argument lays out the same way twice.
  let h = 2166136261;
  for (const ch of n.id) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619); }
  const a = ((h >>> 8) % 6283) / 1000, r0 = 90 + ((h >>> 16) % 150);
  return {id:n.id, text:n.text, type:n.type, depth:n.depth, i,
          x: Math.cos(a) * r0, y: Math.sin(a) * r0, vx: 0, vy: 0,
          r: n.type === "claim" ? 13 : 9};
});
const edges = DATA.edges
  .filter(e => idx.has(e.source) && idx.has(e.target))
  .map(e => ({relation:e.relation, confidence:e.confidence,
              s: idx.get(e.source), t: idx.get(e.target)}));
const adj = nodes.map(() => []);
for (const e of edges) { adj[e.s].push(e.t); adj[e.t].push(e.s); }

const canvas = document.getElementById("c"), ctx = canvas.getContext("2d");
let W = 0, H = 0; const dpr = window.devicePixelRatio || 1;
function resize() {
  const r = canvas.parentElement.getBoundingClientRect();
  W = r.width; H = r.height;
  canvas.width = W * dpr; canvas.height = H * dpr;
}
resize();
window.addEventListener("resize", () => { resize(); if (!running) draw(); });
const cam = {x: 0, y: 0, k: 1};
const toScreen = (x, y) => [(x - cam.x) * cam.k + W / 2, (y - cam.y) * cam.k + H / 2];
const toWorld = (px, py) => [(px - W / 2) / cam.k + cam.x, (py - H / 2) / cam.k + cam.y];

let alpha = 1, selected = null, hovered = null;
let dragNode = null, panning = false, lastX = 0, lastY = 0, moved = false;
function tick() {
  for (let i = 0; i < nodes.length; i++) {
    const a = nodes[i];
    for (let j = i + 1; j < nodes.length; j++) {
      const b = nodes[j];
      let dx = a.x - b.x, dy = a.y - b.y, d2 = dx * dx + dy * dy;
      if (d2 < 1) { d2 = 1; dx = i % 2 ? 1 : -1; dy = 1; }
      const f = 3000 / d2, d = Math.sqrt(d2);
      dx /= d; dy /= d;
      a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
    }
  }
  for (const e of edges) {
    const a = nodes[e.s], b = nodes[e.t];
    const dx = b.x - a.x, dy = b.y - a.y;
    const d = Math.sqrt(dx * dx + dy * dy) || 1;
    const f = (d - 130) * 0.04;
    a.vx += (dx / d) * f; a.vy += (dy / d) * f;
    b.vx -= (dx / d) * f; b.vy -= (dy / d) * f;
  }
  for (const n of nodes) {
    n.vx -= n.x * 0.013; n.vy -= n.y * 0.013;
    if (n !== dragNode) { n.x += n.vx * alpha; n.y += n.vy * alpha; }
    n.vx *= 0.82; n.vy *= 0.82;
  }
  alpha *= 0.99;
}
function snippet(text, n) {
  const one = text.replace(/\s+/g, " ").trim();
  return one.length > n ? one.slice(0, n - 1) + "…" : one;
}
function draw() {
  if (!W || !H) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  const near = selected !== null ? new Set([selected].concat(adj[selected])) : null;

  for (const e of edges) {
    const a = nodes[e.s], b = nodes[e.t];
    const [ax, ay] = toScreen(a.x, a.y), [bx, by] = toScreen(b.x, b.y);
    const dim = near && !(near.has(e.s) && near.has(e.t));
    ctx.globalAlpha = dim ? 0.16 : 0.85;
    ctx.strokeStyle = REL[e.relation] || REL.neutral;
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(bx, by); ctx.stroke();
    // Arrowhead: a premise points at the claim it supports, so direction reads.
    const dx = bx - ax, dy = by - ay, d = Math.sqrt(dx * dx + dy * dy) || 1;
    const ex = bx - (dx / d) * (b.r * cam.k + 4), ey = by - (dy / d) * (b.r * cam.k + 4);
    ctx.beginPath();
    ctx.moveTo(ex, ey);
    ctx.lineTo(ex - (dx / d) * 8 - (dy / d) * 4, ey - (dy / d) * 8 + (dx / d) * 4);
    ctx.lineTo(ex - (dx / d) * 8 + (dy / d) * 4, ey - (dy / d) * 8 - (dx / d) * 4);
    ctx.closePath(); ctx.fillStyle = ctx.strokeStyle; ctx.fill();
    ctx.globalAlpha = 1;
  }

  for (const n of nodes) {
    const [x, y] = toScreen(n.x, n.y);
    const r = Math.max(4, n.r * cam.k);
    ctx.globalAlpha = near && !near.has(n.i) ? 0.2 : 1;
    ctx.beginPath(); ctx.arc(x, y, r, 0, 7);
    ctx.fillStyle = COLOUR[n.type] || COLOUR.background;
    ctx.fill();
    if (n.i === selected || n.i === hovered) {
      ctx.strokeStyle = "#e8e9ea"; ctx.lineWidth = 2; ctx.stroke();
    }
    if (cam.k > 0.5 || n.i === selected || n.i === hovered) {
      ctx.fillStyle = "#e8e9ea";
      ctx.font = (n.i === selected ? "600 " : "") + '11.5px -apple-system,"Segoe UI",sans-serif';
      ctx.textAlign = "center";
      ctx.fillText(snippet(n.text, 34), x, y - r - 7);
    }
    ctx.globalAlpha = 1;
  }
}
let running = false;
function loop() {
  tick(); draw();
  if (alpha > 0.02 || dragNode) requestAnimationFrame(loop);
  else { running = false; draw(); }
}
function kick(a) { alpha = Math.max(alpha, a); if (!running) { running = true; requestAnimationFrame(loop); } }
kick(1);

function nodeAt(px, py) {
  const [wx, wy] = toWorld(px, py);
  for (let i = nodes.length - 1; i >= 0; i--) {
    const n = nodes[i], dx = wx - n.x, dy = wy - n.y;
    const hit = Math.max(9, n.r) / Math.min(cam.k, 1) * 1.3;
    if (dx * dx + dy * dy < hit * hit) return n;
  }
  return null;
}
canvas.addEventListener("mousedown", (ev) => {
  const n = nodeAt(ev.offsetX, ev.offsetY);
  moved = false; lastX = ev.offsetX; lastY = ev.offsetY;
  if (n) { dragNode = n; kick(0.3); } else { panning = true; canvas.style.cursor = "grabbing"; }
});
window.addEventListener("mousemove", (ev) => {
  const r = canvas.getBoundingClientRect();
  const px = ev.clientX - r.left, py = ev.clientY - r.top;
  if (dragNode) {
    const [wx, wy] = toWorld(px, py);
    dragNode.x = wx; dragNode.y = wy; dragNode.vx = dragNode.vy = 0;
    kick(0.3); moved = true;
  } else if (panning) {
    cam.x -= (px - lastX) / cam.k; cam.y -= (py - lastY) / cam.k;
    lastX = px; lastY = py; moved = true;
    if (!running) draw();
  } else {
    const was = hovered;
    const n = nodeAt(px, py);
    hovered = n ? n.i : null;
    canvas.style.cursor = n ? "pointer" : "grab";
    if (hovered !== was && !running) draw();
  }
});
window.addEventListener("mouseup", () => {
  if (dragNode && !moved) select(dragNode.i);
  else if (panning && !moved) select(null);
  dragNode = null; panning = false; canvas.style.cursor = "grab";
});
canvas.addEventListener("wheel", (ev) => {
  ev.preventDefault();
  const [wx, wy] = toWorld(ev.offsetX, ev.offsetY);
  cam.k = Math.min(4, Math.max(0.1, cam.k * (ev.deltaY < 0 ? 1.12 : 1 / 1.12)));
  const [nx, ny] = toWorld(ev.offsetX, ev.offsetY);
  cam.x += wx - nx; cam.y += wy - ny;
  if (!running) draw();
}, {passive: false});

// ---------- detail panel ----------
// Analysed text is written with textContent throughout. It is arbitrary input
// and innerHTML would parse any markup inside it as live HTML.
const panel = document.getElementById("panel");
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
function select(i) {
  selected = i;
  if (!running) requestAnimationFrame(draw);
  panel.textContent = "";
  if (i === null) { renderIdle(); return; }
  const n = nodes[i];

  const tag = el("span", "type", n.type);
  tag.style.background = (COLOUR[n.type] || COLOUR.background) + "22";
  tag.style.color = COLOUR[n.type] || COLOUR.background;
  panel.appendChild(tag);
  panel.appendChild(el("p", "quote", n.text));

  const meta = el("div", "meta");
  const rows = [["depth", String(n.depth)], ["characters", String(n.text.length)],
                ["id", n.id]];
  for (const pair of rows) {
    meta.appendChild(el("span", null, pair[0]));
    meta.appendChild(el("span", null, pair[1]));
  }
  panel.appendChild(meta);

  const out = edges.filter(e => e.s === i), inc = edges.filter(e => e.t === i);
  if (out.length) {
    panel.appendChild(el("hr"));
    panel.appendChild(el("h2", null, "this " + out[0].relation + "s"));
    panel.appendChild(relList(out, e => e.t));
  }
  if (inc.length) {
    panel.appendChild(el("hr"));
    // The noun and the verb disagree in number, so both have to swap.
    panel.appendChild(el("h2", null, inc.length === 1
      ? "1 segment points here"
      : inc.length + " segments point here"));
    panel.appendChild(relList(inc, e => e.s));
  }
  if (!out.length && !inc.length) {
    panel.appendChild(el("hr"));
    panel.appendChild(el("p", "hint",
      "Nothing links to this segment. It stands alone in the graph."));
  }
}
function relList(list, pick) {
  const box = el("div", "rel");
  for (const e of list) {
    const j = pick(e), n = nodes[j];
    const row = el("div");
    const lab = el("small", null, e.relation + " · " + n.type);
    lab.style.color = REL[e.relation] || REL.neutral;
    row.appendChild(lab);
    row.appendChild(document.createTextNode(snippet(n.text, 110)));
    row.addEventListener("click", () => {
      select(j); cam.x = n.x; cam.y = n.y; if (!running) draw();
    });
    box.appendChild(row);
  }
  return box;
}
function renderIdle() {
  panel.appendChild(el("h2", null, "Argument"));
  panel.appendChild(el("p", "hint",
    DATA.nodes.length
      ? "Click a node to read the segment it stands for, and what supports or attacks it."
      : "No argument segments were found in this text."));
  if (FALLACIES.length) {
    panel.appendChild(el("hr"));
    panel.appendChild(el("h2", null, "possible fallacies · " + FALLACIES.length));
    for (const f of FALLACIES) {
      const box = el("div", "fal");
      box.appendChild(el("b", null, f.name));
      box.appendChild(el("p", null, f.description));
      box.appendChild(el("q", null, f.matched_text));
      panel.appendChild(box);
    }
    panel.appendChild(el("p", "hint",
      "Pattern matches on wording, not judgements about the argument. Read each in context."));
  }
}
renderIdle();
</script>
</body>
</html>
"""


def render_html(graph: ArgumentGraph, title: str = "Argument Graph",
                output_path: Path = None, fallacies: list = None) -> str:
    """Render a self-contained HTML page with the argument graph.

    Nothing is fetched at view time, so the page draws the same offline, from a
    ``file://`` URL, or years after it was written.

    ``fallacies`` is optional; when given, the detections are listed in the
    panel with the caveat they carry everywhere else, that they are matches on
    wording rather than judgements about the argument.
    """
    data = _js_json(graph.to_dict())
    detected = _js_json([
        {"name": f.name, "description": f.description, "matched_text": f.matched_text}
        for f in (fallacies or [])
    ])
    # __DATA__ last: the analysed text it carries could otherwise contain one
    # of the other placeholders and have it substituted.
    html = (_TEMPLATE
            .replace("__TITLE__", _escape(title))
            .replace("__FALLACIES__", detected)
            .replace("__DATA__", data))

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
    return html


