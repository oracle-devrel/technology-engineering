#!/usr/bin/env python3
"""Draw the charts for a benchmark run.

    python plots.py results/<run>            # writes PNGs into results/<run>/charts/

Charts (only those the run has data for):
  latency_vs_length.png       TTFA and E2E p50 against target seconds, one line per mode, one panel per language
  rtf_vs_length.png           real-time factor against target seconds
  concurrency.png             throughput and p50 / p99 latency against concurrency level
  wer_vs_length.png           word error rate against target seconds (after wer.py)

Needs pandas and matplotlib.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

# fixed colour per mode (never cycled), validated categorical palette
MODE_COLOR = {"sync": "#2a78d6", "stream": "#eb6834", "chunked": "#1baf7a"}
LANG_COLOR = {"en": "#2a78d6", "ar": "#eb6834"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": MUTED, "ytick.color": MUTED, "font.size": 10, "legend.frameon": False, "lines.linewidth": 2,
    "lines.markersize": 6,
})


def _title(ax, text, sub=None):
    ax.set_title(text, loc="left", fontsize=11, color=INK, pad=22 if sub else 6)
    if sub:
        ax.text(0, 1.03, sub, transform=ax.transAxes, fontsize=8.5, color=MUTED)


def _label_ends(ax, xs, ys, text, color):
    """Queue a direct label at the line end; `_flush_labels` spreads overlapping ones."""
    if len(xs):
        ax.__dict__.setdefault("_end_labels", []).append((xs[-1], ys[-1], text))


def _flush_labels(ax):
    labels = sorted(ax.__dict__.pop("_end_labels", []), key=lambda t: t[1])
    if not labels:
        return
    lo, hi = ax.get_ylim()
    gap = 0.045 * (hi - lo)
    placed = []
    for x, y, text in labels:
        if placed and y - placed[-1] < gap:
            y = placed[-1] + gap
        placed.append(y)
        ax.annotate(text, (x, y), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK)
    if placed[-1] > hi - gap / 2:                       # keep the top label inside the plot
        ax.set_ylim(lo, placed[-1] + gap)


def latency_vs_length(df: pd.DataFrame, out: Path, label: str) -> None:
    d = df[df.concurrency == 1]
    if d.target_s.nunique() < 2:
        return
    langs = sorted(d.lang.unique())
    fig, axes = plt.subplots(2, len(langs), figsize=(5 * len(langs), 7.5), squeeze=False, sharex=True)
    for j, lang in enumerate(langs):
        for i, (metric, name) in enumerate([("ttfa_p50", "Time to first audio, p50 (s)"), ("e2e_p50", "End-to-end latency, p50 (s)")]):
            ax = axes[i][j]
            for mode in ["sync", "stream", "chunked"]:
                g = d[(d.lang == lang) & (d["mode"] == mode)].groupby("target_s")[metric].median().dropna()
                if g.empty:
                    continue
                ax.plot(g.index, g.values, marker="o", color=MODE_COLOR[mode], label=mode)
                _label_ends(ax, list(g.index), list(g.values), mode, MODE_COLOR[mode])
            _title(ax, f"{lang}: {name}")
            ax.set_ylim(bottom=0)
            _flush_labels(ax)
            if i == 1:
                ax.set_xlabel("target seconds of speech")
    axes[0][0].legend(loc="upper left")
    fig.suptitle(f"{label}: latency against input length (concurrency 1)", x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(out / "latency_vs_length.png", dpi=150)
    plt.close(fig)


def rtf_vs_length(df: pd.DataFrame, out: Path, label: str) -> None:
    d = df[df.concurrency == 1]
    if d.target_s.nunique() < 2:
        return
    langs = sorted(d.lang.unique())
    fig, axes = plt.subplots(1, len(langs), figsize=(5 * len(langs), 4), squeeze=False)
    for j, lang in enumerate(langs):
        ax = axes[0][j]
        for mode in ["sync", "stream", "chunked"]:
            g = d[(d.lang == lang) & (d["mode"] == mode)].groupby("target_s")["rtf_p50"].median().dropna()
            if g.empty:
                continue
            ax.plot(g.index, g.values, marker="o", color=MODE_COLOR[mode], label=mode)
            _label_ends(ax, list(g.index), list(g.values), mode, MODE_COLOR[mode])
        ax.axhline(1.0, color=MUTED, linewidth=1, linestyle=":")
        _title(ax, f"{lang}: real-time factor, p50", "E2E seconds per second of speech; below 1 is faster than playback")
        ax.set_ylim(0, max(1.15, ax.get_ylim()[1]))
        ax.text(ax.get_xlim()[1], 1.0, "real time ", ha="right", va="bottom", fontsize=8, color=MUTED)
        ax.set_xlabel("target seconds of speech")
        _flush_labels(ax)
    axes[0][0].legend(loc="center left")
    fig.tight_layout()
    fig.savefig(out / "rtf_vs_length.png", dpi=150)
    plt.close(fig)


def concurrency(df: pd.DataFrame, out: Path, label: str) -> None:
    levels = df.groupby(["lang", "text", "mode", "target_s"]).concurrency.nunique()
    swept = levels[levels > 1].reset_index()[["lang", "text", "mode", "target_s"]]
    if swept.empty:
        return
    d = df.merge(swept, on=["lang", "text", "mode", "target_s"])
    target = d.target_s.value_counts().idxmax()          # one clip length per chart
    d = d[d.target_s == target]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    panels = [("req_per_min", "Throughput (requests per minute)"), ("e2e_p50", "End-to-end latency, p50 (s)"), ("e2e_p99", "End-to-end latency, p99 (s)")]
    for ax, (metric, name) in zip(axes, panels):
        for lang in sorted(d.lang.unique()):
            g = d[d.lang == lang].groupby("concurrency")[metric].median().dropna()
            ax.plot(g.index, g.values, marker="o", color=LANG_COLOR.get(lang, MUTED), label=lang)
            _label_ends(ax, list(g.index), list(g.values), lang, LANG_COLOR.get(lang, MUTED))
        ax.set_xscale("log", base=2)
        ax.set_xticks(sorted(d.concurrency.unique()))
        ax.set_xticklabels([str(c) for c in sorted(d.concurrency.unique())])
        ax.set_xlabel("concurrent requests")
        ax.set_ylim(bottom=0)
        _title(ax, name)
        _flush_labels(ax)
    axes[0].legend(loc="upper left")
    fig.suptitle(f"{label}: load sweep ({', '.join(sorted(d['mode'].unique()))} mode, {target:.0f} s target clips)", x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(out / "concurrency.png", dpi=150)
    plt.close(fig)


def wer_vs_length(run: Path, out: Path, label: str) -> None:
    f = run / "wer.csv"
    if not f.exists():
        return
    w = pd.read_csv(f)
    if w.target_s.nunique() < 2:
        return
    langs = sorted(w.lang.unique())
    fig, axes = plt.subplots(1, len(langs), figsize=(5 * len(langs), 4), squeeze=False)
    for j, lang in enumerate(langs):
        ax = axes[0][j]
        for mode in ["sync", "stream", "chunked"]:
            g = w[(w.lang == lang) & (w["mode"] == mode)].groupby("target_s")["wer"].mean().dropna()
            if g.empty:
                continue
            ax.plot(g.index, 100 * g.values, marker="o", color=MODE_COLOR[mode], label=mode)
            _label_ends(ax, list(g.index), list(100 * g.values), mode, MODE_COLOR[mode])
        _title(ax, f"{lang}: word error rate (%)", "Whisper transcript against the sent text; a jump marks where single-pass output degrades")
        ax.set_ylim(bottom=0)
        ax.set_xlabel("target seconds of speech")
        _flush_labels(ax)
    axes[0][0].legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out / "wer_vs_length.png", dpi=150)
    plt.close(fig)


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run = Path(sys.argv[1])
    df = pd.read_csv(run / "summary.csv")
    out = run / "charts"
    out.mkdir(exist_ok=True)
    label = str(df.label.iloc[0])
    latency_vs_length(df, out, label)
    rtf_vs_length(df, out, label)
    concurrency(df, out, label)
    wer_vs_length(run, out, label)
    made = sorted(p.name for p in out.glob("*.png"))
    print("charts:", ", ".join(made) if made else "none (run has a single length and a single concurrency level)")


if __name__ == "__main__":
    main()
