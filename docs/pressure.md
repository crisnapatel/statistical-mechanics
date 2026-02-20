# Pressure in a Box: Virial, Stress Tensor, and Why Pressure Is Harder Than You Think

!!! info "Practical MD topic — connects to [Density Fluctuations](ch07/7.4-density-fluctuations.md) and [Finite Size](finite-size.md). Pressure is the observable that surprises everyone."

## Here's something that will make you uncomfortable.

Open your LAMMPS log file. Look at the pressure column. Watch it bounce between $-2000$ and $+3000$ bar. Every single timestep. For a system that's supposedly at 1 atm.

Not a typo. Not a bug. That's real. The instantaneous pressure in an MD simulation fluctuates by thousands of atmospheres, even when the average is near zero. And if you don't understand why, you'll either (a) think your simulation is broken, or (b) report a pressure with way too many significant digits.

Pressure in a small box is wild. Let me show you why.

## The virial equation

In an MD simulation, pressure comes from two contributions: kinetic (atoms moving) and configurational (atoms pushing on each other).

$$P = \frac{1}{V}\left[ Nk_BT + \frac{1}{3}\sum_{i<j} \mathbf{r}_{ij} \cdot \mathbf{F}_{ij} \right]$$

The first term is the ideal gas pressure. Atoms moving around, bouncing off the (virtual) walls. This is always positive.

The second term is the **virial**. It sums over all pairs: $\mathbf{r}_{ij}$ is the separation vector, $\mathbf{F}_{ij}$ is the force between atoms $i$ and $j$. For repulsive forces ($\mathbf{F}$ points along $\mathbf{r}$), the virial is positive, adding to the pressure. For attractive forces ($\mathbf{F}$ points opposite to $\mathbf{r}$), the virial is negative, reducing the pressure.

In a dense liquid, the repulsive and attractive contributions nearly cancel. You're left with a small number (maybe 1 atm = 0.0001 GPa) that's the difference of two large numbers (maybe ±1 GPa each). This is why pressure fluctuates so wildly: small fluctuations in the positions produce large changes in the near-cancellation.

!!! tip "Key Insight"
    Pressure in a liquid is the small difference of two large, nearly canceling terms: the ideal gas kinetic pressure (always positive) and the virial from interactions (mostly negative for dense liquids). This near-cancellation means the instantaneous pressure is extremely noisy. Relative fluctuations of 1000% are normal. Compare this to energy, where fluctuations are typically < 1%.

## Why pressure fluctuates so much

Let's put numbers on it. For liquid argon at 100 K with 256 atoms in a box of volume $V = (23.3)^3$ Å$^3$:

- Ideal gas pressure: $Nk_BT / V \approx 2800$ bar
- Average virial contribution: $\approx -2800$ bar (attractive interactions)
- Net average pressure: $\approx 0$ bar (for a liquid at its equilibrium density)

But the virial fluctuates. Hard. Each pair interaction contributes to the sum, and the fluctuations scale as $1/\sqrt{N_\text{pairs}}$. For 256 atoms, that's ~$1/\sqrt{32000} \approx 0.5\%$ relative fluctuation in the virial, which translates to ~15 bar fluctuation in the net pressure. In practice, it's even worse because the pairs are correlated.

The result: instantaneous pressure bounces around by hundreds to thousands of bar. The *average* pressure converges, but slowly. You need long trajectories (many correlation times) to get a precise mean pressure.

!!! warning "Common Mistake"
    Reporting pressure to four digits after a 1 ns simulation. Pressure converges much slower than energy or temperature because of the enormous fluctuations. Always compute the standard error of the mean (accounting for correlation time!) before reporting. A typical 256-atom argon simulation needs tens of nanoseconds to converge the mean pressure to ±10 bar.

## The stress tensor

Pressure is a scalar. But the full mechanical state is described by the **stress tensor**, a $3 \times 3$ symmetric matrix:

$$\sigma_{\alpha\beta} = \frac{1}{V}\left[ \sum_i m_i v_{i\alpha} v_{i\beta} + \frac{1}{2}\sum_{i \neq j} r_{ij\alpha} F_{ij\beta} \right]$$

The diagonal elements ($\sigma_{xx}$, $\sigma_{yy}$, $\sigma_{zz}$) are the normal stresses. The pressure is their average:

$$P = \frac{1}{3}(\sigma_{xx} + \sigma_{yy} + \sigma_{zz})$$

The off-diagonal elements ($\sigma_{xy}$, $\sigma_{xz}$, $\sigma_{yz}$) are the shear stresses. In an isotropic liquid at equilibrium, the average shear stress is zero. But instantaneously, all six independent components fluctuate.

The stress tensor matters when:

- **Computing viscosity**: The Green-Kubo relation uses the autocorrelation of the off-diagonal stress: $\eta = \frac{V}{k_BT}\int_0^\infty \langle \sigma_{xy}(0) \sigma_{xy}(t) \rangle \, dt$
- **Studying anisotropic systems**: Membranes, interfaces, crystals under load. The surface tension of a planar interface is $\gamma = L_z [\langle P_{zz} \rangle - \frac{1}{2}(\langle P_{xx} \rangle + \langle P_{yy} \rangle)]$
- **Detecting problems**: If $\sigma_{xx} \neq \sigma_{yy} \neq \sigma_{zz}$ in a system that should be isotropic, something is wrong (usually insufficient equilibration or too few atoms)

!!! note "MD Connection"
    In LAMMPS: `compute pressure` gives all six stress tensor components. The `thermo_style` keyword `press` reports the scalar pressure. For the full tensor: `thermo_style custom step pxx pyy pzz pxy pxz pyz`. The surface tension of an interface along $z$: `variable gamma equal lz*(pzz-0.5*(pxx+pyy))`.

## Tail corrections for pressure

We covered this on the [finite size page](finite-size.md), but it bears repeating because the effect on pressure is enormous.

When you truncate the LJ potential at $r_\text{cut}$, you miss the attractive interactions beyond the cutoff. For energy, the correction is a few percent. For pressure, it can be 10-20% or more, because pressure involves the derivative of the potential (which amplifies the cutoff artifact).

The tail correction for LJ pressure:

$$P_\text{tail} = \frac{16\pi \rho^2 \epsilon \sigma^3}{3} \left[ \frac{2}{3}\left(\frac{\sigma}{r_\text{cut}}\right)^9 - \left(\frac{\sigma}{r_\text{cut}}\right)^3 \right]$$

For argon at liquid density with $r_\text{cut} = 2.5\sigma$: $P_\text{tail} \approx -200$ bar. That's the difference between your simulation showing $P = +200$ bar (which looks wrong for a liquid at equilibrium) and the corrected $P \approx 0$ bar (which is right).

`pair_modify tail yes`. Always. For homogeneous systems.

## Pressure and the NPT ensemble

In an NPT simulation (constant temperature and pressure), the barostat adjusts the box volume to maintain the target pressure. The instantaneous pressure still fluctuates wildly, but the *running average* is maintained at the target.

What matters is: the average box volume converges to the equilibrium volume at that temperature and pressure. The density (which is $N/V$) is the physical observable, not the instantaneous pressure.

For computing transport properties, you take the average volume from NPT, then switch to NVT or NVE at that fixed volume (as discussed on the [thermostat page](which-thermostat.md)). This avoids the volume fluctuations contaminating the dynamics.

## Takeaway

Pressure in MD is the small difference of two large, nearly canceling terms (kinetic + virial), which is why instantaneous pressure fluctuates by thousands of bar even when the average is near zero. Converging the mean pressure requires long simulations and proper error analysis with correlation time correction. The stress tensor has six independent components; the off-diagonal elements give shear stresses needed for viscosity and surface tension. Tail corrections (`pair_modify tail yes`) can shift the pressure by hundreds of bar and are always worth applying for homogeneous systems. In NPT, the density (average volume) is the physical observable, not the pressure itself.

??? question "Check Your Understanding"
    1. Your LAMMPS log shows instantaneous pressure bouncing between $-1500$ and $+2000$ bar. Your target pressure is 1 atm (about 1 bar). Is the simulation broken?
    2. You compute the average pressure from a 10 ns NVT simulation and get $P = 47 \pm 12$ bar (with proper error bars). Should you conclude the system is at positive pressure, or could it be consistent with zero?
    3. You're computing the surface tension of a liquid-vapor interface using $\gamma = L_z [P_{zz} - \frac{1}{2}(P_{xx} + P_{yy})]$. Why does this formula involve the *difference* of stress tensor components? What happens to $\gamma$ if the interface is perfectly flat vs. curved?
    4. You add `pair_modify tail yes` and the pressure drops from +250 bar to $-50$ bar. Your labmate says "that can't be right, you just shifted it by 300 bar." Is 300 bar a reasonable tail correction? What determines its magnitude?
    5. Why does pressure converge so much slower than temperature in an MD simulation? (Hint: think about what each quantity averages over and how much cancellation is involved.)
