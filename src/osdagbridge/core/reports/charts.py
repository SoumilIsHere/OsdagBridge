"""
charts.py -- matplotlib charts embedded in the design report.

* ur_summary_chart()     Utilization Ratio (UR = Demand / Capacity) bars with a
                         red dashed UR = 1.0 threshold line   -> Section 5.5
* steel_quantity_chart() structural-steel tonnage by member group  -> Chapter 7
* concrete_rebar_chart() concrete volume (m^3) and rebar weight (MT) -> Chapter 7

All styling comes from ``styles.CHART``.  Charts use matplotlib's object API
(Figure + Agg canvas) rather than pyplot, so they are safe to call from the Qt
desktop app / worker threads and never open a window.

Every function returns the saved file path, or ``None`` when there is nothing
meaningful to plot (e.g. every quantity is "N.A."); callers simply skip the
figure in that case.
"""
import os
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import styles

C = styles.CHART


def _num(value):
    """float(value) or None for '', 'N.A.', '---', None, text."""
    try:
        f = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return f if f == f else None          # drop NaN


def _new_fig(ncols=1, figsize=None):
    fig = Figure(figsize=figsize or C["figsize"], dpi=C["dpi"])
    FigureCanvasAgg(fig)
    axes = fig.subplots(1, ncols) if ncols > 1 else fig.subplots()
    return fig, axes


def _style_axis(ax):
    ax.grid(axis="y", alpha=C["grid_alpha"])
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(labelsize=C["font_size"])


def _save(fig, out_path):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=C["dpi"], bbox_inches="tight", facecolor="white")
    return out_path


# ═══════════════════════════════════════════════════════════════════════════
# 1. Utilization-ratio summary  (Section 5.5)
# ═══════════════════════════════════════════════════════════════════════════
UR_GROUP_ORDER = ["Steel Plate Girders", "Concrete Deck Slab", "Cross Bracing", "End Diaphragms"]


def ur_summary_chart(items, out_path, title="Utilization Ratio Summary (Demand / Capacity)"):
    """items: iterable of (group, label, ur).  UR may be str/float/None; entries
    whose UR cannot be read are skipped.  Bars are green when UR <= 1.0 and red
    when UR > 1.0, with a red dashed reference line at UR = 1.0."""
    by_group = {g: [] for g in UR_GROUP_ORDER}
    for group, label, ur in items:
        v = _num(ur)
        if v is None:
            continue
        by_group.setdefault(group, []).append((str(label), v))
    groups = [g for g in by_group if by_group[g]]
    if not groups:
        return None

    n_total = sum(len(by_group[g]) for g in groups)
    fig, ax = _new_fig(figsize=(C["figsize"][0], C["figsize"][1] + (1.0 if n_total > 8 else 0.3 if n_total > 5 else 0)))
    x, ticks, labels, group_spans = 0, [], [], []
    gap = 0.9
    for g in groups:
        start = x
        for label, v in by_group[g]:
            color = C["pass_color"] if v <= C["threshold_ur"] else C["fail_color"]
            ax.bar(x, v, width=C["bar_width"], color=color, zorder=3)
            ax.text(x, v, f"{v:.2f}", ha="center", va="bottom", fontsize=C["font_size"] - 1, zorder=6,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6})
            ticks.append(x)
            labels.append(label)
            x += 1
        group_spans.append((g, start, x - 1))
        x += gap

    ax.axhline(C["threshold_ur"], zorder=5, **C["threshold_style"])
    ymax = max([v for g in groups for _, v in by_group[g]] + [C["threshold_ur"]])
    ax.set_ylim(0, ymax * 1.18)
    ax.set_xticks(ticks)
    crowded = n_total > 5
    ax.set_xticklabels(labels, rotation=45 if crowded else 0,
                       ha="right" if crowded else "center",
                       rotation_mode="anchor" if crowded else "default",
                       fontsize=C["font_size"] - 1)
    ax.set_xlim(-0.8, x - gap + 0.3)          # breathing room so group captions are not clipped
    ax.set_ylabel("Utilization Ratio (UR)", fontsize=C["font_size"])
    ax.set_title(title, fontsize=C["title_size"], fontweight="bold")
    _style_axis(ax)

    # group captions above the bars
    top = ax.get_ylim()[1]
    for g, a, b in group_spans:
        ax.text((a + b) / 2, top * 0.985, g, ha="center", va="top",
                fontsize=C["font_size"] - 1, fontweight="bold", color="#444444")
        if b != group_spans[-1][2]:
            ax.axvline(b + 0.5 + gap / 2, color="#BBBBBB", linewidth=0.8, zorder=1)

    ax.legend(handles=[
        Patch(facecolor=C["pass_color"], label="Pass (UR \u2264 1.0)"),
        Patch(facecolor=C["fail_color"], label="Fail (UR > 1.0)"),
        Line2D([0], [0], label="UR = 1.0", **C["threshold_style"]),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.50 if n_total > 8 else -0.32 if n_total > 5 else -0.12),
        ncol=3, frameon=False, fontsize=C["font_size"] - 1)
    return _save(fig, out_path)


# ═══════════════════════════════════════════════════════════════════════════
# 2. Material quantity charts  (Chapter 7)
# ═══════════════════════════════════════════════════════════════════════════
def _sum_known(values):
    nums = [v for v in (_num(x) for x in values) if v is not None]
    return sum(nums) if nums else None


def steel_quantity_chart(q, out_path):
    """Structural steel tonnage (MT): girders, cross bracing, end diaphragms.
    `q` is the quantities dict (payload.inputs after calculate_material_quantities)."""
    bracing = _sum_known([q.get("bracing_top_wt_total"), q.get("bracing_bot_wt_total"),
                          q.get("bracing_diag_wt_total")])
    if bracing is None:
        bracing = _num(q.get("steel_bracing_wt_total"))
    bars = [("Girders", _num(q.get("steel_girders_wt_total"))),
            ("Cross Bracing", bracing),
            ("End Diaphragms", _num(q.get("end_diaphragm_wt_total")))]   # only if provided
    bars = [(n, v) for n, v in bars if v is not None]
    if not bars:
        return None
    fig, ax = _new_fig(figsize=(C["figsize"][0] * 0.8, C["figsize"][1]))
    names = [n for n, _ in bars]
    vals = [v for _, v in bars]
    ax.bar(names, vals, width=C["bar_width"], color=C["steel_color"], zorder=3)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=C["font_size"])
    ax.set_ylim(0, max(vals) * 1.15 if max(vals) > 0 else 1)
    ax.set_ylabel("Structural steel (MT)", fontsize=C["font_size"])
    ax.set_title("Structural Steel Tonnage", fontsize=C["title_size"], fontweight="bold")
    _style_axis(ax)
    return _save(fig, out_path)


def concrete_rebar_chart(q, out_path):
    """Concrete volume (m^3) and reinforcement-steel weight (MT).  Different
    units, so they are two panels side by side rather than a misleading dual axis."""
    conc = _num(q.get("concrete_deck_vol_total"))
    reb = _num(q.get("rebar_deck_wt_total"))
    if conc is None and reb is None:
        return None
    fig, axes = _new_fig(ncols=2, figsize=(C["figsize"][0] * 0.8, C["figsize"][1]))
    panels = [(axes[0], "Deck Concrete", conc, "Volume (m\u00b3)", C["concrete_color"]),
              (axes[1], "Reinforcement Steel", reb, "Weight (MT)", C["rebar_color"])]
    for ax, name, v, ylabel, color in panels:
        if v is None:
            ax.text(0.5, 0.5, "N.A.", ha="center", va="center", transform=ax.transAxes,
                    fontsize=C["title_size"], color="#888888")
            ax.set_xticks([])
            ax.set_yticks([])
        else:
            ax.bar([name], [v], width=C["bar_width"], color=color, zorder=3)
            ax.text(0, v, f"{v:.2f}", ha="center", va="bottom", fontsize=C["font_size"])
            ax.set_ylim(0, v * 1.15 if v > 0 else 1)
        ax.set_ylabel(ylabel, fontsize=C["font_size"])
        _style_axis(ax)
    fig.suptitle("Concrete Volume and Reinforcement Steel Weight",
                 fontsize=C["title_size"], fontweight="bold")
    return _save(fig, out_path)


# ═══════════════════════════════════════════════════════════════════════════
# LaTeX embedding helper
# ═══════════════════════════════════════════════════════════════════════════
def figure_tex(rel_path, caption):
    """LaTeX figure block for an image already written under the build dir.
    `rel_path` is relative to the LaTeX working directory, e.g. 'charts/x.png'."""
    return (r"""
\begin{figure}[H]
\centering
\includegraphics[width=""" + C["latex_width"] + r"""]{""" + rel_path + r"""}
\caption{""" + caption + r"""}
\end{figure}
""")
