# Finite Size, Periodic Images, and the Ghosts in Your Box

!!! info "Practical MD topic — no specific Huang chapter. This is the stuff you realize matters after your first 'real' project."

## Your simulation box is lying to you about being infinite.

Here's a fun thought experiment. You set up a nice 10 nm box of liquid argon. 4,000 atoms. Periodic boundary conditions. You run it, compute $g(r)$, get a beautiful curve, and move on with your life.

But wait. How big is 10 nm? About 30 atomic diameters across. That's it. Your "bulk liquid" is 30 atoms wide. And every atom in that box is interacting not just with its neighbors, but with an infinite lattice of periodic copies of itself. The "bulk" behavior you're measuring is actually the behavior of a tiny crystal of simulation boxes, tiled to infinity.

Is that OK? Usually, yes. Sometimes, catastrophically no. And knowing the difference is what separates simulation results you can publish from simulation results that belong in the trash.

Let's go.

## What periodic boundary conditions actually do

Strip away the implementation details, and PBC is a simple trick: when an atom exits the box on one side, it re-enters on the opposite side. The box has no walls. No surfaces. No edges. Topologically, it's a 3D torus.

Why do we need this? Because we're trying to simulate a bulk material. Bulk means no surfaces. But a finite box has surfaces. Those surfaces introduce artifacts: atoms near the boundary behave differently from atoms in the interior. For a 10 nm box, the surface-to-volume ratio is enormous. Most of your atoms would be "surface" atoms.

PBC eliminates surfaces entirely. Every atom sees the same environment in every direction. There's no "edge" of the simulation. From any atom's perspective, the universe looks the same.

!!! tip "Key Insight"
    PBC doesn't simulate an infinite system. It simulates a **small system repeated infinitely**. That's a very different thing. Your atoms interact with their periodic images, and the box length becomes a physical parameter of the system. If the box is too small, the periodic images interact with each other in ways that have nothing to do with real physics.

## The minimum image convention

Here's the practical question: atom $i$ is at position $\mathbf{r}_i$ and atom $j$ is at $\mathbf{r}_j$. But $j$ also has images at $\mathbf{r}_j + n\mathbf{L}$ for every integer vector $n$. Which copy of $j$ should $i$ interact with?

The **minimum image convention** says: interact with the closest copy. In a cubic box of side $L$:

$$\Delta x = x_j - x_i - L \cdot \text{round}\!\left(\frac{x_j - x_i}{L}\right)$$

Same for $y$ and $z$. This wraps the displacement vector so that $|\Delta x| \leq L/2$. Simple. Fast. And it has one critical consequence:

**Your interaction cutoff must be less than $L/2$.**

If $r_\text{cut} > L/2$, an atom could interact with two copies of the same neighbor (the "real" one and its image). That's unphysical. It also means the force on atom $i$ depends on which image of $j$ you happen to find first, which is a recipe for energy conservation disasters.

!!! warning "Common Mistake"
    Setting a cutoff of 12 Å in a box that's 20 Å across. The cutoff (12) is greater than $L/2$ (10). LAMMPS will warn you about this, but not all codes do. If you see `WARNING: Pair cutoff > half of box length`, your simulation is broken. Either increase the box or decrease the cutoff.

## The ghosts: what periodic images actually look like

Imagine you could zoom out and see not just your simulation box, but all its periodic copies. In 2D, it would look like a tiled floor. Your 256 atoms become 256 $\times \infty$ atoms, arranged in a pattern that repeats every $L$ in each direction.

Now here's the subtle part. Those image atoms aren't independent. When atom 42 moves to the right by 0.1 Å, every copy of atom 42 in every image box also moves to the right by 0.1 Å. Simultaneously. Because they're not real atoms. They're ghosts. Echoes of the original.

This means your system has exactly $N$ degrees of freedom, not $\infty$. The periodic images add no new information. They just provide a way to compute interactions without surfaces.

But they do impose a constraint: **your system cannot support any fluctuation with a wavelength longer than $L$**. Density waves, sound waves, long-wavelength phonons, anything with $\lambda > L$ is killed by the periodicity. The box acts as a high-pass filter on fluctuations.

For most liquid-state properties at moderate conditions, this doesn't matter. The correlation length is a few atomic diameters, well within the box. But near a phase transition, where correlation lengths diverge? Or for properties that depend on long-wavelength fluctuations (like the compressibility near the critical point)? The box size becomes the dominant source of error.

!!! note "MD Connection"
    In LAMMPS, periodic boundary conditions are set with `boundary p p p`. The `p` means periodic in that dimension. You can also use `f` (fixed) or `s` (shrink-wrapped) for non-periodic boundaries. For bulk simulations, always use `p p p`.

## Finite-size effects: the catalog

Not all finite-size effects are created equal. Here's what can go wrong, ranked by how often it bites people.

### 1. Cutoff artifacts

The most basic finite-size issue. If your box is too small relative to the interaction range, the cutoff truncation removes a significant fraction of the total interaction energy. For LJ with $r_\text{cut} = 2.5\sigma$ in a box of $5\sigma$, you're cutting off interactions that would contribute meaningfully to the energy and pressure.

The fix: **long-range corrections**. For a uniform liquid, the contribution of interactions beyond $r_\text{cut}$ can be estimated analytically. For the LJ potential:

$$U_\text{tail} = \frac{8\pi N \rho \epsilon \sigma^3}{3} \left[ \frac{1}{3}\left(\frac{\sigma}{r_\text{cut}}\right)^9 - \left(\frac{\sigma}{r_\text{cut}}\right)^3 \right]$$

$$P_\text{tail} = \frac{16\pi \rho^2 \epsilon \sigma^3}{3} \left[ \frac{2}{3}\left(\frac{\sigma}{r_\text{cut}}\right)^9 - \left(\frac{\sigma}{r_\text{cut}}\right)^3 \right]$$

These assume $g(r) = 1$ beyond the cutoff, which is good for liquids far from phase transitions and terrible near interfaces or phase boundaries.

In LAMMPS: `pair_modify tail yes`. Two words. But they can shift your pressure by 10-20% for typical LJ cutoffs. Always turn this on for homogeneous systems.

### 2. Self-interaction through images

Your solute molecule interacts with its own periodic image. For a small molecule in a large box, the image is far away and the interaction is negligible. For a protein in a 6 nm box, the protein-image distance might be only 2 nm. The protein "feels" its own ghost.

This is especially bad for charged systems. Coulomb interactions decay as $1/r$, which means even distant images contribute significantly. The interaction energy of a charge with its own periodic images scales as $q^2/L$, and for a typical protein simulation, this artifact can be comparable to the solvation free energy you're trying to compute.

The rule of thumb: keep at least 1-1.5 nm of solvent between the solute and the box edge. For charged systems, you may need more, or you may need finite-size corrections (Makov-Payne, Hummer-Hunenberger-Pratt).

### 3. Concentration artifacts

You put one solute molecule in your periodic box. You think you're simulating dilute solution. But you're not. You're simulating a solution at concentration $c = 1/(N_A V_\text{box})$. For a 5 nm cubic box, that's about 5 mM. Not dilute. And because of PBC, your system is actually a crystal of solute molecules, spaced $L$ apart.

For most liquid-state properties this doesn't matter. But for properties that depend on solute-solute interactions (osmotic pressure, activity coefficients, binding thermodynamics at low concentrations), the effective concentration matters.

### 4. Suppressed long-wavelength fluctuations

This is the subtle one. Near a phase transition (liquid-gas critical point, crystallization, demixing), the correlation length diverges. When $\xi > L$, the box literally cannot contain the critical fluctuations. The result: shifted transition temperatures, suppressed susceptibilities, wrong critical exponents.

Even away from phase transitions, the compressibility $\kappa_T$ involves long-wavelength density fluctuations. In a small box, these are suppressed, and $\kappa_T$ is systematically underestimated.

### 5. Transport property artifacts

We already met this on the [Brownian motion page](brownian-motion.md). The diffusion coefficient in a periodic box has a finite-size correction:

$$D_\text{PBC} = D_\infty - \frac{k_B T \xi}{6\pi \eta L}$$

where $\xi \approx 2.837$ is a lattice constant for cubic PBC and $\eta$ is the shear viscosity. For a typical water box of 4 nm, this correction is 10-15% of $D$. Not small.

Viscosity has its own finite-size effects, though they're typically smaller. The general pattern: transport properties in periodic boxes are system-size dependent, and the dependence goes as $1/L$.

## How to check for finite-size effects

Here's the embarrassingly simple answer: **run two system sizes and compare.**

Double the box (which means 8x the atoms in 3D). Compute your observable at both sizes. If they agree within statistical uncertainty, the smaller box is probably fine. If they don't, you need the bigger box (or you need finite-size corrections).

This sounds expensive, and it is. But it's the only way to be sure. Theoretical estimates of finite-size effects exist for specific observables (the Yeh-Hummer correction for diffusion, analytic tail corrections for energy), but they don't cover every case. The two-size test is your safety net.

For a quick sanity check:

- **$g(r)$**: Should go to 1.0 at $r = L/2$. If it's still oscillating, your box is too small (or your density is too high for that box size).
- **Energy**: Compute with and without tail corrections (`pair_modify tail yes/no`). If the difference is > 1% of the total, your cutoff might be too short.
- **Pressure**: Same test. Pressure is more sensitive to tail corrections than energy.
- **Diffusion**: Compare to a larger box. Apply Yeh-Hummer. If the correction is > 5%, consider whether your box is adequate.

!!! tip "Key Insight"
    The question isn't "is my box big enough?" The question is "is my box big enough for **this** property?" A box that's perfectly adequate for $g(r)$ might be too small for diffusion. A box that's fine for liquid-state properties might be way too small for a phase transition study.

## Long-range corrections in practice

For LJ interactions in homogeneous systems, tail corrections are straightforward and always worth applying. The formulas above assume $g(r) \approx 1$ beyond the cutoff. This works for:

- Bulk liquids at moderate conditions
- Dense fluids away from interfaces
- Any system where the structure is isotropic beyond $r_\text{cut}$

It fails for:

- Vapor-liquid interfaces (density isn't uniform)
- Adsorption on surfaces
- Systems near phase coexistence
- Anything with long-range structure beyond the cutoff

For electrostatic interactions ($1/r$ decay), truncation is never acceptable. You need Ewald summation or one of its grid-based variants (PPPM, PME). That's a whole separate topic, covered on the [electrostatics page](long-range-electrostatics.md).

!!! note "MD Connection"
    In LAMMPS, the key commands are:

    - `pair_modify tail yes` — apply analytic tail corrections for LJ energy and pressure. Two words that can shift your pressure by 10-20%.
    - `kspace_style pppm 1e-4` — PPPM for long-range electrostatics. The `1e-4` is the relative force accuracy. Always use this (or `ewald`) for charged systems.
    - `pair_modify shift yes` — shift the potential so $U(r_\text{cut}) = 0$. This removes the energy discontinuity at the cutoff but changes the effective potential. Use for dynamics (avoids force discontinuity), but note that the thermodynamic properties now correspond to the shifted potential, not the original.

## Takeaway

Periodic boundary conditions eliminate surfaces but create a system that repeats every $L$. Your box length is a physical parameter: too small, and finite-size artifacts contaminate your results. The minimum image convention requires $r_\text{cut} < L/2$. Long-range LJ corrections (`pair_modify tail yes`) are nearly free and always worth applying for homogeneous systems. For electrostatics, truncation is never OK. The definitive test for finite-size effects is running two system sizes, but for known artifacts (diffusion, tail corrections), analytic formulas exist. Always ask: is my box big enough for *this* property?

??? question "Check Your Understanding"
    1. You run a liquid argon simulation in a 20 Å cubic box with `pair_style lj/cut 12.0`. LAMMPS prints a warning. Your labmate says "it's just a warning, ignore it." What exactly goes wrong if you ignore it, and what are your two options to fix it?
    2. You compute $g(r)$ and it flattens out at 0.95 instead of 1.0 at large $r$. Is this a finite-size effect, a normalization bug, or something else? How would you diagnose it?
    3. Someone simulates a protein in a 5 nm box with periodic boundaries. The protein's longest dimension is 4 nm. They claim the results represent "dilute solution" behavior. What's wrong with this claim, and what specific artifact will contaminate their free energy calculations?
    4. You add `pair_modify tail yes` to your LJ simulation and the pressure jumps from $-50$ bar to $+200$ bar. Is that reasonable, or did you break something? What determines the size of the tail correction?
    5. Your computed diffusion coefficient is 15% lower than the experimental value. Before blaming the force field, what finite-size check should you do first?
