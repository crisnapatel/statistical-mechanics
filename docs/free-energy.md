# Free Energy Isn't Free

!!! info "Practical MD topic — connects to [The Chemical Potential](ch07/7.5-chemical-potential.md) and [Thermodynamic Potentials](thermodynamic-potentials.md). This is where stat mech meets real computational science."

## Here's the problem nobody warns you about.

You can run an MD simulation and compute the average energy $\langle E \rangle$. Easy. Just average the values LAMMPS spits out in the log file. You can compute the average pressure $\langle P \rangle$. The temperature. The diffusion coefficient. The radial distribution function. All of these are **ensemble averages** of things you can measure from a single configuration or a trajectory.

Free energy? You can't do that.

$F = -k_B T \ln Z$, and $Z = \int e^{-\beta H} \, d\Gamma$. That integral runs over all of phase space. Your simulation doesn't explore all of phase space. It explores a tiny, thermally accessible neighborhood. The overwhelming majority of configurations have such high energy that they're never visited, but they still contribute to $Z$ (they just contribute very small Boltzmann weights). You can't sum up something you never see.

This is the fundamental difficulty. Free energy is a property of the **entire** partition function, not just the high-probability region your simulation samples. And that's what makes free energy calculations the hardest (and most error-prone) thing in computational thermodynamics.

Let's go.

## Why do we care?

Because free energy determines what actually happens. Which phase is stable? Whichever has lower $G$. Does the drug bind? Compare $\Delta G_\text{bound}$ to $\Delta G_\text{unbound}$. Is the reaction spontaneous? Check the sign of $\Delta G$. Will the crystal nucleate? Compare $\Delta G$ of the nucleus to the thermal fluctuations.

Energy tells you what's energetically favorable. Entropy tells you what's statistically favorable. Free energy combines both. $F = E - TS$. It's the quantity that actually governs equilibrium, and you can't compute it directly from a simulation. That's annoying.

!!! tip "Key Insight"
    You can compute free energy **differences** much more easily than absolute free energies. $\Delta F = F_B - F_A$ only requires sampling the region of phase space that connects states A and B, not the entire partition function. This is why almost every practical free energy method computes differences, not absolutes.

## The trick: connect what you want to what you can compute

Every free energy method works the same way at a conceptual level. You can't compute $F$ directly, but you CAN compute $\langle \partial H / \partial \lambda \rangle$ or $\langle e^{-\beta \Delta U} \rangle$ or similar averages that relate to free energy differences. The game is to design a path from state A to state B, compute something measurable along that path, and integrate.

Three methods dominate. Let's go through them.

## Method 1: Thermodynamic Integration (TI)

The idea is beautiful. Define a hybrid Hamiltonian that interpolates between your initial state ($\lambda = 0$) and your final state ($\lambda = 1$):

$$H(\lambda) = (1 - \lambda) H_A + \lambda H_B$$

At $\lambda = 0$, you have system A. At $\lambda = 1$, system B. As $\lambda$ goes from 0 to 1, the system smoothly transforms from A to B.

The free energy difference is:

$$\Delta F = F_B - F_A = \int_0^1 \left\langle \frac{\partial H}{\partial \lambda} \right\rangle_\lambda \, d\lambda$$

That's it. The integrand $\langle \partial H / \partial \lambda \rangle_\lambda$ is an ensemble average at a given $\lambda$, which is exactly the kind of thing MD can compute. Run separate simulations at $\lambda = 0.0, 0.1, 0.2, \ldots, 1.0$. At each $\lambda$, equilibrate and collect the average of $\partial H / \partial \lambda$. Plot the result. Integrate numerically (trapezoidal rule, Simpson's, Gaussian quadrature, whatever you like).

For our simple linear mixing:

$$\frac{\partial H}{\partial \lambda} = H_B - H_A$$

So at each $\lambda$, you compute $\langle H_B - H_A \rangle_\lambda$. That's the potential energy of the "B" Hamiltonian minus the "A" Hamiltonian, averaged over configurations sampled from $H(\lambda)$.

!!! warning "Common Mistake"
    Poor lambda spacing. The integrand $\langle \partial H / \partial \lambda \rangle_\lambda$ can have sharp features near $\lambda = 0$ or $\lambda = 1$ (especially when atoms are being created or destroyed). If you use evenly spaced $\lambda$ points and miss the sharp region, your integral is wrong. And here's the really insidious part: your statistical error bars on each $\langle \partial H / \partial \lambda \rangle$ can be small (good sampling at each lambda), but the numerical integration is wrong because you missed the sharp feature. **Small error bars, wrong answer.** Use Gaussian quadrature points or cluster more $\lambda$ values near the endpoints.

### Where does the "path" come from?

Here's a point that confuses people. The free energy difference $\Delta F$ is a state function. It doesn't depend on the path. So the $\lambda$-pathway you choose doesn't affect the answer (in principle). It only affects the efficiency.

A good path keeps $\langle \partial H / \partial \lambda \rangle_\lambda$ smooth and finite everywhere. A bad path has singularities (like when you turn on a LJ interaction at $\lambda = 0$ and two atoms overlap, giving $U \to \infty$). This is why people use "soft-core" potentials for alchemical transformations: the LJ repulsion is modified at small $\lambda$ to avoid the singularity.

## Method 2: Free Energy Perturbation (FEP)

Also called **Zwanzig's equation** (1954). The exact relation:

$$\Delta F = F_B - F_A = -k_B T \ln \left\langle e^{-\beta (H_B - H_A)} \right\rangle_A$$

The average is taken in ensemble A. You run a simulation of system A, and at each configuration, you also evaluate $H_B$ (without actually running B). The exponential average gives you the exact free energy difference.

Sounds perfect, right? One simulation. Exact formula. Done.

Not so fast. That exponential average is a disaster. $e^{-\beta \Delta U}$ is dominated by configurations where $H_B - H_A$ is large and negative (meaning configurations of A that happen to look like B). These are rare. Most configurations of A give $e^{-\beta \Delta U} \approx 0$, and a few give huge values. The average converges incredibly slowly.

This is the **overlap problem**. FEP only works well when the phase space of A and B overlap significantly. If they don't (if A and B are very different), you need exponentially many samples to converge the average. The error bars look fine (they shrink as $1/\sqrt{N}$), but the estimate is biased low because you haven't sampled the rare important configurations.

!!! tip "Key Insight"
    FEP is exact in principle but biased in practice. The exponential average is dominated by rare configurations, so finite sampling always underestimates the free energy difference. This bias doesn't show up in your statistical error bars. You can get a converged but wrong answer. TI doesn't have this bias (it averages a smooth function at each lambda), which is why TI is generally more robust than FEP for large perturbations.

## Method 3: Bennett Acceptance Ratio (BAR)

BAR is the statistically optimal way to combine information from simulations of both A and B. Instead of computing the free energy from A alone (forward FEP) or from B alone (reverse FEP), BAR uses data from both and solves for $\Delta F$ self-consistently.

The equation is implicit:

$$\sum_{i=1}^{n_A} \frac{1}{1 + \frac{n_A}{n_B} e^{\beta(U_A^i - U_B^i + C)}} = \sum_{j=1}^{n_B} \frac{1}{1 + \frac{n_B}{n_A} e^{\beta(U_B^j - U_A^j - C)}}$$

where $C = \Delta F$. You solve for $C$ iteratively. This is the maximum likelihood estimator for $\Delta F$ given data from both endpoints.

BAR has the lowest variance of any estimator that uses data from exactly two states. In practice, it converges faster than FEP and is more robust. The multi-state generalization (**MBAR**) extends this to any number of intermediate states and is the current gold standard for alchemical free energy calculations.

## Alchemical transformations: turning lead into gold

The most common application of these methods in biomolecular simulation is **alchemical free energy calculations**. You want to know: if I change molecule A to molecule B, what happens to the binding free energy? The solvation free energy? The relative stability?

Instead of simulating the physical transformation (which might involve breaking and forming bonds, changing topology, waiting for rare events), you use a $\lambda$ parameter to smoothly "mutate" A into B. At $\lambda = 0$, the system contains molecule A. At $\lambda = 1$, molecule B. At intermediate $\lambda$, the system contains a hybrid that's part A, part B.

This isn't physical. Molecules don't actually morph into each other. But free energy is a state function, so the path doesn't matter. The thermodynamic cycle closes:

$$\Delta\Delta G_\text{bind} = \Delta G_\text{bind}^B - \Delta G_\text{bind}^A = \Delta G_\text{alch,complex} - \Delta G_\text{alch,solvent}$$

You compute the alchemical transformation in the protein-ligand complex and in pure solvent, and the difference gives you the relative binding free energy. This is how drug discovery uses MD simulations to rank candidate molecules.

## The connection to stat mech

All of this is deeply connected to what we've been building. The free energy $F = -k_BT \ln Z$ comes from the partition function. The ensemble averages $\langle \partial H / \partial \lambda \rangle$ come from canonical sampling. The exponential average in FEP is literally the ratio of two partition functions. The fluctuation-dissipation theorem guarantees that the variance of the estimator is related to the heat capacity along the $\lambda$ path.

And the [chemical potential](ch07/7.5-chemical-potential.md) $\mu = (\partial F / \partial N)_{T,V}$ is the free energy cost of adding one particle. Widom's test-particle insertion method is just FEP applied to the case where state B has one more particle than state A. Everything connects.

!!! note "MD Connection"
    In LAMMPS, free energy calculations are not built-in (LAMMPS is an engine, not a workflow tool). For TI with LJ modifications, you'd write a loop over $\lambda$ values, each as a separate run with modified `pair_coeff`. For alchemical FEP in biomolecular systems, most people use GROMACS (which has native $\lambda$-dynamics support) or specialized wrappers around LAMMPS/OpenMM. The conceptual framework is the same regardless of the code.

## Takeaway

MD computes ensemble averages, not partition functions, and free energy lives in the partition function. Every practical method (TI, FEP, BAR) works by computing measurable averages that relate to free energy differences. TI integrates $\langle \partial H / \partial \lambda \rangle$ along a path and is robust but requires many intermediate simulations. FEP uses an exponential average and suffers from poor overlap. BAR/MBAR combine data from multiple states optimally and are the current gold standard. The cardinal sin is poor $\lambda$ spacing near endpoints: you get small error bars and wrong answers.

??? question "Check Your Understanding"
    1. Your collaborator says "I computed the Helmholtz free energy by averaging $E - TS$ from my NVT simulation." What's fundamentally wrong with this approach? (Hint: which quantity in that expression can't be obtained from a simple ensemble average?)
    2. You run TI with 11 evenly spaced $\lambda$ points. Your integrand $\langle \partial H / \partial \lambda \rangle$ is smooth from $\lambda = 0.1$ to $1.0$, but at $\lambda = 0.0$ it's three times larger than at $\lambda = 0.1$. Your error bars at each point are tiny. Is your $\Delta F$ trustworthy? What should you do?
    3. You run FEP to compute $\Delta F$ from A to B. Then you run reverse FEP (B to A). The two answers disagree by $3 k_BT$. What does this tell you about the quality of your calculation? Which answer (if either) is more likely to be correct?
    4. Someone says "free energy is a state function, so the $\lambda$ path doesn't matter." This is true in principle. Why does the path matter enormously in practice?
    5. Widom's test-particle insertion computes the chemical potential by randomly inserting a "ghost" particle and averaging $e^{-\beta \Delta U}$. This works great for ideal gases and dilute solutions. Why does it fail catastrophically for dense liquids? (Hint: think about what happens when the ghost particle overlaps with a real atom.)
