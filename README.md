# sherpa-ONNX CPU tuning

Experimental, independently maintained CPU-session patch and binary build of
[sherpa-ONNX 1.13.4](https://github.com/k2-fsa/sherpa-onnx/tree/v1.13.4).
This is not an official k2-fsa release. The initial release is intentionally
limited to the platform on which its binary was tested.

## Download and compatibility

[Release v1.13.4-cpu.1](https://github.com/KoljaB/sherpa-onnx-cpu-tuning/releases/tag/v1.13.4-cpu.1)
contains the tested wheel, patched sdist, native build sources, dependency notices,
configuration, provenance, benchmark measurements, and SHA256 checksums.

**Tested:** Ubuntu 24.04, Linux x86-64, CPython 3.12, CPU inference.
The binary requires glibc >= 2.38, libstdc++ with GLIBCXX_3.4.32, and
`libasound.so.2` (Ubuntu 24.04 package `libasound2t64`). It is not a portable
manylinux wheel; Windows, macOS, ARM, older distributions, and other Python
versions are not supported by this binary release.

The model weights are separate and are not included. The native wheel also
contains upstream TTS dependencies, including GPLv3 eSpeak NG. See [NOTICE](NOTICE)
and the release's dependency notices and corresponding build sources; the
upstream Apache license alone does not describe every bundled dependency.

## Install

Use a Python 3.12 virtual environment. Install the exact wheel with a pinned hash:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install numpy "https://github.com/KoljaB/sherpa-onnx-cpu-tuning/releases/download/v1.13.4-cpu.1/sherpa_onnx-1.13.4%2Borukeet.cpu1-cp312-cp312-linux_x86_64.whl#sha256=1c781606aa4e4e261e48b5e4972d6f5a85c89e097cac52ec803cbd6fe9aaa99f"
python -c 'from importlib.metadata import version; import sherpa_onnx; print(version("sherpa-onnx"))'
```

The reported distribution version must be `1.13.4+orukeet.cpu1`. The wheel itself
retains sherpa's upstream module/API names. Installing it replaces the
`sherpa-onnx` distribution in that environment; it does not change model weights.
The version is a local-version build downloadable from GitHub, not from PyPI.

The patch is opt-in. To enable it, save [cpu-sessions.conf](examples/cpu-sessions.conf)
as a local file and pass its absolute path using sherpa's existing provider field:

```text
cpu:/absolute/path/cpu-sessions.conf
```

The example config uses encoder/decoder/joiner thread counts **7/1/1**, inter-op
threads **1**, and disables both intra-op and inter-op spinning. These component
values override `num_threads`. Plain `provider="cpu"` keeps the upstream settings.
Choose the encoder count for available cores and concurrent workloads; seven is
the measured setting for one host, not an automatic hardware optimum.
**Stock sherpa 1.13.4 ignores the new keys. Verify the distribution version first.**

## RealtimeSTT integration

The following public source revision includes Orukeet's pinned model installer
and adapter. Use a fresh environment; install RealtimeSTT, then the patched wheel
from the command above:

```bash
python -m pip install "RealtimeSTT[server,sherpa-onnx] @ git+https://github.com/KoljaB/RealtimeSTT.git@777727553eedfa19aead15337ce66bab549add3f"
stt-install-sherpa-models --root ./models/sherpa-onnx --model orukeet
```

```python
from importlib.metadata import version
from pathlib import Path
from RealtimeSTT import AudioToTextRecorder

if version("sherpa-onnx") != "1.13.4+orukeet.cpu1":
    raise RuntimeError("Install the tested CPU-tuning wheel first")

config = Path("cpu-sessions.conf").resolve(strict=True)
recorder = AudioToTextRecorder(
    transcription_engine="sherpa_onnx_parakeet",
    model="oruk/orukeet",
    download_root="./models/sherpa-onnx",
    device="cpu",
    language="en",
    transcription_engine_options={
        "provider": f"cpu:{config}",
        "verify_model_files": True,
    },
)
```

For the production server, pass the same dictionary through `--engine-options`.
Language and live-ASR choices remain application settings. This runtime release
provides no automatic thread tuning and changes no RealtimeSTT defaults.

## Why this patch exists

The stock NeMo transducer loader uses the same thread count for three separate
native sessions. Their waiting worker pools can compete for the same cores.
The patch exposes `EncoderNumThreads`, `DecoderNumThreads`, `JoinerNumThreads`,
`InterOpNumThreads`, and `AllowSpinning` in the existing provider config.

On one Linux host, a control holding all three pools at seven threads measured
**662.35 ms with spinning and 107.17 ms without spinning** for five-second audio.
The selected 7/1/1 configuration was verified in twelve alternating-order rounds,
with identical inputs, fixed CPU affinity, two warmups per duration, and inactive
benchmark processes stopped to avoid competing pools:

| Native median | 3-second audio | 5-second audio |
| --- | ---: | ---: |
| Stock Orukeet, two threads per session | 154.47 ms | 245.28 ms |
| Patched Orukeet, 7/1/1, no spinning | 74.18 ms | 112.22 ms |
| Tuned Parakeet, onnx-asr backend | 100.20 ms | 152.17 ms |

Orukeet transcripts were identical across both runtime configurations. The real
ASR API median fell from 252.27 to 120.09 ms. Ten Preview events including
continuation succeeded. These are bounded ASR measurements, not a broad accuracy
study or an audible assistant-response benchmark. The Parakeet row uses a
different model/backend combination. [Measurement data](benchmarks/2026-09-17.json)
contains timings only, without user audio or transcripts.

## Sources and verification

- [Exact native patch](patches/cpu-sessions.patch)
- [Guarded patch generator](tools/prepare_cpu_session_build.py)
- [Rebuild instructions](BUILDING.md)
- [Artifact and live-runtime provenance](release/provenance.json)
- [Release checksums](release/SHA256SUMS)
- [Benchmark worker](tools/benchmark_cpu_sessions.py)

The public wheel is byte-for-byte the artifact verified against the live ASR
runtime. All 14 installed sherpa package files matched the wheel. The unchanged
bundled ONNX Runtime is 1.27.0. The release includes the exact patched source
archive plus the native dependency source trees and notices needed to inspect
and reproduce the build.

Upstream integration is the preferred long-term path; no upstream pull request
has been submitted as part of this release.
