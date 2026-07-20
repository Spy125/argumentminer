"""ArgumentMiner CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from argumentminer.segmenter import ArgumentSegmenter
from argumentminer.fallacy import FallacyDetector
from argumentminer.graph import build_graph
from argumentminer.visualiser import render_text_tree, render_html

app     = typer.Typer(name="argumentminer", add_completion=False)
console = Console()


@app.command("analyse")
def analyse(
    text: str   = typer.Argument(None, help="Text to analyse (or use --file)"),
    file: Path  = typer.Option(None, "--file", "-f", help="Read text from file"),
    html_out: Path = typer.Option(None, "--html", help="Save HTML graph"),
    json_out: Path = typer.Option(None, "--json", help="Save JSON output"),
    no_fallacies: bool = typer.Option(False, "--no-fallacies"),
):
    """Segment text into argument units, build a graph, and detect fallacies."""
    if file:
        text = file.read_text(encoding="utf-8")
    if not text:
        console.print("[red]Provide text as argument or with --file[/red]")
        raise typer.Exit(1)

    segmenter = ArgumentSegmenter()
    detector  = FallacyDetector()

    segments  = segmenter.segment(text)
    graph     = build_graph(segments)

    console.print("\n[bold]Argument Structure:[/bold]")
    console.print(render_text_tree(graph))

    if not no_fallacies:
        fallacies = detector.detect_unique(text)
        if fallacies:
            table = Table(title="Detected Fallacies")
            table.add_column("Fallacy")
            table.add_column("Matched Text")
            table.add_column("Confidence")
            for f in fallacies:
                table.add_row(f.name, f.matched_text, f"{f.confidence:.0%}")
            console.print(table)
        else:
            console.print("[green]No obvious fallacies detected.[/green]")

    if html_out:
        render_html(graph, title="ArgumentMiner Analysis", output_path=html_out)
        console.print(f"HTML saved -> {html_out}")

    if json_out:
        data = {
            "segments": [{"text": s.text, "type": s.type,
                           "confidence": s.confidence} for s in segments],
            "graph": graph.to_dict(),
        }
        json_out.write_text(json.dumps(data, indent=2))
        console.print(f"JSON saved -> {json_out}")


if __name__ == "__main__":
    app()
