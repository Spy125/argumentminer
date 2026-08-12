"""Render argument graphs as HTML or plain-text trees."""

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


def render_html(graph: ArgumentGraph, title: str = "Argument Graph",
                output_path: Path = None) -> str:
    """Render an HTML page with an interactive D3 graph.

    D3 is loaded from a CDN, so the page needs network access to draw anything.
    """
    graph_data = _js_json(graph.to_dict())
    title = _escape(title)

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
body {{ background:#111; color:#eee; font-family:sans-serif; }}
.node {{ stroke:#fff; stroke-width:1.5px; cursor:pointer; }}
.link {{ stroke-opacity:.6; }}
.label {{ fill:#eee; font-size:12px; }}
</style>
</head><body>
<h2 style="padding:1rem">{title}</h2>
<svg id="graph" width="900" height="600"></svg>
<div id="detail" style="padding:1rem;max-width:800px;"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const data = {graph_data};
// simple force layout
const svg = d3.select("#graph");
const w = +svg.attr("width"), h = +svg.attr("height");
const color = d3.scaleOrdinal()
  .domain(["claim","premise","conclusion","background"])
  .range(["#4f8ef7","#f7a54f","#4ff7a5","#aaa"]);

const sim = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d=>d.id).distance(150))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(w/2, h/2));

const link = svg.append("g").selectAll("line")
  .data(data.edges).join("line")
  .attr("class","link")
  .attr("stroke", d => d.relation === "attack" ? "#f74f4f" : "#4ff74f")
  .attr("stroke-width", 2);

const node = svg.append("g").selectAll("circle")
  .data(data.nodes).join("circle")
  .attr("class","node").attr("r",12)
  .attr("fill", d => color(d.type))
  .call(d3.drag()
    .on("start", e => {{ if(!e.active) sim.alphaTarget(0.3).restart(); e.subject.fx=e.subject.x; e.subject.fy=e.subject.y; }})
    .on("drag",  e => {{ e.subject.fx=e.x; e.subject.fy=e.y; }})
    .on("end",   e => {{ if(!e.active) sim.alphaTarget(0); e.subject.fx=null; e.subject.fy=null; }}));

node.on("click", (e,d) => {{
  // Built as nodes rather than assigned through innerHTML: d.text is analysed
  // text, and innerHTML would parse any markup inside it as live HTML.
  const detail = document.getElementById("detail");
  detail.textContent = "";
  const label = document.createElement("strong");
  label.textContent = d.type.toUpperCase() + ": ";
  detail.appendChild(label);
  detail.appendChild(document.createTextNode(d.text));
}});

sim.on("tick", () => {{
  link.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y)
      .attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
  node.attr("cx",d=>d.x).attr("cy",d=>d.y);
}});
</script></body></html>"""

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")
    return html
