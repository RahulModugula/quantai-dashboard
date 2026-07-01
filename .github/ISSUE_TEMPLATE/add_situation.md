---
name: Add a distressed-credit situation
about: Propose a real restructuring to add as a bundled worked example (great first PR)
labels: good first issue, situation
---

## The situation
<!-- Company, year, and what makes the structure interesting to teach.
     e.g. "J.Crew 2017 — the trapdoor / IP drop-down"; "Revlon 2020 — the
     accidental $900M repayment"; "Rite Aid 2023"; "iHeartMedia 2019". -->

## Why it's worth adding
<!-- What does this case teach that the bundled ones (ATI loan-to-own,
     Serta uptier, Hertz asset-coverage) don't? -->

## Sources
<!-- Public filings / court dockets / rating actions you'd ground the numbers in.
     Every figure must trace to a source; approximations marked `# ~approx`,
     gaps marked "unknown" rather than guessed. -->

## Decision point
<!-- The date the committee would be meeting (the entry, not the outcome). -->

---

To build it: `quantai-credit new examples/distressed/situations/<name>.yaml`, fill
it in against your sources, then `quantai-credit validate <name>.yaml` (free, no
key). See CONTRIBUTING.md and the bundled files for the shape. Note if the
structure is an uptier/priming or asset-backed/silo case — `validate` will warn
that the generic pari-passu waterfall doesn't fully model those.
