"""Benchmark pywebrtc-audio throughput.

Usage:
    python bench.py          # quick run (~30s) - 16kHz int16, key combos
    python bench.py --full   # exhaustive - all sample rates, dtypes, chunk sizes, stereo
"""

import argparse
import json
import platform
import subprocess
import time
import uuid
from datetime import datetime, timezone

import numpy as np

from pywebrtc_audio import (
    AudioProcessor,
    EchoCanceller,
    GainController,
    NoiseSuppressor,
    VoiceDetector,
)

WARMUP_ITERS = 5
MIN_BENCH_TIME = 2.0


def _get_cpu_name():
    try:
        if platform.system() == "Darwin":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        elif platform.system() == "Linux":
            out = subprocess.check_output(["lscpu"]).decode()
            for line in out.splitlines():
                if line.startswith("Model name:"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()


def make_noise(n_samples, dtype, rng):
    if dtype == np.int16:
        return rng.integers(-3000, 3000, size=n_samples, dtype=np.int16)
    return rng.uniform(-0.1, 0.1, size=n_samples).astype(np.float32)


def bench(fn, warmup=WARMUP_ITERS, min_time=MIN_BENCH_TIME):
    for _ in range(warmup):
        fn()

    iters = 0
    elapsed = 0.0
    while elapsed < min_time:
        batch = max(1, iters)
        t0 = time.perf_counter()
        for _ in range(batch):
            fn()
        elapsed += time.perf_counter() - t0
        iters += batch

    return elapsed / iters


def bench_one(name, fn, sr, dtype_name, dur, n, results):
    t = bench(fn)
    rt = dur / t
    results.append({
        "class": name, "sample_rate": sr, "dtype": dtype_name,
        "duration_s": dur, "samples": n,
        "time_per_call_us": t * 1e6, "realtime_factor": rt,
    })
    print(f"  {name:24s} {sr}Hz/{dtype_name}/{dur}s ({n:>6} samples): {t*1e6:8.1f} µs  ({rt:6.1f}x RT)")


def run_benchmarks(full=False):
    rng = np.random.default_rng(42)
    results = []

    sample_rates = [16000, 32000, 48000] if full else [16000]
    dtypes = [(np.int16, "int16"), (np.float32, "float32")] if full else [(np.int16, "int16")]
    durations = [0.01, 0.02, 0.1, 0.5, 1.0, 5.0, 10.0] if full else [0.01, 0.1]

    ap_combos = [
        ("AP(ns)", {"noise_suppression": True}),
        ("AP(aec)", {"echo_cancellation": True}),
        ("AP(agc)", {"auto_gain_control": True}),
        ("AP(aec+ns)", {"echo_cancellation": True, "noise_suppression": True}),
        ("AP(aec+ns+agc)", {"echo_cancellation": True, "noise_suppression": True,
                            "auto_gain_control": True}),
        ("AP(all)", {"echo_cancellation": True, "noise_suppression": True,
                     "auto_gain_control": True, "high_pass_filter": True}),
    ]
    if not full:
        ap_combos = [
            ("AP(ns)", {"noise_suppression": True}),
            ("AP(aec)", {"echo_cancellation": True}),
            ("AP(aec+ns+agc)", {"echo_cancellation": True, "noise_suppression": True,
                                "auto_gain_control": True}),
        ]

    mode = "full" if full else "quick"
    print(f"Running {mode} benchmark...\n")

    for sr in sample_rates:
        for dtype, dtype_name in dtypes:
            for dur in durations:
                n = int(sr * dur)
                near = make_noise(n, dtype, rng)
                far = make_noise(n, dtype, rng)

                bench_one("NoiseSuppressor", lambda: ns.process(near), sr, dtype_name, dur, n, results) if False else None
                ns = NoiseSuppressor(sample_rate=sr)
                bench_one("NoiseSuppressor", lambda: ns.process(near), sr, dtype_name, dur, n, results)

                ec = EchoCanceller(sample_rate=sr)
                bench_one("EchoCanceller", lambda: ec.process(near, far), sr, dtype_name, dur, n, results)

                gc = GainController(sample_rate=sr)
                bench_one("GainController", lambda: gc.process(near), sr, dtype_name, dur, n, results)

                vd = VoiceDetector(sample_rate=sr)
                bench_one("VoiceDetector", lambda: vd.process(near), sr, dtype_name, dur, n, results)

                for combo_name, kwargs in ap_combos:
                    ap = AudioProcessor(sample_rate=sr, **kwargs)
                    needs_far = kwargs.get("echo_cancellation", False)
                    fn = (lambda: ap.process(near, far)) if needs_far else (lambda: ap.process(near))
                    bench_one(combo_name, fn, sr, dtype_name, dur, n, results)

    if full:
        print("\n--- Stereo (2ch) ---")
        for sr in sample_rates:
            for dtype, dtype_name in dtypes:
                dur = 1.0
                n = int(sr * dur * 2)
                near = make_noise(n, dtype, rng)
                far = make_noise(n, dtype, rng)

                ap = AudioProcessor(sample_rate=sr, num_channels=2,
                                    echo_cancellation=True, noise_suppression=True,
                                    auto_gain_control=True)
                bench_one("AP(aec+ns+agc) stereo", lambda: ap.process(near, far),
                          sr, dtype_name, dur, n, results)

    meta = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": _get_cpu_name(),
        "numpy": np.__version__,
        "mode": mode,
    }

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = uuid.uuid4().hex[:8]
    filename = f"bench_results_{mode}_{ts}_{uid}.json"
    with open(filename, "w") as f:
        json.dump({"meta": meta, "results": results}, f, indent=2)

    print(f"\nResults saved to {filename}")
    print(f"System: {meta['platform']}, {meta['processor']}, Python {meta['python']}, NumPy {meta['numpy']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark pywebrtc-audio throughput")
    parser.add_argument("--full", action="store_true", help="Run exhaustive benchmarks (all sample rates, dtypes, chunk sizes, stereo)")
    args = parser.parse_args()
    run_benchmarks(full=args.full)
