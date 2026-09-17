Experimental sherpa-ONNX 1.13.4 CPU tuning, first public build.

This is an independently maintained build, not an official k2-fsa release.
Tested on Ubuntu 24.04 x86-64 with CPython 3.12. Requires glibc >= 2.38,
GLIBCXX_3.4.32, and libasound.so.2. No Windows, macOS, ARM, older Linux or other
Python binaries are included. The optimization is opt-in through the provider
configuration file; install the wheel and apply the documented CPU profile.

The exact tested wheel reduced Orukeet's five-second native median from 245.28
to 112.22 ms; tuned Parakeet measured 152.17 ms in twelve alternating-order rounds.
Orukeet text was unchanged. These results cover one host and bounded fixtures.

Assets include the wheel, patched source distribution, full native build source
bundle, dependency license notices, exact patch, sample config, checksums,
provenance and anonymized timing data. The wheel includes upstream dependencies
with their own licenses, including GPLv3 eSpeak NG; see NOTICE.txt and the supplied
corresponding sources. No model weights, user recordings or transcripts are shipped.

See the repository README for the exact install command, compatibility details,
RealtimeSTT integration, and measured limits.
