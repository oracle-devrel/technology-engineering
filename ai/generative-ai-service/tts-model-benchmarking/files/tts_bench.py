#!/usr/bin/env python3
"""Benchmark a text-to-speech endpoint on OCI Generative AI.

Measures, per language, input length, request mode and concurrency level:
  TTFA     time to first audio byte (what a listener waits before playback starts)
  E2E      end-to-end latency until the last byte
  audio_s  seconds of speech produced
  RTF      real-time factor = E2E / audio_s   (1.0 = as fast as the speech itself)
  err      error rate
  req/min and audio_s/s   throughput of the whole run at that concurrency
with p50 / p90 / p95 / p99 over `--n` requests per cell.

Modes
  sync      one request, stream=false; audio arrives as one body. TTFA = E2E.
  stream    one request, stream=true; TTFA = first non-empty chunk.
  chunked   client-side split at sentence ends into pieces of ~--chunk-seconds,
            sent one after another, same voice throughout. This is the workaround
            for models whose single-pass output degrades past a certain length.

Suites (presets; any flag overrides the preset)
  quick         smoke test, ~2 min                 en+ar, 10 s and 30 s, stream, n=3
  latency       latency vs input length            7 lengths x 3 modes, n=10
  long-text     where does single-pass degrade?    15..60 s, stream vs chunked, n=3, samples for wer.py
  concurrency   throughput and tail latency        15 s text, stream, 1/2/4/8/16 parallel
  full          latency + long-text + concurrency

Examples
  python tts_bench.py --suite quick --label H100_X1
  python tts_bench.py --suite latency --label H100_X1 --langs en
  python tts_bench.py --suite concurrency --concurrency 1,4,8 --n 24
  python tts_bench.py --durations 15,20,25,30 --modes stream,chunked --n 5 --score
  python tts_bench.py --suite full --label A10_X1 --score      # then: python plots.py results/<run>

Texts come from texts/<lang>_<name>.txt and are cut at the sentence end nearest
each target duration, using a per-language characters-per-second rate that is
calibrated from the warm-up requests. Results land in results/<label>_<time>/:
requests.csv (one row per request), summary.csv, summary.md, config.json and
samples/*.wav (first successful request per cell, for listening and for wer.py).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

from tts_client import TTSClient, TTSError, cut_at_sentence, pcm_seconds, pcm_to_wav, split_text

HERE = Path(__file__).resolve().parent
DEFAULT_CPS = {"en": 15.0, "ar": 12.0}      # chars of text per second of speech, before calibration
FALLBACK_CPS = 14.0

SUITES = {
    "quick":       dict(durations="10,30", modes="stream", n=3, concurrency="1", warmup=1),
    "latency":     dict(durations="10,15,20,25,30,40,60", modes="sync,stream,chunked", n=10, concurrency="1"),
    "long-text":   dict(durations="15,20,25,30,35,40,50,60", modes="stream,chunked", n=3, concurrency="1"),
    "concurrency": dict(durations="15", modes="stream", n=16, concurrency="1,2,4,8,16"),
}
SUITES["full"] = None   # expands to latency + long-text + concurrency

PCTS = (50, 90, 95, 99)


# --- data ----------------------------------------------------------------------

@dataclass
class Job:
    suite: str
    lang: str
    text_name: str
    text: str
    mode: str
    target_s: float
    concurrency: int
    idx: int
    chunk_chars: int


@dataclass
class Row:
    label: str
    suite: str
    lang: str
    text: str
    mode: str
    target_s: float
    chars: int
    pieces: int
    concurrency: int
    idx: int
    started_at: str
    ttfa_s: float | None
    e2e_s: float
    audio_s: float
    rtf: float | None
    bytes: int
    ok: bool
    error: str
    request_id: str
    pcm: bytes = field(default=b"", repr=False, compare=False)

    def csv_row(self) -> dict:
        d = asdict(self)
        d.pop("pcm")
        return d


# --- one request -----------------------------------------------------------------

def run_job(client: TTSClient, job: Job, voice: dict, label: str) -> Row:
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    t0 = time.perf_counter()
    ttfa = None
    audio = b""
    pieces = 1
    request_id = ""
    try:
        if job.mode == "sync":
            r = client.speak(job.text, response_format="pcm", language=job.lang, **voice)
            ttfa = time.perf_counter() - t0
            audio, request_id = r.audio, r.request_id or ""
        elif job.mode == "stream":
            parts = []
            with client.speak_stream(job.text, response_format="pcm", language=job.lang, **voice) as s:
                request_id = s.request_id or ""
                for chunk in s.chunks():
                    if chunk and ttfa is None:
                        ttfa = time.perf_counter() - t0
                    parts.append(chunk)
            audio = b"".join(parts)
        elif job.mode == "chunked":
            texts = split_text(job.text, job.chunk_chars)
            pieces = len(texts)
            kw = dict(voice)
            parts = []
            for i, piece in enumerate(texts):
                r = client.speak(piece, response_format="pcm", language=job.lang, **kw)
                request_id = r.request_id or request_id
                parts.append(r.audio)
                if i == 0:
                    ttfa = time.perf_counter() - t0
                    if "ref_audio" not in kw:        # no fixed voice: keep the first piece's voice
                        kw.update(ref_audio=pcm_to_wav(r.audio), ref_text=piece)
                        kw.pop("instructions", None)
            audio = b"".join(parts)
        else:
            raise ValueError(f"unknown mode {job.mode}")
        e2e = time.perf_counter() - t0
        secs = pcm_seconds(audio)
        return Row(label, job.suite, job.lang, job.text_name, job.mode, job.target_s, len(job.text), pieces,
                   job.concurrency, job.idx, started, ttfa, e2e, secs, (e2e / secs if secs else None),
                   len(audio), True, "", request_id, audio)
    except (TTSError, Exception) as exc:        # noqa: BLE001 - every failure is a data point
        e2e = time.perf_counter() - t0
        rid = getattr(exc, "request_id", None) or request_id or ""
        msg = " ".join(str(exc).split())[:300]
        return Row(label, job.suite, job.lang, job.text_name, job.mode, job.target_s, len(job.text), pieces,
                   job.concurrency, job.idx, started, None, e2e, 0.0, None, 0, False, msg, rid)


# --- aggregation -------------------------------------------------------------------

def pct(xs: list[float], p: int) -> float | None:
    return float(np.percentile(xs, p)) if xs else None


def summarise(rows: list[Row], wall: float) -> dict:
    ok = [r for r in rows if r.ok]
    ttfa = [r.ttfa_s for r in ok if r.ttfa_s is not None]
    e2e = [r.e2e_s for r in ok]
    aud = [r.audio_s for r in ok]
    rtf = [r.rtf for r in ok if r.rtf]
    first = rows[0]
    s = dict(label=first.label, suite=first.suite, lang=first.lang, text=first.text, mode=first.mode,
             target_s=first.target_s, chars=first.chars, pieces=first.pieces, concurrency=first.concurrency,
             n=len(rows), errors=len(rows) - len(ok), error_rate=(len(rows) - len(ok)) / len(rows),
             audio_s_mean=statistics.fmean(aud) if aud else None,
             rtf_p50=pct(rtf, 50),
             wall_s=wall, req_per_min=60 * len(ok) / wall if ok and wall else None,
             audio_s_per_s=sum(aud) / wall if ok and wall else None)
    for p in PCTS:
        s[f"ttfa_p{p}"] = pct(ttfa, p)
    for p in PCTS:
        s[f"e2e_p{p}"] = pct(e2e, p)
    return s


def fmt(v, w=6, d=2) -> str:
    return f"{v:{w}.{d}f}" if isinstance(v, (int, float)) and v is not None else " " * (w - 1) + "-"


HEADER = (f"{'mode':8s} {'lang':4s} {'text':10s} {'tgt_s':>5s} {'chars':>5s} {'conc':>4s} {'audio_s':>7s} "
          f"{'ttfa50':>6s} {'ttfa90':>6s} {'e2e50':>6s} {'e2e90':>6s} {'e2e99':>6s} {'rtf':>5s} {'err':>4s} "
          f"{'req/min':>7s} {'aud_s/s':>7s}")


def console_line(s: dict) -> str:
    return (f"{s['mode']:8s} {s['lang']:4s} {s['text'][:10]:10s} {s['target_s']:5.0f} {s['chars']:5d} {s['concurrency']:4d} "
            f"{fmt(s['audio_s_mean'], 7, 1)} {fmt(s['ttfa_p50'])} {fmt(s['ttfa_p90'])} {fmt(s['e2e_p50'])} "
            f"{fmt(s['e2e_p90'])} {fmt(s['e2e_p99'])} {fmt(s['rtf_p50'], 5)} {100 * s['error_rate']:3.0f}% "
            f"{fmt(s['req_per_min'], 7, 1)} {fmt(s['audio_s_per_s'], 7, 1)}")


# --- report --------------------------------------------------------------------------

def md_table(cells: list[dict], cols: list[tuple[str, str, int]]) -> str:
    head = "| " + " | ".join(c[1] for c in cols) + " |"
    sep = "|" + "|".join("---" if c[0] in ("lang", "text", "mode") else "---:" for c in cols) + "|"
    lines = [head, sep]
    for s in cells:
        vals = []
        for key, _, d in cols:
            v = s.get(key)
            if isinstance(v, float):
                vals.append(f"{100 * v:.0f}%" if key == "error_rate" else f"{v:.{d}f}")
            else:
                vals.append("-" if v is None else str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def write_report(run_dir: Path, cfg: dict, cells: list[dict], cps: dict, interrupted: bool) -> None:
    cols = [("lang", "lang", 0), ("text", "text", 0), ("mode", "mode", 0), ("target_s", "target s", 0),
            ("chars", "chars", 0), ("pieces", "pieces", 0), ("concurrency", "conc.", 0), ("n", "n", 0),
            ("audio_s_mean", "audio s", 1), ("ttfa_p50", "TTFA p50", 2), ("ttfa_p90", "TTFA p90", 2),
            ("e2e_p50", "E2E p50", 2), ("e2e_p90", "E2E p90", 2), ("e2e_p95", "E2E p95", 2),
            ("e2e_p99", "E2E p99", 2), ("rtf_p50", "RTF", 2), ("error_rate", "errors", 0),
            ("req_per_min", "req/min", 1), ("audio_s_per_s", "audio s/s", 1)]
    out = [f"# TTS benchmark: {cfg['label']}", "",
           f"Run started {cfg['started']} on {cfg['host']} with `{cfg['command']}`." + (" **Interrupted; partial results.**" if interrupted else ""),
           "", f"- Model: `{cfg['model']}`", f"- Auth: {cfg['auth_mode']}, inference host `{cfg['url']}`",
           f"- Voice: {cfg['voice']}", f"- Chunked mode cuts at ~{cfg['chunk_seconds']} s per piece",
           "- Characters per second of speech (calibrated): " + ", ".join(f"{k} {v:.1f}" for k, v in cps.items()),
           f"- Warm-up requests per language (not counted): {cfg['warmup']}", ""]
    out += ["## How to read it", "",
            "- **TTFA** is the time until the first audio byte, **E2E** until the last. For a listener, TTFA is the pause before playback and E2E the time until the clip is complete.",
            "- **RTF** (real-time factor) is E2E divided by seconds of speech produced. Below 1.0 the model generates faster than it plays; a streaming player can keep up.",
            "- **req/min** and **audio s/s** are the throughput of the whole cell at that concurrency; compare them across concurrency levels to find where the endpoint saturates (latency rises, throughput flattens).",
            "- `stream` and `sync` send the whole text in one request. `chunked` splits it client-side; its TTFA is the first piece and its E2E the last, as a player pipelining the pieces would see it.",
            "- Latency does not show quality. Listen to `samples/*.wav` or score them with `python wer.py <run dir>` to see where single-pass output degrades.", ""]
    for suite in dict.fromkeys(c["suite"] for c in cells):
        out += [f"## Suite: {suite}", "", md_table([c for c in cells if c["suite"] == suite], cols), ""]
    (run_dir / "summary.md").write_text("\n".join(out), encoding="utf-8")


# --- main ------------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 1)[1])
    ap.add_argument("--suite", choices=list(SUITES), default="quick")
    ap.add_argument("--label", default=None, help="name for this run, e.g. the hosting shape: H100_X1 (default: suite name)")
    ap.add_argument("--langs", default=None, help="comma list of language codes matching texts/<lang>_*.txt (default: all present)")
    ap.add_argument("--texts", type=Path, default=HERE / "texts", help="folder with <lang>_<name>.txt files")
    ap.add_argument("--text-names", default=None, help="comma list of text names to use, e.g. science,coffee (default: all)")
    ap.add_argument("--durations", default=None, help="comma list of target audio seconds, e.g. 15,20,25,30")
    ap.add_argument("--modes", default=None, help="comma list of sync,stream,chunked")
    ap.add_argument("--concurrency", default=None, help="comma list of parallel request counts, e.g. 1,4,8")
    ap.add_argument("--n", type=int, default=None, help="measured requests per cell (per language, text, duration, mode, concurrency)")
    ap.add_argument("--warmup", type=int, default=None, help="uncounted requests per language before measuring; also calibrates chars/second")
    ap.add_argument("--chunk-seconds", type=float, default=15.0, help="target seconds of speech per piece in chunked mode")
    ap.add_argument("--chars-per-second", default=None, help="skip calibration and use these rates, e.g. en=15,ar=12")
    ap.add_argument("--voice", choices=["clone", "design", "preset", "none"], default="clone",
                    help="clone: send --ref-audio with every request (default, constant voice); design: send --instructions; "
                         "preset: send --voice-name (models with built-in voices); none: let the model pick")
    ap.add_argument("--ref-audio", type=Path, default=HERE / "voices" / "ref_voice.wav")
    ap.add_argument("--ref-text", default=None, help="transcript of --ref-audio (default: the .txt next to it, if any)")
    ap.add_argument("--instructions", default="a calm, clear adult voice at a natural pace")
    ap.add_argument("--voice-name", default=None, help="preset voice name for --voice preset")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--timeout", type=float, default=300.0, help="per-request HTTP timeout in seconds")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    ap.add_argument("--no-samples", action="store_true", help="do not keep a sample wav per cell")
    ap.add_argument("--score", action="store_true", help="after the run, transcribe the samples and report WER/CER (needs a whisper backend)")
    ap.add_argument("--model", default=None, help="override TTS_MODEL")
    ap.add_argument("--profile", default=None, help="override OCI_CONFIG_PROFILE")
    ap.add_argument("--auth", choices=["api_key", "resource_principal", "instance_principal", "security_token", "bearer"],
                    default=None, help="override OCI_AUTH")
    return ap.parse_args()


def expand_suites(args) -> list[dict]:
    """One plan per suite; `full` is three plans. Explicit flags override presets."""
    names = ["latency", "long-text", "concurrency"] if args.suite == "full" else [args.suite]
    plans = []
    for name in names:
        p = dict(SUITES[name], suite=name)
        for k in ("durations", "modes", "concurrency", "n", "warmup"):
            if getattr(args, k) is not None:
                p[k] = getattr(args, k)
        p["durations"] = [float(x) for x in str(p["durations"]).split(",")]
        p["modes"] = str(p["modes"]).split(",")
        p["concurrency"] = [int(x) for x in str(p["concurrency"]).split(",")]
        p.setdefault("warmup", 2)
        plans.append(p)
    return plans


def load_texts(folder: Path, langs: list[str] | None, names: list[str] | None) -> dict[str, dict[str, str]]:
    texts: dict[str, dict[str, str]] = {}
    for p in sorted(folder.glob("*_*.txt")):
        lang, name = p.stem.split("_", 1)
        if (langs and lang not in langs) or (names and name not in names):
            continue
        texts.setdefault(lang, {})[name] = " ".join(p.read_text(encoding="utf-8").split())
    if not texts:
        sys.exit(f"no texts found in {folder} (expected <lang>_<name>.txt)")
    return texts


def main() -> None:
    load_dotenv(HERE / ".env")
    load_dotenv()
    args = parse_args()
    plans = expand_suites(args)
    label = args.label or args.suite
    langs = args.langs.split(",") if args.langs else None
    texts = load_texts(args.texts, langs, args.text_names.split(",") if args.text_names else None)

    voice: dict = {}
    if args.voice == "clone":
        if not args.ref_audio.exists():
            sys.exit(f"--voice clone needs a reference clip; {args.ref_audio} not found")
        ref_txt = args.ref_text or (args.ref_audio.with_suffix(".txt").read_text(encoding="utf-8").strip()
                                    if args.ref_audio.with_suffix(".txt").exists() else None)
        from tts_client import data_uri
        voice = dict(ref_audio=data_uri(args.ref_audio), ref_text=ref_txt)   # encode once, reuse per request
    elif args.voice == "design":
        voice = dict(instructions=args.instructions)
    elif args.voice == "preset":
        if not args.voice_name:
            sys.exit("--voice preset needs --voice-name")
        voice = dict(voice=args.voice_name)
    if args.speed:
        voice["speed"] = args.speed

    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_dir = args.out / f"{label}_{stamp}"
    (run_dir / "samples").mkdir(parents=True, exist_ok=True)
    csv_path = run_dir / "requests.csv"
    client = TTSClient(model=args.model, profile=args.profile, auth_mode=args.auth, timeout=args.timeout)
    cfg = dict(label=label, started=time.strftime("%Y-%m-%d %H:%M:%S"), host=platform.node(),
               command=" ".join(["python"] + [Path(sys.argv[0]).name] + sys.argv[1:]), model=client.model,
               auth_mode=client.auth_mode, url=client.url, voice=args.voice + (f" ({args.ref_audio.name})" if args.voice == "clone" else ""),
               chunk_seconds=args.chunk_seconds, warmup=plans[0]["warmup"], suites=plans, langs=sorted(texts),
               texts={l: sorted(t) for l, t in texts.items()}, python=platform.python_version())
    print(f"model {client.model}\nauth  {client.auth_mode} -> {client.url}\nout   {run_dir}\n")

    # -- warm-up and calibration: how many characters make one second of speech, per language
    cps: dict[str, float] = {}
    fixed = dict(kv.split("=") for kv in args.chars_per_second.split(",")) if args.chars_per_second else {}
    for lang, by_name in texts.items():
        if lang in fixed:
            cps[lang] = float(fixed[lang])
            continue
        guess = DEFAULT_CPS.get(lang, FALLBACK_CPS)
        name, full = next(iter(by_name.items()))
        probe = cut_at_sentence(full, int(10 * guess))
        ratios = []
        for i in range(max(1, plans[0]["warmup"])):
            r = run_job(client, Job("warmup", lang, name, probe, "sync", 10, 1, i, 10**6), voice, label)
            if r.ok and r.audio_s > 0.5:
                ratios.append(r.chars / r.audio_s)
            elif not r.ok:
                print(f"warm-up {lang}: {r.error}")
        cps[lang] = statistics.median(ratios) if ratios else guess
        print(f"warm-up {lang}: {len(ratios)} ok, {cps[lang]:.1f} chars per second of speech"
              + ("" if ratios else " (default, calibration failed)"))
    cfg["chars_per_second"] = cps
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")

    # -- the measured cells
    cells: list[dict] = []
    interrupted = False
    fieldnames = list(Row.__dataclass_fields__)
    fieldnames.remove("pcm")
    print("\n" + HEADER)
    try:
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for plan in plans:
                for conc in plan["concurrency"]:
                    for mode in plan["modes"]:
                        for lang, by_name in texts.items():
                            chunk_chars = max(40, int(args.chunk_seconds * cps[lang]))
                            for name, full in by_name.items():
                                for target in plan["durations"]:
                                    want = int(target * cps[lang])
                                    text = cut_at_sentence(full, want)
                                    if len(full) < want * 0.8:
                                        print(f"note: {lang}_{name} has {len(full)} chars, too short for {target:.0f} s; using all of it")
                                    jobs = [Job(plan["suite"], lang, name, text, mode, target, conc, i, chunk_chars) for i in range(plan["n"])]
                                    t0 = time.perf_counter()
                                    with ThreadPoolExecutor(conc) as pool:
                                        rows = list(pool.map(lambda j: run_job(client, j, voice, label), jobs))
                                    wall = time.perf_counter() - t0
                                    for r in rows:
                                        writer.writerow(r.csv_row())
                                    fh.flush()
                                    if not args.no_samples:
                                        first = next((r for r in rows if r.ok), None)
                                        if first:
                                            stem = run_dir / "samples" / f"{lang}__{name}__{mode}__{target:.0f}s"
                                            if not stem.with_suffix(".wav").exists():
                                                stem.with_suffix(".wav").write_bytes(pcm_to_wav(first.pcm))
                                                stem.with_suffix(".txt").write_text(text, encoding="utf-8")
                                    s = summarise(rows, wall)
                                    cells.append(s)
                                    print(console_line(s), flush=True)
                                    errs = {r.error for r in rows if not r.ok}
                                    for e in list(errs)[:2]:
                                        print(f"    error: {e[:160]}")
    except KeyboardInterrupt:
        interrupted = True
        print("\ninterrupted; writing partial results")
    finally:
        client.close()
        if cells:
            with open(run_dir / "summary.csv", "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(cells[0]))
                w.writeheader()
                w.writerows(cells)
            write_report(run_dir, cfg, cells, cps, interrupted)
        print(f"\nresults: {run_dir}\n  requests.csv  one row per request\n  summary.csv / summary.md  per cell\n  samples/  one wav per cell")

    if args.score and cells and not interrupted:
        try:
            import wer
        except ImportError as exc:
            sys.exit(f"--score: {exc}")
        wer.score_run(run_dir)
    elif cells:
        print(f"\nnext: python plots.py {run_dir}        # charts\n      python wer.py {run_dir}          # intelligibility (needs a whisper backend)")


if __name__ == "__main__":
    main()
