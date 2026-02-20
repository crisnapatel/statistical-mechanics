# Neighbors, Cutoffs, and the Fine Print of Pair Interactions

!!! info "Practical MD topic — connects to [Force Fields](force-fields.md) and [Finite Size](finite-size.md). The neighbor list is the most computationally important data structure in MD."

## The thing that actually takes all the time.

Your LAMMPS simulation has 10,000 atoms. At each timestep, you need forces on every atom. For pair interactions, that's $N(N-1)/2 \approx 50$ million pairs to check. At 1 million timesteps, that's $5 \times 10^{13}$ pair evaluations. Even at 1 ns per evaluation, that's 14 hours of wall time just for pair forces.

But most of those pairs are far apart. If two atoms are 20 Å apart and your cutoff is 10 Å, they don't interact. Why waste time computing a zero force?

The **neighbor list** is the solution. Instead of checking all $N^2$ pairs every step, you build a list of which atoms are close to each other, and only compute forces for those pairs. This reduces the cost from $O(N^2)$ to $O(N)$ per step (for short-range interactions with a cutoff). It's the single most important algorithmic optimization in MD.

## How neighbor lists work

The basic idea: at some interval (every 10-20 steps), scan all pairs and find which ones are within $r_\text{cut} + r_\text{skin}$. Store these pairs in a list. For the next 10-20 steps, only compute forces for pairs on the list.

The **skin distance** $r_\text{skin}$ is a buffer. Because atoms move between list rebuilds, a pair that was at $r_\text{cut} + 0.5$ Å might have moved to $r_\text{cut} - 0.1$ Å by the next rebuild. The skin ensures you don't miss any pairs that might come within $r_\text{cut}$ before the next rebuild.

In LAMMPS: `neighbor 2.0 bin` sets the skin distance to 2.0 Å and uses the binning algorithm. `neigh_modify every 10 delay 0 check yes` rebuilds every 10 steps, with a safety check that triggers early rebuilds if any atom has moved more than half the skin distance.

Too small a skin: you miss pairs, get wrong forces, energy conservation breaks. LAMMPS will warn you with "dangerous builds."

Too large a skin: the neighbor list contains too many non-interacting pairs, wasting time on zero-force calculations.

A skin of 2.0 Å is reasonable for most systems. For very fast-moving atoms (high temperature, small masses), increase it. For slow, dense systems, you can decrease it.

!!! warning "Common Mistake"
    Ignoring "dangerous builds" warnings. This means atoms moved far enough between rebuilds that they might have passed through the skin buffer. Your forces are potentially wrong. The fix: rebuild more often (`neigh_modify every 1`) or increase the skin distance. Never ignore this warning.

## Cutoff selection

The cutoff determines which interactions you include. Too short: you miss significant interactions and your thermodynamics are wrong. Too long: you include too many pairs and the simulation is slow.

For LJ interactions:

- $r_\text{cut} = 2.5\sigma$: the minimum reasonable cutoff. Captures ~98% of the interaction energy. Always use tail corrections (`pair_modify tail yes`) with this.
- $r_\text{cut} = 3.5\sigma$: a safer choice. Tail corrections are smaller. Standard for careful work.
- $r_\text{cut} = 5.0\sigma$ or more: overkill for most purposes, but necessary for studying structure at larger length scales.

The cost scales roughly as $r_\text{cut}^3$ (because the number of neighbors within the cutoff grows as the volume of the cutoff sphere). Doubling the cutoff increases the cost by 8x.

For Coulomb: never use a direct cutoff. Use Ewald-based methods (see [Long-Range Electrostatics](long-range-electrostatics.md)).

## The shifted potential and the shifted-force potential

When you truncate at $r_\text{cut}$, there's a discontinuity: $U(r_\text{cut}^-) \neq 0$. This means:

- **Unshifted**: $U_\text{trunc}(r) = U(r)$ for $r < r_\text{cut}$, $0$ for $r > r_\text{cut}$. There's an energy discontinuity. Forces are correct, but energy isn't continuous. This creates small impulsive kicks when atoms enter/leave the cutoff sphere.

- **Shifted potential**: $U_\text{shift}(r) = U(r) - U(r_\text{cut})$ for $r < r_\text{cut}$. Energy is continuous at the cutoff. But the force still has a discontinuity (the derivative jumps). In LAMMPS: `pair_modify shift yes`.

- **Shifted force**: Both potential and force are shifted to be continuous at $r_\text{cut}$. Smoothest behavior. Best energy conservation. But the effective potential is modified from the original, affecting thermodynamics slightly.

For production simulations: shifted potential (`pair_modify shift yes`) plus tail corrections (`pair_modify tail yes`) is a good default. The shift makes dynamics smoother, the tail corrections restore the missing long-range thermodynamics.

!!! note "MD Connection"
    In LAMMPS, key neighbor/cutoff commands:

    - `pair_style lj/cut 10.0` — LJ with 10 Å cutoff
    - `pair_modify shift yes tail yes` — shift potential, apply tail corrections
    - `neighbor 2.0 bin` — 2 Å skin, use spatial binning
    - `neigh_modify every 10 check yes` — rebuild every 10 steps with safety check
    - `comm_modify cutoff 14.0` — increase communication cutoff (needed when skin is large or for multi-body potentials)

## Special pairs: 1-2, 1-3, 1-4 exclusions

In molecular systems, bonded atoms (1-2 pairs), atoms two bonds apart (1-3 pairs), and atoms three bonds apart (1-4 pairs) are handled specially. Their nonbonded interactions are either excluded entirely or scaled down, because the bonded terms already account for their interaction.

- **1-2 excluded**: Always. The bond potential handles atoms directly bonded.
- **1-3 excluded**: Almost always. The angle potential handles atoms separated by one intermediate atom.
- **1-4 scaled**: Depends on the force field. OPLS and AMBER scale LJ and Coulomb by 0.5 for 1-4 pairs. CHARMM uses different scaling for LJ and Coulomb.

Getting the exclusions wrong (including full LJ for 1-2 pairs, or using the wrong 1-4 scaling) is a subtle bug that produces plausible but wrong results. Always check that your exclusions match the force field specification.

In LAMMPS: `special_bonds lj/coul 0.0 0.0 0.5` excludes 1-2 and 1-3, scales 1-4 by 0.5. This must match your force field.

## Takeaway

The neighbor list reduces force computation from $O(N^2)$ to $O(N)$ by only evaluating pairs within $r_\text{cut} + r_\text{skin}$. Cutoff selection balances accuracy against cost: $2.5\sigma$ minimum for LJ with tail corrections, never truncate Coulomb. The skin distance must be large enough that no pairs are missed between rebuilds ("dangerous builds" means your skin is too small). Shifted potentials improve energy conservation; tail corrections restore missing long-range thermodynamics. For molecular systems, 1-2/1-3/1-4 exclusions must match the force field specification exactly.

??? question "Check Your Understanding"
    1. Your LAMMPS log says "Dangerous builds: 47." Your simulation ran for 100,000 steps. Is this a minor issue or a simulation-breaking problem? What are your two fixes?
    2. You increase $r_\text{cut}$ from 10 Å to 15 Å. By what factor does the number of neighbor pairs (approximately) increase? By what factor does the total computational cost increase?
    3. You add `pair_modify shift yes` and the average pressure changes by 50 bar. Is the shifted or unshifted pressure more "correct"? (Trick question. Think about what "correct" means when you're using a truncated potential.)
    4. Your simulation uses OPLS-AA with `special_bonds lj 0.0 0.0 0.5`. Someone changes it to `special_bonds lj 0.0 0.0 1.0` by mistake. What kind of error does this introduce, and would you notice it easily?
    5. Why does the cost of evaluating pair forces scale as $r_\text{cut}^3$ rather than $r_\text{cut}^2$ or $r_\text{cut}$?
