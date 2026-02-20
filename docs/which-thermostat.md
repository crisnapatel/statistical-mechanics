# Which Thermostat? Which Barostat?

!!! info "LiveCoMS Best Practices for Foundations in Molecular Simulations, Section 4.4–4.5"

## Your thermostat is not innocent.

Here's something that took me way too long to internalize. You set up your LAMMPS simulation. Pick a thermostat. Set the target temperature. Run production. Compute your observable. And you never question whether the thermostat itself changed the answer.

It did. Maybe a little. Maybe a lot. Depends on what you're computing and which thermostat you picked.

Every thermostat works by modifying Newton's equations of motion. The whole point of MD is to integrate those equations faithfully. And then you bolt on a thermostat that deliberately messes with them. That's the fundamental tension: you *need* to control temperature (because real experiments happen at constant $T$, not constant $E$), but every method for doing so introduces artifacts. The question isn't "does my thermostat affect my results?" It's "how much, and do I care?"

This page is a decision tree. By the end, you'll know which thermostat to use, which barostat to pair it with, and (most importantly) which combinations to avoid. Let's go.

## Why you need a thermostat at all

In a perfect NVE simulation, energy is conserved. The system explores the microcanonical ensemble. Temperature fluctuates naturally (we covered that in the [energy fluctuations section](ch07/7.2-energy-fluctuations.md)).

But experiments don't happen at constant energy. They happen at constant temperature. Your sample sits on a bench, surrounded by air, in thermal contact with its environment. That's the canonical ensemble. To sample it in MD, you need something that plays the role of that thermal reservoir. That's what a thermostat does.

There's also a practical reason: numerical integration isn't perfect. Round-off errors, force truncation, and constraint algorithms cause slow energy drift in NVE. A thermostat absorbs that drift. Without one, a very long NVE simulation can slowly heat up or cool down.

!!! tip "Key Insight"
    A thermostat couples your system to a heat bath. It adds or removes kinetic energy to maintain a target temperature. The question is *how* it does this, because different methods produce different artifacts.

## The thermostat zoo

There are seven or eight thermostats in common use. Most of them you should never touch. Here's the honest breakdown.

### Velocity rescaling (simple)

The simplest possible thermostat. After each integration step, multiply all velocities by a factor that makes the instantaneous kinetic energy match the target temperature exactly. No fluctuations. The instantaneous temperature is *always* the target.

The problem? That's the isokinetic ensemble, not the canonical ensemble. In the canonical ensemble, kinetic energy *should* fluctuate (we derived exactly how much in [Section 7.2](ch07/7.2-energy-fluctuations.md)). Killing those fluctuations gives wrong thermodynamic properties. And it doesn't even sample the isokinetic ensemble correctly except for infinitesimal timesteps.

**Verdict**: Not for production. Can be useful for the first few hundred steps of equilibration to quickly bring a system from a far-off temperature to the ballpark, then switch to a proper thermostat.

### Berendsen

An improvement on simple rescaling. Instead of snapping the temperature to the target instantly, it relaxes toward it exponentially with a user-specified time constant $\tau$:

$$\frac{dT}{dt} = \frac{T_\text{target} - T}{\tau}$$

Smooth. Stable. Fast equilibration. Sounds great, right?

Here's the catch. The Berendsen thermostat does not sample any well-defined statistical ensemble. Not canonical. Not isokinetic. Not anything with a name. It suppresses kinetic energy fluctuations below their correct canonical values. Which means properties that depend on fluctuations (heat capacity, compressibility, anything computed via fluctuation formulas) will be systematically wrong.

**Verdict**: Fine for equilibration (it's stable and fast at bringing the system to the target $T$). Never use it for production. The ensemble it samples is undefined, and fluctuation-dependent properties are wrong.

!!! warning "Common Mistake"
    Berendsen is the default thermostat in some older simulation packages, and many legacy scripts use it for production runs. If you inherited a simulation setup from someone else, check this first. Berendsen production data cannot be trusted for any fluctuation-derived property.

### Bussi-Donadio-Parrinello (velocity rescaling done right)

Also called "canonical sampling through velocity rescaling" or CSVR. This is what Berendsen should have been. Instead of rescaling to the target kinetic energy, it rescales to a kinetic energy drawn stochastically from the correct canonical distribution. One small tweak, and suddenly the thermostat samples the canonical ensemble exactly.

It has the same user-friendly time constant as Berendsen (so equilibration is fast), but with correct fluctuations. Structural properties are exact. Dynamical properties are mostly preserved for reasonable coupling strengths, though they're technically modified (it's still rescaling velocities).

In LAMMPS: `fix csvr` or `fix temp/csvr`.

**Verdict**: Excellent general-purpose thermostat. The LiveCoMS paper recommends it as the default choice for most applications. If you're not sure what to use, use this.

### Andersen

Completely different approach. At random intervals, pick a random particle and replace its velocity with a new one drawn from the Maxwell-Boltzmann distribution. The particle "collides" with the heat bath. This rigorously samples the canonical ensemble.

The problem? Those random velocity reassignments destroy velocity correlations. Diffusion coefficients, viscosities, any dynamical property: garbage. The dynamics between collisions are Newtonian, but the collisions themselves are completely artificial.

**Verdict**: Correct canonical sampling. Great for structural properties (RDFs, free energies). Terrible for dynamics. Never use it when computing transport properties.

### Langevin

We already met this one on the [Brownian motion page](brownian-motion.md). It adds friction ($-\gamma v$) and random kicks ($\xi(t)$) to the equations of motion:

$$m\dot{v} = F_\text{interaction} - \frac{m}{\tau_\text{damp}} v + F_\text{random}$$

The friction and noise are linked by the fluctuation-dissipation theorem, so the canonical ensemble is correctly sampled. The damping parameter $\tau_\text{damp}$ controls the coupling strength.

Same problem as Andersen: the stochastic forces destroy natural velocity correlations. Diffusion coefficients are artificially reduced. Viscosity is artificially increased. For implicit solvent simulations this is actually the point (you're modeling solvent friction). For explicit solvent, it's contamination.

In LAMMPS: `fix langevin` (adds the stochastic forces; pair it with `fix nve` for the integration).

**Verdict**: Correct ensemble. Useful for equilibration and for implicit-solvent simulations. Don't use it for computing transport properties in explicit-solvent systems.

### Nose-Hoover

The workhorse. The most widely used thermostat in production MD.

Instead of stochastic collisions or velocity rescaling, Nose-Hoover adds a single extra degree of freedom to the equations of motion. This fictional "heat bath variable" $\eta$ acts as a feedback controller. If the system is too hot, $\eta$ grows, draining kinetic energy. If it's too cold, $\eta$ shrinks, injecting energy. The coupling strength is controlled by a time constant $\tau$.

The equations of motion become:

$$m\dot{v}_i = F_i - \frac{p_\eta}{Q} m v_i$$

where $Q$ is the "mass" of the thermostat (related to $\tau$) and $p_\eta$ is its momentum. The extended system (real particles + thermostat variable) is deterministic, time-reversible, and samples the canonical ensemble.

The key advantage: because there are no stochastic forces, dynamical properties are largely preserved. For reasonable coupling strengths ($\tau \geq 100$ timesteps), diffusion coefficients and viscosities are statistically indistinguishable from NVE results.

In LAMMPS: `fix nvt` (which is Nose-Hoover under the hood). The coupling time is set via `Tdamp`:

```
fix 1 all nvt temp 300.0 300.0 $(100.0*dt)
```

That `$(100.0*dt)` sets $\tau = 100$ timesteps, which is LAMMPS's recommendation for most systems.

One caveat: for small systems or weakly coupled subsystems, a single Nose-Hoover thermostat can fail to be ergodic (it oscillates instead of thermalizing). The fix is **Nose-Hoover chains**, where multiple thermostats are chained together. Most modern implementations (including LAMMPS) use chains by default.

**Verdict**: The standard choice for production MD. Deterministic, time-reversible, correct ensemble, minimal dynamical artifacts. Use this unless you have a specific reason not to.

!!! note "MD Connection"
    In LAMMPS, `fix nvt` is Nose-Hoover with chains. `Tdamp` should be ~100 timesteps (e.g., 0.1 ps for a 1 fs timestep). Too small: temperature oscillates wildly. Too large: equilibration takes forever. The `$(100.0*dt)` syntax ensures the coupling adapts if you change the timestep.

## The summary table

Here's what actually matters. Can you trust the thermostat to give you correct structural properties (RDF, coordination numbers, free energies)? Can you trust it for dynamical properties (diffusion, viscosity, correlation functions)?

| Thermostat | Ensemble | Structural properties | Dynamical properties |
|:---|:---|:---:|:---:|
| None (NVE) | Microcanonical | Correct | Correct |
| Simple velocity rescaling | Isokinetic (wrong) | Wrong | Wrong |
| Berendsen | Undefined | Wrong | Wrong |
| Bussi (CSVR) | Canonical | Correct | Mostly correct |
| Andersen | Canonical | Correct | Wrong |
| Langevin | Canonical | Correct | Wrong |
| Nose-Hoover | Canonical | Correct | Mostly correct |

"Mostly correct" means: for reasonable coupling strengths, dynamical properties are indistinguishable from NVE within statistical noise. Push the coupling too tight (small $\tau$), and you'll see artifacts.

The pattern is clear. If your thermostat randomizes velocities (Andersen, Langevin), dynamics are destroyed. If it modifies the equations of motion smoothly (Nose-Hoover, Bussi), dynamics are mostly preserved.

## The decision tree

**"What should I use?"**

**For equilibration**: Berendsen or Bussi. Both bring the system to the target temperature quickly and stably. Berendsen is slightly more robust for systems that start far from equilibrium. But since Bussi works just as well and also gives the right ensemble, there's no reason not to just use Bussi for everything.

**For production (structural properties only)**: Bussi, Nose-Hoover, or even Andersen/Langevin. All sample the correct canonical ensemble.

**For production (dynamical properties)**: Nose-Hoover or Bussi, with reasonable coupling ($\tau \geq 100$ timesteps). Or better yet: run equilibration with a thermostat, then switch to NVE for production. NVE has zero thermostat artifacts. This is the gold standard for transport properties.

**For implicit solvent**: Langevin. That's what it's designed for. The friction and noise model the missing solvent.

**If you don't know what you're computing yet**: Nose-Hoover. It's safe for both structural and dynamical properties.

## Barostats: the pressure side

Everything we said about thermostats has an analog for pressure control. Barostats maintain a target pressure by adjusting the simulation box volume. And just like thermostats, the *how* matters.

A barostat controls pressure, not temperature. If you want constant $T$ and $P$ (the NPT ensemble), you need both a thermostat and a barostat. A barostat alone gives you the NPH (constant enthalpy, constant pressure) ensemble.

### Berendsen barostat

Same philosophy as the Berendsen thermostat. Exponentially relaxes toward the target pressure. Same problem: the ensemble it samples is undefined. Pressure fluctuations are suppressed below their correct values.

**Verdict**: Fine for equilibration (stable, fast convergence). Never for production.

### Parrinello-Rahman

Extended-system barostat analogous to Nose-Hoover for temperature. Adds the box dimensions as dynamical variables with a fictitious "mass" (controlled by a damping parameter `Pdamp`). Samples the correct NPT ensemble. Supports anisotropic pressure coupling, which matters for solids and membranes where the box shape can change.

**Verdict**: Good for production. Pair with Nose-Hoover thermostat for NPT.

### MTTK (Martyna-Tuckerman-Tobias-Klein)

An improvement over Parrinello-Rahman that correctly handles small systems. The original Parrinello-Rahman equations of motion are only exact in the large-system limit. MTTK fixes this. In LAMMPS, `fix npt` uses the MTTK formulation.

**Verdict**: The default recommendation. LAMMPS's `fix npt` implements this.

In LAMMPS, the barostat damping parameter `Pdamp` should be ~1000 timesteps (e.g., 1.0 ps for a 1 fs timestep):

```
fix 1 all npt temp 300.0 300.0 $(100.0*dt) iso 1.0 1.0 $(1000.0*dt)
```

!!! warning "Common Mistake"
    Never use a barostat during production runs for computing transport properties. The box volume changes shift all atomic positions, contaminating the dynamics completely. The protocol is: NPT equilibration (to get the right density), then NVT or NVE production at fixed volume.

## The full protocol

Putting thermostats and barostats together, here's what a well-designed simulation workflow looks like:

**Step 1: Energy minimization.** Remove bad contacts and overlaps. No dynamics yet.

**Step 2: NVT equilibration.** Thermostat (Bussi or Nose-Hoover) at the target temperature. Fixed box volume. Let the system relax.

**Step 3: NPT equilibration.** Add the barostat. Let the density equilibrate to the target pressure. Monitor the box dimensions until they stabilize.

**Step 4: Production.** This depends on what you're computing:

- **Structural properties** (RDF, coordination numbers, free energies): NPT production is fine. Use Nose-Hoover + MTTK (LAMMPS `fix npt`).
- **Transport properties** (diffusion, viscosity, thermal conductivity): Fix the box at the average NPT volume. Run NVT with Nose-Hoover ($\tau \geq 100$ timesteps), or better yet, switch to NVE. This is the NPT → NVT → NVE cascade from the [Brownian motion page](brownian-motion.md).

!!! tip "Key Insight"
    The cascade (NVT → NPT → NVT/NVE) separates concerns. NVT equilibrates the temperature. NPT equilibrates the density. And the final NVT or NVE production runs at fixed volume with minimal (or zero) thermostat interference. Each step does one job.

## Takeaway

Not all thermostats are created equal. Berendsen and simple velocity rescaling don't sample any correct ensemble, so never use them for production. Andersen and Langevin give the right ensemble but destroy dynamics. Nose-Hoover and Bussi (CSVR) give the right ensemble with minimal dynamical artifacts. For most work, Nose-Hoover (`fix nvt`) with $\tau \approx 100$ timesteps is the safe default. For transport properties, the gold standard is NVE production after equilibrating with NPT → NVT. And always pair your thermostat with the right barostat: MTTK/Parrinello-Rahman for production, Berendsen only for early equilibration.

??? question "Check Your Understanding"
    1. You run production with Berendsen and compute $C_V$ from the energy fluctuation formula ($C_V = \sigma_E^2 / k_BT^2$). Your value comes out suspiciously low. Is that a coincidence, or is Berendsen systematically doing this to you?
    2. You run production with the Andersen thermostat and compute two things: the RDF and the Green-Kubo diffusion coefficient. One of them is trustworthy. Which one, and why is the other one garbage?
    3. Someone computes a diffusion coefficient from an NPT production run and gets a weird number. You tell them the barostat ruined it. They ask "how can box volume changes mess up diffusion?" Give them a concrete answer.
    4. "Why not just run NVE from the start and skip the thermostat cascade entirely?" Your labmate asks this. What goes wrong if you skip NPT equilibration and NVT equilibration and jump straight to NVE?
