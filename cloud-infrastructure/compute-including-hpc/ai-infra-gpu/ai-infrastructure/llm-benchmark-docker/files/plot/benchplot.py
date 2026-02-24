# Copyright (c) 2025 Oracle and/or its affiliates.
from pathlib import Path

import altair as alt
import json
import logging
import polars as pl


PER_REQUEST_THROUGHPUT = "results_request_output_throughput_token_per_s_mean"
PER_REQUEST_THROUGHPUT_THRESHOLD = 10.0

# Remove these from genai-perf output
COLUMNS_TO_REMOVE = [
    "image_format",
    "goodput",
    "header",
    "request_rate",
    "synthetic_input_files",
    "extra_inputs",
    "port",
]


def _process_genai_output(pth: Path):
    """Processes the genai-perf output to return a flattened dictionary.
    """
    with pth.open() as fd:
        data = json.load(fd)

    result = {}
    for k, v in data.items():
        if isinstance(v, dict) and "avg" in v:
            value = v["avg"]
            if v.get("unit") == "ms":
                value /= 1_000
            result[k] = value
        elif isinstance(v, dict):
            result.update(v)

    for col in COLUMNS_TO_REMOVE:
        result.pop(col, None)

    return result


def process_benchmark_results(directory: Path) -> pl.DataFrame:
    """Reads all benchmark results contained in a directory into a single data frame.
    """
    pattern = "**/*_summary.json"
    df = pl.DataFrame()
    for pth in directory.glob(pattern):
        try:
            row = (
                pl
                .read_json(pth)
                .with_columns(
                    pl.concat_str(pl.col("use_case"), pl.lit("_llmperf")).alias("use_case")
                )
                .select(
                    "results_mean_output_throughput_token_per_s",
                    PER_REQUEST_THROUGHPUT,
                    "results_ttft_s_mean",
                    "results_request_latency",
                    "num_concurrent_requests",
                    "use_case",
                    "system",
                    "model",
                )
            )
            if len(df) == 0:
                df = row
            else:
                df.extend(row)
        except:
            print(f"ERROR parsing {pth}")

    pattern = "*.json"
    return pl.DataFrame(_process_genai_output(pth) for pth in directory.glob(pattern)).with_columns(
        pl.col("output_token_throughput").alias("results_mean_output_throughput_token_per_s"),
        pl.col("output_token_throughput_per_request").alias(PER_REQUEST_THROUGHPUT),
        pl.col("time_to_first_token").alias("results_ttft_s_mean"),
        pl.col("concurrency").alias("num_concurrent_requests"),
        pl.col("shape").alias("system"),
    )


def _add_disclaimer(plot, df):
    """Adds a note to the bottom of the plot."""
    note = "Note: marker labels represent number of concurrent requests"

    if len(tps := df["tensor_parallel_size"].unique()) == 1:
        note += f"; tensor parallel size: {int(tps[0])}"

    if len(uses := df["use_case"].unique()) == 1:
        note += f"; use case: {uses[0]}"

    return plot.properties(title=alt.TitleParams(
            ["", note],
            baseline='bottom',
            orient='bottom',
            anchor='end',
            fontWeight='normal',
            fontSize=10))


def _filter_df(df, color):
    """Remove datapoints below threshold."""
    if ":" in color:
        color, _ = color.split(":", 1)
    colors = df[color].unique()
    for flavor in colors:
        values = df.filter(
            pl.col(color) == flavor,
            pl.col(PER_REQUEST_THROUGHPUT) <= PER_REQUEST_THROUGHPUT_THRESHOLD
        )[PER_REQUEST_THROUGHPUT]

        if len(values) >= 2:
            value = values[0]
            df = df.filter(
                (
                    pl.col(color) != flavor
                ).or_(
                    pl.col(PER_REQUEST_THROUGHPUT) >= value
                )
            )
    return df


def plot_token_throughput(df, model_title, system, color="use_case", size=None):
    df = _filter_df(df, color)
    line = alt.Chart(
        df, 
        title=alt.Title(f"{model_title} on {system}", 
        subtitle="Total token throughput vs. inference token throughput")
    ).mark_line(
        point=alt.OverlayMarkDef(filled=False, fill="white")
    ).encode(
        x="results_mean_output_throughput_token_per_s", 
        y=PER_REQUEST_THROUGHPUT,
        order="num_concurrent_requests",
        color=color,
    ).properties(
    )
    
    text = line.mark_text(
        align="left",
        baseline="middle",
        dx=6, dy=-6
    ).encode(text="num_concurrent_requests")

    return _add_disclaimer(alt.concat(line + text), df)

def plot_ttft(df, model_title, system, color="use_case"):
    df = _filter_df(df, color)
    line = alt.Chart(df, 
                     title=alt.Title(f"{model_title} on {system}", 
                     subtitle="Total token throughput vs. inference TTFT mean")).mark_line(
        point=alt.OverlayMarkDef(filled=False, fill="white")).encode(
        x="results_mean_output_throughput_token_per_s", 
        y=alt.Y("results_ttft_s_mean").scale(type="log"),
        order="num_concurrent_requests",
        color=alt.Color(color).legend(orient="right"),
    ).properties(
    )
    text = line.mark_text(
        align="left",
        baseline="middle",
        dx=6, dy=-6
    ).encode(text="num_concurrent_requests")
    
    return _add_disclaimer(alt.concat(line + text), df)

def plot_latency(df, model_title, system, color="use_case"):
    df = _filter_df(df, color)
    line = alt.Chart(df,
                     title=alt.Title(f"{model_title} on {system}",
                     subtitle="Total token throughput vs. inference latency")).mark_line(
        point=alt.OverlayMarkDef(filled=False, fill="white")).encode(
        x="results_mean_output_throughput_token_per_s",
        y="results_request_latency",
        order="num_concurrent_requests",
        color=alt.Color(color).legend(orient="right"),
    ).properties(
    )

    text = line.mark_text(
        align="left",
        baseline="middle",
        dx=6, dy=-6
    ).encode(text="num_concurrent_requests")
    
    return _add_disclaimer(alt.concat(line + text), df)

def generate_plots(basedir: Path, output: Path):
    """Generate plots and save them in the output directory.

    Takes a mapping to convert directories within the base directory to plot titles and shape names.
    """
    plots = []
    for pth in basedir.iterdir():
        if not pth.is_dir():
            continue
        results = process_benchmark_results(pth)
        if results.is_empty():
            continue
        model = results['model'].unique()[0]
        shape = results['system'].unique()[0]
        
        thru = plot_token_throughput(results, model, shape)
        thru.save(output / f"{pth.name}_token_throughput.png", scale_factor=3)
        ttft = plot_ttft(results, model, shape)
        ttft.save(output / f"{pth.name}_ttft.png", scale_factor=3)
        plots.extend([thru, ttft])
    return plots


def cli():
    import argparse
    parser = argparse.ArgumentParser("Plot LLM benchmarking data")
    parser.add_argument(
        "results",
        type=Path,
        default="results",
        nargs="?",
        help="The directory storing the results",
    )
    parser.add_argument(
        "plots",
        type=Path,
        default="plots",
        nargs="?",
        help="The directory to store the resulting plots in",
    )
    args = parser.parse_args()
    args.plots.mkdir(parents=True, exist_ok=True)

    data = process_benchmark_results(args.results)
    for (shape, model, tp), group in data.group_by("shape", "model", "tensor_parallel_size"):
        logging.warn(f"plotting {model} running on {shape}")
        group = group.group_by("use_case", "concurrency").mean()
        stub = f"{shape}__{model}__tp{tp}".lower()
    
        thru = plot_token_throughput(group, model, shape)
        thru.save(args.plots / f"{stub}__token_throughput.png", scale_factor=3)
        
        ttft = plot_ttft(group, model, shape)
        ttft.save(args.plots / f"{stub}__ttft.png", scale_factor=3)
