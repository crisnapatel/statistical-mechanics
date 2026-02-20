# Coarse-Graining: Throwing Away Details on Purpose

!!! info "Practical MD topic — connects to [Force Fields](force-fields.md) and the partition function. When all-atom is too expensive, you throw away degrees of freedom. The question is which ones."

## Let me tell you about the most expensive simulation I've ever run.

Actually, let me tell you about the simulation I *couldn't* run. A lipid bilayer with embedded proteins. All-atom. Explicit water. 500,000 atoms. I needed microsecond timescales to see the protein-lipid rearrangement I cared about. At 1 fs per step, that's $10^{12}$ steps. On our cluster? A year.

So I did what everyone does. I threw away 90% of the atoms and replaced them with bigger, softer beads. Four water molecules become one bead. A lipid tail of 15 carbons becomes 4 beads. The simulation ran 100x faster. I got my microseconds.

But here's the question that keeps me up at night: which details did I lose? And did any of them matter?

## What coarse-graining is

The idea is simple. Group several atoms into one "bead." Define effective interactions between the beads. Run the simulation with fewer particles and softer (therefore faster-timescale) potentials.

A typical all-atom water model has 3 interaction sites per molecule. The MARTINI coarse-grained model represents 4 water molecules as 1 bead. That's a 12-fold reduction in interaction sites. Plus the interactions are smoother, so you can use a larger timestep (20-40 fs instead of 1-2 fs). Combined: 100-1000x speedup.

The price: you've lost the hydrogen-bond network, the dipole moment, the rotational dynamics, the vibrational spectrum. The bead captures the average thermodynamic behavior (density, compressibility, partitioning free energies) but not the molecular-level details.

## The stat mech behind it

Coarse-graining is, at its core, a partial trace over the partition function. You start with the all-atom partition function:

$$Z = \int e^{-\beta H(\mathbf{r}_1, \ldots, \mathbf{r}_N)} \, d\mathbf{r}_1 \cdots d\mathbf{r}_N$$

Define coarse-grained coordinates $\mathbf{R}_I = M(\{\mathbf{r}_i\})$ (some mapping from atomic to CG positions, usually center of mass of each group). The CG partition function is:

$$Z_\text{CG} = \int e^{-\beta U_\text{CG}(\mathbf{R}_1, \ldots, \mathbf{R}_M)} \, d\mathbf{R}_1 \cdots d\mathbf{R}_M$$

The exact CG potential $U_\text{CG}$ is defined by integrating out the fine-grained degrees of freedom:

$$e^{-\beta U_\text{CG}(\{\mathbf{R}\})} = \int e^{-\beta H(\{\mathbf{r}\})} \prod_I \delta(\mathbf{R}_I - M_I(\{\mathbf{r}\})) \, d\{\mathbf{r}\}$$

This is a many-body potential of mean force. It's exact. It's also impossible to compute for any realistic system.

In practice, $U_\text{CG}$ is approximated by pairwise potentials (or simple tabulated functions) fitted to reproduce target properties. The fitting can target:

- **Structure**: Match the all-atom $g(r)$ between CG sites (Iterative Boltzmann Inversion, Inverse Monte Carlo)
- **Thermodynamics**: Match densities, partitioning free energies, compressibilities (MARTINI approach)
- **Forces**: Match the average force on CG sites from all-atom simulations (force matching / multiscale coarse-graining)

Each approach gives different CG potentials that reproduce different properties. No single CG model reproduces everything.

!!! tip "Key Insight"
    Coarse-graining is not just "bigger atoms." It's a systematic elimination of degrees of freedom. The exact CG potential is many-body and state-dependent (it changes with temperature and density). Any pairwise CG model is an approximation to this exact potential. The question isn't whether the approximation is perfect. It's whether it's good enough for the property you care about.

## The representability problem

Here's the deep issue. A CG model fitted to reproduce $g(r)$ at 300 K and 1 g/cm$^3$ will get the structure right at those conditions. But the pressure will be wrong. Change the temperature to 350 K? The $g(r)$ is now wrong too.

This is the **representability problem**: a pairwise CG potential can exactly reproduce at most one thermodynamic observable at one state point. You can fit the structure or the pressure, but not both. You can fit at 300 K or at 350 K, but not both with the same potential.

Why? Because the exact CG potential is many-body and state-dependent. A pairwise potential has fewer parameters than the exact potential has degrees of freedom. Something has to give.

MARTINI handles this by fitting to partitioning free energies (which capture the thermodynamics at one state point) and accepting that the structure at the bead level isn't perfectly matched. Structure-based methods (IBI, IMC) get the structure right but accept thermodynamic errors.

## When to coarse-grain

**Do CG when:**

- You need timescales or length scales beyond all-atom reach (membrane remodeling, polymer self-assembly, large-scale conformational changes)
- The property you care about is captured at the CG level (phase behavior, morphology, slow collective motions)
- You've validated that the CG model reproduces the relevant all-atom observables

**Don't CG when:**

- You need atomistic detail (hydrogen bonds, specific binding poses, electronic effects)
- Your property depends on fast dynamics that CG removes (vibrational spectra, sub-ps relaxation)
- You haven't validated the CG model for your system and conditions

!!! warning "Common Mistake"
    Using a CG model outside its parameterization domain without validation. MARTINI was parameterized against partitioning free energies at 300 K. If you run it at 200 K or at 500 K, the effective interactions are wrong because the exact CG potential is temperature-dependent. Always check that the CG model reproduces known all-atom results at your conditions before trusting it for new predictions.

## Takeaway

Coarse-graining trades resolution for speed by grouping atoms into beads with effective interactions. The exact CG potential is many-body and state-dependent; practical CG models use pairwise potentials fitted to target properties (structure, thermodynamics, or forces). No single CG model reproduces everything, so the choice of fitting target determines what the model gets right and wrong. Typical speedups are 100-1000x. Use CG when you need access to large scales and the relevant physics is captured at the bead level. Always validate against all-atom benchmarks before trusting predictions.

??? question "Check Your Understanding"
    1. You build a CG water model by matching the all-atom O-O $g(r)$. The structure looks perfect. But the density is 5% too high. Can you fix the density without breaking the $g(r)$? Why is this tricky?
    2. MARTINI represents 4 water molecules as 1 bead. This bead has no dipole moment. What properties of water can MARTINI NOT reproduce, even in principle?
    3. You run a CG lipid bilayer simulation at 300 K and get the right area per lipid. You then raise the temperature to 350 K without reparameterizing. The area per lipid is now too large. Why did the model fail?
    4. Someone says "CG simulations are faster because the timestep is larger." That's true but incomplete. What's the other reason CG is faster, and which factor typically contributes more?
    5. The exact CG potential for water at 300 K is different from the exact CG potential at 350 K. Why? What changes in the many-body potential of mean force when you change temperature?
