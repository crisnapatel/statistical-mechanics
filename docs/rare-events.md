# Rare Events and Transition State Theory

!!! info "Practical MD topic — connects to [Enhanced Sampling](enhanced-sampling.md) and [Free Energy Isn't Free](free-energy.md). This is the framework for understanding why things happen slowly."

## Most of the time, nothing interesting happens.

Think about what your simulation actually does, step by step. The atoms vibrate. They bounce around. They explore the local free energy basin. For 99.999% of the trajectory, the system is doing the molecular equivalent of pacing in a room.

Then, rarely, something happens. A bond rotates. A barrier is crossed. A molecule detaches. A crystal nucleates. The system transitions from one metastable state to another. These **rare events** determine the rates of chemical reactions, phase transitions, protein folding, diffusion in solids, and essentially every dynamical process that matters.

The problem: if the event happens once per microsecond, and your simulation runs for nanoseconds, you'll never see it. Brute-force MD samples the boring parts beautifully and misses the interesting parts entirely.

Transition state theory (TST) provides a way to calculate the rate without simulating the event directly. Let me show you how.

## The free energy barrier

Every rare event can be described (at least approximately) as crossing a free energy barrier along some reaction coordinate $q$. The system starts in basin A, crosses a barrier at $q^\ddagger$ (the transition state), and ends in basin B.

The rate of crossing, from TST:

$$k_\text{TST} = \frac{k_B T}{2\pi m^\ddagger} \frac{e^{-\beta F(q^\ddagger)}}{\int_{A} e^{-\beta F(q)} \, dq}$$

More intuitively: the rate is proportional to the probability of being at the transition state, times the velocity of crossing. The exponential factor $e^{-\beta \Delta F^\ddagger}$ (where $\Delta F^\ddagger = F(q^\ddagger) - F_A$) dominates everything. A barrier of 20 $k_BT$ means the transition state is visited $e^{-20} \approx 2 \times 10^{-9}$ as often as the basin minimum.

TST has one major assumption: every trajectory that reaches the transition state from A continues to B (no recrossing). In reality, many trajectories cross the dividing surface and immediately come back. The **transmission coefficient** $\kappa$ corrects for this:

$$k_\text{true} = \kappa \cdot k_\text{TST}, \quad 0 < \kappa \leq 1$$

For reactions in solution, $\kappa$ is often 0.1-0.5 (most attempted crossings fail due to solvent friction). This is Kramers' correction.

!!! tip "Key Insight"
    TST says: if you know the free energy profile along the reaction coordinate, you know the rate. You don't need to simulate the actual crossing event. This is why free energy methods ([TI, FEP, umbrella sampling](free-energy.md)) are so important: they give you the barrier height, which determines the rate through the exponential.

## Computing rates from simulation

Three approaches, from simplest to most rigorous:

### Direct counting

If the event happens on your simulation timescale, just count transitions. Watch $q(t)$. Count how many times it goes from A to B. Rate = $n_\text{transitions} / t_\text{simulation}$.

This only works for barriers $\lesssim 10 \, k_BT$ (events faster than ~100 ns). For larger barriers, you'll never see a transition in a standard simulation.

### Free energy + TST

Compute $F(q)$ along the reaction coordinate using umbrella sampling, metadynamics, or TI. Read off $\Delta F^\ddagger$. Plug into the TST formula. Compute $\kappa$ from a separate short simulation that starts configurations at the transition state and watches whether they commit to A or B.

This works for any barrier height (enhanced sampling gives you $F(q)$) but requires choosing a good reaction coordinate. If the coordinate doesn't capture the true bottleneck, the rate will be wrong.

### Transition path sampling (TPS)

The most rigorous approach. Don't assume a reaction coordinate at all. Instead, harvest an ensemble of actual reactive trajectories, paths that start in A and end in B, by shooting from existing trajectories and accepting/rejecting based on whether the new path is reactive.

TPS gives you the true rate, the mechanism, and the transition state ensemble without ever choosing a reaction coordinate. The downside: it's computationally demanding and complex to implement.

## The reaction coordinate problem

Choosing the right reaction coordinate is the hardest part. For a simple bond rotation, it's the dihedral angle. For protein folding, it could be anything (RMSD, radius of gyration, native contacts, some combination).

A bad reaction coordinate leads to:

- **Wrong TST rate** (the barrier along the wrong coordinate doesn't correspond to the true bottleneck)
- **Low transmission coefficient** (many recrossings because the coordinate doesn't capture the true dividing surface)
- **Misleading free energy profiles** (apparent barriers that aren't real barriers, hidden barriers that don't show up)

The committor analysis is the gold standard for validating a reaction coordinate. Start configurations along $q$. Run short, unbiased simulations. Measure the probability of reaching B before A (the committor $p_B$). At the true transition state, $p_B = 0.5$. If the committor doesn't change smoothly from 0 to 1 along your coordinate, you've chosen wrong.

!!! warning "Common Mistake"
    Computing a free energy profile along an intuitive reaction coordinate and assuming the barrier height gives the correct rate. If the true reaction involves a motion orthogonal to your coordinate (a "hidden" barrier), your $\Delta F^\ddagger$ underestimates the true barrier, and your predicted rate is too fast. Always check the committor or the transmission coefficient.

## Takeaway

Rare events (barrier crossings) determine reaction rates, phase transition kinetics, and all the slow processes in molecular systems. Transition state theory connects the rate to the free energy barrier height through $k \propto e^{-\beta \Delta F^\ddagger}$. Computing the barrier requires free energy methods; the barrier height is the single most important number. The reaction coordinate choice determines whether your barrier is meaningful: a bad coordinate gives wrong rates. Committor analysis validates the coordinate. For barriers beyond ~10 $k_BT$, brute-force MD can't see the event; you need enhanced sampling or TST-based rate calculations.

??? question "Check Your Understanding"
    1. A reaction has $\Delta F^\ddagger = 15 \, k_BT$. The attempt frequency is $10^{12}$ s$^{-1}$. What's the TST rate? How long would you need to simulate to see one event? Is brute-force MD feasible?
    2. You compute $\kappa = 0.05$ for a barrier crossing in solution. This means 95% of barrier crossings are recrossings. Is this surprising for a reaction in a dense liquid? What's causing all the recrossings?
    3. Your free energy profile along coordinate $q$ shows a barrier of 8 $k_BT$. But the committor at the top of the barrier is 0.8 (not 0.5). What does this tell you about your reaction coordinate?
    4. Someone uses umbrella sampling to get $\Delta F^\ddagger$ and TST to predict a rate of $10^6$ s$^{-1}$. The experimental rate is $10^4$ s$^{-1}$. They conclude "TST overestimates by 100x." Is this the right interpretation, or is something else going on?
    5. Transition path sampling doesn't require choosing a reaction coordinate. So why isn't everyone using it instead of umbrella sampling + TST?
