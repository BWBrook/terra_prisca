"""Draw the review figure from saved Jacobian results; no new model runs."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

here = Path(__file__).resolve().parent
rows = json.loads((here / 'thermal_relaxation_results.json').read_text())
rows = [r for r in rows if r['stencil_step'] == 1e-4]
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'font.family': 'DejaVu Sans', 'axes.titleweight': 'bold'})
fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
colors = {0.0: '#0072B2', 0.5: '#D55E00'}
for ax, activity, title in zip(axes, ['fixed', 'products'], ['A  Fixed product activities', 'B  Product-dependent activities']):
    for r in rows:
        if r['activity_feedback'] != activity:
            continue
        pts = r['thermal_relaxation_rows']
        ax.plot([p['tau_temperature_years'] for p in pts],
                [p['max_real_per_year'] for p in pts], color=colors[r['f']],
                marker='o', markersize=4, linewidth=1.7, label=f"Recycling f = {r['f']:g}")
    ax.axhline(0, color='#555555', linewidth=1, linestyle='--')
    ax.set_xscale('log')
    ax.set_xlim(0.008, 16000)
    ax.set_xlabel('Thermal relaxation time (years)')
    ax.set_title(title, loc='left', pad=13)
    ax.grid(axis='y', color='#e8e8e8')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.3f}'))
    ax.set_ylabel('Largest eigenvalue real part (year⁻¹)')
axes[0].set_ylim(-0.0015, 0.0145)
axes[1].set_ylim(-0.0175, 0.0012)
axes[1].set_yticks([-0.015, -0.010, -0.005, 0.0])
axes[0].annotate('Loss of stability\nf = 0: 0.149 yr\nf = 0.5: 1.103 yr',
                 xy=(0.14921426, 0), xytext=(0.025, 0.0085),
                 arrowprops={'arrowstyle': '->', 'color': '#444444'}, fontsize=10)
axes[0].text(0.035, 0.0128, 'Positive = locally unstable', fontsize=10, color='#333333')
axes[1].text(0.024, -0.0025, 'Stable at all 16 sampled lags\n10⁻⁵ to 10⁴ years', fontsize=11)
axes[1].text(0.024, -0.0043, 'Negative = locally stable', fontsize=10, color='#333333')
axes[0].legend(loc='upper right', frameon=False, fontsize=10)
fig.suptitle('Chemical feedback changes stability under finite thermal response',
             x=0.055, y=0.99, ha='left', fontsize=16, fontweight='bold')
fig.text(0.055, 0.035, 'Same equilibrium budgets; one additional temperature state. Separate vertical scales. Lines connect sampled points.\nThe 10⁻⁵-year points are included in the stated grid but lie left of the plotted range. These are uncalibrated structural sensitivities.',
         fontsize=9, color='#444444', va='bottom')
fig.tight_layout(rect=(0.02, 0.13, 0.99, 0.94), w_pad=2.5)
dest = here.parent / 'figures'
dest.mkdir(exist_ok=True)
fig.savefig(dest / 'thermal_stability.png', dpi=180)
fig.savefig(dest / 'thermal_stability.svg')
plt.close(fig)
