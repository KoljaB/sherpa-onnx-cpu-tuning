# Updating the tested CPU runtime

This procedure upgrades an isolated candidate, measures it against the last
working runtime, and promotes the exact verified artifact. The paired runner is
implemented; scheduled release detection, PR creation and automatic deployment
are not configured.

## 1. Inspect the upstream change

Pin a release tag or commit and inspect changes to native session options,
NeMo loading, feature normalization, Python packaging and bundled ONNX Runtime.
Check whether upstream already supports any custom behavior. Version 1.13.8
supports `SessionConfig.*` forwarding, making the no-spinning profile available
with official wheels. Per-component thread counts remain a custom feature, but
were not necessary to beat the previous production configuration in this test.

Use official packages first. If a remaining patch is needed, apply it to a fresh
pinned source tree with strict expected-fragment checks, review the diff and
build a new artifact. Do not simply change the guard's version: the 1.13.8
source-only review also found a changed profiling anchor. The legacy generator
remains intentionally restricted to 1.13.4; no patched 1.13.8 binary was built.

## 2. Prepare a candidate without modifying the working environment

Create a separate venv using the intended Python version. Download exact wheels,
verify their SHA256 against the publisher's metadata and retain them. For the
validated official candidate both packages are pinned to 1.13.8:

```bash
python -m pip download --only-binary=:all: --no-deps --dest artifacts \
  "sherpa-onnx==1.13.8" "sherpa-onnx-core==1.13.8"
```

Keep the RealtimeSTT wheel, model hashes, fixture audio and unrelated dependencies
identical between environments. Install the downloaded artifacts and verify
imports resolve to the candidate. Record sherpa's bundled native ORT version;
the Python `onnxruntime` distribution is a separate package. Preserve the old
venv for rollback. Dependency paths borrowed through `.pth` must remain available.

The tested server uses the profile in `examples/official-cpu-sessions.conf`.
Choose threads based on available affinity and workload; test a small set such
as 2, 4 and 7 only where those cores are available. Do not claim seven is portable.

## 3. Run the paired native comparison on a fixed Linux host

The examples contain absolute-path placeholders. Create one engine config per
variant using `examples/official-benchmark.json` as the candidate template and
the previous runtime's actual config for the baseline. Update model/config
paths and CPU affinity. Set each Python, config and worker path in a copy of
`examples/benchmark-manifest.json`. Supply an approved mono 16-kHz PCM16 WAV
containing at least five seconds of audio. Keep the durations at 3 and 5 seconds.

```bash
python3 tools/compare_cpu_runtimes.py /path/to/manifest.json \
  /path/to/new-results.json --rounds 20
```

The runner warms each duration twice, alternates forward/reverse variant order,
and suspends only its own inactive worker processes so their pools cannot
contaminate another measurement. It saves every timing and transcript, plus
median, nearest-rank p95, parity checks, versions and a short idle-CPU sample.
**Raw output contains transcripts and machine paths; keep it private.** Share a
sanitized timing-only report like `benchmarks/2026-09-18.json`.

Check every transcript difference and the median/p95 for each duration. A
changed transcript is not automatically an improvement or regression: review
against the audio. Repeat the selected comparison under a declared bounded
contention workload. The 2026-09-18 test used four benchmark-owned workers on
SMT siblings 0,2,6,8, each busy for 25 ms of a 50-ms cycle; this is synthetic
load, not a recording of real TTS use. Terminate all owned load workers afterward.

A shared GitHub-hosted runner is suitable for build, import and configuration
checks, not authoritative latency acceptance. Use the same fixed benchmark host
for version comparisons. Do not broaden the suite after these checks pass
unless a change or unresolved concern justifies it.

## 4. Promote and verify

Before restarting, ensure client activity can tolerate the interruption and save
the exact current launch/config. Record authenticated API timings on the old
runtime with one warmup and 20 measured requests. Switch only the runtime Python
and selected provider/thread settings using a new reversible service override.
Require a new PID, authenticated readiness and unchanged model/live-ASR contract.
Verify installed package hashes against the exact tested wheels and confirm the
mapped native libraries belong to the candidate.

Repeat the API fixture and compare transcripts, decode timing and wall timing.
Run the actual Preview/Live client smoke with a continuation, checking candidate
identity, one inference attempt, empty/error behavior and unchanged Final policy.
Restore the old override immediately if readiness, correctness or latency fails.
Record before/after API results as sequential; the native test supplies the paired
comparison. Neither proves audible assistant latency.

## 5. Record the selection

Keep versions, hashes, configuration, package parity, performance results,
limitations and rollback instructions together. Preserve all old public assets.
Official wheel use needs no new custom binary release; if a custom binary is
required, publish a new immutable version with corresponding sources and notices
only after that exact artifact passes acceptance. Do not upload under upstream's
PyPI package name.

A future CI workflow can detect releases, open a candidate change and run the
cheap checks automatically. Promotion should depend on fixed-host benchmark and
live acceptance evidence; upstream version ordering alone is not a performance
gate. Enabling that automation is a separate configuration step.
