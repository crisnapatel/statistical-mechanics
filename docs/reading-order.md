# Reading Order for MD Practitioners

Huang's book follows the standard graduate course order. That's fine if you're taking a course. But if you're coming from **molecular dynamics simulations** and want to understand the physics underneath what you're already doing, here's a suggested path.

## The Idea

Start from what your simulation computes. Build outward to the theory.

## Suggested Path

| Step | Topic | Huang Chapters | Why this order |
|------|-------|---------------|----------------|
| 1 | What is statistical mechanics? | Ch 6 intro | Frame the whole subject |
| 2 | Phase space & microstates | Ch 6.0–6.2 | "What your simulation is actually computing" |
| 3 | Velocity initialization | Ch 4.2 | "Where your atom velocities come from" |
| 4 | Ensembles | Ch 6–7 | "What your thermostat/barostat enforces" |
| 4b | Which thermostat? Which barostat? | [Thermostat page](which-thermostat.md) | "Which `fix` for which job?" |
| 4c | Your force field is a lie | [Force Field page](force-fields.md) | "What `pair_coeff` actually means" |
| 4d | Finite size & periodic images | [Finite Size page](finite-size.md) | "What `boundary p p p` really means" |
| 4e | Free energy isn't free | [Free Energy page](free-energy.md) | "Why $\Delta G$ is so hard to compute" |
| 4f | The radial distribution function | [RDF page](rdf.md) | "Your simulation's fingerprint" |
| 5 | The partition function | Ch 7 | The one function that generates everything |
| 6 | Thermodynamic potentials | [Potentials page](thermodynamic-potentials.md) | "Which energy is my simulation minimizing?" |
| 7 | Connecting to thermodynamics | Ch 7–8 | Bridge micro → macro |
| 8 | Brownian motion & diffusion | [Brownian Motion page](brownian-motion.md) | "Why does `compute msd` work?" |
| 9 | Uncertainty & sampling | [Uncertainty page](uncertainty-sampling.md) | "Are my error bars honest?" |
| 10 | Ideal gas | Ch 8 | First real calculation |
| 11 | Interacting systems | Later chapters | Where MD actually lives |

!!! note
    This is a suggestion, not a rule. Every chapter page also shows its Huang chapter number so you can follow the book's order if you prefer.

## Or Just Follow the Book

Each chapter page maps directly to Huang's chapters. If you're reading the book alongside this site, just go chapter by chapter — every page tells you exactly where in the book it corresponds to.
