"""
Generate charts for the One-Pager slide as PNG images.

- Revenue Split: donut chart with segment labels
- Key Financials: grouped bar chart (Revenue + EBITDA) with margin line
"""

import io
import os
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

# Constellation Capital color palette
DARK_BLUE = "#1F4E79"
MID_BLUE = "#2E75B6"
LIGHT_BLUE = "#BDD7EE"
ACCENT_COLORS = [DARK_BLUE, MID_BLUE, LIGHT_BLUE, "#5B9BD5", "#9DC3E6", "#DEEBF7"]
WHITE = "#FFFFFF"
DARK_GRAY = "#404040"
FONT_FAMILY = "sans-serif"


def generate_revenue_donut(
    segments: list[dict],
    total: str,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Generate a donut chart for revenue split.

    Args:
        segments: list of {"name": str, "pct": float, "growth": str|None}
        total: Total revenue string (e.g. "EUR 4.3m")
        output_path: Optional file path to save PNG

    Returns:
        PNG image bytes
    """
    if not segments:
        return _empty_chart_bytes("No revenue data")

    labels = [s["name"] for s in segments]
    sizes = [s["pct"] for s in segments]
    colors = ACCENT_COLORS[: len(segments)]

    fig, ax = plt.subplots(figsize=(4, 3.2))

    wedges, _ = ax.pie(
        sizes,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor=WHITE, linewidth=1.5),
        startangle=90,
        counterclock=False,
    )

    # Center text
    ax.text(0, 0.08, total, ha="center", va="center",
            fontsize=11, fontweight="bold", color=DARK_BLUE, family=FONT_FAMILY)
    ax.text(0, -0.12, "Revenue", ha="center", va="center",
            fontsize=8, color=DARK_GRAY, family=FONT_FAMILY)

    # Legend with percentages and growth
    legend_labels = []
    for s in segments:
        line = f"{s['name']} ({s['pct']}%)"
        if s.get("growth"):
            line += f"  {s['growth']}"
        legend_labels.append(line)

    ax.legend(
        wedges,
        legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.18),
        fontsize=7,
        frameon=False,
        ncol=1,
    )

    plt.tight_layout()
    return _save_fig(fig, output_path)


def generate_financials_chart(
    years: list[str],
    revenue: list[Optional[float]],
    ebitda: list[Optional[float]],
    ebitda_margin: list[Optional[float]],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Generate a grouped bar chart for key financials.

    Args:
        years: e.g. ["23A", "24A", "25A", "26P", "27P", "28P"]
        revenue: Revenue values (None for projected/missing)
        ebitda: EBITDA values
        ebitda_margin: EBITDA margin as decimals (0.28 = 28%)
        output_path: Optional file path to save PNG

    Returns:
        PNG image bytes
    """
    if not years:
        return _empty_chart_bytes("No financial data")

    n = len(years)
    x = np.arange(n)
    width = 0.35

    # Pad lists to match years length
    revenue = list(revenue) + [None] * (n - len(revenue))
    ebitda = list(ebitda) + [None] * (n - len(ebitda))
    ebitda_margin = list(ebitda_margin or []) + [None] * (n - len(ebitda_margin or []))

    # Replace None with 0 for plotting
    rev_vals = [v if v is not None else 0 for v in revenue[:n]]
    ebit_vals = [v if v is not None else 0 for v in ebitda[:n]]

    fig, ax = plt.subplots(figsize=(5, 3.2))

    # Distinguish actual vs projected
    rev_colors = []
    ebit_colors = []
    for y in years:
        if "P" in y.upper():
            rev_colors.append(LIGHT_BLUE)
            ebit_colors.append("#D6E8F7")
        else:
            rev_colors.append(DARK_BLUE)
            ebit_colors.append(MID_BLUE)

    # Revenue bars
    bars_rev = ax.bar(x - width / 2, rev_vals, width, color=rev_colors,
                      edgecolor=WHITE, linewidth=0.5, zorder=3)

    # EBITDA bars
    bars_ebit = ax.bar(x + width / 2, ebit_vals, width, color=ebit_colors,
                       edgecolor=WHITE, linewidth=0.5, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars_rev, rev_vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=7,
                    color=DARK_GRAY, family=FONT_FAMILY)

    for bar, val in zip(bars_ebit, ebit_vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                    f"{val:.1f}", ha="center", va="bottom", fontsize=7,
                    color=DARK_GRAY, family=FONT_FAMILY)

    # EBITDA margin labels below x-axis
    if ebitda_margin:
        for i, margin in enumerate(ebitda_margin):
            if margin is not None:
                ax.text(x[i], -0.25, f"{int(margin * 100)}%",
                        ha="center", fontsize=7, color=MID_BLUE, family=FONT_FAMILY)

    # Styling
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=8, family=FONT_FAMILY)
    ax.set_ylabel("EUR m", fontsize=8, color=DARK_GRAY, family=FONT_FAMILY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(DARK_GRAY)
    ax.spines["bottom"].set_color(DARK_GRAY)
    ax.tick_params(axis="y", labelsize=7, colors=DARK_GRAY)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f"))
    ax.set_ylim(bottom=0)

    # Grid
    ax.yaxis.grid(True, linestyle="--", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=DARK_BLUE, label="Revenue"),
        mpatches.Patch(facecolor=MID_BLUE, label="EBITDA"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=7, frameon=False)

    plt.tight_layout()
    return _save_fig(fig, output_path)


def _save_fig(fig, output_path: Optional[str] = None) -> bytes:
    """Save figure to bytes and optionally to file."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight",
                transparent=True, pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    data = buf.read()

    if output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(data)

    return data


def _empty_chart_bytes(message: str) -> bytes:
    """Generate a placeholder chart with a message."""
    fig, ax = plt.subplots(figsize=(3, 2))
    ax.text(0.5, 0.5, message, ha="center", va="center",
            fontsize=10, color=DARK_GRAY, family=FONT_FAMILY)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    return _save_fig(fig)
