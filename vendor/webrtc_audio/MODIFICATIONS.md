# Modifications to vendored WebRTC audio source

Source: [ewan-xu/AEC3](https://github.com/ewan-xu/AEC3)

## Changes

1. **Directory restructuring**: Flattened `base/` subdirectories (`rtc_base/`, `system_wrappers/`, `abseil/`, `jsoncpp/`) to top level so include paths resolve correctly (e.g. `#include "rtc_base/checks.h"`).

2. **`audio_processing/splitting_filter_c.c`**: Replaced `#include "rtc_base/checks.h"` (C++ header) with C-compatible equivalents (`<stddef.h>`, `<assert.h>`, macro definitions for `RTC_DCHECK_LE` and `RTC_DCHECK_EQ`).

3. **`third_party/jsoncpp/json.h`**: Created mapping file so `#include "third_party/jsoncpp/json.h"` resolves to the vendored jsoncpp header.

4. **CMakeLists.txt**: Replaced WebRTC's GN build with CMake. Builds all required sources as a static library with platform-specific SIMD selection (SSE2 on x86_64, NEON on aarch64).

5. **Excluded files**: Removed unit tests (`*_unittest.cc`), benchmarks (`*_benchmark.cc`), MIPS-specific code (`ooura_fft_mips.cc`), Android cpu features (`cpu_features_android.c`), and pffft wrapper (unused).

6. **Noise suppression (`audio_processing/ns/`)**: Added WebRTC's modern noise suppressor from upstream `modules/audio_processing/ns/`. Include paths rewritten from `modules/audio_processing/` to `audio_processing/` and `api/array_view.h` to `rtc_base/array_view.h` to match the vendored tree layout.

7. **Ooura FFT 256 (`common_audio/third_party/ooura/fft_size_256/`)**: Added the 256-point FFT implementation required by the noise suppressor (separate from the existing Ooura FFT used by AEC3).

8. **`audio_processing/ns/noise_suppressor.h`**: Added public `GetSpeechProbability()` method that returns the prior speech probability (0.0-1.0) averaged across channels. The value was already computed internally by `SpeechProbabilityEstimator` but not exposed.

9. **AGC2 (`audio_processing/agc2/`)**: Added WebRTC's AGC2 (Automatic Gain Control) from upstream `modules/audio_processing/agc2/`. Include paths rewritten from `modules/audio_processing/` to `audio_processing/` and `common_audio/include/audio_util.h` to `audio_processing/include/audio_util.h`. Unqualified `rtc::` namespace references (SafeClamp, CheckedDivExact, StringBuilder, etc.) resolved via `compat.h` shim. Excluded `vad_wrapper.cc`, `cpu_features.cc`, and `rnn_vad/` directory (we use NoiseSuppressor for VAD instead). Created minimal shim headers for upstream API dependencies: `api/audio/audio_processing.h` (Config structs only), `api/audio/audio_view.h` (DeinterleavedView/MonoView), `api/audio/audio_frame.h` (kDefaultAudioBuffersPerSec), `api/field_trials_view.h` (no-op), `api/array_view.h` (redirect to rtc_base/array_view.h), `audio_processing/include/audio_frame_view.h` (AudioFrameView wrapper), and `audio_processing/agc2/agc2_testing_common.h` (limiter constants only).

10. **RNN VAD (`audio_processing/agc2/rnn_vad/`)**: Added WebRTC's RNN-based Voice Activity Detector from upstream `modules/audio_processing/agc2/rnn_vad/`. This is the same trained neural network used in Chrome for speech detection. Include paths rewritten. Also added `vad_wrapper.cc/h` (resamples input to 24kHz and runs the RNN) and `cpu_features.cc/h` (SIMD detection for optimized inference).

11. **PushResampler (`audio_processing/resampler/push_resampler.cc/h`)**: Added from upstream `common_audio/resampler/`. Required by the RNN VAD wrapper to resample audio to 24kHz. Removed the `InterleavedView` overload of `Resample()` (not needed, and depends on `Deinterleave`/`Interleave` helpers we don't have). Include paths rewritten.

12. **rnnoise (`third_party/rnnoise/src/`)**: Added RNN model weights (`rnn_vad_weights.h/cc`) and activation functions (`rnn_activations.h`) from chromium's `third_party/rnnoise/src/`. These contain the trained model parameters for the RNN VAD.

13. **pffft (`third_party/pffft/src/`)**: Added the PFFFT (Pretty Fast FFT) library from chromium's `third_party/pffft/src/`. Required by the RNN VAD's spectral feature extraction. Also added `pffft_wrapper.cc` to the build (was already vendored but not compiled since existing code didn't need it).

14. **cpu_info (`rtc_base/cpu_info.h/cc`)**: Added from upstream. Provides CPU feature detection (SSE2, AVX2, NEON) used by the RNN VAD for SIMD-optimized inference.

15. **function_view (`api/function_view.h`)**: Added from upstream. Lightweight non-owning callable wrapper used by RNN VAD internals.

16. **ArrayView extensions (`rtc_base/array_view.h`)**: Added `subspan()`, `subspan<Offset, Count>()`, `first<N>()`, `rbegin()`/`rend()` methods to the existing `rtc::ArrayView` class. These are `std::span`-style APIs used extensively by the upstream RNN VAD code.

17. **Compat includes header (`compat_includes.h`)**: Added a header force-included via compiler flags for all C++ sources (`-include compat_includes.h` on GCC/Clang, `/FI` on MSVC). Provides `<cstddef>`, `<cstdint>`, `<memory>`, `<vector>`, `<algorithm>`, and `<functional>` which older GCC (manylinux2014 devtoolset-10) does not provide transitively. C sources get `-include stddef.h` instead.

18. **`audio_processing/logging/wav_header.cc`**: Removed explicit `WavHeader(const WavHeader&) = default` and `operator=` declarations (which prevent aggregate initialization in C++20) and replaced `rtc::MsanUninitialized<WavHeader>({})` with `WavHeader header = {}`. The copy/assignment declarations were redundant for a trivially copyable struct, and `MsanUninitialized` is a no-op outside sanitizer builds.
