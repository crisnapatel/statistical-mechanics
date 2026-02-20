"""
Analyze Argon NVE simulation for Section 6.1.

Generates two plots:
  1. Phase space trajectory (x, p_x) and (y, p_y) for a single atom
  2. Energy conservation (KE, PE, Etotal vs time)

Usage:
  python analyze.py

Expects log.lammps and dump.argon.lammpstrj in the current directory
(produced by running argon-nve.lammps).
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# ── Configuration ────────────────────────────────────────────────────────────
LOG_FILE = "log.lammps"
DUMP_FILE = "dump.argon.lammpstrj"
M_AR = 39.948  # argon mass (g/mol) for computing momentum p = m*v
DT = 0.001     # timestep in ps (metal units)

# ── Parse log file (NVE production block only) ───────────────────────────────
print("Parsing log file...")
steps, times, temps, kes, pes, etotals = [], [], [], [], [], []
reading_thermo = False
thermo_block = 0

with open(LOG_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        if line.startswith("Step") and "Time" in line and "Temp" in line:
            thermo_block += 1
            reading_thermo = (thermo_block == 2)  # second block = NVE production
            continue
        if reading_thermo:
            if line.startswith("Loop time") or not line:
                reading_thermo = False
                continue
            parts = line.split()
            if len(parts) >= 7:
                try:
                    steps.append(int(parts[0]))
                    times.append(float(parts[1]))
                    temps.append(float(parts[2]))
                    kes.append(float(parts[3]))
                    pes.append(float(parts[4]))
                    etotals.append(float(parts[5]))
                except (ValueError, IndexError):
                    reading_thermo = False

steps = np.array(steps)
times = np.array(times)
temps = np.array(temps)
kes = np.array(kes)
pes = np.array(pes)
etotals = np.array(etotals)

print(f"  {len(steps)} entries, {times[0]:.1f} to {times[-1]:.1f} ps")
print(f"  T = {temps.mean():.1f} +/- {temps.std():.1f} K")
print(f"  Etotal = {etotals.mean():.6f} +/- {etotals.std():.2e} eV")

# ── Parse dump file for atom 1 trajectory ────────────────────────────────────
print("Parsing dump file for atom 1...")
atom1_data = []

with open(DUMP_FILE, 'r') as f:
    while True:
        line = f.readline()
        if not line:
            break
        if "ITEM: TIMESTEP" in line:
            ts = int(f.readline().strip())
            f.readline()  # ITEM: NUMBER OF ATOMS
            natoms = int(f.readline().strip())
            f.readline()  # ITEM: BOX BOUNDS
            for _ in range(3):
                f.readline()
            f.readline()  # ITEM: ATOMS header
            for _ in range(natoms):
                parts = f.readline().strip().split()
                if int(parts[0]) == 1:
                    atom1_data.append([ts] + [float(x) for x in parts[1:]])

atom1_data = np.array(atom1_data)
atom1_times = atom1_data[:, 0] * DT
px = M_AR * atom1_data[:, 4]  # p_x = m * v_x
py = M_AR * atom1_data[:, 5]  # p_y = m * v_y
print(f"  {len(atom1_data)} frames")

# ── Plot 1: Phase space trajectory ───────────────────────────────────────────
print("Generating phase space plot...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

for ax, pos, mom, labels in [
    (ax1, atom1_data[:, 1], px, (r'$x$ ($\AA$)', r'$p_x$ (amu$\cdot\AA$/ps)', r'$(x, \, p_x)$')),
    (ax2, atom1_data[:, 2], py, (r'$y$ ($\AA$)', r'$p_y$ (amu$\cdot\AA$/ps)', r'$(y, \, p_y)$')),
]:
    ax.scatter(pos, mom, c=atom1_times, cmap='viridis', s=3, alpha=0.8, edgecolors='none')
    pts = np.column_stack([pos, mom])
    segs = np.stack([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap='viridis', linewidths=0.4, alpha=0.35)
    lc.set_array(atom1_times[:-1])
    ax.add_collection(lc)
    ax.set_xlabel(labels[0], fontsize=12)
    ax.set_ylabel(labels[1], fontsize=12)
    ax.set_title(labels[2], fontsize=13)
    ax.grid(True, alpha=0.15)

fig.colorbar(ax2.collections[0], ax=[ax1, ax2], label='Time (ps)', pad=0.02, aspect=30)
fig.suptitle('Phase Space Trajectory of One Argon Atom (NVE, 108 atoms, ~87 K)',
             fontsize=13, fontweight='semibold', y=1.03)
fig.tight_layout()
fig.savefig("phase-space.png", dpi=180, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("  Saved phase-space.png")

# ── Plot 2: Energy conservation ──────────────────────────────────────────────
print("Generating energy plot...")
fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(9, 5.5),
                                      gridspec_kw={'height_ratios': [3, 1]}, sharex=True)

ax_top.plot(times, kes, color='#e74c3c', lw=0.9, alpha=0.7, label='Kinetic energy')
ax_top.plot(times, pes, color='#3498db', lw=0.9, alpha=0.7, label='Potential energy')
ax_top.plot(times, etotals, color='black', lw=1.8, label='Total energy', zorder=3)
ax_top.set_ylabel('Energy (eV)', fontsize=12)
ax_top.set_title('Energy Conservation in NVE Ensemble (108 Ar atoms)', fontsize=13, fontweight='semibold')
ax_top.legend(fontsize=10, framealpha=0.9)
ax_top.grid(True, alpha=0.2)

e_mean = etotals.mean()
delta_e = (etotals - e_mean) * 1000  # meV
ax_bot.plot(times, delta_e, color='black', lw=0.8)
ax_bot.axhline(0, color='gray', lw=0.5, ls='--')
ax_bot.set_xlabel('Time (ps)', fontsize=12)
ax_bot.set_ylabel(r'$E_{total} - \langle E \rangle$ (meV)', fontsize=11)
ax_bot.grid(True, alpha=0.2)

rel_drift = abs(etotals[-1] - etotals[0]) / abs(e_mean)
ax_bot.text(0.98, 0.92, f'Relative drift: {rel_drift:.2e}',
            transform=ax_bot.transAxes, fontsize=9, ha='right', va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF3C7', alpha=0.9))

fig.subplots_adjust(hspace=0.08)
fig.savefig("energy.png", dpi=180, bbox_inches='tight', facecolor='white')
plt.close(fig)
print("  Saved energy.png")

print("\nDone!")
