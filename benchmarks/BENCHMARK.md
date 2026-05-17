# Benchmarks

Throughput benchmarks for all processing classes across sample rates, dtypes, and chunk sizes. All numbers are from a single run on one machine - your results will vary by CPU, but the relative ordering and realtime factors should be similar.

Run the benchmarks yourself:

```bash
python bench.py          # quick (~30s) - 16kHz int16, key combos
python bench.py --full   # exhaustive - all sample rates, dtypes, chunk sizes, stereo
```

## Test environment

- Apple M3 Pro
- macOS 26.3.1 (arm64)
- Python 3.12.12
- NumPy 2.2.6

## Summary

Everything runs well above real-time. The GIL is released during processing, so these numbers reflect pure C++ throughput.

At 16kHz (the most common voice sample rate), processing 100ms of audio:

| Component | int16 | float32 |
|-----------|------:|--------:|
| VoiceDetector | 4,665x RT | 4,899x RT |
| NoiseSuppressor | 3,089x RT | 2,924x RT |
| GainController | 970x RT | 962x RT |
| EchoCanceller | 161x RT | 161x RT |
| AudioProcessor (NS) | 2,823x RT | 2,927x RT |
| AudioProcessor (AEC) | 153x RT | 156x RT |
| AudioProcessor (AEC+NS+AGC) | 154x RT | 150x RT |
| AudioProcessor (all features) | 146x RT | 150x RT |

Echo cancellation dominates the cost. Noise suppression and AGC add minimal overhead on top of AEC. The full pipeline (AEC+NS+AGC+HPF) runs at ~150x real-time at 16kHz, meaning it processes 1 second of audio in ~6.8ms.

## Detailed results

### 16kHz int16

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 2 µs | 4 µs | 21 µs | 108 µs | 209 µs | 1,054 µs | 2,151 µs |
| NoiseSuppressor | 4 µs | 7 µs | 32 µs | 176 µs | 351 µs | 1,810 µs | 3,515 µs |
| GainController | 11 µs | 21 µs | 103 µs | 555 µs | 1,105 µs | 5,742 µs | 11,426 µs |
| EchoCanceller | 60 µs | 122 µs | 622 µs | 3,263 µs | 6,453 µs | 32,480 µs | 64,422 µs |
| AP(ns) | 4 µs | 7 µs | 35 µs | 179 µs | 351 µs | 1,760 µs | 3,583 µs |
| AP(aec) | 60 µs | 125 µs | 655 µs | 3,333 µs | 6,732 µs | 33,688 µs | 68,457 µs |
| AP(agc) | 11 µs | 21 µs | 100 µs | 571 µs | 1,115 µs | 5,643 µs | 11,446 µs |
| AP(aec+ns) | 63 µs | 126 µs | 649 µs | 3,373 µs | 6,948 µs | 34,243 µs | 68,276 µs |
| AP(aec+ns+agc) | 62 µs | 130 µs | 649 µs | 3,411 µs | 6,935 µs | 34,897 µs | 68,797 µs |
| AP(all) | 64 µs | 127 µs | 686 µs | 3,393 µs | 6,995 µs | 34,488 µs | 68,971 µs |

### 16kHz float32

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 2 µs | 4 µs | 20 µs | 99 µs | 203 µs | 1,034 µs | 1,987 µs |
| NoiseSuppressor | 4 µs | 7 µs | 34 µs | 168 µs | 338 µs | 1,670 µs | 3,431 µs |
| GainController | 12 µs | 23 µs | 104 µs | 525 µs | 1,040 µs | 5,238 µs | 10,366 µs |
| EchoCanceller | 66 µs | 129 µs | 623 µs | 3,161 µs | 5,824 µs | 29,860 µs | 62,715 µs |
| AP(ns) | 4 µs | 7 µs | 34 µs | 172 µs | 334 µs | 1,691 µs | 3,349 µs |
| AP(aec) | 69 µs | 136 µs | 643 µs | 3,141 µs | 6,218 µs | 31,550 µs | 63,169 µs |
| AP(agc) | 12 µs | 23 µs | 106 µs | 513 µs | 1,006 µs | 5,292 µs | 10,273 µs |
| AP(aec+ns) | 70 µs | 144 µs | 665 µs | 3,216 µs | 6,064 µs | 32,082 µs | 62,726 µs |
| AP(aec+ns+agc) | 68 µs | 136 µs | 666 µs | 3,266 µs | 6,130 µs | 32,584 µs | 66,161 µs |
| AP(all) | 68 µs | 134 µs | 666 µs | 3,277 µs | 6,205 µs | 33,573 µs | 64,754 µs |

### 32kHz int16

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 5 µs | 10 µs | 48 µs | 250 µs | 464 µs | 2,308 µs | 4,768 µs |
| NoiseSuppressor | 10 µs | 19 µs | 89 µs | 458 µs | 893 µs | 4,603 µs | 9,179 µs |
| GainController | 11 µs | 23 µs | 109 µs | 537 µs | 1,054 µs | 5,449 µs | 11,095 µs |
| EchoCanceller | 76 µs | 153 µs | 730 µs | 3,577 µs | 6,911 µs | 37,407 µs | 71,623 µs |
| AP(ns) | 10 µs | 19 µs | 93 µs | 441 µs | 906 µs | 4,402 µs | 8,909 µs |
| AP(aec) | 78 µs | 143 µs | 714 µs | 3,548 µs | 7,201 µs | 35,980 µs | 75,392 µs |
| AP(agc) | 17 µs | 33 µs | 156 µs | 799 µs | 1,611 µs | 8,230 µs | 16,951 µs |
| AP(aec+ns) | 75 µs | 147 µs | 719 µs | 3,598 µs | 7,057 µs | 37,187 µs | 76,813 µs |
| AP(aec+ns+agc) | 78 µs | 156 µs | 729 µs | 3,656 µs | 7,239 µs | 37,686 µs | 77,005 µs |
| AP(all) | 80 µs | 149 µs | 751 µs | 3,942 µs | 7,178 µs | 40,305 µs | 76,207 µs |

### 32kHz float32

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 5 µs | 10 µs | 47 µs | 240 µs | 487 µs | 2,533 µs | 4,968 µs |
| NoiseSuppressor | 10 µs | 19 µs | 87 µs | 455 µs | 928 µs | 4,682 µs | 9,299 µs |
| GainController | 12 µs | 23 µs | 108 µs | 559 µs | 1,081 µs | 5,559 µs | 11,087 µs |
| EchoCanceller | 74 µs | 147 µs | 725 µs | 3,635 µs | 7,193 µs | 35,732 µs | 73,654 µs |
| AP(ns) | 10 µs | 18 µs | 90 µs | 451 µs | 919 µs | 4,628 µs | 9,901 µs |
| AP(aec) | 74 µs | 146 µs | 710 µs | 3,587 µs | 7,024 µs | 36,273 µs | 76,621 µs |
| AP(agc) | 17 µs | 34 µs | 170 µs | 845 µs | 1,611 µs | 8,460 µs | 17,319 µs |
| AP(aec+ns) | 75 µs | 152 µs | 758 µs | 3,592 µs | 7,342 µs | 37,607 µs | 74,890 µs |
| AP(aec+ns+agc) | 77 µs | 154 µs | 737 µs | 3,600 µs | 7,284 µs | 36,629 µs | 76,320 µs |
| AP(all) | 77 µs | 148 µs | 738 µs | 3,680 µs | 7,555 µs | 37,708 µs | 77,807 µs |

### 48kHz int16

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 7 µs | 14 µs | 75 µs | 360 µs | 685 µs | 3,471 µs | 7,414 µs |
| NoiseSuppressor | 14 µs | 29 µs | 139 µs | 722 µs | 1,379 µs | 6,992 µs | 14,065 µs |
| GainController | 13 µs | 24 µs | 129 µs | 593 µs | 1,212 µs | 5,877 µs | 11,615 µs |
| EchoCanceller | 88 µs | 175 µs | 900 µs | 4,323 µs | 8,264 µs | 41,943 µs | 86,451 µs |
| AP(ns) | 14 µs | 29 µs | 146 µs | 710 µs | 1,366 µs | 7,002 µs | 14,783 µs |
| AP(aec) | 84 µs | 163 µs | 829 µs | 4,212 µs | 8,114 µs | 42,371 µs | 86,287 µs |
| AP(agc) | 22 µs | 46 µs | 224 µs | 1,109 µs | 2,179 µs | 11,142 µs | 24,059 µs |
| AP(aec+ns) | 87 µs | 171 µs | 820 µs | 4,220 µs | 8,235 µs | 41,353 µs | 87,156 µs |
| AP(aec+ns+agc) | 88 µs | 176 µs | 842 µs | 4,134 µs | 8,308 µs | 41,669 µs | 91,244 µs |
| AP(all) | 89 µs | 177 µs | 853 µs | 4,134 µs | 8,654 µs | 41,451 µs | 88,066 µs |

### 48kHz float32

| Component | 10ms | 20ms | 100ms | 500ms | 1s | 5s | 10s |
|-----------|-----:|-----:|------:|------:|---:|---:|----:|
| VoiceDetector | 7 µs | 15 µs | 73 µs | 364 µs | 701 µs | 3,425 µs | 6,984 µs |
| NoiseSuppressor | 15 µs | 30 µs | 144 µs | 732 µs | 1,377 µs | 6,793 µs | 13,587 µs |
| GainController | 13 µs | 25 µs | 127 µs | 624 µs | 1,179 µs | 6,001 µs | 11,742 µs |
| EchoCanceller | 91 µs | 182 µs | 885 µs | 4,441 µs | 8,456 µs | 42,182 µs | 83,298 µs |
| AP(ns) | 15 µs | 29 µs | 149 µs | 722 µs | 1,362 µs | 6,831 µs | 13,960 µs |
| AP(aec) | 87 µs | 171 µs | 891 µs | 4,083 µs | 8,208 µs | 40,211 µs | 80,452 µs |
| AP(agc) | 25 µs | 48 µs | 241 µs | 1,089 µs | 2,201 µs | 10,943 µs | 22,052 µs |
| AP(aec+ns) | 89 µs | 179 µs | 875 µs | 4,040 µs | 8,032 µs | 40,484 µs | 82,239 µs |
| AP(aec+ns+agc) | 91 µs | 178 µs | 886 µs | 4,222 µs | 8,303 µs | 41,511 µs | 83,672 µs |
| AP(all) | 91 µs | 177 µs | 907 µs | 4,120 µs | 8,211 µs | 41,341 µs | 86,242 µs |

### Stereo (2 channels, 1 second of audio)

| Sample rate | int16 | float32 |
|-------------|------:|--------:|
| 16kHz | 8,782 µs (114x RT) | 8,788 µs (114x RT) |
| 32kHz | 10,819 µs (92x RT) | 10,785 µs (93x RT) |
| 48kHz | 12,259 µs (82x RT) | 12,043 µs (83x RT) |

Full pipeline (AEC+NS+AGC). Stereo is roughly 1.3x the cost of mono at the same sample rate due to per-channel processing.

## Observations

- Processing time scales linearly with audio duration - no per-call overhead worth worrying about.
- int16 and float32 perform nearly identically. The conversion overhead is negligible compared to the DSP work.
- Echo cancellation (AEC3) is by far the most expensive operation, accounting for ~95% of the full pipeline cost. This is expected - AEC3 maintains an adaptive filter with significant state.
- Noise suppression and AGC add minimal overhead when AEC is already enabled, because the frequency-band splitting (the expensive part) is shared.
- At 48kHz with all features enabled, the full pipeline still runs at ~110x real-time. Even stereo 48kHz runs at 82x real-time.
- VoiceDetector is extremely cheap (~2µs for 10ms at 16kHz) since it only runs the spectral analysis without the Wiener filter.
- Higher sample rates cost more because the 10ms frame size grows (160 samples at 16kHz vs 480 at 48kHz), and AEC3's internal processing scales with it.
