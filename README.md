# ArgumentMiner

Analyses argumentative text - debates, opinion pieces, forum threads - and extracts the logical structure. It identifies claims, premises, and conclusions, detects support/attack relationships between them, flags logical fallacies, and renders everything as an interactive directed graph.

Built to explore how argument structure can be modelled programmatically and how rule-based NLP compares to trained models on structured reasoning tasks.

---

## How it works

1. Input text is split into argument units (sentences or clauses) and classified as claim, premise, or conclusion using marker phrase patterns
2. Consecutive unit pairs are checked for support or attack relationships using a second set of patterns
3. Eight fallacy detectors run over each unit: Ad Hominem, Appeal to Popularity, False Dichotomy, Appeal to Authority, Slippery Slope, Straw Man, Hasty Generalisation, Appeal to Emotion
4. A directed graph is built with NetworkX (nodes = argument units, edges = relations)
5. The graph is rendered as an interactive HTML file using Pyvis

---

## Usage

```bash
pip install -r requirements.txt

python -m argumentminer.cli mine "text to analyse"
# or from a file:
python -m argumentminer.cli mine --file debate.txt

# just list the fallacies, without building a graph:
python -m argumentminer.cli fallacies "text to analyse"
```

`mine` prints a terminal table of argument units and fallacies and can save an
HTML graph with `--html`. `fallacies` runs only the fallacy detectors.

---

## Graph legend

- Green edges: support relationships
- Red edges: attack relationships
- Red node border: fallacy detected on that unit

---

## Testing

Install the dependencies and run the suite:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt pytest   # Linux/macOS: .venv/bin/pip
.venv/Scripts/python -m pytest -v
```

Exercise the CLI directly with `python -m argumentminer.cli --help`.

---

## Project structure

```
argumentminer/
├── argumentminer/
│   ├── segmenter.py    # argument unit classification
│   ├── fallacy.py      # 8 fallacy pattern detectors
│   ├── graph.py        # support/attack relations, NetworkX graph construction
│   ├── visualiser.py   # Pyvis HTML rendering
│   └── cli.py
└── tests/
    └── test_fallacy.py
```

---

## Stack

Python 3.10, NetworkX, Pyvis, Typer, Rich
