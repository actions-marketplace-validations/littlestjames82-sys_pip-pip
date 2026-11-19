# Persona packs

A persona pack teaches PIP a new manager voice. The evidence in a review never
changes; the persona owns the verdict lines, the plan introduction, and the
sign-off. Load one with:

```
on-a-pip --persona-file personas/drill-sergeant.json
```

## Format (v1, frozen)

A pack is a single JSON object. Only `name` is required; every other field
falls back to the Corporate persona.

| Field | Type | Meaning |
|---|---|---|
| `name` | string, required | The pack's identifier, shown in `--persona-file` errors. Use lowercase words and hyphens. |
| `label` | string | Display name shown as "Review style" in the review. Defaults to `name`. |
| `verdicts` | object | One line per overall grade: keys `A`, `B`, `C`, `D`, `F`. Missing grades fall back to Corporate's line for that grade. |
| `plan_intro` | string | The paragraph introducing the 30-day improvement plan. |
| `signoff` | string | The closing text above the signature. |

Rules of the format:

- Plain JSON, UTF-8, no comments, no trailing commas.
- Keep verdicts to one or two sentences. The review is a formal document that
  happens to be funny; the persona is seasoning, not the meal.
- A pack changes tone only. It must never change evidence, scores, or awards;
  the loader ignores any other keys.

## Packs in this folder

- `pirate.json`: the Pirate Captain (also a built-in persona).
- `noir.json`: the Noir Detective (also a built-in persona).
- `drill-sergeant.json`: inspections at dawn.
- `therapist.json`: the record sounds tired, honestly.
- `vc.json`: milestones, traction, and one open door.

## Submitting a pack

Open a pull request adding one JSON file per persona to this folder, and add
yourself to the list above in the same PR. Packs are reviewed for the same
standard as the built-ins: funny because the evidence is real, never mean
about a real person, and readable as a formal document.
