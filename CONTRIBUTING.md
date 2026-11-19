# Contributing to PIP

PIP is one Python file of plain arithmetic, plus tests. Contributions that
keep it that way are welcome.

## Ground rules

- **Zero dependencies.** The standard library only. If a feature needs a
  package, it does not ship.
- **Local only.** No network calls except the clones and GitHub API reads
  the user explicitly asks for (`--org`, URL targets). No telemetry, ever.
- **Evidence never changes.** Personas, themes, and jokes may change tone;
  scores, awards, and findings come from the record and nothing else.
- **Not for employment decisions.** Every artifact carries the notice. New
  output surfaces must carry it too.

## Dev setup

```
git clone https://github.com/littlestjames82-sys/pip-pip
cd pip-pip
python -m unittest discover -s tests
```

Python 3.9+ and git are the whole toolchain. Tests build real fixture
repositories with known-answer histories; weekday-sensitive fixtures must
pin their weekdays (a fixed offset lands on different weekdays depending
on the run date).

## Good first contributions

- **Persona packs.** One JSON file in `personas/`, format in
  [personas/README.md](personas/README.md). Funny because the evidence is
  real, never mean about a real person.
- **Gallery entries.** `tools/make_gallery.py` reviews landmark projects;
  propose additions in an issue first so the set stays landmark-shaped.
- **Fairness fixes.** Found a way the record lies (a bot pattern, a
  generated-file shape, an authorship edge)? Those are the highest-value
  bug reports this project gets. Include a minimal repo that reproduces it.

## Pull requests

Run the full suite on the oldest Python you have access to as well as your
own; CI covers 3.9, 3.10, and 3.12 on Linux, Windows, and macOS. Keep the
diff to one idea. The changelog gets an entry under the unreleased heading.
