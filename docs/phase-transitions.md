# Phase Transitions in a Box

!!! info "Practical MD topic — connects to [Density Fluctuations](ch07/7.4-density-fluctuations.md) and [Equivalence of Ensembles](ch07/7.6-equivalence.md). Phase transitions are where everything you thought you knew about finite systems gets tested."

## Your simulation can't melt properly. And that's not a bug.

Here's the thing about phase transitions that textbooks gloss over: they're defined in the thermodynamic limit ($N \to \infty$). Your simulation has 256, maybe 10,000, maybe 100,000 atoms. That's not infinity. And for phase transitions, the difference between "large" and "infinite" matters enormously.

In the thermodynamic limit, a first-order phase transition happens at a sharp temperature $T_m$. Below $T_m$, the system is solid. Above, liquid. The transition is discontinuous. There's a latent heat. The density jumps.

In your simulation box? None of that is sharp. The transition is smeared over a range of temperatures. The "melting point" shifts with system size. The latent heat is hard to measure. And depending on how you heat the system, you might overshoot $T_m$ by 20% before anything happens (superheating).

Understanding why requires connecting stat mech concepts (free energy barriers, fluctuations, nucleation) to the practical reality of what your MD simulation can and can't do.

Let's go.

## First-order transitions: the nucleation problem

Melting, freezing, boiling, condensation. These are first-order transitions. In the thermodynamic limit, the system switches discontinuously from one phase to another at a well-defined temperature and pressure.

In a finite box, the transition requires **nucleation**: a small region of the new phase has to form spontaneously within the old phase. This nucleus has to be large enough to overcome the surface energy penalty. The free energy barrier for forming a critical nucleus scales as:

$$\Delta G^* \propto \frac{\gamma^3}{(\Delta \mu)^2}$$

where $\gamma$ is the surface tension and $\Delta \mu$ is the chemical potential difference between phases (which is zero at the transition point and grows as you move away from it).

At the exact transition temperature, $\Delta \mu = 0$, and the nucleation barrier is infinite. The system never transitions. You have to superheat (or supercool) to drive $\Delta \mu$ large enough that nucleation happens on your simulation timescale.

This is why:

- Simulated melting points are always higher than the true $T_m$ if you heat a solid (superheating)
- Simulated freezing points are always lower if you cool a liquid (supercooling)
- The hysteresis depends on system size, heating/cooling rate, and luck

!!! warning "Common Mistake"
    Reporting the temperature where your simulation melts as "the melting point." It's not. It's the superheating limit, which can be 10-20% above the actual $T_m$. To get the true melting point, you need coexistence methods (two-phase simulations) or free energy calculations. Just heating a crystal until it melts gives you the wrong number.

## Two-phase simulations

The most reliable way to find a first-order transition temperature in simulation: set up a box with both phases present. Put a crystal slab in contact with liquid. Run NVE or NPT at various temperatures. If the crystal grows, you're below $T_m$. If it shrinks, you're above. The temperature where neither phase grows is $T_m$.

This works because you've eliminated the nucleation barrier. The interface already exists. The system just needs to decide which way to grow. The precision is limited by your ability to detect small growth rates, but with patience you can bracket $T_m$ to within a few Kelvin.

The method requires a large-enough box that both phases can coexist without their interfaces interacting across the periodic boundaries. In practice, that's at least a few thousand atoms.

## Second-order transitions: finite-size scaling

Second-order (continuous) transitions are different. No nucleation barrier. No latent heat. Instead, the correlation length $\xi$ diverges as $T \to T_c$:

$$\xi \sim |T - T_c|^{-\nu}$$

In your simulation, $\xi$ can't exceed $L$ (the box length). When $\xi \sim L$, the system "feels" the finite box, and the transition gets rounded and shifted. The apparent $T_c$ differs from the true $T_c$ by an amount that scales as:

$$T_c(L) - T_c(\infty) \sim L^{-1/\nu}$$

This is the basis of **finite-size scaling**: run simulations at multiple system sizes $L$, measure the apparent $T_c(L)$, and extrapolate to $L \to \infty$. The scaling exponent $\nu$ tells you the universality class of the transition.

This is where simulation and stat mech theory come together beautifully. The finite-size effects that seem like a nuisance are actually a tool: they encode the critical exponents through their system-size dependence.

## Ensemble matters

Here's where ensemble choice becomes critical. Near a first-order transition, the NVT ensemble at the transition temperature shows **phase coexistence**: configurations that are partly liquid, partly solid (or partly liquid, partly gas). The energy histogram has two peaks (one for each phase) separated by a valley (the interfacial configurations).

The NPT ensemble is worse. Near a first-order transition, the system can jump between phases abruptly. The volume (and energy) shows bimodal distributions. The simulation may oscillate between phases or get stuck in one.

The NVE ensemble avoids these issues entirely (there's no thermostat to fight), but you need to choose the energy carefully to land in the two-phase region.

For studying phase transitions, people often use specialized techniques: Wang-Landau sampling, multicanonical methods, or expanded ensembles that specifically target the two-phase region. Standard MD just isn't designed for this.

!!! tip "Key Insight"
    Phase transitions are where ensemble equivalence breaks down most dramatically for finite systems. In the thermodynamic limit, NVT and NPT give the same phase diagram. In a finite box, NVT shows stable two-phase coexistence while NPT shows phase flipping. Choose your ensemble based on what physics you want to see.

## Takeaway

Phase transitions in simulation are fundamentally affected by finite size. First-order transitions require nucleation, which leads to superheating/supercooling artifacts. The "melting point" from heating a crystal is not the true melting point. Two-phase coexistence simulations eliminate the nucleation barrier and give reliable transition temperatures. Second-order transitions are rounded and shifted by the box, but finite-size scaling extracts the true critical point and critical exponents. Ensemble choice matters more near phase transitions than anywhere else in simulation.

??? question "Check Your Understanding"
    1. You heat a perfect FCC crystal of LJ argon at constant volume. At 110 K it's solid. At 120 K it's still solid. At 130 K it melts. You report $T_m = 130$ K. The experimental melting point is ~84 K. What happened?
    2. Someone sets up a two-phase simulation (crystal + liquid) to find the melting point. They use a box of 500 atoms (250 solid, 250 liquid). Is this box large enough? What artifact do you expect from the periodic images of the interfaces?
    3. Near the liquid-gas critical point, your 500-atom simulation shows the density fluctuating smoothly. Your 50,000-atom simulation at the same state point shows much sharper fluctuations. Which one is giving the more "correct" picture, and why?
    4. You're running NPT near the freezing point. The volume oscillates wildly between two values (one for liquid, one for solid). Your average volume is somewhere in between. Is this average physically meaningful?
    5. Why is the nucleation barrier infinite at exactly the transition temperature? What does this mean for the practical task of finding $T_m$ from a single-phase simulation?
