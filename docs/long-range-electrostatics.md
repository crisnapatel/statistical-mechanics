# Long-Range Electrostatics: Ewald, PPPM, and Slowly Convergent Series

!!! info "Practical MD topic — connects to [Finite Size](finite-size.md) and [Force Fields](force-fields.md). If you simulate anything with charges, you need to understand this."

## You can't just cut off Coulomb.

For Lennard-Jones interactions, a cutoff at $2.5\sigma$ captures 99% of the energy. The potential decays as $r^{-6}$. By 3 atomic diameters, there's essentially nothing left. Truncate it. Apply a tail correction. Move on.

Coulomb interactions decay as $1/r$. That's not fast enough. In 3D, the integral $\int_0^\infty (1/r) \cdot 4\pi r^2 \, dr$ diverges. The contribution from atoms 10 nm away is smaller than from atoms 1 nm away, sure, but it never becomes negligible. The sum of all Coulombic interactions in a periodic system is conditionally convergent: the answer depends on the order you add the terms.

If you truncate Coulomb at a cutoff, you get artifacts. Sharp. Serious. The electric field has a discontinuity at $r_\text{cut}$. Charges near the cutoff boundary feel artificial forces. The energy depends on which atoms happen to be near the cutoff surface. For ionic systems, truncation can shift the energy by 10-30%. For proteins in water, it can produce incorrect solvation structures and wrong conformational energies.

You can't truncate Coulomb. You need a smarter approach. That's Ewald summation.

## The Ewald trick

Paul Peter Ewald (1921) solved this for crystallographers, a century ago. The idea is gorgeous.

You have a sum of $1/r$ terms over all periodic images that doesn't converge well. Ewald's trick: split each point charge into two parts.

1. **A screened charge**: the original point charge surrounded by a diffuse Gaussian cloud of opposite charge. This screened interaction decays fast (like $\text{erfc}(r)/r$, which goes to zero exponentially). You can sum this in real space with a cutoff, just like LJ.

2. **A compensating smooth charge distribution**: the negative of those Gaussian clouds. This is a smooth, slowly varying charge density. Its electrostatic energy is most naturally computed in reciprocal (Fourier) space, where it converges rapidly.

3. **A self-energy correction**: you added Gaussian clouds centered on each charge. The interaction of each charge with its own cloud has to be subtracted. This is computed once and is trivial.

The total energy is:

$$E_\text{Coulomb} = E_\text{real} + E_\text{reciprocal} - E_\text{self}$$

The real-space sum converges fast because $\text{erfc}(\alpha r)/r$ decays exponentially. The reciprocal-space sum converges fast because the Fourier transform of the smooth Gaussian distributions is concentrated at low $k$. The parameter $\alpha$ controls the split: large $\alpha$ puts more work in reciprocal space (fewer $k$-vectors but more real-space screening), small $\alpha$ puts more work in real space (more pairs to sum but fewer $k$-vectors).

!!! tip "Key Insight"
    Ewald doesn't approximate the Coulomb sum. It computes it exactly (to within numerical precision). The "trick" is purely mathematical: splitting one poorly convergent sum into two rapidly convergent sums. The parameter $\alpha$ controls the split but doesn't affect the answer. Any $\alpha$ gives the same total energy.

## The cost problem: $O(N^{3/2})$

For $N$ charges, the real-space sum has $O(N)$ terms (with a cutoff). The reciprocal-space sum has $O(N^{1/2})$ $k$-vectors, but evaluating each one costs $O(N)$ (you sum over all charges). Total: $O(N^{3/2})$.

For 1,000 atoms, fine. For 100,000 atoms, expensive. For a million atoms, prohibitive.

## PPPM, PME, SPME: making it $O(N \log N)$

The solution: instead of evaluating the reciprocal-space sum analytically, interpolate the charges onto a regular grid and use the Fast Fourier Transform (FFT).

**Particle-Particle Particle-Mesh (PPPM)**: Assign charges to a 3D grid using interpolation. Solve Poisson's equation on the grid using FFT. Interpolate the forces back to the particles. The real-space part is still done particle-to-particle (hence the first "PP"). Total cost: $O(N \log N)$ for the mesh part, $O(N)$ for the real part.

**Particle Mesh Ewald (PME)** and **Smooth PME (SPME)**: Same idea, different interpolation schemes. SPME uses B-splines for the charge assignment, giving smooth forces and better energy conservation. This is what GROMACS and AMBER use.

In LAMMPS, all of this is handled by `kspace_style`:

```
kspace_style pppm 1e-4
```

The `1e-4` is the desired relative force accuracy. LAMMPS automatically chooses the grid spacing, real-space cutoff, and $\alpha$ to meet this target. You don't need to tune any of it.

!!! note "MD Connection"
    In LAMMPS:

    - `kspace_style ewald 1e-4` — exact Ewald ($O(N^{3/2})$). Use for small systems or benchmarking.
    - `kspace_style pppm 1e-4` — PPPM ($O(N \log N)$). Use this for everything.
    - The accuracy parameter ($10^{-4}$) is the relative RMS force error. Tighter accuracy = finer grid = slower. For most work, $10^{-4}$ to $10^{-5}$ is fine. For free energy calculations, use $10^{-5}$ or tighter.
    - `pair_style lj/cut/coul/long 10.0` — LJ with cutoff, Coulomb handled by kspace. The `long` means "the long-range part goes to the kspace solver."

## Alternatives: reaction field, Wolf, DSF

Not everyone uses Ewald. Some alternatives:

**Reaction field**: Treats everything beyond $r_\text{cut}$ as a dielectric continuum. Cheap but approximate. Works OK for bulk water but fails for heterogeneous systems (membranes, interfaces).

**Wolf method**: A clever truncation scheme that achieves charge neutrality within the cutoff sphere. Faster than Ewald, surprisingly accurate for some systems, but not systematically improvable and not recommended for production unless you've carefully validated it.

**Damped shifted force (DSF)**: Similar spirit to Wolf but with better energy conservation. Gaining popularity for large-scale simulations where Ewald is too expensive.

For most work, just use PPPM. It's fast, accurate, and well-tested. The alternatives exist for special situations (very large systems, GPU codes where FFTs are expensive, non-periodic systems).

## The tin-foil boundary condition

One subtle point. The Ewald sum assumes your periodic system is surrounded by a conducting medium at infinity (the "tin-foil" boundary condition). This means the average electric field in the box is zero. The macroscopic dipole moment of the simulation cell produces no long-range field.

If your system has a net dipole (which it shouldn't for a neutral periodic system, but can happen for polar systems with a preferred orientation), the tin-foil boundary condition zeroes it out. For most simulations, this is correct. For simulations of polar interfaces (water surfaces, ferroelectric materials), it's a constraint you need to be aware of.

## Takeaway

Coulomb interactions decay too slowly for simple cutoffs. Ewald summation splits the $1/r$ sum into a fast-converging real-space sum and a fast-converging reciprocal-space sum, computing the exact Coulomb energy. PPPM/PME use FFTs to reduce the cost from $O(N^{3/2})$ to $O(N \log N)$. In LAMMPS: `kspace_style pppm 1e-4` handles everything automatically. Always use Ewald-based methods for charged systems. Truncating Coulomb introduces artifacts that are worse than whatever computational savings you gain.

??? question "Check Your Understanding"
    1. You simulate a protein in water using `pair_style lj/cut/coul/cut 10.0` (note: `coul/cut`, not `coul/long`). This means Coulomb interactions are truncated at 10 Å with no long-range solver. Your solvation free energy is wrong by 15 kcal/mol. Is this error expected?
    2. Someone increases the PPPM accuracy from $10^{-4}$ to $10^{-6}$ and their simulation becomes 3x slower. Their computed energy changes by 0.01%. Was the extra accuracy worth it?
    3. Why can't you fix the Coulomb truncation problem by just using a really large cutoff (say 30 Å)? What's still wrong, and why is Ewald fundamentally different from a large cutoff?
    4. Your system is a single NaCl ion pair in a periodic box of water. The Na$^+$ and Cl$^-$ interact not only with each other but with all their periodic images. How does this affect the computed binding free energy, and what correction would you need?
    5. The Ewald parameter $\alpha$ doesn't affect the total energy (it just shifts work between real and reciprocal space). So why does LAMMPS let you tune it via the accuracy parameter?
