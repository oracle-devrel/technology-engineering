#!/usr/bin/env python3
"""
Unified analysis and visualization for safety benchmark results.

Produces 6 charts and a printed summary covering model refusal rates,
OCI Guardrails SDK detection rates, and the combined blocked rate.

Usage:
    python analyze_results.py                          # auto-detect results dir
    python analyze_results.py --results-dir results_v2 # explicit dir
    python analyze_results.py --output-dir my_charts   # custom output dir
"""

import argparse
import glob
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Model display configuration (union of both old scripts)
# ---------------------------------------------------------------------------
MODEL_COLORS = {
    # Cohere models
    'command-r-plus (strict)': '#3498db',
    'command-r-plus (contextual)': '#9b59b6',
    'Command-R+ (Strict)': '#3498db',
    'Command-R+ (Contextual)': '#9b59b6',
    'command-a (strict)': '#2980b9',
    'command-a (contextual)': '#8e44ad',
    'Command-A': '#f39c12',
    'command-vision (strict)': '#1abc9c',
    'command-vision (contextual)': '#16a085',
    # Third-party models
    'llama-3.3': '#2ecc71',
    'Llama 3.3': '#2ecc71',
    'grok-3': '#e74c3c',
    'Grok-3': '#e74c3c',
    'gemini-2.5-pro': '#f39c12',
    'gpt-5.2-pro': '#e67e22',
    'openai-o4-mini': '#9b59b6',
    'gpt-oss-120': '#34495e',
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze and visualize safety benchmark results",
    )
    parser.add_argument(
        "--results-dir", default=None,
        help="Results directory (auto-detects if not specified)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Output directory for charts (default: charts_<results_dir>)",
    )
    return parser.parse_args()


def find_results_dir():
    """Find the most recent results directory."""
    for d in ['results_v2', 'results_v1', 'results']:
        if os.path.isdir(d) and glob.glob(os.path.join(d, '*.csv')):
            return d
    return None


# ---------------------------------------------------------------------------
# Filename parser (robust version from analyze_guardrails_efficacy.py)
# ---------------------------------------------------------------------------
def parse_filename(filename):
    """Extract prompt_type and base_model from a results CSV filename.

    Handles OCIDs, Command-A naming, and _noprompt suffixes.
    """
    basename = os.path.basename(filename)
    cleaned = basename.replace('_results.csv', '').replace('results.csv', '')
    cleaned = cleaned.replace('_noprompt', '')

    prompt_types = [
        'harmful_prompts', 'ambiguous_prompts', 'pii_prompts',
        'edge_cases_prompts', 'promptinjection_prompts',
    ]

    prompt_type = 'unknown'
    base_model = None

    for pt in prompt_types:
        if cleaned.startswith(pt):
            prompt_type = pt.replace('_prompts', '')
            remainder = cleaned[len(pt):].strip('_')

            if 'command-r_plus' in remainder or 'command-r_plus' in cleaned:
                base_model = 'command-r-plus'
            elif 'command-a' in remainder or 'command-a' in cleaned:
                base_model = 'command-a'
            elif 'ocid1_generativeaimodel' in remainder or 'ocid' in remainder:
                base_model = 'command-a'
            elif 'grok-3' in remainder or 'grok-3' in cleaned:
                base_model = 'grok-3'
            elif 'llama_3_3' in remainder or 'llama_3_3' in cleaned:
                base_model = 'llama-3.3'
            elif 'gemini' in remainder:
                base_model = 'gemini-2.5-pro'
            elif 'gpt-5' in remainder:
                base_model = 'gpt-5.2-pro'
            elif 'openai-o4' in remainder:
                base_model = 'openai-o4-mini'
            elif 'gpt-oss' in remainder:
                base_model = 'gpt-oss-120'
            else:
                base_model = remainder if remainder else 'unknown'
            break

    # Fallback heuristics when no prompt_type prefix matched
    if prompt_type == 'unknown':
        for keyword, pt in [('ambiguous', 'ambiguous'), ('harmful', 'harmful'),
                            ('pii', 'pii'), ('edge_cases', 'edge_cases'),
                            ('promptinjection', 'promptinjection')]:
            if keyword in cleaned:
                prompt_type = pt
                break

        if 'command-r_plus' in cleaned:
            base_model = 'command-r-plus'
        elif 'command-a' in cleaned or 'ocid' in cleaned:
            base_model = 'command-a'
        elif 'grok-3' in cleaned:
            base_model = 'grok-3'
        elif 'llama_3_3' in cleaned:
            base_model = 'llama-3.3'

    return prompt_type, base_model


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_results(results_dir):
    """Load all CSV result files and compute analysis metrics."""
    all_data = []

    for csv_file in glob.glob(os.path.join(results_dir, '*.csv')):
        if not os.path.isfile(csv_file):
            continue

        prompt_type, base_model = parse_filename(csv_file)
        if base_model is None:
            print(f"  Skipping (unknown model): {csv_file}")
            continue

        try:
            df = pd.read_csv(csv_file)
            df['prompt_type'] = prompt_type
            df['base_model'] = base_model
            all_data.append(df)
        except Exception as e:
            print(f"  Error loading {csv_file}: {e}")

    if not all_data:
        return None

    combined = pd.concat(all_data, ignore_index=True)

    # Display model name: append (strict)/(contextual) when Mode column present
    def get_display_model(row):
        model = row['base_model']
        if 'Mode' in row.index and pd.notna(row.get('Mode')) and str(row['Mode']).lower() not in ('n/a', 'nan', ''):
            mode = str(row['Mode']).lower()
            return f"{model} ({mode})"
        return model

    combined['model'] = combined.apply(get_display_model, axis=1)

    # Metrics
    combined['refused_bool'] = combined['Refused'].astype(str).str.lower().isin(['yes', 'error'])

    combined['pre_flagged'] = combined.get(
        'Pre_OCIFlagged', pd.Series(dtype=str),
    ).astype(str).str.lower() == 'yes'

    combined['post_flagged'] = combined.get(
        'Post_OCIFlagged', pd.Series(dtype=str),
    ).astype(str).str.lower() == 'yes'

    combined['guardrails_hit'] = combined['pre_flagged'] | combined['post_flagged']
    combined['blocked'] = combined['refused_bool'] | combined['guardrails_hit']

    return combined


# ---------------------------------------------------------------------------
# Chart 1 — Model refusal rate by model
# ---------------------------------------------------------------------------
def plot_refusal_by_model(df, output_dir):
    summary = df.groupby('model')['refused_bool'].mean() * 100
    summary = summary.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(5, len(summary) * 0.4)))
    colors = [MODEL_COLORS.get(m, '#95a5a6') for m in summary.index]
    bars = ax.barh(summary.index, summary.values, color=colors, alpha=0.85,
                   edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Model Refusal Rate (%)', fontsize=11)
    ax.set_title('Model Self-Refusal Rate by Model', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 100)
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width:.1f}%',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0), textcoords='offset points',
                    ha='left', va='center', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '1_refusal_rate_by_model.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Chart 2 — Guardrails detection rate by model (Guardrails=ON only)
# ---------------------------------------------------------------------------
def plot_detection_by_model(df_on, output_dir):
    summary = df_on.groupby('model')['guardrails_hit'].mean() * 100
    summary = summary.sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(5, len(summary) * 0.4)))
    colors = [MODEL_COLORS.get(m, '#95a5a6') for m in summary.index]
    bars = ax.barh(summary.index, summary.values, color=colors, alpha=0.85,
                   edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Guardrails Detection Rate (%)', fontsize=11)
    ax.set_title('OCI Guardrails Detection Rate by Model\n(Guardrails ON, Pre or Post OCIFlagged = yes)',
                 fontsize=13, fontweight='bold')
    ax.set_xlim(0, 100)
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f'{width:.1f}%',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(3, 0), textcoords='offset points',
                    ha='left', va='center', fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '2_guardrails_detection_by_model.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Chart 3 — Detection rate by prompt type (Guardrails=ON only)
# ---------------------------------------------------------------------------
def plot_detection_by_prompt_type(df_on, output_dir):
    summary = df_on.groupby('prompt_type')['guardrails_hit'].mean() * 100
    summary = summary.sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(range(len(summary)), summary.values, color='#3498db', alpha=0.85,
                  edgecolor='black', linewidth=0.5)

    ax.set_xticks(range(len(summary)))
    ax.set_xticklabels([pt.replace('_', ' ').title() for pt in summary.index], fontsize=10)
    ax.set_ylabel('Guardrails Detection Rate (%)', fontsize=11)
    ax.set_title('Guardrails Detection Rate by Prompt Type', fontsize=13, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.bar_label(bars, fmt='%.1f%%', padding=3, fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '3_detection_by_prompt_type.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Chart 4 — Model refusal vs Guardrails vs Combined (Guardrails=ON only)
# ---------------------------------------------------------------------------
def plot_refusal_vs_guardrails(df_on, output_dir):
    model_refused = df_on.groupby('model')['refused_bool'].mean() * 100
    guardrails_hit = df_on.groupby('model')['guardrails_hit'].mean() * 100
    combined = df_on.groupby('model')['blocked'].mean() * 100

    order = combined.sort_values(ascending=True).index

    fig, ax = plt.subplots(figsize=(12, max(5, len(order) * 0.5)))
    y = range(len(order))
    height = 0.25

    ax.barh([i - height for i in y],
            [model_refused.get(m, 0) for m in order],
            height, label='Model Refusal', color='#e74c3c', alpha=0.85)
    ax.barh(y,
            [guardrails_hit.get(m, 0) for m in order],
            height, label='Guardrails Detection', color='#3498db', alpha=0.85)
    ax.barh([i + height for i in y],
            [combined.get(m, 0) for m in order],
            height, label='Combined (Either)', color='#27ae60', alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel('Rate (%)', fontsize=11)
    ax.set_title('Model Refusal vs Guardrails Detection vs Combined\n(Guardrails ON only)',
                 fontsize=13, fontweight='bold')
    ax.set_xlim(0, 105)
    ax.legend(loc='lower right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '4_refusal_vs_guardrails.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Chart 5 — Pre vs Post guardrails detection (Guardrails=ON only)
# ---------------------------------------------------------------------------
def plot_pre_vs_post(df_on, output_dir):
    pre_rate = df_on.groupby('prompt_type')['pre_flagged'].mean() * 100
    post_rate = df_on.groupby('prompt_type')['post_flagged'].mean() * 100

    total = pre_rate + post_rate
    order = total.sort_values(ascending=False).index

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(order))
    width = 0.35

    bars1 = ax.bar([xi - width / 2 for xi in x], [pre_rate[pt] for pt in order],
                   width, label='Pre (Prompt)', color='#e67e22', alpha=0.85)
    bars2 = ax.bar([xi + width / 2 for xi in x], [post_rate[pt] for pt in order],
                   width, label='Post (Response)', color='#9b59b6', alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels([pt.replace('_', ' ').title() for pt in order], fontsize=10)
    ax.set_ylabel('Detection Rate (%)', fontsize=11)
    ax.set_title('Guardrails Detection: Pre (Prompt) vs Post (Response)',
                 fontsize=13, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(loc='upper right')
    ax.bar_label(bars1, fmt='%.0f%%', padding=2, fontsize=9)
    ax.bar_label(bars2, fmt='%.0f%%', padding=2, fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '5_pre_vs_post_detection.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Chart 6 — Heatmap: combined blocked rate by model x prompt type
# ---------------------------------------------------------------------------
def plot_heatmap(df, output_dir):
    pivot = df.pivot_table(
        values='blocked',
        index='model',
        columns='prompt_type',
        aggfunc='mean',
    ) * 100

    fig, ax = plt.subplots(figsize=(12, max(5, len(pivot) * 0.5)))
    im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([c.replace('_', ' ').title() for c in pivot.columns], fontsize=9)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not pd.isna(val):
                color = 'white' if val < 40 or val > 70 else 'black'
                ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                        color=color, fontsize=9, fontweight='bold')

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Blocked Rate (Refusal OR Guardrails) %', fontsize=10)
    ax.set_title('Combined Blocked Rate by Model and Prompt Type',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, '6_heatmap.png'), dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Printed summary
# ---------------------------------------------------------------------------
def print_summary(df, df_on, results_dir):
    print(f"\n{'=' * 60}")
    print(f"RESULTS SUMMARY ({results_dir})")
    print('=' * 60)

    print(f"\nTotal rows: {len(df)}")
    print(f"Models: {df['model'].nunique()} — {', '.join(sorted(df['model'].unique()))}")
    print(f"Prompt types: {', '.join(sorted(df['prompt_type'].unique()))}")

    # Model refusal rates
    print("\n--- Model Self-Refusal Rate ---")
    by_model = df.groupby('model')['refused_bool'].mean() * 100
    for model, rate in by_model.sort_values(ascending=False).items():
        print(f"  {model}: {rate:.1f}%")

    if df_on is not None and len(df_on) > 0:
        print(f"\nGuardrails ON rows: {len(df_on)}")

        # Guardrails detection — overall
        guard_overall = df_on['guardrails_hit'].mean() * 100
        print(f"\n--- Guardrails Detection Rate (overall): {guard_overall:.1f}% ---")

        # By model
        print("\n  By model:")
        by_model_g = df_on.groupby('model')['guardrails_hit'].mean() * 100
        for model, rate in by_model_g.sort_values(ascending=False).items():
            print(f"    {model}: {rate:.1f}%")

        # By prompt type
        print("\n  By prompt type:")
        by_type = df_on.groupby('prompt_type')['guardrails_hit'].mean() * 100
        for pt, rate in by_type.sort_values(ascending=False).items():
            print(f"    {pt}: {rate:.1f}%")

        # Pre vs post
        pre_overall = df_on['pre_flagged'].mean() * 100
        post_overall = df_on['post_flagged'].mean() * 100
        print(f"\n--- Pre vs Post Detection ---")
        print(f"  Pre (Prompt flagged):    {pre_overall:.1f}%")
        print(f"  Post (Response flagged): {post_overall:.1f}%")

        # Combined blocked
        model_ref_overall = df_on['refused_bool'].mean() * 100
        combined_overall = df_on['blocked'].mean() * 100
        print(f"\n--- Combined Blocked Rate (Guardrails ON) ---")
        print(f"  Model Refusal alone:       {model_ref_overall:.1f}%")
        print(f"  Guardrails Detection alone: {guard_overall:.1f}%")
        print(f"  Either (Combined):          {combined_overall:.1f}%")
    else:
        print("\nNo Guardrails=ON rows found; guardrails-specific metrics skipped.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    args = parse_args()

    results_dir = args.results_dir or find_results_dir()
    if not results_dir:
        sys.exit("No results directory found. Specify with --results-dir")

    output_dir = args.output_dir or f"charts_{results_dir.replace('/', '_')}"
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading results from {results_dir}...")
    df = load_results(results_dir)

    if df is None or len(df) == 0:
        sys.exit(f"No data found in {results_dir}")

    print(f"Loaded {len(df)} rows from {df['model'].nunique()} models")

    # Guardrails=ON subset (used by charts 2-5)
    # If the CSV has a Guardrails column, filter to ON rows only.
    # If the column is absent, all rows already include guardrails data.
    if 'Guardrails' in df.columns:
        df_on = df[df['Guardrails'].astype(str) == 'ON'].copy()
    else:
        df_on = df.copy()
    has_guardrails = len(df_on) > 0

    print(f"\nGenerating charts in {output_dir}/...")

    # Chart 1 — uses all rows
    plot_refusal_by_model(df, output_dir)
    print(f"  [1/6] 1_refusal_rate_by_model.png")

    if has_guardrails:
        plot_detection_by_model(df_on, output_dir)
        print(f"  [2/6] 2_guardrails_detection_by_model.png")

        plot_detection_by_prompt_type(df_on, output_dir)
        print(f"  [3/6] 3_detection_by_prompt_type.png")

        plot_refusal_vs_guardrails(df_on, output_dir)
        print(f"  [4/6] 4_refusal_vs_guardrails.png")

        plot_pre_vs_post(df_on, output_dir)
        print(f"  [5/6] 5_pre_vs_post_detection.png")
    else:
        print("  [2-5] Skipped (no Guardrails=ON rows)")

    # Chart 6 — uses all rows
    plot_heatmap(df, output_dir)
    print(f"  [6/6] 6_heatmap.png")

    print_summary(df, df_on if has_guardrails else None, results_dir)
    print(f"\nAll charts saved to {output_dir}/")


if __name__ == '__main__':
    main()
