#!/usr/bin/env python3
"""Score the sample audio of a benchmark run for intelligibility.

Transcribes every results/<run>/samples/*.wav with Whisper and compares the
transcript with the text that was sent, giving word error rate (WER) and
character error rate (CER). This is how the "speech turns to babble past N
seconds" problem shows up as a number: WER stays in the low single digits
for good audio and jumps to 30-60% where the model degrades.

    python wer.py results/H100_X1_20261002-160726
    python wer.py results/<run> --model small --device cpu      # faster, less accurate
    python wer.py results/<run> --backend faster-whisper --device cuda

Backends (install one):  pip install faster-whisper   (CPU or NVIDIA GPU; OCI Data Science)
                         pip install openai-whisper   (reference, needs ffmpeg)
                         pip install mlx-whisper      (Apple Silicon)

Text normalisation before scoring: lower-case, punctuation removed; Arabic
additionally loses diacritics and tatweel, and alef / yaa / taa-marbuta
variants are unified (the usual Arabic ASR normalisation). Digits are left
as written, so texts with many numbers score a few points worse than their
audio deserves because Whisper may write "4.82" where the text says "4.82
million" or vice versa. Compare modes on the same text, not texts to each other.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_AR_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_PUNCT = re.compile(r"[^\w\s]|_", re.UNICODE)


def normalise(text: str, lang: str) -> list[str]:
    text = text.lower().replace("-", " ")
    if lang == "ar":
        text = _AR_DIACRITICS.sub("", text)
        text = re.sub("[إأآا]", "ا", text)
        text = text.replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    return _PUNCT.sub(" ", text).split()


def edit_distance(ref: list, hyp: list) -> int:
    d = list(range(len(hyp) + 1))
    for i in range(1, len(ref) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(hyp) + 1):
            cur = d[j]
            d[j] = min(d[j] + 1, d[j - 1] + 1, prev + (ref[i - 1] != hyp[j - 1]))
            prev = cur
    return d[-1]


def wer(ref: list[str], hyp: list[str]) -> float:
    return edit_distance(ref, hyp) / max(1, len(ref))


def cer(ref: list[str], hyp: list[str]) -> float:
    r, h = list(" ".join(ref)), list(" ".join(hyp))
    return edit_distance(r, h) / max(1, len(r))


# --- transcription backends -----------------------------------------------------

def pick_backend(name: str) -> str:
    order = [name] if name != "auto" else ["faster-whisper", "mlx-whisper", "openai-whisper"]
    mods = {"faster-whisper": "faster_whisper", "mlx-whisper": "mlx_whisper", "openai-whisper": "whisper"}
    for b in order:
        try:
            __import__(mods[b])
            return b
        except ImportError:
            continue
    sys.exit("no transcription backend found; pip install faster-whisper (or openai-whisper, or mlx-whisper on a Mac)")


class Transcriber:
    def __init__(self, backend: str, model: str, device: str):
        self.backend = backend
        if backend == "faster-whisper":
            from faster_whisper import WhisperModel
            dev = device
            if dev == "auto":
                try:
                    import torch  # noqa: F401
                    dev = "cuda" if __import__("torch").cuda.is_available() else "cpu"
                except ImportError:
                    dev = "cpu"
            self.m = WhisperModel(model, device=dev, compute_type="float16" if dev == "cuda" else "int8")
        elif backend == "openai-whisper":
            import whisper
            self.m = whisper.load_model(model, device=None if device == "auto" else device)
        else:
            import mlx_whisper
            self.m = mlx_whisper
            self.repo = model if "/" in model else f"mlx-community/whisper-{model}"

    def __call__(self, path: Path, lang: str) -> str:
        if self.backend == "faster-whisper":
            segs, _ = self.m.transcribe(str(path), language=lang, condition_on_previous_text=False, beam_size=5)
            return " ".join(s.text for s in segs)
        if self.backend == "openai-whisper":
            return self.m.transcribe(str(path), language=lang, condition_on_previous_text=False)["text"]
        return self.m.transcribe(str(path), path_or_hf_repo=self.repo, language=lang, condition_on_previous_text=False)["text"]


# --- scoring a run ---------------------------------------------------------------------

def score_run(run_dir: Path, model: str = "large-v3-turbo", device: str = "auto", backend: str = "auto") -> list[dict]:
    run_dir = Path(run_dir)
    wavs = sorted((run_dir / "samples").glob("*.wav"))
    if not wavs:
        sys.exit(f"no samples in {run_dir / 'samples'}")
    backend = pick_backend(backend)
    print(f"transcribing {len(wavs)} clips with {backend} / {model} ...")
    asr = Transcriber(backend, model, device)
    rows = []
    print(f"{'lang':4s} {'text':10s} {'mode':8s} {'target_s':>8s} {'words':>5s} {'WER':>7s} {'CER':>7s}")
    for wav in wavs:
        lang, text, mode, target = wav.stem.split("__")
        ref_text = wav.with_suffix(".txt").read_text(encoding="utf-8")
        hyp_text = asr(wav, lang)
        ref, hyp = normalise(ref_text, lang), normalise(hyp_text, lang)
        row = dict(lang=lang, text=text, mode=mode, target_s=float(target.rstrip("s")), words=len(ref),
                   wer=wer(ref, hyp), cer=cer(ref, hyp), file=wav.name, transcript=hyp_text.strip())
        rows.append(row)
        print(f"{lang:4s} {text[:10]:10s} {mode:8s} {row['target_s']:8.0f} {len(ref):5d} {100 * row['wer']:6.1f}% {100 * row['cer']:6.1f}%", flush=True)
    out = run_dir / "wer.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    md = run_dir / "summary.md"
    if md.exists():
        lines = ["", "## Intelligibility (Whisper WER / CER of one sample per cell)", "",
                 f"Backend {backend}, model {model}. WER under 5% is good audio; a jump to tens of percent marks where the model degrades.", "",
                 "| lang | text | mode | target s | words | WER | CER |", "|---|---|---|---:|---:|---:|---:|"]
        lines += [f"| {r['lang']} | {r['text']} | {r['mode']} | {r['target_s']:.0f} | {r['words']} | {100 * r['wer']:.1f}% | {100 * r['cer']:.1f}% |" for r in rows]
        with open(md, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    print(f"\nwrote {out}" + (f" and appended to {md}" if md.exists() else ""))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n", 1)[1])
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--model", default="large-v3-turbo", help="whisper size: tiny, base, small, medium, large-v3, large-v3-turbo")
    ap.add_argument("--device", default="auto", help="auto, cpu or cuda")
    ap.add_argument("--backend", default="auto", choices=["auto", "faster-whisper", "openai-whisper", "mlx-whisper"])
    a = ap.parse_args()
    score_run(a.run_dir, a.model, a.device, a.backend)


if __name__ == "__main__":
    main()
