# Non-Equilibrium MD: Driving Your System Out of Equilibrium

!!! info "Practical MD topic — connects to [Brownian Motion](brownian-motion.md) and transport properties. Equilibrium MD waits for fluctuations. NEMD creates them."

## There's a faster way to measure viscosity.

Equilibrium MD computes transport properties from fluctuations. The Green-Kubo relation for viscosity involves the stress-stress autocorrelation function, which is noisy, slow to converge, and requires long simulations. The Einstein relation for diffusion involves the mean-squared displacement, which converges faster but still needs many correlation times.

Non-equilibrium MD (NEMD) takes a different approach. Instead of waiting for the system to spontaneously fluctuate, you *drive* it. Apply a shear gradient. Measure the resulting momentum flux. Viscosity = stress / strain rate. Done. The signal is strong (you imposed it), the noise is controlled (by the driving strength), and convergence is typically much faster.

The catch: you've driven the system out of equilibrium. The distribution is no longer Boltzmann. Linear response theory says the near-equilibrium properties should match, but "near" is doing a lot of work in that sentence. Push too hard, and you're measuring the nonlinear response, which isn't what you wanted.

## The basic idea

In equilibrium, transport coefficients come from the fluctuation-dissipation theorem. The dissipative response (viscosity, conductivity, diffusivity) is related to equilibrium fluctuations. That's Green-Kubo.

In NEMD, you apply the conjugate thermodynamic force directly:

| Transport property | Equilibrium (Green-Kubo) | NEMD driving force |
|---|---|---|
| Viscosity $\eta$ | Stress autocorrelation | Imposed shear rate |
| Thermal conductivity $\kappa$ | Heat flux autocorrelation | Imposed temperature gradient |
| Diffusion $D$ | MSD or velocity autocorrelation | Concentration gradient (or color field) |

The NEMD approach measures the steady-state response to the applied perturbation. In linear response (small perturbation), the result equals the equilibrium value. The advantage: the signal-to-noise ratio is orders of magnitude better than waiting for spontaneous fluctuations.

## Shear viscosity: the workhorse application

The most common NEMD method for viscosity is the **Müller-Plathe** (reverse NEMD) approach:

1. Divide the box into slabs along $z$.
2. Periodically swap the $x$-momentum of the fastest atom in the top slab with the slowest atom in the bottom slab.
3. This imposes a momentum flux (shear stress) without adding energy.
4. The system responds by developing a velocity gradient (shear rate).
5. Viscosity = imposed stress / measured strain rate.

The beauty: the momentum transfer is exact (you know exactly how much momentum you moved), so the stress is precise. The velocity profile is the noisy part, but it's an average over all atoms in each slab, which converges quickly.

In LAMMPS: `fix viscosity` implements the Müller-Plathe method. You specify which direction to swap momentum and how often.

An alternative: the **SLLOD** equations of motion with Lees-Edwards periodic boundaries. This imposes a uniform shear rate throughout the box (no slabs, no velocity profile). Theoretically cleaner, but more complex to implement. Available in LAMMPS as `fix deform` with `fix nvt/sllod`.

!!! tip "Key Insight"
    NEMD measures the same transport coefficients as Green-Kubo, just from a different route. In the linear response regime (small perturbation), both give the same answer. The advantage of NEMD is better signal-to-noise. The danger is pushing too hard: if the perturbation is large enough to take the system into the nonlinear regime, you're measuring something different from the equilibrium transport coefficient.

## The linear response check

How do you know you're in the linear regime? Run NEMD at several driving strengths. Plot the transport coefficient vs. driving force. If it's constant (flat), you're linear. If it changes with driving strength, you're in the nonlinear regime. Extrapolate to zero driving force to get the equilibrium value.

For viscosity: run at several shear rates $\dot{\gamma}$. If $\eta(\dot{\gamma})$ decreases with increasing $\dot{\gamma}$ (shear thinning), you're too aggressive. Typical safe shear rates for simple liquids: $\dot{\gamma} < 10^{10}$ s$^{-1}$. This sounds enormous, but in the molecular world, it's mild.

## Thermal conductivity

Apply a temperature gradient (e.g., hot slab at $z = 0$, cold slab at $z = L/2$). Measure the heat flux. $\kappa = J_q / (dT/dz)$.

In LAMMPS: `fix heat` or `fix ehex` applies controlled energy addition/removal to specific regions. The steady-state temperature profile gives the gradient. The imposed heat flux gives $J_q$.

Alternatively: the Müller-Plathe method for thermal conductivity swaps the kinetic energy of atoms between slabs instead of momentum.

!!! note "MD Connection"
    Key LAMMPS commands for NEMD:

    - `fix viscosity` — Müller-Plathe reverse NEMD for shear viscosity
    - `fix deform` + `fix nvt/sllod` — SLLOD algorithm with Lees-Edwards boundaries
    - `fix heat` — apply heat flux for thermal conductivity
    - `fix ehex` — enhanced heat exchange method (conserves energy better)
    - `compute temp/profile` — remove streaming velocity when computing temperature in a sheared system

## When to use NEMD vs. Green-Kubo

**Use NEMD when:**

- You need viscosity or thermal conductivity and Green-Kubo is too noisy
- You want to study nonlinear response (shear thinning, non-Newtonian behavior)
- Your system is large enough that slab-based methods have sufficient resolution

**Use Green-Kubo when:**

- You need diffusion (NEMD for diffusion is awkward)
- Your system is small (slab methods need many atoms per slab)
- You want all transport coefficients from one equilibrium simulation

!!! warning "Common Mistake"
    Not removing the streaming velocity when computing temperature in a sheared NEMD simulation. If the system has a velocity gradient (from the imposed shear), the kinetic energy includes both thermal motion and streaming motion. Temperature should only include the thermal part. Use `compute temp/profile` in LAMMPS, not the default temperature compute.

## Takeaway

NEMD drives the system out of equilibrium by applying thermodynamic forces (shear rate, temperature gradient) and measuring the steady-state response. The signal-to-noise ratio is much better than Green-Kubo for viscosity and thermal conductivity. The Müller-Plathe method (reverse NEMD) imposes a known stress and measures the resulting strain rate. Always verify linear response by testing multiple driving strengths. Remove streaming velocity when computing temperature in sheared systems. NEMD and Green-Kubo give the same transport coefficients in the linear regime; they're complementary tools, not alternatives.

??? question "Check Your Understanding"
    1. You run Müller-Plathe NEMD for viscosity at three shear rates: $\dot{\gamma} = 10^9, 10^{10}, 10^{11}$ s$^{-1}$. The measured viscosities are 0.92, 0.85, and 0.61 mPa·s. Which value is closest to the equilibrium viscosity? What's happening at the highest shear rate?
    2. Your NEMD thermal conductivity simulation has hot and cold slabs separated by $L/2 = 5$ nm. The temperature difference between them is 200 K. Is this gradient ($4 \times 10^{10}$ K/m) "small" enough for linear response? How would you check?
    3. Why does the Müller-Plathe method swap atoms rather than just adding/removing momentum? What conservation law is being respected?
    4. You compute temperature in a sheared NEMD simulation without removing streaming velocity. The apparent temperature is 340 K. The thermostat target is 300 K. Where did the extra 40 K come from?
    5. Someone says "I'll just use NEMD for everything, it's faster." Why might you still prefer Green-Kubo for diffusion?
