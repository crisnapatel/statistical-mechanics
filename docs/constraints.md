# Constraints and Rigid Bodies: Freezing Degrees of Freedom

!!! info "Practical MD topic — connects to [Time Integration](time-integration.md) and the equipartition theorem. Sometimes the best thing to do with a degree of freedom is remove it."

## You're paying to simulate vibrations you don't care about.

Every C-H bond in your simulation vibrates at ~$10^{14}$ Hz. That's 100 THz. One oscillation per 10 femtoseconds. To integrate that motion accurately, you need a timestep of ~1 fs. Which means: the fastest, most boring degree of freedom in your system (a quantum-mechanical vibration that has almost zero effect on any thermodynamic property) determines how fast your entire simulation can run.

What if you just froze it?

That's what constraints do. You declare: "this bond has a fixed length." The integrator enforces that constraint by applying corrective forces at each step. The fast vibration is gone. Your timestep can be larger. Your simulation is faster. And for most properties, the results are identical.

## SHAKE and RATTLE

**SHAKE** (1977) is the original constraint algorithm. After each Verlet position update, it iteratively adjusts positions to satisfy the constraint $|\mathbf{r}_i - \mathbf{r}_j| = d_0$ (fixed bond length). The iteration converges in 3-5 cycles for simple constraints.

**RATTLE** (1983) extends SHAKE to velocity Verlet. It constrains both positions and velocities, ensuring the velocities are consistent with the constraints (no velocity component along the constrained bond).

Both algorithms apply constraint forces that are perpendicular to the bond (or, more precisely, along the bond direction). These forces don't do work in the constrained direction, so they don't add or remove energy. The constrained system samples the correct distribution on the constraint surface.

In LAMMPS: `fix shake all shake 1e-4 100 0 t 1 2` constrains bonds involving atom types 1 and 2. The `1e-4` is the tolerance, `100` is the max iterations per step. For water: `fix shake all shake 1e-4 100 0 b 1 a 1` constrains bond type 1 and angle type 1 (both O-H bonds and the H-O-H angle).

## What you gain

Constraining X-H bonds (the fastest vibrations) lets you increase the timestep from 1 fs to 2 fs. That's a factor of 2 speedup for free.

Constraining all bonds (not just X-H) might let you push to 2.5-3 fs, though this is more aggressive and requires validation. Some force fields (like CHARMM) include bond flexibility in their parameterization, so constraining all bonds changes the effective potential slightly.

For rigid water models (SPC, SPC/E, TIP3P), constraining all three internal degrees of freedom (two O-H bonds + one H-O-H angle) is standard. The model was parameterized with these constraints. Using flexible water with a rigid-water force field is wrong; using rigid water with a flexible-water force field is also wrong. Match the constraint to the model.

## Rigid bodies

Constraints freeze specific internal coordinates (bond lengths, sometimes angles). **Rigid bodies** go further: they freeze all internal degrees of freedom. The molecule translates and rotates as a unit, with no internal motion at all.

This is appropriate for small, rigid molecules (water, CO$_2$, benzene) where the internal vibrations are quantum-mechanically frozen anyway and have negligible coupling to the translations and rotations.

In LAMMPS: `fix rigid` or `fix rigid/small` treats groups of atoms as rigid bodies. Each body has 6 degrees of freedom (3 translational + 3 rotational) regardless of how many atoms it contains. For water, this reduces from 9 degrees of freedom (3 atoms $\times$ 3) to 6.

!!! tip "Key Insight"
    Constraints and rigid bodies change the number of degrees of freedom, which affects how temperature is computed. If you constrain $N_c$ bonds, you have $3N - N_c$ remaining degrees of freedom. Temperature should be calculated from $\langle K \rangle = \frac{1}{2}(3N - N_c) k_B T$, not $\frac{1}{2}(3N) k_B T$. LAMMPS handles this automatically if you use `fix shake` or `fix rigid`, but if you're doing manual temperature calculations, get the count right.

## The statistical mechanics

Constraining a degree of freedom removes it from the partition function. The constrained partition function is:

$$Z_\text{constrained} = \int e^{-\beta H} \prod_k \delta(g_k(\{\mathbf{r}\})) \, d\{\mathbf{r}\}$$

where $g_k = 0$ defines the constraints. The delta functions restrict the integral to the constraint surface.

For thermodynamic properties that don't depend on the constrained coordinates (average energy of the unconstrained modes, diffusion, $g(r)$ beyond the constrained bond length), the constrained and unconstrained simulations give the same results.

For properties that DO depend on the constrained coordinates (vibrational spectra, certain entropy calculations), the results are obviously different. If you need vibrational properties, don't constrain those vibrations.

!!! note "MD Connection"
    Quick reference for LAMMPS constraints:

    - `fix shake` — constrain bonds and/or angles. Use for O-H bonds, C-H bonds, rigid water.
    - `fix rigid` — entire molecule as rigid body. Use for small rigid molecules.
    - `fix rigid/small` — optimized version for many small rigid bodies (water).
    - After applying constraints, check that `fix_modify` reports the correct number of degrees of freedom. If temperature is wrong after adding constraints, the DOF count is probably off.

## Takeaway

Constraints freeze fast vibrations (X-H bonds at ~$10^{14}$ Hz) that limit the timestep but don't affect most thermodynamic properties. SHAKE/RATTLE enforce fixed bond lengths within velocity-Verlet integration, enabling 2 fs timesteps (2x speedup). Rigid body fixes go further, freezing all internal motion. Constraints change the number of degrees of freedom, affecting temperature calculations. Match constraints to the force field: rigid water for rigid-water models, flexible water for flexible models. Don't constrain degrees of freedom you want to measure.

??? question "Check Your Understanding"
    1. You constrain all O-H bonds with SHAKE and increase $\Delta t$ from 1 fs to 2 fs. Your diffusion coefficient changes by 1%. Is this expected? What's the likely cause?
    2. You run SPC/E water with `fix rigid/small` (fully rigid) and with `fix shake` (bonds and angle constrained). Both should give the same dynamics since SPC/E is a rigid model. But the temperatures differ slightly. What went wrong?
    3. Someone uses a flexible water model (SPC/Fw) but adds `fix shake` to constrain the O-H bonds "for speed." Is this valid? What changes about the thermodynamics?
    4. After adding `fix shake`, you notice the reported temperature drops from 300 K to 285 K, even though the thermostat target is still 300 K. What happened?
    5. You want to compute the vibrational spectrum (velocity autocorrelation function) of liquid water. Can you use rigid water for this? What about SHAKE-constrained water?
